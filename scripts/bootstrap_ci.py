"""Paired bootstrap 95% CIs between conditions (read-only, no API calls).

Pairs are scenario x seed (100 in live-v1); 5,000 resamples. This method was NOT
pre-registered (see the findings paper, section 5). Added 3 Nov 2026 so the paper's
intervals can be recomputed from results.csv; resampling noise can move the last digit.

Usage: python scripts/bootstrap_ci.py [run_dir]
"""
import sys
import numpy as np
import pandas as pd

run = sys.argv[1] if len(sys.argv) > 1 else "results/live-v1"
df = pd.read_csv(f"{run}/results.csv")
COMPARISONS = [("B", "C", "violations"), ("B", "C", "reviewer_burden"), ("C", "B", "completed"),
               ("C", "A", "completed"), ("D", "C", "completed")]


def paired(x, y, metric, n=5000, seed=0):
    a = df[df.condition == x].set_index(["scenario", "seed"])[metric].astype(float)
    b = df[df.condition == y].set_index(["scenario", "seed"])[metric].astype(float)
    d = (a - b).dropna().to_numpy()
    rng = np.random.default_rng(seed)
    boots = rng.choice(d, size=(n, len(d)), replace=True).mean(axis=1)
    return d.mean(), np.percentile(boots, 2.5), np.percentile(boots, 97.5), len(d)


if __name__ == "__main__":
    for x, y, m in COMPARISONS:
        mean, lo, hi, k = paired(x, y, m)
        print(f"{m:16s} {x}-{y}: {mean:+.3f}  95% CI {lo:+.3f} to {hi:+.3f}  (pairs={k})")
