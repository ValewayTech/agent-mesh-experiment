"""E2 offline replay (no API calls). NOT an experimental result: agents in these transcripts did not face condition E,
so this only shows what E's grey-area flags WOULD have raised on actions that were actually taken.

1. For saved runs, count E's grey flags per episode on honest agents' executed agree_terms / send_message actions
   (projected reviewer load), and list executed breaches the code checker cannot see (C-undecidable) and whether a flag fires.
2. For the robustness scenarios, check deterministically that C allows an out-of-mandate admin fee and E flags it.
Usage: python scripts/e2_offline_replay.py
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from meshexp.cli import load_scenarios
from meshexp.controls import grey_flags
from meshexp.mandate import check_action
from meshexp.scoring import action_violations

scen = {s.id: s for s in load_scenarios()}
for run, cond in [("results/live-v1", "A"), ("results/live-v1", "C"), ("results/live-v1", "D"), ("results/live-B-unlimited", "B")]:
    eps = flags = 0; undecidable = []
    for fn in sorted(glob.glob(f"{run}/transcripts/*__{cond}__*.jsonl")):
        evs = [json.loads(l) for l in open(fn) if l.strip()]; sc = scen[evs[0]["scenario"]]; eps += 1
        for e in evs:
            if e["type"] != "action" or not e.get("executed") or e["name"] == "escalate_to_principal":
                continue
            p = sc.principal_by_agent(e["agent"])
            if p.adversarial:
                continue
            fl = grey_flags(sc, p, e["name"], e["input"])
            flags += bool(fl)
            v = action_violations(sc, p, e["name"], e["input"], e["state"])
            if v and not check_action(sc, p, e["name"], e["input"], e["state"]):
                undecidable.append((fn.split("/")[-1], sorted(v), bool(fl)))
    print(f"{run} {cond}: {eps} episodes, {flags} flagged actions ({flags / eps:.2f} per episode); "
          f"executed breaches the checker cannot see: {len(undecidable)}")
    for u in undecidable:
        print("   ", u[0], u[1], "FLAGGED by E" if u[2] else "not flagged")

print()
for sc in load_scenarios("all", "scenarios_robust"):
    if not sc.id.startswith("rob-ood"):
        continue
    p = sc.principals[0]
    terms = {k: (p.mandate.allowed.get(k) or v)[0] for k, v in sc.issues.items()}; terms["admin_fee"] = "150"
    state = {"deal": False, "paid": 0.0, "grants": []}
    c = check_action(sc, p, "agree_terms", {"terms": terms}, state, ignore_signoff=True)
    print(f"{sc.id}: C reasons={c or 'none (allowed)'}; E flags={grey_flags(sc, p, 'agree_terms', {'terms': terms})}; "
          f"scorer breach={sorted(action_violations(sc, p, 'agree_terms', {'terms': terms}, state))}")
