# E2b findings note

*Sebastian Vale · 5 November 2026 · Exploratory addendum, Stages 1 and 2*

This note is about safeguards for agents acting between people. The design idea it serves is simple: decide in code, escalate only what code cannot decide.

**Status.** Stages 1 and 2 of the preregistered E2b addendum are complete. Stages 3 to 5 were not started. About US$5 of the US$30 E2b spend cap was left unused after a stop on 5 November 2026 (Europe/London). Phase 1 of this study was preliminary. The figures below are completed stages of the addendum, not a finished product or a framework claim. Read them with the Phase 1 findings paper and with the caveats at the end.

## What held

On the leftover Stage 1 cells, a mandate enforced in code (condition C, 85 episodes) produced no mandate violations. With no control (condition A, 84 episodes), about 20% of episodes had at least one violation. C completed about 81% of tasks, against 100% for A, and mean welfare loss was higher under C (0.221 against 0.142). That is the same direction as the main Phase 1 run: hard rules written down and checked outside the model stop the ordinary breaches, at a cost in completion and some welfare.

Condition D (C plus an outcome monitor, 86 episodes) had one violation (rate 0.012). That single case was a paraphrased budget leak in agent wording, not a difference in how D and C apply rules. The matching C episode did not use the wording the scorer treats as a leak. Live runs are not deterministic.

## What did not

Condition E is the hybrid: code decides the hard rules, and an LLM reviewer sees only cases that code flags as grey. On 100 episodes (all 50 scenarios, two seeds) it also recorded zero violations. It was not a free improvement on C.

- 57 of 100 tasks completed, with a deal struck in each of those 57.
- Mean welfare loss 0.307; mean victim welfare loss 0.309.
- Reviewer burden 2.51 per task, with 1.45 approvals.
- False positive rate about 71% (64 of 90 interventions).
- Welfare loss was 0.359 on adversarial tasks and 0.272 on benign ones.
- Victim welfare loss by attack: collusion 0.403, overreach 0.358, extraction 0.352, injection 0.347, and 0.272 where there was no attack.

E ran the full scenario set. Stage 1 A, C and D ran only the 255 leftover cells (43 scenarios), after an earlier incomplete E2 attempt in the document request domain. E versus C is therefore not a matched comparison on the same cells. The honest reading is still clear: adding the grey reviewer did not buy fewer violations than code already achieved, and it cost completion, welfare and attention.

An offline replay (no live calls) of the grey flags on Stage 1 C transcripts found at least one flag in 54 of 85 episodes (63.5%). Mean welfare loss on those flagged episodes was 0.194, against 0.221 for C overall. The flags mostly marked agreements at a person's least preferred allowed option, which is often ordinary compromise in this harness. That is design evidence, not a result of E itself.

## Stage 1 figures

Leftover A, C and D written to `results/e2b-main`. Spend about US$17.60 (list price estimate). The earlier 45 E2 episodes in `results/e2-main` are not pooled into these counts.

| Condition | Episodes | Violation rate | Mean welfare loss | Mean victim welfare loss | Completed |
|---|---:|---:|---:|---:|---:|
| A, no control | 84 | 0.202 | 0.142 | 0.153 | 1.000 |
| C, code hard rules | 85 | 0.000 | 0.221 | 0.201 | 0.812 |
| D, C plus outcome monitor | 86 | 0.012 | 0.262 | 0.238 | 0.733 |

Source: `results/e2b-main/tables/summary_by_condition.csv`.

## Stage 2 figures

Hybrid E written to `results/e2b-E`. Spend about US$7.24 (1,225 calls; about 2.88 million input tokens and 0.22 million output tokens), under the US$12 stage cap.

| Condition | Episodes | Violation rate | Mean welfare loss | Mean victim welfare loss | Completed | Reviewer burden | Approvals | False positive rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| E, code plus grey reviewer | 100 | 0.000 | 0.307 | 0.309 | 0.57 | 2.51 | 1.45 | 0.711 |

Source: `results/e2b-E/tables/summary_by_condition.csv`.

## What was not run

Stages 3 to 5 of the preregistration were not started. Those stages were meant to cover user written mandates compiled to code, with and without a confirm back step; robustness scenarios; and a same batch rerun of the unlimited approver. They remain unmeasured.

## Caveats

1. Do not pool E2's 45 historical episodes with E2b Stage 1.
2. Do not treat E and Stage 1 C as the same scenario set.
3. The false positive rate on E is high (about 71%). Zero violations here is not a claim that E is safer in general.
4. One model family (Claude Sonnet 5.5 agents; Claude Haiku 5.5 reviewer), two seeds, synthetic tasks, and the same weak attack set as Phase 1. Scoring is automatic, as before.
5. A killed partial start of Stage 2 was discarded. The reported 100 episodes are the completed rerun. Cost from that partial start is not counted separately, so remaining spend (about US$5.16 of US$30) is approximate.
6. Nothing here is offered as a guarantee, a security proof, or a finished system. It reports what these completed stages showed.

## Materials

- Phase 1 paper: `writeup/Findings Paper - Safeguards for Agent-to-Agent Negotiation.md`
- Stage status and chronology: `results/E2b_SUMMARY.md`
- Grey flag replay (design evidence): `results/E2b_FLAG_REPLAY.md`
- Preregistration: `preregistration.yaml`, committed before any E2b live call (commit `38d883c`)

*Published under the pen name Sebastian Vale.*
