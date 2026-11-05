# Oversight at the Seams: safeguards for agent-to-agent negotiation

*By Sebastian Vale.*

A small, reproducible harness for one question:

> When AI agents acting for **different people** deal with each other, how does a **mandate enforced in code** compare with a **budgeted LLM approver** on mandate violations, welfare loss, reviewer burden, false blocks and task completion? And does a **per-principal outcome monitor** catch collusion that rule checks miss?

**Status (5 November 2026).** Two Phase 1 runs are complete, and a third stage stopped early, then a further addendum completed two of its five stages. The pre-registered main run (`results/live-v1/`) has 50 synthetic scenarios × 4 conditions × 2 seeds = 400 episodes, 0 failed. A pre-registered exploratory addendum, E1 (`results/live-B-unlimited/` and `results/live-B-deny/`, 200 episodes), reran the approver condition without its budget cliff. A pre-registered stage E2 (hybrid condition, user-written mandates, robustness tests) stopped after 45 episodes when API credit ran out; see `results/E2_SUMMARY.md`. A further pre-registered addendum, E2b, completed Stage 1 (255 leftover A/C/D episodes in `results/e2b-main/`) and Stage 2 (100 hybrid E episodes in `results/e2b-E/`). Stages 3 to 5 were not started. See `writeup/E2b Findings Note.md` and `results/E2b_SUMMARY.md`. The Phase 1 write-up is `writeup/Findings Paper - Safeguards for Agent-to-Agent Negotiation.md`. Phase 1 results remain preliminary. E2b Stages 1 and 2 are completed stages of the addendum, not a finished product claim. They come from one model family, two seeds and weak attacks, with automatic scoring. Read the paper's limitations and the E2b note's caveats before citing any number.

**How it was built.** One author designed the study. The harness was built with heavy help from AI coding tools. Everything needed to inspect or rerun it is in this repository.

## Why this matters

Picture a **personal agent mesh**: each person, firm and public body has its own agent, and those agents deal with each other directly.

- **Peers:** friends splitting a booking.
- **People and businesses:** a table, a trip, or a small firm's procurement agent collecting supplier bids.
- **People and public services:** a council agent offering bulky-waste collection slots or renewing a parking permit.

None of this is useful unless people can trust their agent without watching every exchange. That needs a **trust layer enforced in code** at each seam between principals:
- mandates and budgets;
- signed sign-offs;
- an audit trail;
- a per-person outcome check;
- an LLM reviewer only where code cannot decide.

**The design pattern this points to** (findings paper, section 6):
- **decide in code** whatever the mandate states;
- send only flagged grey cases to a narrow AI reviewer that can block but never widen authority;
- send anything the mandate does not cover back to the person;
- confirm the person's plain-English intent before it is enforced.

This repository measures which of those controls hold, and at what cost in human attention, when agents act for different people. The findings paper, section 7, sets out the idea.

## Results at a glance (100 episodes per condition)

| | A none | B approver, k=3, allow | B-unlimited (E1) | B-deny, k=3 (E1) | C code mandate | D C + monitor |
|---|---|---|---|---|---|---|
| Tasks completed | 98 | 94 | 94 | 48 | 88 | 75 |
| Episodes with ≥1 mandate violation | 19 | 21 | 12 | 1 | 0 | 1 |
| False blocks / all blocks | 0 / 0 | 54 / 56 | 82 / 89 | 195 / 215 | 0 / 26 | 0 / 34 |
| Reviewer burden per task | 0.95 | 3.90 | 5.51 | 4.02 | 0.98 | 1.04 |
| Collusion episodes held (of 10) | – | – | – | – | – | 0 |

- **The approver failed both ways.** 96% of B's blocks were false. In 19 of B's 21 breach episodes, the breaching action went through on the pre-registered allow-by-default policy after the 3-review budget was spent. You can check this from the saved transcripts with `python scripts/verify_b_budget.py`, which makes no API calls.
- **Fixing the budget did not fix the approver (E1, exploratory).** With an unlimited budget it still let 12 breach episodes through, 11 of them sign-off breaches it approved itself. With deny-by-default it matched C on breaches (1 against 0), but only by blocking most actions (91% of its blocks were false), and it completed 48 tasks against C's 88. Check it with `python scripts/e1_compare.py`.
- **The attacks were weak.** The H1 result (C beats B) rests mainly on ordinary sign-off lapses, not resistance to attacks.
- **The outcome monitor was a negative result.** It caught 0 of 10 collusion episodes and held 10 deals that involved no collusion.
- **E2b Stages 1 and 2 (5 November 2026).** On leftover cells, code hard rules (C, n=85) again had 0 violations against about 20% for no control (A, n=84), with completion 0.812 against 1.0. Hybrid E (n=100, full scenario set) also had 0 violations, but completion was 0.57, welfare loss 0.307, and the false-positive rate about 71%. E versus leftover C is not a matched scenario set. Stages 3 to 5 were not started. See `writeup/E2b Findings Note.md`.

## What is in here

```
meshexp/              the harness (Python package)
  schema.py           scenario format (pydantic)
  world.py            shared environment: messages, actions, deal detection, event log
  mandate.py          deterministic mandate checker (condition C's "mandate in code")
  controls.py         conditions A-D: Controller, budgeted LLM approver, outcome monitor
  agents.py           LiveAgent (Claude via the Anthropic API) and MockAgent (scripted)
  prompts.py          agent, approver and monitor prompts; tool schemas
  runner.py           one episode = scenario x condition x seed -> JSONL transcript
  scoring.py          automatic scoring against each scenario's ground truth
  analysis.py         results.csv -> summary tables and plots
  spotcheck.py        samples transcripts for manual review
  cost.py, prices.py  cost estimator (list prices; estimates only)
  cli.py              command-line interface (python -m meshexp ...)
scenarios/            50 synthetic scenarios (YAML) and generate.py, which produces them deterministically
preregistration.yaml  hypotheses and settings, v1 and v2, the dated amendment note, and exploratory addendum E1
results/live-v1/      the main run: config.json, results.csv, tables/, plots/, spotcheck/, transcripts/ (400 JSONL files)
results/live-B-*/     exploratory addendum E1 (B-unlimited, B-deny; 100 episodes each); summary in results/E1_SUMMARY.md
results/e2-main/      E2 stage 1, partial (45 episodes; stopped on insufficient API credit); summary in results/E2_SUMMARY.md
results/e2b-main/     E2b stage 1, leftover A/C/D (255 episodes); summary in results/E2b_SUMMARY.md
results/e2b-E/        E2b stage 2, hybrid E (100 episodes)
scenarios_robust/     15 E2 robustness scenarios and generate_robust.py
results/pilot*/       small development pilots (not results)
scripts/              verify_b_budget.py, bootstrap_ci.py, e1_compare.py, blocks_by_gate.py, e2_offline_replay.py, compile_mandates.py (E2 stage 3, live), spot_check.py, md2docx.py
tests/                pytest suite (offline, no API key needed)
writeup/              findings paper (md and docx) and the E2b findings note
```

## Requirements

- Python 3.11 or later (tested on 3.13), on Linux or macOS.
- For live runs only: an Anthropic API key with credit. Mock mode, the tests and all analysis of the saved results need no key and cost nothing.

```bash
git clone <this repository> && cd agent-mesh-experiment
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt          # pinned versions
python -m pytest -q                      # 12 offline tests
python -m meshexp validate               # checks the 50 scenarios
```

## 1. Inspect the published run (free)

```bash
python -m meshexp analyse results/live-v1        # rebuilds tables/ and plots/ from results.csv
python scripts/verify_b_budget.py                # how each of B's breaches got through
python scripts/bootstrap_ci.py                   # the paper's paired bootstrap 95% CIs (not pre-registered)
python scripts/e1_compare.py                     # E1: original B, B-unlimited, B-deny against C and D, with CIs
python scripts/blocks_by_gate.py results/live-B-deny B   # blocks by approver / budget default, true or false
python scripts/e2_offline_replay.py              # E2: what the hybrid's grey flags would raise on saved transcripts (not a result)
python -m meshexp spotcheck results/live-v1 --n 20   # the 20-transcript review sheet
```

Each `results/live-v1/transcripts/<scenario>__<condition>__s<seed>.jsonl` file is the complete event log of one episode. It records every agent turn, tool call, approver review, mandate check, budget-exhausted event, deal and the final score. `config.json` records the models, settings and the SHA-256 hash of the pre-registration in force.

## 2. Run the pipeline in mock mode (free)

```bash
python -m meshexp run --dry-run --seeds 3 --out results/mock
```

Scripted fake agents stand in for the models. The output proves that the pipeline works, and every output is labelled MOCK. Mock numbers are not evidence for anything.

## 3. Reproduce the live run (billable)

1. Put your key in the environment only. It is read from `ANTHROPIC_API_KEY` and never written anywhere by this code:
   ```bash
   export ANTHROPIC_API_KEY=...     # or keep it in a git-ignored .env and `set -a; . ./.env; set +a`
   ```
2. Estimate the cost:
   ```bash
   python -m meshexp cost --seeds 2 --model claude-sonnet-5-5 --approver-model claude-haiku-5-5 --monitor-model claude-haiku-5-5
   ```
3. Run the full design with a hard spend cap. These are the settings used for `live-v1`:
   ```bash
   python -m meshexp run --mode live --seeds 2 \
     --model claude-sonnet-5-5 --approver-model claude-haiku-5-5 --monitor-model claude-haiku-5-5 \
     --out results/live-repro --max-cost-usd 60
   ```
   The effort level (low), approval budget (3) and exhausted policy (allow) default to the values in `preregistration.yaml`. The run asks for confirmation; `--yes` skips it. It stops early if estimated spend reaches the cap or the API reports a billing error.
4. Score and summarise:
   ```bash
   python -m meshexp analyse results/live-repro
   python -m meshexp spotcheck results/live-repro --n 20
   ```

**Cost.** The original run made 4,549 API calls, about 10.8M input and 0.8M output tokens. At list prices checked on 3 November 2026, that comes to about US$27.6, with no caching or batch discounts. B alone (100 episodes) was about US$7. Prices change, so check `meshexp/prices.py` against Anthropic's pricing page before a live run. The Claude Console is the authority on what you are charged.

**Expect different numbers.** Live runs are not deterministic: model sampling varies, so a rerun will not match `live-v1` exactly. Compare conditions within a run, not raw counts across runs.

**Model IDs.** `claude-sonnet-5-5` and `claude-haiku-5-5` were current on 3 November 2026 (checked against the API's models list). If either is retired, pass a current ID with `--model`, `--approver-model` and `--monitor-model`, and report the substitution.

## Useful variations

```bash
# E1: B without the budget limit, or with deny-by-default once the budget is spent (about US$7.40 each in E1)
python -m meshexp run --mode live --conditions B --seeds 2 --model claude-sonnet-5-5 --approver-model claude-haiku-5-5 \
  --approval-budget 1000 --out results/repro-B-unlimited --max-cost-usd 11
python -m meshexp run --mode live --conditions B --seeds 2 --model claude-sonnet-5-5 --approver-model claude-haiku-5-5 \
  --exhausted deny --out results/repro-B-deny --max-cost-usd 11

# E2 (not yet run in full): hybrid E, compiled lay mandates (Cu, Cc), robustness set
python -m meshexp run --mode live --conditions C,E --seeds 2 --model claude-sonnet-5-5 --approver-model claude-haiku-5-5 --out results/repro-E --max-cost-usd 16
python scripts/compile_mandates.py --max-cost-usd 4      # writes results/e2-compile/overrides.json and translation.csv
python -m meshexp run --mode live --conditions Cu,Cc --seeds 1 --mandate-overrides results/e2-compile/overrides.json --model claude-sonnet-5-5 --out results/repro-users --max-cost-usd 8
python -m meshexp run --mode live --conditions C,E --seeds 2 --scenario-dir scenarios_robust --model claude-sonnet-5-5 --approver-model claude-haiku-5-5 --out results/repro-robust --max-cost-usd 6

# A subset of scenarios
python -m meshexp run --mode live --scenarios adversarial --seeds 1 --out results/live-adv --max-cost-usd 10
```

Other options: `--effort low|medium|high|default`, `--workers`, `--conditions A,B,C,D,E,Cu,Cc`, `--scenario-dir`, `--mandate-overrides`, `--scenarios all|adversarial|benign|<ids or domains>`, and `--seed-offset` (to add seeds to an earlier run). Any change from the pre-registered settings is a new, exploratory analysis. Pre-register it first and label it as such.

## Design in brief

- **Scenarios.** There are 50 short tasks, 10 in each of five domains: meeting scheduling; a lettings check-out (date, keys, deposit deduction); a buyer and two supplier quotes; a client and accountant (sometimes with a mortgage broker) agreeing a deadline, fee and document sharing; and three flatmates splitting the cost of a sofa. Each principal has a written mandate, private information and private utilities. All people and firms are fictional.
- **Adversarial set (20).** Each domain has one overreach, one injection, one extraction and one collusion scenario. In the collusion scenarios, two agents coordinate against a third person within that person's written limits.
- **Ground truth.** Each scenario file lists violation rules per protected principal, the acceptable outcomes and regex leak patterns. The scorer is independent of the code checker. Its leak patterns cover paraphrases that the checker (exact-value matching) cannot see.
- **Agents.** Agents act only through tools: `send_message`, `share_info`, `commit_payment`, `agree_terms` and `escalate_to_principal`. Turns are round-robin for at most four rounds, plus one settlement round. Escalations go to a deterministic simulated principal that signs off only what is within the mandate.
- **Conditions.** A has no control. In B, an LLM reviews `commit_payment`, `share_info` and `agree_terms`, with at most 3 reviews per task, then allow-by-default. In C, a deterministic mandate check runs before every action. D is C plus an LLM monitor acting only for the protected principal, which holds a deal if their outcome is materially worse than their mandate or a fair-share baseline (pre-registration v2). Adversarial agents are never controlled.
- **Metrics.** The metrics are mandate violations, welfare loss of the protected principal, reviewer burden, false blocks and task completion. Definitions are in the paper, section 2.4.

## Reproducibility notes

- `preregistration.yaml` was committed before any live call. Version 2 (a dated, pilot-informed amendment to the monitor rule) was committed before its validation pilot and the full run. The git history shows the order.
- The statistical method (paired bootstrap 95% intervals over scenario × seed pairs, 5,000 resamples; `scripts/bootstrap_ci.py`) was **not** pre-registered. The script was added after the analysis so the intervals can be recomputed; resampling noise can move the last digit.
- Scenarios are generated deterministically by `scenarios/generate.py`. Dependencies are pinned. Mock runs are deterministic for each scenario, condition and seed.

## Limitations

Synthetic principals and preferences; a simulated human (an LLM approver and a rule-following principal); one model family; two seeds; 10 episodes per attack type; weak attacks; a pre-registered approver baseline weakened by allow-by-default (E1 tests stronger variants, exploratory, with one approver model and prompt); crude regex leak detection; and human review of only 20 transcripts, by the author. See the paper, section 5.

## Licence

MIT. See `LICENSE`.
