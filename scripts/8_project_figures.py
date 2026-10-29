#!/usr/bin/env python3
"""Generate the figures referenced by the project report.

Run: PYTHONPATH=src .venv/bin/python scripts/8_project_figures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "phase8"
OUT.mkdir(parents=True, exist_ok=True)


def monitoring_kpi() -> None:
    p2 = json.loads((ROOT / "results/phase2/monitoring_report.json").read_text())
    p4 = json.loads((ROOT / "results/phase4/monitoring_estimated_report.json").read_text())
    labels = ["True trajectory (oracle)", "RF-estimated trajectory"]
    detected = [p2["n_below_target_detected_by_monitor"], p4["n_below_target_detected"]]
    lead = [p2["n_below_target_with_lead_over_assay"], p4["n_below_target_with_lead_over_assay"]]
    x = np.arange(len(labels))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].bar(x, detected, width=0.5, label="detected (of 26)")
    axes[0].bar(x, lead, width=0.25, label="with early-warning lead")
    axes[0].set_xticks(x); axes[0].set_xticklabels(labels, fontsize=8)
    axes[0].set_ylim(0, 30); axes[0].set_ylabel("batches (of 26 below-target)")
    axes[0].legend(fontsize=8); axes[0].set_title("Below-target detection (held-out)")
    axes[1].bar(x, [p2["median_lead_h"], p4["median_lead_h"]], width=0.45,
                color=["#4C72B0", "#DD8452"])
    axes[1].set_xticks(x); axes[1].set_xticklabels(labels, fontsize=8)
    axes[1].set_ylabel("median lead over assay stream (h)")
    axes[1].set_title("Early-warning lead time")
    fig.tight_layout()
    fig.savefig(OUT / "monitoring_oracle_vs_estimated.png", dpi=140)
    plt.close(fig)


def representative_batch() -> None:
    """Show batch 99 (fault, below-target) vs the golden band and assay samples."""
    traj = pd.read_parquet(ROOT / "data/processed/p_estimated.parquet")
    df = pd.read_parquet(ROOT / "data/processed/process_named.parquet")
    splits = json.loads((ROOT / "results/splits.json").read_text())
    train = splits["train_batches"]
    from bioreactor_monitoring.monitor import build_golden_bands

    batch = 99
    rt = df[df["batch"].isin(train) & (df["regime"] == "apc") & (df["below_target"] == 0)]
    band_true = build_golden_bands(rt, ["p_true_g_l"], k=3.0)
    b = df[df["batch"] == 99]
    rt2 = traj[traj["batch"].isin(train) & (traj["regime"] == "apc") & (traj["below_target"] == 0)]
    band_est = build_golden_bands(rt2[["batch", "time_h", "p_est_smooth"]].rename(
        columns={"p_est_smooth": "p_true_g_l"}), ["p_true_g_l"], k=3.0)
    g = band_true["grid"]
    tr = traj[traj["batch"] == batch]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(g, band_true["mean"][:, 0], color="teal", label="healthy mean (true)")
    ax.fill_between(g, band_true["lower"][:, 0], band_true["upper"][:, 0],
                    color="teal", alpha=0.18, label="healthy +/- 3 sigma (true)")
    ax.plot(b["time_h"], b["p_true_g_l"], color="black", lw=1.6, label="true P")
    ax.plot(tr["time_h"], tr["p_est_smooth"], color="#DD8452", lw=1.3, ls="--",
            label="RF estimate (smoothed)")
    off = b[b["p_offline_g_l"].notna()]
    ax.plot(off["time_h"], off["p_offline_g_l"], "o", color="crimson", ms=4,
            label="offline assay samples")
    ax.axhline(20.0, color="grey", ls=":", lw=1, label="20 g/L endpoint target")
    ax.set_xlabel("batch time (h)"); ax.set_ylabel("penicillin (g/L)")
    ax.set_title(f"Batch {batch} (fault, below-target) vs golden band")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "representative_batch_99.png", dpi=140)
    plt.close(fig)


def control_by_sigma() -> None:
    p6 = pd.read_csv(ROOT / "results/phase6/per_run_control.csv")
    p7 = pd.read_csv(ROOT / "results/phase7/per_run_mpc.csv")
    fig, ax = plt.subplots(figsize=(8, 5))
    for frame, controller, color in ((p6, "rule-based PI", "#55A868"),
                                     (p7, "constrained MPC", "#4C72B0")):
        arms = sorted(set(frame["arm"].tolist()))
        for arm in arms:
            if arm.startswith("noisy_sigma"):
                sub = frame[frame["arm"] == arm]
                sigma = float(arm.split("_sigma")[1])
                ax.scatter([sigma], sub["P_final_g_l"].mean(),
                           color=color, marker="o",
                           label=f"{controller}" if arm == arms[0] else None)
                ax.errorbar(sigma, sub["P_final_g_l"].mean(),
                            yerr=sub["P_final_g_l"].std(), color=color, alpha=0.7)
    ax.set_xscale("log")
    ax.set_xlabel("estimator noise sigma (relative)")
    ax.set_ylabel("final penicillin, mean over seeds (g/L)")
    ax.set_title("Control outcome vs soft-sensor accuracy")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "control_p_vs_sigma.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    monitoring_kpi()
    representative_batch()
    control_by_sigma()
    print("figures written to", OUT)
