"""Verify, from the live-v1 transcripts, how condition B's mandate violations were gated.

For every executed action by an honest agent that the scorer counts as a violation, record how
it got through: approved by the LLM approver ('review'), let through by the allow-by-default
policy after the approval budget was spent ('budget_exhausted'), or never reviewed ('unreviewed').
Read-only: uses saved transcripts, makes no API calls.
"""
import collections, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from meshexp.cli import load_scenarios
from meshexp.scoring import action_violations

run = sys.argv[1] if len(sys.argv) > 1 else "results/live-v1"
cond = sys.argv[2] if len(sys.argv) > 2 else "B"
scen = {s.id: s for s in load_scenarios("all")}
ep_gate = collections.Counter(); act_gate = collections.Counter(); eps = 0; detail = []
for fn in sorted(glob.glob(f"{run}/transcripts/*__{cond}__*.jsonl")):
    evs = [json.loads(l) for l in open(fn) if l.strip()]
    sc = scen[evs[0]["scenario"]]
    honest = {p.agent_id: p for p in sc.principals if not p.adversarial}
    seen, gates, last = set(), [], {}
    for ev in evs:
        if ev["type"] in ("review", "approval_budget_exhausted"):
            last[(ev["agent"], ev["action"])] = "approver_approved" if ev["type"] == "review" else "budget_exhausted"
        if ev["type"] == "action" and ev.get("executed") and ev["agent"] in honest:
            v = action_violations(sc, honest[ev["agent"]], ev["name"], ev["input"], ev["state"])
            g = last.pop((ev["agent"], ev["name"]), "unreviewed")
            new = v - seen
            if v:
                act_gate[g] += 1
            if new:
                gates.append(g); seen |= new
    if seen:
        eps += 1
        first = gates[0]
        ep_gate[first] += 1
        detail.append((fn.split("/")[-1], sorted(seen), gates))
print(f"{cond}: episodes with >=1 violation: {eps}")
print("by how the FIRST violating action got through:", dict(ep_gate))
print("all violating actions by gate:", dict(act_gate))
for d in detail: print(" ", *d)
