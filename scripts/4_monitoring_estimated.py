#!/usr/bin/env python3
"""Phase 4: monitoring on the soft-sensor-estimated trajectory.

The Phase 2 monitor used the true penicillin trajectory (oracle). This phase
replaces the true trajectory with leak-free random-forest estimates so the
achievable early-warning performance under realistic estimation error is
measured, and the degradation relative to the oracle is quantified.

Run: .venv/bin/python scripts/4_monitoring_estimated.py
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
    REGIME,
    SOFT_SENSOR_FEATURES,
)
from bioreactor_monitoring.softsensor import predict_trajectories, score_metrics

ASSAY_DELAY_H = 4.0


def assay_baseline_alarm_time(batch_df: pd.DataFrame, bands: dict,
                              z_threshold: float) -> float | None:
    m = bands["mean"][:, 0]
    s_raw = (bands["upper"][:, 0] - bands["lower"][:, 0]) / 2.0
    s = np.maximum(s_raw, 0.02 * np.abs(m) + 0.05)
    grid = bands["grid"]
    rows = batch_df[(batch_df[P_OFFLINE].notna())]
    if rows.empty:
        return None
    times = rows["time_h"].to_numpy(dtype=float)
    values = rows[P_OFFLINE].to_numpy(dtype=float)
    idx = np.interp(times, grid, np.arange(len(grid))).astype(int)
    idx = np.clip(idx, 0, len(grid) - 1)
    lower = m[idx] - z_threshold * s[idx]
    below = values < lower
    if not np.any(below):
        return None
    return float(times[int(np.argmax(below))] + ASSAY_DELAY_H)


def oracle_from_phase2(root: Path) -> dict:
    path = root / "results" / "phase2" / "monitoring_report.json"
    if not path.exists():
        return {"note": "Phase 2 oracle report not found"}
    r = json.loads(path.read_text())
    return {
        "true_trajectory_detected": r["n_below_target_detected_by_monitor"],
        "true_trajectory_with_lead": r["n_below_target_with_lead_over_assay"],
        "true_trajectory_median_lead_h": r["median_lead_h"],
        "true_trajectory_far_healthy": r["false_alarm_rate_on_healthy_batches"],
    }


def main() -> None:
    cfg = Config.from_yaml()
    root = cfg.root
    out_dir = root / "results" / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(root / "data" / "processed" / "process_named.parquet")
    splits = json.loads((root / "results" / "splits.json").read_text())
    train_batches = np.array(splits["train_batches"])
    test_batches = np.array(splits["test_batches"])
    seed = splits["seed"]

    train_df = df[df[BATCH].isin(train_batches)]
    eval_df = df[~df[BATCH].isin(train_batches)]

    model_name = cfg.softsensor().get("models", ["random_forest"])[0]
    # Prefer the random forest when present because Ridge is clearly worse.
    if "random_forest" in cfg.softsensor().get("models", []):
        model_name = "random_forest"

    traj = predict_trajectories(train_df, eval_df, SOFT_SENSOR_FEATURES, model_name, seed)
    # Light smoothing to reduce single-sample flicker in online predictions.
    win = cfg.monitoring().get("estimate_smooth_h", 1.0)
    step = 0.2
    traj["p_est_smooth"] = (
        traj.groupby(BATCH)["p_est"].transform(
            lambda x: x.rolling(int(round(win / step)), center=True, min_periods=1).median()
        )
    )
    traj = traj.merge(
        df[[BATCH, "time_h", "p_true_g_l", REGIME, FAULT, BELOW_TARGET]],
        on=[BATCH, "time_h"], how="left",
    )
    traj.to_parquet(root / "data" / "processed" / "p_estimated.parquet", index=False)

    k = cfg.monitoring().get("golden_band_k", 3.0)
    z_threshold = cfg.monitoring().get("deviation_z_threshold", 1.0)
    min_dur = cfg.monitoring().get("min_alarm_duration_h", 2.0)

    rows_out = []
    for regime in ("recipe", "operator", "apc"):
        reg_train = traj[
            traj[BATCH].isin(train_batches) & (traj[REGIME] == regime) & (traj[BELOW_TARGET] == 0)
        ]
        if reg_train.empty or reg_train[BATCH].nunique() < 2:
            continue
        reg_bands_df = reg_train[["batch", "time_h", "p_est_smooth"]].rename(
            columns={"p_est_smooth": "p_true_g_l"})
        bands = build_golden_bands(reg_bands_df, ["p_true_g_l"], k=k)
        # The assay baseline compares against the maintained healthy envelope of
        # the true trajectory, identical to Phase 2, so lead times are comparable.
        true_healthy = df[
            (df[BATCH].isin(train_batches)) & (df[REGIME] == regime) & (df[BELOW_TARGET] == 0)
        ]
        true_bands = build_golden_bands(true_healthy, ["p_true_g_l"], k=k)
        for bno, batch_df in traj[traj[REGIME] == regime].groupby(BATCH):
            bdf = batch_df[["batch", "time_h", "p_est_smooth"]].rename(
                columns={"p_est_smooth": "p_true_g_l"})
            dev = deviation_series(bdf, bands, ["p_true_g_l"])
            z_down = (dev["z_p_true_g_l"] * -1.0).to_numpy()
            grid = bands["grid"]
            cross_idx = np.argmax(z_down > z_threshold) if np.any(z_down > z_threshold) else None
            first_cross = None if cross_idx is None or z_down[cross_idx] <= z_threshold else float(grid[cross_idx])
            events = alarm_events(z_down, grid, z_threshold, min_dur)
            assay_alarm = assay_baseline_alarm_time(batch_df, true_bands, z_threshold)
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

    # estimated-vs-true trajectory error on held-out batches only
    err = traj[traj["batch"].isin([int(b) for b in test_batches])].dropna(subset=["p_est_smooth"])
    pooled = score_metrics(err["p_true_g_l"].to_numpy(), err["p_est_smooth"].to_numpy())

    det = summary[summary["below_target"] == 1]
    detected = det[det["monitor_first_alarm_h"].notna()]
    with_lead = det[det["lead_h"].notna() & (det["lead_h"] > 0)]
    healthy = summary[(summary["below_target"] == 0) & (summary["fault"] == 0)]
    far = float((healthy["monitor_sustained_alarms"] > 0).mean())

    report = {
        "config": {"seed": seed, "model": model_name, "k": k, "z_threshold": z_threshold,
                   "min_duration_h": min_dur, "smooth_h": win, "assay_delay_h": ASSAY_DELAY_H},
        "trajectory_estimation_error_heldout": {
            "mae_g_l": round(pooled["mae"], 3), "rmse_g_l": round(pooled["rmse"], 3),
            "r2": round(pooled["r2"], 3),
            "note": "Smoothed estimated vs true trajectory on held-out batches, fed-batch scale 0 to about 36 g/L.",
        },
        "oracle_comparison": oracle_from_phase2(root),
        "n_below_target_batches": int(len(det)),
        "n_below_target_detected": int(len(detected)),
        "n_below_target_with_lead_over_assay": int(len(with_lead)),
        "median_lead_h": None if det["lead_h"].notna().sum() == 0 else round(float(det["lead_h"].median()), 1),
        "false_alarm_rate_on_healthy_batches": round(far, 3),
        "n_healthy_batches": int(len(healthy)),
        "per_batch": summary.to_dict(orient="records"),
    }
    (out_dir / "monitoring_estimated_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary.to_csv(out_dir / "per_batch_monitoring_estimated.csv", index=False)
    print(json.dumps({k: v for k, v in report.items() if k != "per_batch"}, indent=2))


if __name__ == "__main__":
    main()
