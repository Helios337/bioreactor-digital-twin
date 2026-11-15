#!/usr/bin/env python3
"""Run the full reproducible pipeline in order.

Steps:
  1  dataset inspection (hash check, schema, labels, splits)
  2  golden-batch CQA monitoring (oracle)
  3  soft-sensor baselines
  4  monitoring on the estimated trajectory
  6  rule-based control arms
  7  constrained MPC arms

The GRU forecasting experiment (phase 5) is NOT run here: it needs the optional
torch/xgboost stack and is compute-intensive, so it is invoked separately via
scripts/5_gru_forecasting.py. Project figures (script 8) are also not part of
this sequential pipeline; run it explicitly when you regenerate figures.

Each step writes its report under results/ and prints progress. The dashboard
then reads these results.

Run: PYTHONPATH=src .venv/bin/python scripts/0_run_all.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

STEPS = [
    ("1_inspect_data.py", "dataset inspection"),
    ("2_monitoring.py", "oracle monitoring"),
    ("3_soft_sensor.py", "soft-sensor baselines"),
    ("4_monitoring_estimated.py", "estimated-trajectory monitoring"),
    ("6_control_rule_based.py", "rule-based control arms"),
    ("7_control_mpc.py", "constrained MPC arms"),
]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    for script, label in STEPS:
        print(f"\n=== {label} ({script}) ===", flush=True)
        r = subprocess.run(
            [sys.executable, str(root / "scripts" / script)],
            cwd=root, env={"PYTHONPATH": str(root / "src")},
            check=False,
        )
        if r.returncode != 0:
            print(f"FAILED {script} with exit {r.returncode}", flush=True)
            sys.exit(r.returncode)
    print("\nPipeline complete.", flush=True)


if __name__ == "__main__":
    main()
