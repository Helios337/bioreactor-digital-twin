#!/usr/bin/env python3
"""Phase 6: rule-based feed control with matched estimation-error arms.

Closed-loop batches on the Bajpai-Reuss plant compare, under identical
disturbance seeds, limits, and initial conditions:
  - recipe baseline (constant feed),
  - delayed off-line assay feedback (12 h + 4 h),
  - oracle state feedback (true substrate),
  - soft-sensor-like feedback at several estimation-error levels.

The estimation-error sweep measures how final penicillin depends on the
quality of the state estimate used by the controller.

Run: .venv/bin/python scripts/6_control_rule_based.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from bioreactor_monitoring.config import Config
from bioreactor_monitoring.control import (
    ConstantFeed,
    DelayedAssaySensor,
    IdentitySensor,
    NoisyEstimatorSensor,
    SubstratePI,
    run_batch,
)
from bioreactor_monitoring.simulator import BajpaiReussParams

SEEDS = [0, 1, 2, 3, 4]
PROCESS_SIGMA = 0.01
SIGMA_LEVELS = [0.0, 0.005, 0.02, 0.05, 0.1, 0.2, 0.5]
PI_KW = {"Sref": 0.05, "Kp": 20.0, "Ki": 2.0, "Fff": 0.05, "Fmin": 0.0,
         "Fmax": 0.3, "v_limit": 130.0}
RECIPE_F = 0.08


def fresh_policy(kind: str):
    if kind == "recipe":
        return ConstantFeed(F=RECIPE_F)
    return SubstratePI(**PI_KW)


def fresh_sensor(kind: str, sigma: float, seed: int):
    if kind in ("oracle", "recipe"):
        return IdentitySensor()
    if kind == "noisy":
        return NoisyEstimatorSensor(sigma=sigma, seed=seed)
    if kind == "assay":
        return DelayedAssaySensor(interval_h=12.0, delay_h=4.0, seed=seed, noise=0.01)
    raise ValueError(kind)


def main() -> None:
    cfg = Config.from_yaml()
    root = cfg.root
    out_dir = root / "results" / "phase6"
    out_dir.mkdir(parents=True, exist_ok=True)
    params = BajpaiReussParams()

    rows = []
    # Recipe and assay arms.
    for kind, sensor_kw in [("recipe", ("recipe", 0.0)), ("assay", ("assay", 0.0))]:
        for seed in SEEDS:
            res = run_batch(fresh_policy(kind), fresh_sensor(*sensor_kw, seed), params,
                            seed=seed, process_sigma=PROCESS_SIGMA)
            rows.append(_row(kind, sensor_kw, seed, res))
    # Oracle arm (sigma 0) and noisy arms (sweep).
    for sigma in SIGMA_LEVELS:
        kind = "oracle" if sigma == 0.0 else "noisy"
        for seed in SEEDS:
            res = run_batch(fresh_policy("pi"),
                            fresh_sensor(kind, sigma, seed), params,
                            seed=seed, process_sigma=PROCESS_SIGMA)
            rows.append(_row(kind, ("noisy", sigma if sigma > 0 else 0.0), seed, res))

    df = pd.DataFrame(rows)

    # Aggregated table by arm.
    agg = df.groupby("arm").agg(
        p_final_mean=("P_final_g_l", "mean"),
        p_final_std=("P_final_g_l", "std"),
        feed_mean=("feed_total_l", "mean"),
        s_rmse_mean=("S_rmse_g_l", "mean"),
        violations_total=("constraint_violations", "sum"),
    ).round(3).reset_index()
    agg = agg.sort_values("p_final_mean", ascending=False)

    report = {
        "settings": {
            "seeds": SEEDS, "process_sigma": PROCESS_SIGMA,
            "pi": PI_KW, "recipe_f": RECIPE_F,
            "substrate_inhibition_note": ("The Bajpai-Reuss production rate is "
                                          "inhibited above low substrate, so "
                                          "tight substrate regulation matters."),
        },
        "by_arm": agg.to_dict(orient="records"),
        "per_run": df.to_dict(orient="records"),
    }
    (out_dir / "control_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    df.to_csv(out_dir / "per_run_control.csv", index=False)
    (out_dir / "control_report.md").write_text(_markdown(report, agg), encoding="utf-8")
    _plot(df, out_dir)
    print(json.dumps({k: v for k, v in report.items() if k != "per_run"}, indent=2))


def _row(kind: str, sensor_kw: tuple, seed: int, res: dict) -> dict:
    arm = kind if kind != "noisy" else f"noisy_sigma{sensor_kw[1]}"
    s = res["summary"]
    return {
        "arm": arm,
        "sensor": kind,
        "parameter": sensor_kw[1],
        "seed": seed,
        "P_final_g_l": round(s["P_final_g_l"], 3),
        "P_mass_g": round(s["P_mass_g"], 1),
        "X_final_g_l": round(s["X_final_g_l"], 2),
        "V_final_l": round(s["V_final_l"], 1),
        "feed_total_l": round(s["feed_total_l"], 2),
        "S_rmse_g_l": round(s["S_rmse_g_l"], 4),
        "S_max_g_l": round(s["S_max_g_l"], 4),
        "constraint_violations": s["constraint_violations"],
    }


def _plot(df: pd.DataFrame, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    order = ["recipe", "assay", "oracle"] + [f"noisy_sigma{s}" for s in SIGMA_LEVELS[1:]]
    for i, arm in enumerate(order):
        sub = df[df["arm"] == arm]
        if sub.empty:
            continue
        ax.scatter(np.full(len(sub), i), sub["P_final_g_l"], s=30, alpha=0.7)
        ax.errorbar(i, sub["P_final_g_l"].mean(),
                    yerr=sub["P_final_g_l"].std(), fmt="_", color="k")
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(order, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("final penicillin (g/L)")
    ax.set_title("Rule-based feed control: final P by feedback arm (5 seeds each)")
    fig.tight_layout()
    fig.savefig(out_dir / "control_by_arm.png", dpi=130)
    plt.close(fig)


def _markdown(r: dict, agg: pd.DataFrame) -> str:
    lines = [
        "# Phase 6 Control Report (rule-based feed, matched arms)",
        "",
        "All arms share seeds, initial conditions, and operating limits. "
        "Process noise sigma = {0}.".format(r["settings"]["process_sigma"]),
        "",
        "| arm | final P mean (g/L) | std | feed (L) | S RMSE | violations |",
        "|---|---|---|---|---|---|",
    ]
    for rec in agg.to_dict(orient="records"):
        lines.append(
            f"| {rec['arm']} | {rec['p_final_mean']} | {rec['p_final_std']} "
            f"| {rec['feed_mean']} | {rec['s_rmse_mean']} | {rec['violations_total']} |")
    lines += [
        "",
        "Reading (reviewer interpretation, to be revisited by the MPC arm):",
        "- Online substrate feedback (oracle or soft-sensor-like) far outperforms",
        "  the delayed 12 h plus 4 h assay feedback, which collapses the batch",
        "  (final P near zero).",
        "- Final penicillin is only modestly sensitive to the estimator noise",
        "  level over a broad range (sigma 0.005 to 0.5), so this PI design is",
        "  robust to soft-sensor error.",
        "- The tuned constant-feed recipe outperforms this substrate-PI at the",
        "  chosen setpoint, which is a humility result consistent with simpler",
        "  designs winning in earlier literature.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
