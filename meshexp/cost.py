"""Cost estimator for a live run. Prices are Anthropic's published list prices; everything here is an ESTIMATE.

Two methods:
  * parametric: token assumptions below (deliberately on the high side, no prompt caching);
  * calibrated: --from-run results/<pilot> extrapolates from real usage logged in a small live pilot.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass

from .prices import PRICE_SOURCE, USD_TO_GBP, cost_usd


@dataclass
class Assumptions:
    agents_per_episode: float = 2.88      # 44 of 50 scenarios have three principals
    rounds_used: float = 3.0              # of max 4 (most deals settle by round 2-3, plus a settlement round)
    base_prompt_tokens: int = 2300        # system prompt + mandate + tool definitions + tool-use system prompt
    growth_per_turn: int = 450            # history added per prior turn (messages, tool calls, results, thinking)
    output_per_turn: int = 600            # visible output + thinking at effort=low (conservative)
    approver_calls: float = 3.0           # condition B: approval budget k=3
    approver_in: int = 1300
    approver_out: int = 250
    monitor_in: int = 3500                # condition D: protected principal, whole transcript
    monitor_out: int = 350
    honest_principals: float = 1.0       # prereg v2: monitor judges the protected principal only


def episode_tokens(a: Assumptions, condition: str) -> dict:
    turns = int(round(a.rounds_used))
    agent_in = sum(a.base_prompt_tokens + k * a.growth_per_turn for k in range(turns)) * a.agents_per_episode
    agent_out = turns * a.output_per_turn * a.agents_per_episode
    out = {"agent_in": agent_in, "agent_out": agent_out, "approver_in": 0, "approver_out": 0, "monitor_in": 0, "monitor_out": 0}
    if condition == "B":
        out["approver_in"], out["approver_out"] = a.approver_calls * a.approver_in, a.approver_calls * a.approver_out
    if condition == "D":
        out["monitor_in"], out["monitor_out"] = a.honest_principals * a.monitor_in, a.honest_principals * a.monitor_out
    return out


def estimate(n_scenarios: int, conditions: list[str], seeds: int, agent_model: str, approver_model: str, monitor_model: str,
             a: Assumptions | None = None, usd_to_gbp: float = USD_TO_GBP) -> dict:
    a = a or Assumptions()
    tot_in = tot_out = usd = 0.0
    for c in conditions:
        t = episode_tokens(a, c)
        n = n_scenarios * seeds
        usd += n * (cost_usd(agent_model, t["agent_in"], t["agent_out"]) + cost_usd(approver_model, t["approver_in"], t["approver_out"])
                    + cost_usd(monitor_model, t["monitor_in"], t["monitor_out"]))
        tot_in += n * (t["agent_in"] + t["approver_in"] + t["monitor_in"])
        tot_out += n * (t["agent_out"] + t["approver_out"] + t["monitor_out"])
    return {"episodes": n_scenarios * len(conditions) * seeds, "input_tokens": int(tot_in), "output_tokens": int(tot_out),
            "usd": usd, "gbp": usd * usd_to_gbp}


def from_run(run_dir: str, n_scenarios: int, conditions: list[str], seeds: int, usd_to_gbp: float = USD_TO_GBP) -> dict:
    """Extrapolate from a live pilot's logged usage (mean cost per episode per condition)."""
    per: dict[str, list[float]] = {}
    for f in pathlib.Path(run_dir, "transcripts").glob("*.jsonl"):
        last = json.loads(f.read_text().strip().splitlines()[-1])
        if last.get("mode") == "live":
            per.setdefault(last["condition"], []).append(last["cost_usd_est"])
    if not per:
        raise SystemExit(f"No live transcripts in {run_dir}; run a small live pilot first.")
    allmean = sum(sum(v) for v in per.values()) / sum(len(v) for v in per.values())
    usd = sum((sum(per[c]) / len(per[c]) if c in per else allmean) * n_scenarios * seeds for c in conditions)
    return {"episodes": n_scenarios * len(conditions) * seeds, "usd": usd, "gbp": usd * usd_to_gbp,
            "pilot_episodes": sum(len(v) for v in per.values())}


def report(n_scenarios, conditions, seeds, agent_model, approver_model, monitor_model, usd_to_gbp=USD_TO_GBP) -> str:
    lines = [f"Cost ESTIMATE (list prices from {PRICE_SOURCE}; USD->GBP {usd_to_gbp}; no caching or batch discounts assumed)",
             f"Models: agents={agent_model}, approver={approver_model}, monitor={monitor_model}",
             f"Scenarios={n_scenarios}, conditions={','.join(conditions)}"]
    for s in sorted({1, 3, 5, 10, seeds}):
        e = estimate(n_scenarios, conditions, s, agent_model, approver_model, monitor_model, usd_to_gbp=usd_to_gbp)
        mark = "  <- selected" if s == seeds else ""
        lines.append(f"  seeds={s:>2}: {e['episodes']:>5} episodes, ~{e['input_tokens']/1e6:.1f}M in / {e['output_tokens']/1e6:.1f}M out "
                     f"tokens, ~${e['usd']:.2f} (~GBP {e['gbp']:.2f}){mark}")
    lines.append("Treat these as rough: real token use depends on how chatty the agents are. Calibrate with a pilot: "
                 "`python -m meshexp cost --from-run results/pilot`.")
    return "\n".join(lines)
