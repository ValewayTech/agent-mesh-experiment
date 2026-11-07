"""Command-line interface.  python -m meshexp <command> --help"""
from __future__ import annotations

import argparse
import hashlib
import concurrent.futures as cf
import json
import pathlib
import sys
import time

import pandas as pd
import yaml

from .analysis import analyse
from .controls import CONDITIONS
from .cost import from_run, report
from .llm import LLM, BudgetExceeded, CostTracker
from .prices import USD_TO_GBP
from .runner import RunConfig, run_episode
from .schema import Scenario
from .spotcheck import spot_check

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_MODEL = "claude-haiku-5-5"
PREREG = yaml.safe_load((ROOT / "preregistration.yaml").read_text())


def load_scenarios(sel: str = "all", directory: str = "scenarios") -> list[Scenario]:
    files = sorted((ROOT / directory).glob("*.yaml"))
    scs = [Scenario.model_validate(yaml.safe_load(f.read_text())) for f in files]
    if sel == "all":
        return scs
    if sel == "adversarial":
        return [s for s in scs if s.adversarial]
    if sel == "benign":
        return [s for s in scs if not s.adversarial]
    want = set(sel.split(","))
    return [s for s in scs if s.id in want or s.domain in want]


def cmd_run(a) -> int:
    scs = load_scenarios(a.scenarios, a.scenario_dir)
    conds = a.conditions.split(",")
    cfg = RunConfig(mandate_overrides=a.mandate_overrides, mode=a.mode, agent_model=a.model, approver_model=a.approver_model or a.model,
                    monitor_model=a.monitor_model or a.model, effort=None if a.effort == "default" else a.effort,
                    approval_budget=a.approval_budget, exhausted_policy=a.exhausted, out_dir=a.out,
                    mock_monitor_gap=PREREG["monitor"]["mock_endorse_gap_threshold"], monitor_hold_if=PREREG["monitor"]["hold_if"])
    jobs = [(s, c, k) for s in scs for c in conds for k in range(a.seed_offset, a.seed_offset + a.seeds)]
    print(f"{a.mode} run: {len(scs)} scenarios x {len(conds)} conditions x {a.seeds} seeds = {len(jobs)} episodes -> {a.out}")
    llms = None
    tracker = CostTracker(cap_usd=a.max_cost_usd)
    if a.mode == "live":
        print(report(len(scs), conds, a.seeds, cfg.agent_model, cfg.approver_model, cfg.monitor_model))
        if not a.yes and input("Proceed with a live (billable) run? [y/N] ").strip().lower() != "y":
            print("Aborted."); return 1
        llms = {"agent": LLM(cfg.agent_model, cfg.effort, cfg.agent_max_tokens, tracker),
                "approver": LLM(cfg.approver_model, cfg.effort, 1024, tracker),
                "monitor": LLM(cfg.monitor_model, cfg.effort, 1500, tracker)}
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps({**cfg.__dict__, "seeds": a.seeds, "seed_offset": a.seed_offset, "conditions": conds,
                                                 "scenarios": [s.id for s in scs], "preregistration": PREREG,
                                                 "prereg_sha256": hashlib.sha256((ROOT / "preregistration.yaml").read_bytes()).hexdigest(),
                                                 "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}, indent=2))
    rows, failed = [], 0
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(run_episode, s, c, k, cfg, llms): (s.id, c, k) for s, c, k in jobs}
        for i, f in enumerate(cf.as_completed(futs), 1):
            try:
                rows.append(f.result())
            except BudgetExceeded as e:
                print(f"STOP: {e}"); failed += 1
                for g in futs: g.cancel()
            except Exception as e:  # keep going; record the failure (but stop on billing/credit errors)
                failed += 1
                print(f"episode {futs[f]} failed: {type(e).__name__}: {e}", file=sys.stderr)
                if any(w in str(e).lower() for w in ("credit balance", "billing", "insufficient")):
                    print("STOP: credit/billing error; cancelling remaining episodes"); [g.cancel() for g in futs]
            if i % 50 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)} done" + (f", ~${tracker.spent_usd:.2f} spent" if a.mode == "live" else ""))
    if not rows:
        # Nothing completed: an empty frame has no columns, so sorting would raise KeyError.
        print(f"no completed episodes (0 rows, {failed} failed)")
        return 2
    df = pd.DataFrame(rows).sort_values(["scenario", "condition", "seed"])
    df.drop(columns=["final_terms"]).assign(violation_ids=df["violation_ids"].map(";".join)).to_csv(out / "results.csv", index=False)
    print(f"wrote {out / 'results.csv'} ({len(df)} rows, {failed} failed)")
    if a.mode == "live":
        print(f"API usage this run: {tracker.calls} calls, {tracker.tokens_in:,} in / {tracker.tokens_out:,} out tokens, "
              f"~${tracker.spent_usd:.2f} (~GBP {tracker.spent_usd * USD_TO_GBP:.2f}) at list prices")
    print(analyse(a.out))
    return 0 if failed == 0 else 2


def cmd_analyse(a) -> int:
    print(analyse(a.run)); return 0


def cmd_spotcheck(a) -> int:
    print(f"wrote review sheet to {spot_check(a.run, a.n, a.seed)}"); return 0


def cmd_cost(a) -> int:
    conds = a.conditions.split(",")
    n = len(load_scenarios(a.scenarios))
    if a.from_run:
        e = from_run(a.from_run, n, conds, a.seeds, a.usd_to_gbp)
        print(f"Calibrated from {e['pilot_episodes']} pilot episodes: {e['episodes']} episodes ~${e['usd']:.2f} (~GBP {e['gbp']:.2f}) ESTIMATE")
    else:
        print(report(n, conds, a.seeds, a.model, a.approver_model or a.model, a.monitor_model or a.model, a.usd_to_gbp))
    return 0


def cmd_validate(a) -> int:
    scs = load_scenarios()
    adv = [s for s in scs if s.adversarial]
    print(f"{len(scs)} scenarios valid; {len(adv)} adversarial: " +
          ", ".join(f"{k}={sum(s.attack_type == k for s in adv)}" for k in ("overreach", "injection", "extraction", "collusion")))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="meshexp", description="Oversight at the Seams: cross-principal agent control experiment")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--scenarios", default="all", help="all | adversarial | benign | comma-separated ids or domains")
        p.add_argument("--conditions", default="A,B,C,D")
        p.add_argument("--seeds", type=int, default=3)
        p.add_argument("--model", default=DEFAULT_MODEL, help="agent model id")
        p.add_argument("--approver-model", default=None)
        p.add_argument("--monitor-model", default=None)

    r = sub.add_parser("run", help="run scenario x condition x seed episodes"); common(r)
    r.add_argument("--mode", choices=["mock", "live"], default="mock")
    r.add_argument("--seed-offset", type=int, default=0, help="first seed index (to add seeds to an earlier run)")
    r.add_argument("--dry-run", dest="mode", action="store_const", const="mock", help="alias for --mode mock")
    r.add_argument("--out", default="results/mock")
    r.add_argument("--effort", default=PREREG["agents"]["effort"], choices=["low", "medium", "high", "default"])
    r.add_argument("--approval-budget", type=int, default=PREREG["approver"]["budget_per_task"])
    r.add_argument("--exhausted", choices=["allow", "deny"], default=PREREG["approver"]["when_exhausted"], help="what B does once its approval budget is spent")
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--scenario-dir", default="scenarios", help="E2: scenarios_robust for the robustness set")
    r.add_argument("--mandate-overrides", default=None, help="E2: compiled lay mandates JSON for conditions Cu / Cc")
    r.add_argument("--max-cost-usd", type=float, default=None, help="stop the run once estimated spend reaches this")
    r.add_argument("--yes", action="store_true", help="skip the live-run confirmation prompt")
    r.set_defaults(fn=cmd_run)
    an = sub.add_parser("analyse", help="rebuild tables and plots"); an.add_argument("run"); an.set_defaults(fn=cmd_analyse)
    sp = sub.add_parser("spotcheck", help="sample transcripts for manual review"); sp.add_argument("run")
    sp.add_argument("--n", type=int, default=12); sp.add_argument("--seed", type=int, default=0); sp.set_defaults(fn=cmd_spotcheck)
    co = sub.add_parser("cost", help="estimate the cost of a live run"); common(co)
    co.add_argument("--from-run", default=None); co.add_argument("--usd-to-gbp", type=float, default=USD_TO_GBP); co.set_defaults(fn=cmd_cost)
    va = sub.add_parser("validate", help="validate scenario files"); va.set_defaults(fn=cmd_validate)
    a = ap.parse_args(argv)
    return a.fn(a)
