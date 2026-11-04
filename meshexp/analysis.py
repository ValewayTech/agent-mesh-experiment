"""Aggregate results.csv into summary tables and plots."""
from __future__ import annotations

import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .controls import CONDITIONS  # noqa: E402

METRICS = ["violations", "welfare_loss", "victim_welfare_loss", "reviewer_burden", "approvals", "escalations",
           "false_positives", "interventions", "completed"]


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("condition")
    s = g[METRICS].mean()
    s["fp_rate"] = g["false_positives"].sum() / g["interventions"].sum().replace(0, float("nan"))
    s["episodes"] = g.size()
    s["violation_rate"] = g["violations"].apply(lambda x: (x > 0).mean())
    sem = g[["violations", "reviewer_burden", "welfare_loss"]].sem().add_suffix("_sem")
    return s.join(sem).round(3)


def analyse(run_dir: str) -> str:
    run = pathlib.Path(run_dir)
    df = pd.read_csv(run / "results.csv")
    mock = (df["mode"] == "mock").any()
    tag = " [MOCK DATA - NOT RESULTS]" if mock else f" [LIVE: {df['scenario'].nunique()} scenarios x {df['seed'].nunique()} seed(s)]"
    overall = summarise(df)
    by_adv = df.groupby(["adversarial", "condition"])[["violations", "welfare_loss", "reviewer_burden", "completed"]].mean().round(3)
    by_attack = df.groupby(["attack_type", "condition"])[["violations", "victim_welfare_loss", "completed"]].mean().round(3).unstack("condition")
    (run / "tables").mkdir(exist_ok=True)
    overall.to_csv(run / "tables" / "summary_by_condition.csv")
    by_adv.to_csv(run / "tables" / "by_adversarial.csv")
    by_attack.to_csv(run / "tables" / "by_attack_type.csv")
    md = [f"# Summary{tag}", "", f"Episodes: {len(df)}; scenarios: {df['scenario'].nunique()}; seeds: {df['seed'].nunique()}", "",
          "## By condition", "", overall.to_markdown() if _has_tabulate() else overall.to_string(), "",
          "## Adversarial vs benign", "", by_adv.to_string(), "", "## By attack type", "", by_attack.to_string(), ""]
    (run / "tables" / "summary.md").write_text("\n".join(md))
    _plots(df, overall, run / "plots", tag)
    return "\n".join(md)


def _has_tabulate() -> bool:
    try:
        import tabulate  # noqa: F401
        return True
    except ImportError:
        return False


def _plots(df, overall, out: pathlib.Path, tag: str) -> None:
    out.mkdir(exist_ok=True)
    colours = {"A": "#999999", "B": "#d95f02", "C": "#1b9e77", "D": "#7570b3"}
    # 1. violations against reviewer burden (the headline curve)
    fig, ax = plt.subplots(figsize=(6, 4.2))
    for c, row in overall.iterrows():
        ax.errorbar(row["reviewer_burden"], row["violations"], xerr=row.get("reviewer_burden_sem", 0), yerr=row.get("violations_sem", 0),
                    fmt="o", ms=9, color=colours.get(c, "#777777"), capsize=3, label=f"{c}: {CONDITIONS[c]}")
    ax.set_xlabel("Reviewer burden (approvals + escalations + holds per task)")
    ax.set_ylabel("Mandate violations per task")
    ax.set_title("Violations vs reviewer burden" + tag, fontsize=10)
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(out / "violations_vs_burden.png", dpi=150); plt.close(fig)
    # 2. per-metric bars split by adversarial
    m = df.groupby(["condition", "adversarial"])[["violations", "victim_welfare_loss", "completed"]].mean().unstack("adversarial")
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
    for ax, metric in zip(axes, ["violations", "victim_welfare_loss", "completed"]):
        m[metric].plot.bar(ax=ax, color=["#a6cee3", "#e31a1c"], rot=0)
        ax.set_title(metric.replace("_", " "), fontsize=10); ax.set_xlabel("condition")
        ax.legend(["benign", "adversarial"], fontsize=7)
    fig.suptitle("Metrics by condition" + tag, fontsize=10)
    fig.tight_layout(); fig.savefig(out / "metrics_by_condition.png", dpi=150); plt.close(fig)
    # 3. victim welfare loss by attack type
    w = df.groupby(["attack_type", "condition"])["victim_welfare_loss"].mean().unstack("condition")
    fig, ax = plt.subplots(figsize=(7, 3.8))
    w.plot.bar(ax=ax, color=[colours.get(c, "#777777") for c in w.columns], rot=0)
    ax.set_ylabel("Mean welfare loss of protected principal"); ax.set_title("Welfare loss by attack type" + tag, fontsize=10)
    fig.tight_layout(); fig.savefig(out / "welfare_by_attack.png", dpi=150); plt.close(fig)
