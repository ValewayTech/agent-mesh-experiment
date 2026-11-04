"""Exploratory addendum E1: original B, B-unlimited, B-deny against C and D (read-only, no API calls).
Paired bootstrap 95% CIs over scenario x seed pairs, 5,000 resamples, seed 0.
Usage: python scripts/e1_compare.py
"""
import numpy as np, pandas as pd

RUNS = {"B (k=3, allow-by-default)": ("results/live-v1", "B"), "B-unlimited": ("results/live-B-unlimited", "B"),
        "B-deny (k=3, deny-by-default)": ("results/live-B-deny", "B"), "C": ("results/live-v1", "C"), "D": ("results/live-v1", "D")}


def load(p, c):
    return pd.read_csv(f"{p}/results.csv").query("condition == @c").set_index(["scenario", "seed"])


def ci(a, b, m):
    d = (a[m].astype(float) - b[m].astype(float)).dropna().to_numpy()
    bs = np.random.default_rng(0).choice(d, (5000, len(d))).mean(1)
    return f"{d.mean():+.2f} ({np.percentile(bs, 2.5):+.2f} to {np.percentile(bs, 97.5):+.2f})"


dfs = {k: load(*v) for k, v in RUNS.items()}
print("| Condition | Breach episodes | Blocks | False blocks | Reviewer burden | Completed | Cost US$ |")
for k, d in dfs.items():
    blocks = d.false_positives.sum() + d.true_positives.sum()
    fb = f"{d.false_positives.sum()} ({d.false_positives.sum() / blocks:.0%})" if blocks else "0"
    print(f"| {k} | {(d.violations > 0).sum()} | {blocks} | {fb} | {d.reviewer_burden.mean():.2f} | {d.completed.sum()} | {d.cost_usd_est.sum():.2f} |")
print()
for k in list(RUNS)[:3]:
    print(f"{k} minus C: breaches {ci(dfs[k], dfs['C'], 'violations')}; burden {ci(dfs[k], dfs['C'], 'reviewer_burden')}; "
          f"completed {ci(dfs[k], dfs['C'], 'completed')}; protected-principal welfare loss {ci(dfs[k], dfs['C'], 'victim_welfare_loss')}")
