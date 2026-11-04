"""Count blocked actions by who blocked them (approver, checker, budget_exhausted deny-by-default)
and whether the scorer says they would have been violations (true block) or not (false block).
Read-only: uses saved transcripts, makes no API calls.  Usage: python scripts/blocks_by_gate.py RUN COND
"""
import collections, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from meshexp.cli import load_scenarios
from meshexp.scoring import action_violations

run, cond = sys.argv[1], sys.argv[2]
scen = {s.id: s for s in load_scenarios("all")}
c = collections.Counter()
for fn in sorted(glob.glob(f"{run}/transcripts/*__{cond}__*.jsonl")):
    evs = [json.loads(l) for l in open(fn) if l.strip()]
    sc = scen[evs[0]["scenario"]]
    honest = {p.agent_id: p for p in sc.principals if not p.adversarial}
    for ev in evs:
        if ev["type"] == "action" and not ev.get("executed") and ev["agent"] in honest and ev.get("blocked_by"):
            would = action_violations(sc, honest[ev["agent"]], ev["name"], ev["input"], ev["state"])
            c[(ev["blocked_by"], "true" if would else "false")] += 1
for gate in sorted({g for g, _ in c}):
    t, f = c[(gate, "true")], c[(gate, "false")]
    print(f"{run} {cond} blocked_by={gate}: {t+f} blocks, {t} true, {f} false ({f/(t+f):.0%} false)")
