#!/usr/bin/env python3
"""Phase 3: penicillin soft-sensor baselines on held-out batches.

Trains a linear ridge and a random forest on the published online feature set,
evaluates on complete held-out batches, and compares against the published
IndPenSim baselines with the split documented.

Run: .venv/bin/python scripts/3_soft_sensor.py
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
from bioreactor_monitoring.preprocess import (
    BATCH,
    FAULT,
    SOFT_SENSOR_FEATURES,
    split_batches,
)
from bioreactor_monitoring.softsensor import fit_predict, score_metrics


def main() -> None:
    cfg = Config.from_yaml()
    root = cfg.root
    out_dir = root / "results" / "phase3"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(root / "data" / "processed" / "process_named.parquet")
    splits_path = root / "results" / "splits.json"
    if splits_path.exists():
        splits = json.loads(splits_path.read_text())
        train_batches = np.array(splits["train_batches"])
        test_batches = np.array(splits["test_batches"])
        seed = splits["seed"]
    else:
        from bioreactor_monitoring.preprocess import BELOW_TARGET, split_batches
        seed = cfg.splits().get("seed", 42)
        label_map = df.groupby(BATCH)[BELOW_TARGET].first().astype(int).to_dict()
        train_batches, test_batches = split_batches(
            df[BATCH].unique(), seed, cfg.splits().get("test_fraction", 0.2), labels=label_map
        )
    train = df[df[BATCH].isin(train_batches)]
    test_and_dev = df[df[BATCH].isin(test_batches)]
    norm_test = test_and_dev[test_and_dev[BATCH] <= 90]
    fault_test = test_and_dev[test_and_dev[BATCH] > 90]

    models = cfg.softsensor().get("models", ["ridge", "random_forest"])
    results = {}
    for name in models:
        res = fit_predict(train, test_and_dev, SOFT_SENSOR_FEATURES, name, seed)
        res_norm = fit_predict(train, norm_test, SOFT_SENSOR_FEATURES, name, seed)
        res_fault = fit_predict(train, fault_test, SOFT_SENSOR_FEATURES, name, seed)
        per_batch = res.predictions.groupby("batch").apply(
            lambda g: score_metrics(g["y_true"].to_numpy(), g["y_pred"].to_numpy()), include_groups=False
        ).to_frame("m").reset_index()
        per_batch["mae"] = per_batch["m"].map(lambda d: round(d["mae"], 3))
        per_batch["rmse"] = per_batch["m"].map(lambda d: round(d["rmse"], 3))
        per_batch = per_batch.drop(columns=["m"])
        results[name] = {
            "pooled": res.metrics,
            "normal_test": res_norm.metrics,
            "fault_test": res_fault.metrics,
            "per_batch": per_batch.to_dict(orient="records"),
        }
        _plot(res.predictions, name, out_dir)

    report = {
        "features": SOFT_SENSOR_FEATURES,
        "seed": seed,
        "train_batch_count": len(train_batches),
        "test_and_dev_batch_count": len(test_batches),
        "results": results,
        "published_baselines": {
            "acosta_pavas_2024_cubist": {
                "source": "Computers and Chemical Engineering 187:108736",
                "r2": 0.908, "rmse": 3.149, "mae": 1.920,
                "note": "Reported on their own IndPenSim split; not directly comparable to ours.",
            },
            "metcalfe_2025_lstm_deviation_batches": {
                "source": "Computers and Chemical Engineering 194:108991",
                "mae_range_g_l": [2.39, 2.68],
                "note": "MAE on deviation batches 94, 99, 100 for an 8 h forecast.",
            },
        },
        "comparability_note": ("Model numbers are only comparable on identical "
                               "data partitions; published splits differ."),
    }
    (out_dir / "softsensor_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "softsensor_report.md").write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("results",)}, indent=2))


def _plot(pred: pd.DataFrame, name: str, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(pred["y_true"], pred["y_pred"], s=12, alpha=0.6)
    lim = [0, float(max(pred["y_true"].max(), pred["y_pred"].max()) * 1.05)]
    ax.plot(lim, lim, "k--", lw=1)
    ax.set_xlabel("offline penicillin (g/L)")
    ax.set_ylabel("predicted penicillin (g/L)")
    ax.set_title(f"soft sensor {name} on held-out batches")
    fig.tight_layout()
    fig.savefig(out_dir / f"softsensor_{name}.png", dpi=130)
    plt.close(fig)


def _markdown(r: dict) -> str:
    lines = [
        "# Phase 3 Soft-Sensor Report",
        "",
        f"- Features: {', '.join(r['features'])}",
        f"- Train batches: {r['train_batch_count']} (plus 10 deviation batches held out)",
        f"- Held-out batches: {r['test_and_dev_batch_count']}",
        "",
        "| model | split | MAE | RMSE | R2 |",
        "|---|---|---|---|---|",
    ]
    for name, blk in r["results"].items():
        for split in ("pooled", "normal_test", "fault_test"):
            m = blk[split]
            lines.append(f"| {name} | {split} | {m['mae']:.3f} | {m['rmse']:.3f} | {m['r2']:.3f} |")
    lines += [
        "",
        "Published baselines (different splits, quoted for context only):",
        "- Acosta-Pavas 2024 Cubist: R2 0.908, RMSE 3.149, MAE 1.920.",
        "- Metcalfe 2025 LSTM on deviation batches 94, 99, 100: MAE 2.39 to 2.68 g/L.",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
