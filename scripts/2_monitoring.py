#!/usr/bin/env python3
"""Phase 2: golden-batch CQA monitoring vs the delayed assay baseline.

A golden band for the penicillin trajectory is built from healthy training
batches of each control regime. For every held-out batch, the monitor reports
the first time its trajectory drops below the band (12 min cadence, no delay).
The assay baseline applies the identical rule to the offline assay stream
(12 hour samples, revealed 4 hours later). The detection lead is the difference
between the two alarming times, isolating the value of finer-cadence monitoring
over laboratory assays.

Run: .venv/bin/python scripts/2_monitoring.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from bioreactor_monitoring.config import Config
from bioreactor_monitoring.monitor import (
    alarm_events,
    build_golden_bands,
    deviation_series,
)
from bioreactor_monitoring.preprocess import (
    BATCH,
    BELOW_TARGET,
    FAULT,
    P_OFFLINE,
    P_TRUE,
    REGIME,
    split_batches,
    assay_available,
)

ASSAY_DELAY_H = 4.0
MONITOR_VAR = "p_true_g_l"


def assay_baseline_alarm_time(batch_df: pd.DataFrame, bands: dict,
                              z_threshold: float) -> float | None:
    """First time a delayed off-line assay reveals the batch below the band.

    The assay value at sample time t is usable at t + delay. It is compared
    against the golden band at its own sample time. The first such available
    assay below the lower band is the baseline detection time.
    """
    m = bands["mean"][:, 0]
    s = (bands["upper"][:, 0] - bands["lower"][:, 0]) / 2.0
    grid = bands["grid"]
    rows = batch_df[(batch_df[P_OFFLINE].notna())]
    if rows.empty:
        return None
    times = rows["time_h"].to_numpy(dtype=float)
    values = rows[P_OFFLINE].to_numpy(dtype=float)
    # band at each sample time
    idx = np.interp(times, grid, np.arange(len(grid))).astype(int)
    idx = np.clip(idx, 0, len(grid) - 1)
    lower_band = m[idx] - z_threshold * s[idx]
    below = values < lower_band
    if not np.any(below):
        return None
    first = int(np.argmax(below))
    return float(times[first] + ASSAY_DELAY_H)


def main() -> None:
    cfg = Config.from_yaml()
    root = cfg.root
    out_dir = root / "results" / "phase2"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(root / "data" / "processed" / "process_named.parquet")
    seed = cfg.splits().get("seed", 42)
    label_map = df.groupby(BATCH)[BELOW_TARGET].first().astype(int).to_dict()
    train_batches, test_batches = split_batches(
        df[BATCH].unique(), seed, cfg.splits().get("test_fraction", 0.2), labels=label_map
    )
    (root / "results" / "splits.json").write_text(json.dumps({
        "seed": seed, "train_batches": sorted(int(b) for b in train_batches),
        "test_batches": sorted(int(b) for b in test_batches),
    }), encoding="utf-8")

    k = cfg.monitoring().get("golden_band_k", 3.0)
    z_threshold = cfg.monitoring().get("deviation_z_threshold", 1.0)
    min_dur = cfg.monitoring().get("min_alarm_duration_h", 2.0)

    rows_out = []
    for regime in ("recipe", "operator", "apc"):
        reg_train = df[df[BATCH].isin(train_batches) & (df[REGIME] == regime) & (df[BELOW_TARGET] == 0)]
        if reg_train.empty or reg_train[BATCH].nunique() < 2:
            continue
        bands = build_golden_bands(reg_train, [MONITOR_VAR], k=k)
        for bno, batch_df in df[df[REGIME] == regime].groupby(BATCH):
            dev = deviation_series(batch_df, bands, [MONITOR_VAR])
            z_down = (dev[f"z_{MONITOR_VAR}"] * -1.0).to_numpy()
            grid = bands["grid"]
            # First crossing (raw detection time, matched to the assay stream).
            cross_idx = np.argmax(z_down > z_threshold) if np.any(z_down > z_threshold) else None
            first_cross = None if cross_idx is None or z_down[cross_idx] <= z_threshold else float(grid[cross_idx])
            # Sustained alarms (robustness).
            events = alarm_events(z_down, grid, z_threshold, min_dur)
            assay_alarm = assay_baseline_alarm_time(batch_df, bands, z_threshold)
            lead = None
            if first_cross is not None and assay_alarm is not None:
                lead = assay_alarm - first_cross
            rows_out.append({
                "batch": int(bno),
                "regime": regime,
                "fault": int(batch_df[FAULT].iloc[0]),
                "below_target": int(batch_df[BELOW_TARGET].iloc[0]),
                "monitor_first_alarm_h": None if first_cross is None else round(first_cross, 1),
                "monitor_sustained_alarms": len(events),
                "assay_alarm_h": None if assay_alarm is None else round(assay_alarm, 1),
                "lead_h": None if lead is None else round(lead, 1),
            })
    summary = pd.DataFrame(rows_out)

    det = summary[summary["below_target"] == 1]
    detected = det[det["monitor_first_alarm_h"].notna()]
    with_lead = det[det["lead_h"].notna() & (det["lead_h"] > 0)]
    healthy = summary[(summary["below_target"] == 0) & (summary["fault"] == 0)]
    far = float((healthy["monitor_sustained_alarms"] > 0).mean())
    both = det[det["monitor_first_alarm_h"].notna() & det["assay_alarm_h"].notna()]

    report = {
        "config": {"seed": seed, "k": k, "z_threshold": z_threshold,
                   "min_duration_h": min_dur, "monitor_var": MONITOR_VAR,
                   "assay_delay_h": ASSAY_DELAY_H},
        "n_below_target_batches": int(len(det)),
        "n_below_target_detected_by_monitor": int(len(detected)),
        "n_below_target_with_lead_over_assay": int(len(with_lead)),
        "median_lead_h": None if both.empty else round(float(both["lead_h"].median()), 1),
        "mean_lead_h": None if both.empty else round(float(both["lead_h"].mean()), 1),
        "false_alarm_rate_on_healthy_batches": round(far, 3),
        "n_healthy_batches": int(len(healthy)),
        "note": ("Lead time is the difference between the first below-band crossing "
                 "of the true 12 min trajectory and the identical rule applied to "
                 "the delayed 12 h assay stream. The sustained-alarm rule is used "
                 "for the false-alarm assessment."),
        "per_batch": summary.to_dict(orient="records"),
    }
    (out_dir / "monitoring_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary.to_csv(out_dir / "per_batch_monitoring.csv", index=False)
    (out_dir / "monitoring_report.md").write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "per_batch"}, indent=2))


def _markdown(r: dict) -> str:
    lines = [
        "# Phase 2 Monitoring Report (CQA monitor vs assay baseline)",
        "",
        f"- Seed {r['config']['seed']}, k={r['config']['k']}, z-threshold {r['config']['z_threshold']}, min duration {r['config']['min_duration_h']} h",
        f"- Below-target batches: {r['n_below_target_batches']}",
        f"- Detected by the 12 min monitor: {r['n_below_target_detected_by_monitor']}",
        f"- With lead over the delayed assay stream: {r['n_below_target_with_lead_over_assay']}",
        f"- Median lead time (h): {r['median_lead_h']}",
        f"- Mean lead time (h): {r['mean_lead_h']}",
        f"- False-alarm rate on healthy batches: {r['false_alarm_rate_on_healthy_batches']}",
        f"- Healthy batches: {r['n_healthy_batches']}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
