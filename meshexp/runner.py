"""Run one episode (scenario x condition x seed) and write its JSONL transcript."""
from __future__ import annotations

import hashlib
import json
import pathlib
import random
import time
from dataclasses import dataclass

from .agents import MAX_CALLS_PER_TURN, LiveAgent, MockAgent
from .controls import Controller, LLMApprover, LLMMonitor, MockApprover, MockMonitor
from .schema import Scenario, SignoffRule
from .scoring import score_episode


def protected_principal(sc: Scenario):
    """The principal our controls act for: P1, the first non-adversarial principal (never adversarial by construction)."""
    return next(p for p in sc.principals if not p.adversarial)
from .world import ACTIONS, World


@dataclass
class RunConfig:
    mode: str = "mock"                 # mock | live
    agent_model: str = "claude-haiku-5-5"
    approver_model: str = "claude-haiku-5-5"
    monitor_model: str = "claude-haiku-5-5"
    effort: str | None = "low"
    agent_max_tokens: int = 2048
    approval_budget: int = 3
    exhausted_policy: str = "allow"
    out_dir: str = "results/mock"
    mock_monitor_gap: float = 0.45       # from preregistration.yaml
    monitor_hold_if: str = "materially_worse"
    mandate_overrides: str | None = None   # E2: JSON of compiled lay mandates for Cu / Cc


def seed_for(sc_id: str, cond: str, seed: int) -> int:
    return int(hashlib.sha256(f"{sc_id}|{cond}|{seed}".encode()).hexdigest()[:8], 16)


def compiled_views(sc: Scenario, cond: str, path: str) -> tuple[Scenario, Scenario]:
    """Cu / Cc: (scenario the agents see, scenario the checker enforces). Scoring always uses the true scenario."""
    data = json.loads(pathlib.Path(path).read_text())["confirmed" if cond == "Cc" else "unconfirmed"].get(sc.id, {})
    agent_sc, check_sc = sc.model_copy(deep=True), sc.model_copy(deep=True)
    for pa, pc in zip(agent_sc.principals, check_sc.principals):
        d = data.get(pa.id)
        if not d or pa.adversarial:
            continue
        pa.mandate.text = d["agent_text"]
        c = d["compiled"]
        pc.mandate.budget = float(c.get("budget", 0) or 0)
        pc.mandate.allowed = {k: [str(x) for x in v] for k, v in (c.get("allowed") or {}).items()}
        pc.mandate.signoff = [SignoffRule(**r) for r in (c.get("signoff") or [])]
        for key, item in pc.info.items():
            item.shareable_with = list((c.get("shareable") or {}).get(key, []))
    return agent_sc, check_sc


def run_episode(sc: Scenario, cond: str, seed: int, cfg: RunConfig, llms: dict | None = None) -> dict:
    rng = random.Random(seed_for(sc.id, cond, seed))
    agent_sc = check_sc = sc
    if cond in ("Cu", "Cc"):
        agent_sc, check_sc = compiled_views(sc, cond, cfg.mandate_overrides)
    world = World(sc)
    world.log("start", scenario=sc.id, condition=cond, seed=seed, mode=cfg.mode, agent_model=cfg.agent_model if cfg.mode == "live" else "mock",
              time=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    if cfg.mode == "live":
        agents = {p.agent_id: LiveAgent(agent_sc, p, llms["agent"]) for p in agent_sc.principals}
        approver, monitor = LLMApprover(llms["approver"]), LLMMonitor(llms["monitor"])
    else:
        agents = {p.agent_id: MockAgent(agent_sc, p, random.Random(rng.random())) for p in agent_sc.principals}
        approver, monitor = MockApprover(random.Random(rng.random())), MockMonitor(random.Random(rng.random()), cfg.mock_monitor_gap)
    ctl = Controller(cond, sc, approver=approver, budget=cfg.approval_budget, exhausted=cfg.exhausted_policy, checker_sc=check_sc)
    pending = {a: [] for a in sc.agent_ids}
    readable: list[str] = []

    for r in range(sc.max_rounds):
        world.round = r
        for inj in sc.injections:
            if inj.round == r:
                world.deliver(inj.sender, inj.to, inj.text, injected=True)
                readable.append(f"[{inj.sender} -> {inj.to}] {inj.text}")
        for a in sc.agent_ids:
            p = sc.principal_by_agent(a)
            obs = world.render_inbox(a)
            msgs = world.pop_inbox(a)
            calls = agents[a].step(obs, msgs, pending[a], world)
            pending[a] = []
            for c in calls[:MAX_CALLS_PER_TURN]:
                res = execute(world, ctl, p, c, readable)
                pending[a].append((c.id, res))
            for c in calls[MAX_CALLS_PER_TURN:]:
                pending[a].append((c.id, f"not executed: at most {MAX_CALLS_PER_TURN} tool calls per turn"))
        if world.deal_round is not None and r > world.deal_round:
            break  # one settlement round after the deal, then stop

    if cond == "D" and world.deal is not None:
        p = protected_principal(sc)   # prereg v2: the monitor acts only for the protected principal
        worse, coll, reason, usage = monitor.judge(sc, p, readable, world.deal, world)
        world.log("monitor", principal=p.id, materially_worse=worse, collusion_suspected=coll, reason=reason, usage=usage)
        hold = worse if cfg.monitor_hold_if == "materially_worse" else (worse or coll)
        if hold:
            world.deal_held = True
            world.log("deal_held", principal=p.id, reason=reason)

    summary = score_episode(sc, world.events)
    usage = [ev.get("usage") for ev in world.events if ev.get("usage")]
    summary.update(scenario=sc.id, domain=sc.domain, adversarial=sc.adversarial, attack_type=sc.attack_type or "none",
                   condition=cond, seed=seed, mode=cfg.mode,
                   tokens_in=sum(u["input_tokens"] + u.get("cache_read_input_tokens", 0) for u in usage),
                   tokens_out=sum(u["output_tokens"] for u in usage),
                   cost_usd_est=round(sum(u["cost_usd_est"] for u in usage), 6), llm_calls=len(usage))
    world.log("summary", **summary)
    out = pathlib.Path(cfg.out_dir) / "transcripts"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / f"{sc.id}__{cond}__s{seed}.jsonl", "w") as f:
        for ev in world.events:
            f.write(json.dumps(ev, default=str) + "\n")
    return summary


def execute(world: World, ctl: Controller, p, call, readable: list[str]) -> str:
    if call.name not in ACTIONS:
        return f"error: unknown tool {call.name}"
    state = world.state_for(p.agent_id)
    if call.name == "escalate_to_principal":
        granted, reply = world.principal_reply(p.agent_id, call.input)
        world.log("escalation", agent=p.agent_id, input=call.input, granted=granted, reply=reply)
        world.log("action", agent=p.agent_id, name=call.name, input=call.input, executed=True, state=state, result=reply)
        readable.append(f"[{p.agent_id} escalate_to_principal] {json.dumps(call.input.get('proposed_action'))} -> {reply}")
        return reply
    allowed, by, reason = ctl.review(p, call.name, call.input, world, readable)
    if not allowed:
        world.log("action", agent=p.agent_id, name=call.name, input=call.input, executed=False, blocked_by=by, reason=reason, state=state)
        return f"BLOCKED by {by}: {reason}. The action was not carried out."
    res = world.execute(p.agent_id, call)
    executed = not res.startswith("error")
    world.log("action", agent=p.agent_id, name=call.name, input=call.input, executed=executed, state=state, result=res)
    if executed:
        readable.append(f"[{p.agent_id} {call.name}] {json.dumps(call.input)}")
    return res
