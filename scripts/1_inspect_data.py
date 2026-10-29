#!/usr/bin/env python3
"""Phase 1: dataset acquisition check and inspection report.

Verifies the archive hash, loads the statistics and process tables, applies
the canonical schema, and writes an inspection report plus a processed
parquet cache.

Run: .venv/bin/python scripts/1_inspect_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from bioreactor_monitoring.config import Config
from bioreactor_monitoring.loader import (
    PROCESS_CSV,
    STATISTICS_CSV,
    find_file,
    load_statistics,
    sha256_of,
)
from bioreactor_monitoring.preprocess import (
    BATCH,
    BELOW_TARGET,
    FAULT,
    P_OFFLINE,
    P_TRUE,
    REGIME,
    add_below_target,
    add_regime_and_fault,
    rename_columns,
    split_batches,
    write_processed_cache,
)


def main() -> None:
    cfg = Config.from_yaml()
    root = cfg.root
    data_dir = cfg.data_dir()
    extracted = cfg.resolve(cfg.data.get("data", {}).get("extracted_dir", "data/extracted"))
    results_dir = (root / "results" / "phase1")
    results_dir.mkdir(parents=True, exist_ok=True)

    archive = cfg.resolve(cfg.data.get("data", {}).get("archive", "data/100_Batches_IndPenSim.zip"))
    report: dict = {"doi": cfg.data["data"]["doi"], "licence": cfg.data["data"]["licence"]}

    # 1. Archive hash check.
    actual_hash = sha256_of(archive)
    expected_hash = cfg.data["data"]["sha256"]
    report["archive_sha256_match"] = actual_hash == expected_hash
    report["archive_sha256"] = actual_hash
    if actual_hash != expected_hash:
        raise SystemExit(f"SHA256 mismatch: expected {expected_hash}, got {actual_hash}")

    # 2. Statistics table.
    stats_path = find_file(extracted, STATISTICS_CSV)
    stats = load_statistics(stats_path)
    st = stats.copy()
    st.columns = [str(c).strip() for c in st.columns]
    yield_col = "Penicllin_yield_total (kg)"
    st["yield_total_kg"] = st[yield_col] / 1000.0
    n_below = int((st["yield_total_kg"] < 2000.0).sum())
    report["statistics"] = {
        "rows": len(st),
        "yield_col_labelled_kg": yield_col,
        "yield_min_kg": round(float(st["yield_total_kg"].min()), 1),
        "yield_max_kg": round(float(st["yield_total_kg"].max()), 1),
        "n_fault_batches": int(st["Fault ref(0-NoFault 1-Fault)"].sum()),
        "n_below_target_2000kg": n_below,
    }
    report["unit_caveat"] = (
        "The statistics yield columns are labelled (kg) but the values are grams; "
        "dividing by 1000 gives per-batch totals in the kilogram range reported "
        "in the benchmark paper."
    )

    # 3. Process table (named columns only; Raman columns are excluded here).
    process_path = find_file(extracted, PROCESS_CSV)
    df_raw = pd.read_csv(
        process_path,
        usecols=lambda c: not str(c).isdigit(),
        low_memory=False,
    )
    df = rename_columns(df_raw)
    df = add_regime_and_fault(df)
    df = add_below_target(df)

    n_rows = len(df)
    n_batches = int(df[BATCH].nunique())
    report["process"] = {
        "rows": n_rows,
        "batches": n_batches,
        "batch_min": int(df[BATCH].min()),
        "batch_max": int(df[BATCH].max()),
    }
    report["labeling"] = {
        "below_target_rule": "endpoint penicillin concentration < 20 g/L",
        "n_below_target": int(df.groupby(BATCH)[BELOW_TARGET].first().sum()),
        "note": ("This rule reproduces the published count of 33 below-target "
                 "batches (Luo et al. 2024). A total-yield-in-kg rule instead "
                 "yields 13 and is volume-confounded, so it is not used."),
    }

    # 4. Schema and completeness.
    schema = []
    for col in df.columns:
        s = df[col]
        row = {
            "column": col,
            "dtype": str(s.dtype),
            "non_null_pct": round(100.0 * s.notna().mean(), 2),
        }
        if pd.api.types.is_numeric_dtype(s):
            row.update({
                "min": None if pd.isna(s.min()) else round(float(s.min()), 4),
                "max": None if pd.isna(s.max()) else round(float(s.max()), 4),
                "mean": None if pd.isna(s.mean()) else round(float(s.mean()), 4),
            })
        schema.append(row)
    report["schema"] = schema

    # 5. Per-batch summary.
    per_batch = []
    for bno, sub in df.groupby(BATCH):
        po = sub[P_OFFLINE].dropna()
        per_batch.append({
            "batch": int(bno),
            "regime": sub[REGIME].iloc[0],
            "fault": int(sub[FAULT].iloc[0]),
            "below_target": int(sub[BELOW_TARGET].iloc[0]),
            "rows": int(len(sub)),
            "span_h": round(float(sub["time_h"].max() - sub["time_h"].min()), 1),
            "n_offline_samples": int(len(po)),
            "p_max_true_g_l": round(float(sub[P_TRUE].max()), 2),
        })
    report["per_batch"] = per_batch

    # 6. Offline assay cadence and consistency.
    gaps = []
    first_times = []
    for bno, sub in df.groupby(BATCH):
        times = sub.loc[sub[P_OFFLINE].notna(), "time_h"].to_numpy()
        if len(times) > 1:
            gaps.extend(np.diff(times).tolist())
        if len(times):
            first_times.append(float(times.min()))
    labeled = df[P_OFFLINE].notna()
    diff = np.abs(df.loc[labeled, P_TRUE].to_numpy() - df.loc[labeled, P_OFFLINE].to_numpy())
    report["assay"] = {
        "n_labeled_rows": int(labeled.sum()),
        "gap_h_median": None if not gaps else round(float(np.median(gaps)), 2),
        "first_sample_h_median": None if not first_times else round(float(np.median(first_times)), 2),
        "max_abs_p_minus_p_offline": round(float(diff.max()), 4),
        "cadence_note": "Offline assay sampling and its 4 hour delay are the realistic label schedule."
    }

    # 7. Split bookkeeping (documented, deterministic).
    train, test = split_batches(df[BATCH].unique(), cfg.splits().get("seed", 42),
                                cfg.splits().get("test_fraction", 0.2))
    report["splits"] = {
        "seed": cfg.splits().get("seed", 42),
        "train_batches": sorted(int(b) for b in train),
        "test_batches": sorted(int(b) for b in test),
    }

    # 8. Persist artifacts.
    cache_dir = root / "data" / "processed"
    write_processed_cache(df, cache_dir / "process_named.parquet")
    (results_dir / "inspection_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    (results_dir / "inspection_report.md").write_text(_render_markdown(report), encoding="utf-8")
    print(f"Wrote report to {results_dir}")
    print(f"Wrote processed cache to {cache_dir}")
    print(f"Batches: {n_batches}, rows: {n_rows}, below-target: {report['labeling']['n_below_target']}")


def _render_markdown(report: dict) -> str:
    lines = [
        "# Phase 1 Dataset Inspection Report",
        "",
        f"DOI: {report['doi']} License: {report['licence']}",
        f"Archive SHA256 match: {report['archive_sha256_match']}",
        "",
        "## Statistics",
    ]
    s = report["statistics"]
    lines.append(f"- Batches: {s['rows']}")
    lines.append(f"- Total yield range (kg): {s['yield_min_kg']} to {s['yield_max_kg']}")
    lines.append(f"- Fault batches: {s['n_fault_batches']}")
    lines.append(f"- Below-target batches (< 2000 kg): {s['n_below_target_2000kg']}")
    lines.append(f"- Unit caveat: {report['unit_caveat']}")
    lines += ["", "## Per-batch summary"]
    lines.append("| batch | regime | fault | below_target | rows | span_h | n_offline |")
    lines.append("|---|---|---|---|---|---|---|")
    for b in report["per_batch"]:
        lines.append(
            f"| {b['batch']} | {b['regime']} | {b['fault']} | {b['below_target']} "
            f"| {b['rows']} | {b['span_h']} | {b['n_offline_samples']} |"
        )
    lines += ["", "## Assay schedule"]
    a = report["assay"]
    lines.append(f"- Labeled rows: {a['n_labeled_rows']}")
    lines.append(f"- Median sample gap (h): {a['gap_h_median']}")
    lines.append(f"- Median first sample (h): {a['first_sample_h_median']}")
    lines.append(f"- Max |P true - P offline| at labeled rows: {a['max_abs_p_minus_p_offline']}")
    lines += ["", "## Splits"]
    lines.append(f"- Seed: {report['splits']['seed']}")
    lines.append(f"- Train batches: {report['splits']['train_batches']}")
    lines.append(f"- Test and deviation batches: {report['splits']['test_batches']}")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
