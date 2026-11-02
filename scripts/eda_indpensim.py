from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from bioreactor_monitoring.config import Config
from bioreactor_monitoring.preprocess import rename_columns, add_regime_and_fault, add_below_target, BATCH, P_TRUE, P_OFFLINE, REGIME, FAULT, BELOW_TARGET, TIME

def main() -> None:
    cfg = Config.from_yaml()
    root = cfg.root
    extracted = (cfg.root / "data" / "IndPenSim" / "extracted" / "Mendeley_data")
    process_path = (extracted / "100_Batches_IndPenSim_V3.csv")
    out_dir = root / "eda_results"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load and preprocess
    df_raw = pd.read_csv(process_path, usecols=lambda c: not str(c).isdigit(), low_memory=False)
    df = rename_columns(df_raw)
    df = add_regime_and_fault(df)
    df = add_below_target(df)

    # ---- 1. Overview statistics ----
    batches = sorted(df[BATCH].unique())
    stats = {
        "total_batches": int(len(batches)),
        "total_records": len(df),
        "online_variables": len([c for c in df.columns if c not in (BATCH, TIME, P_TRUE, P_OFFLINE, REGIME, FAULT, BELOW_TARGET, "fault_ref")]),
        "batch_span_h": round(float(df.groupby(BATCH)[TIME].max().mean() - df.groupby(BATCH)[TIME].min().mean()), 1),
        "offline_samples_per_batch_median": int(df.groupby(BATCH)[P_OFFLINE].apply(lambda s: s.notna().sum()).median()),
        "below_target_count": int(df.groupby(BATCH)[BELOW_TARGET].first().sum()),
        "fault_batch_count": int(df.groupby(BATCH)[FAULT].first().sum()),
    }
    (out_dir / "eda_summary.json").write_text(json.dumps(stats, indent=2))

    # ---- 2. Variable distributions ----
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    vars_plot = ["feed_rate_l_h", "ph", "temperature_k", "do2_mg_l", "volume_l", "co2_out_pct"]
    for ax, var in zip(axes.flat, vars_plot):
        if var in df.columns:
            df[var].dropna().hist(bins=50, ax=ax, color="steelblue", edgecolor="black", alpha=0.7)
            ax.set_title(var)
            ax.set_xlabel("Value")
            ax.set_ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(out_dir / "eda_variable_distributions.png", dpi=150)
    plt.close()

    # ---- 3. Batch trajectory overview ----
    fig, ax = plt.subplots(figsize=(12, 6))
    for b in batches[:10]:
        sub = df[df[BATCH] == b]
        ax.plot(sub[TIME], sub[P_TRUE], alpha=0.5, label=f"Batch {b}" if b == batches[0] else "")
    ax.set_title("Penicillin Concentration Trajectories (First 10 Batches)")
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("P_true (g/L)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "eda_trajectories_first10.png", dpi=150)
    plt.close()

    # ---- 4. Batch quality / regime comparison ----
    fig, ax = plt.subplots(figsize=(10, 5))
    batch_summary = df.groupby(BATCH).agg({
        P_TRUE: "max",
        REGIME: "first",
        FAULT: "first",
        BELOW_TARGET: "first",
    }).reset_index()
    regime_counts = batch_summary.groupby(REGIME)[BELOW_TARGET].mean()
    regime_counts.plot(kind="bar", ax=ax, color=["#4C78A8", "#F58518", "#E45756"])
    ax.set_title("Below-Target Rate by Regime")
    ax.set_ylabel("Fraction Below Target")
    ax.set_xlabel("Regime")
    plt.tight_layout()
    plt.savefig(out_dir / "eda_regime_quality.png", dpi=150)
    plt.close()

    # ---- 5. Offline assay timing ----
    fig, ax = plt.subplots(figsize=(10, 5))
    assay_times = df.loc[df[P_OFFLINE].notna()].groupby(BATCH)[TIME].apply(lambda s: s.values)
    gaps = []
    for b, times in assay_times.items():
        if len(times) > 1:
            gaps.extend(np.diff(times).tolist())
    ax.hist(gaps, bins=30, color="steelblue", edgecolor="black", alpha=0.8)
    ax.axvline(np.median(gaps) if gaps else 0, color="red", linestyle="--", label=f"Median gap: {np.median(gaps):.1f} h")
    ax.set_title("Offline Assay Sampling Gaps")
    ax.set_xlabel("Gap (h)")
    ax.set_ylabel("Count")
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "eda_offline_assay_gaps.png", dpi=150)
    plt.close()

    # ---- 6. Feature correlation heatmap ----
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in (BATCH, TIME, P_TRUE, P_OFFLINE)]
    # Pick a representative subset
    subset = ["feed_rate_l_h", "agitator_rpm", "ph", "temperature_k", "do2_mg_l", "volume_l", "co2_out_pct", "o2_out_pct", "our_g_min"]
    subset = [c for c in subset if c in df.columns]
    corr = df[subset].corr()
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(subset)))
    ax.set_yticks(range(len(subset)))
    ax.set_xticklabels(subset, rotation=45, ha="right")
    ax.set_yticklabels(subset)
    for i in range(len(subset)):
        for j in range(len(subset)):
            ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center", fontsize=7, color="black" if abs(corr.values[i,j]) < 0.5 else "white")
    plt.colorbar(im, ax=ax, label="Correlation")
    plt.title("Feature Correlation Heatmap")
    plt.tight_layout()
    plt.savefig(out_dir / "eda_correlation_heatmap.png", dpi=150)
    plt.close()

    # ---- Save full CSV summary ----
    batch_summary.to_csv(out_dir / "eda_batch_summary.csv", index=False)
    (out_dir / "eda_readme.md").write_text(
        "# EDA Results\n\n"
        "- eda_summary.json: basic dataset statistics\n"
        "- eda_variable_distributions.png: histograms for 6 key process variables\n"
        "- eda_trajectories_first10.png: penicillin trajectories for first 10 batches\n"
        "- eda_regime_quality.png: below-target rate by control regime\n"
        "- eda_offline_assay_gaps.png: offline assay sampling intervals\n"
        "- eda_correlation_heatmap.png: feature correlations\n"
        "- eda_batch_summary.csv: per-batch summary statistics\n"
        "- Source: IndPenSim V3 (DOI 10.17632/pdnjz7zz5x.2, CC BY 4.0)\n"
        "- Note: Simulated benchmark data; not plant measurements.\n"
    )
    print(f"EDA complete. Results saved to {out_dir}")
    print(f"Stats: batches={stats['total_batches']}, records={stats['total_records']}, below_target={stats['below_target_count']}")

if __name__ == "__main__":
    main()