"""Sample transcripts for manual human review and write a review sheet (Markdown + CSV for your verdicts)."""
from __future__ import annotations

import json
import pathlib
import random

import pandas as pd


def render(path: pathlib.Path) -> str:
    lines = []
    for raw in path.read_text().splitlines():
        ev = json.loads(raw)
        t = ev["type"]
        if t == "start":
            lines.append(f"**{ev['scenario']} | condition {ev['condition']} | seed {ev['seed']} | {ev['mode']}**")
        elif t == "injection":
            lines.append(f"- r{ev['round']} INJECTION {ev['sender']}->{ev['to']}: {ev['text'][:300]}")
        elif t == "action":
            status = "OK" if ev["executed"] else f"BLOCKED({ev.get('blocked_by')}: {ev.get('reason', '')})"
            lines.append(f"- r{ev['round']} {ev['agent']} {ev['name']} {json.dumps(ev['input'])[:300]} -> {status}")
        elif t in ("review", "monitor", "deal", "deal_held", "approval_budget_exhausted"):
            keep = {k: v for k, v in ev.items() if k not in ("t", "usage", "state")}
            lines.append(f"- {t}: {json.dumps(keep)[:300]}")
        elif t == "summary":
            lines.append(f"- SCORE: violations={ev['violations']} {ev['violation_ids']} welfare_loss={ev['welfare_loss']:.2f} "
                         f"burden={ev['reviewer_burden']} fp={ev['false_positives']} completed={ev['completed']}")
    return "\n".join(lines)


def spot_check(run_dir: str, n: int = 12, seed: int = 0) -> pathlib.Path:
    run = pathlib.Path(run_dir)
    files = sorted((run / "transcripts").glob("*.jsonl"))
    rng = random.Random(seed)
    # stratify: half adversarial, spread over conditions
    adv = [f for f in files if any(a in f.name for a in ("overreach", "injection", "extraction", "collusion"))]
    ben = [f for f in files if f not in adv]
    pick = rng.sample(adv, min(len(adv), n // 2)) + rng.sample(ben, min(len(ben), n - n // 2))
    out = run / "spotcheck"
    out.mkdir(exist_ok=True)
    md = ["# Spot-check sheet", "", "For each transcript: does the automatic score match your reading? Record verdicts in spotcheck.csv.", ""]
    for f in pick:
        md += [render(f), ""]
    (out / "spotcheck.md").write_text("\n".join(md))
    pd.DataFrame({"transcript": [f.name for f in pick], "auto_score_correct (y/n)": "", "violation_missed_or_wrong": "",
                  "welfare_judgement_ok (y/n)": "", "notes": ""}).to_csv(out / "spotcheck.csv", index=False)
    return out
