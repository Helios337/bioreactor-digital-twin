#!/usr/bin/env python3
"""Phase 7: constrained MPC arms, matched to the Phase 6 rule-based arms.

The same plant, seeds, and limits are used. MPC is run with the oracle
sensor and with soft-sensor-like estimates at several error levels, plus the
delayed assay sensor. The comparison isolates whether a constraint-respecting
predictive controller is more sensitive to estimation quality.

Run: .venv/bin/python scripts/7_control_mpc.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from bioreactor_monitoring.config import Config
from bioreactor_monitoring.control import (
    DelayedAssaySensor,
    IdentitySensor,
    NoisyEstimatorSensor,
    NonLinearMPC,
    run_batch,
)
from bioreactor_monitoring.simulator import BajpaiReussParams

SEEDS = [0, 1, 2, 3, 4]
PROCESS_SIGMA = 0.01
SIGMA_LEVELS = [0.0, 0.005, 0.02, 0.05, 0.1, 0.2, 0.5]
MPC_KW = {"N": 5, "wS": 1.0, "wV": 100.0, "lam": 1e-3,
          "Sref": 0.05, "Fmax": 0.3, "v_limit": 130.0}


def main() -> None:
    cfg = Config.from_yaml()
    root = cfg.root
    out_dir = root / "results" / "phase7"
    out_dir.mkdir(parents=True, exist_ok=True)
    params = BajpaiReussParams()

    rows = []
    # oracle and noisy estimator arms
    for sigma in SIGMA_LEVELS:
        kind = "oracle" if sigma == 0.0 else f"noisy_sigma{sigma}"
        for seed in SEEDS:
            policy = NonLinearMPC(params=params, **MPC_KW)
            sensor = (IdentitySensor() if sigma == 0.0
                      else NoisyEstimatorSensor(sigma=sigma, seed=seed))
            res = run_batch(policy, sensor, params, seed=seed,
                            process_sigma=PROCESS_SIGMA)
            rows.append(_row(kind, sigma, seed, res))
    # delayed assay arm
    for seed in SEEDS:
        policy = NonLinearMPC(params=params, **MPC_KW)
        sensor = DelayedAssaySensor(interval_h=12.0, delay_h=4.0, seed=seed, noise=0.01)
        res = run_batch(policy, sensor, params, seed=seed,
                        process_sigma=PROCESS_SIGMA)
        rows.append(_row("assay", "assay", seed, res))

    df = pd.DataFrame(rows)
    agg = df.groupby("arm").agg(
        p_final_mean=("P_final_g_l", "mean"),
        p_final_std=("P_final_g_l", "std"),
        feed_mean=("feed_total_l", "mean"),
        s_rmse_mean=("S_rmse_g_l", "mean"),
        violations_total=("constraint_violations", "sum"),
    ).round(3).reset_index()

    report = {
        "settings": {"seeds": SEEDS, "process_sigma": PROCESS_SIGMA, "mpc": MPC_KW,
                     "note": ("MPC uses the correct plant model and observes "
                              "states through the sensor; the sweep varies only "
                              "the sensing layer.")},
        "by_arm": agg.to_dict(orient="records"),
        "per_run": df.to_dict(orient="records"),
        "phase6_comparison": {
            "recipe_final_p_mean_g_l": None,
            "pi_oracle_final_p_mean_g_l": None,
            "note": "Phase 6 table in results/phase6/control_report.md",
        },
    }
    (out_dir / "mpc_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    df.to_csv(out_dir / "per_run_mpc.csv", index=False)
    (out_dir / "mpc_report.md").write_text(_markdown(report, agg), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "per_run"}, indent=2))


def _row(arm: str, parameter, seed: int, res: dict) -> dict:
    s = res["summary"]
    return {
        "arm": arm,
        "parameter": str(parameter),
        "seed": seed,
        "P_final_g_l": round(s["P_final_g_l"], 3),
        "P_mass_g": round(s["P_mass_g"], 1),
        "X_final_g_l": round(s["X_final_g_l"], 2),
        "V_final_l": round(s["V_final_l"], 1),
        "feed_total_l": round(s["feed_total_l"], 2),
        "S_rmse_g_l": round(s["S_rmse_g_l"], 4),
        "S_max_g_l": round(s["S_max_g_l"], 4),
        "constraint_violations": s["constraint_violations"],
        "max_feed_l_h": round(s["max_feed_l_h"], 3),
    }


def _markdown(r: dict, agg: pd.DataFrame) -> str:
    lines = [
        "# Phase 7 Control Report (constrained nonlinear MPC)",
        "",
        "All arms share seeds, initial conditions, and limits. MPC predicts with",
        "the correct plant model; only the sensing layer differs.",
        "",
        "| arm | final P mean (g/L) | std | feed (L) | S RMSE | violations |",
        "|---|---|---|---|---|---|",
    ]
    for rec in agg.to_dict(orient="records"):
        lines.append(
            f"| {rec['arm']} | {rec['p_final_mean']} | {rec['p_final_std']} "
            f"| {rec['feed_mean']} | {rec['s_rmse_mean']} | {rec['violations_total']} |")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
