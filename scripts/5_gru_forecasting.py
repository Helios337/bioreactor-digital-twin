#!/usr/bin/env python3
"""Phase 5: standalone GRU penicillin forecasting experiment (Workstream C).

Two independent modes, each written to its own report so their metrics are never
merged:

  mode=dense   (primary)  target is the dense simulated trajectory p_true_g_l.
                          The target is used only as y, never as an input.
  mode=sparse  (secondary) target is the offline assay p_offline_g_l at recorded
                          sample times. The four-hour assay delay is respected:
                          the label can supervise training but is not an input
                          before its availability time.

This script is self-contained: it does not import dashboard, monitoring,
golden-batch, or control code. It requires the forecasting extra (torch and
optionally xgboost) to train the GRU; the base monitoring workflow does not need
it.

Run (from the repository root):
  PYTHONPATH=src .venv/bin/python scripts/5_gru_forecasting.py --mode dense
  PYTHONPATH=src .venv/bin/python scripts/5_gru_forecasting.py --mode sparse
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from bioreactor_monitoring.config import Config
from bioreactor_monitoring.gru_forecaster import train_forecaster, predict
from bioreactor_monitoring.preprocess import (
    BATCH,
    BELOW_TARGET,
    FAULT,
    P_OFFLINE,
    P_TRUE,
    REGIME,
    SOFT_SENSOR_FEATURES,
    TIME,
)
from bioreactor_monitoring.sequence import build_windows
from bioreactor_monitoring.softsensor import score_metrics

TARGET_COL_DENSE = P_TRUE
TARGET_COL_SPARSE = P_OFFLINE


def _load_data(root: Path) -> pd.DataFrame:
    path = root / "data" / "processed" / "process_named.parquet"
    if not path.exists():
        raise FileNotFoundError(
            "processed parquet cache not found. Run scripts/1_inspect_data.py "
            f"first so that {path} exists.")
    return pd.read_parquet(path)


def _partition(df: pd.DataFrame, root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    splits_path = root / "results" / "splits.json"
    if not splits_path.exists():
        raise FileNotFoundError(
            "results/splits.json not found; run scripts/2_monitoring.py first.")
    splits = json.loads(splits_path.read_text())
    train_batches = np.array(splits["train_batches"])
    test_batches = np.array(splits["test_batches"])
    train = df[df[BATCH].isin(train_batches)]
    test = df[df[BATCH].isin(test_batches)]
    # A grouped validation split is taken from the training partition only, so
    # final test batches stay untouched during early stopping / selection.
    rng = np.random.default_rng(int(splits["seed"]))
    train_ids = sorted(set(int(b) for b in train_batches))
    val_ids = set(rng.choice(train_ids, size=max(1, int(0.15 * len(train_ids))),
                             replace=False).tolist())
    val = train[train[BATCH].isin(list(val_ids))]
    fit = train[~train[BATCH].isin(list(val_ids))]
    return fit, val, test


def _persistence_baseline(meta_test: pd.DataFrame, df_test: pd.DataFrame,
                          target: str) -> np.ndarray:
    """Last-observed target value at each window's final input time (t)."""
    preds = []
    for _, row in meta_test.iterrows():
        b = int(row[BATCH]); t = float(row[TIME])
        sub = df_test[(df_test[BATCH] == b) & (df_test[TIME] <= t)][target]
        preds.append(float(sub.iloc[-1]) if len(sub) else np.nan)
    return np.asarray(preds)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["dense", "sparse"], default="dense")
    args = parser.parse_args()

    cfg = Config.from_yaml()
    root = cfg.root
    gc = cfg.data.get("gru_forecasting", {})
    features = list(SOFT_SENSOR_FEATURES)
    target = TARGET_COL_DENSE if args.mode == "dense" else TARGET_COL_SPARSE

    df = _load_data(root)
    fit, val, test = _partition(df, root)

    run_id = f"{args.mode}_L{gc.get('lookback', 24)}_h{gc.get('horizon', 12)}"
    out_dir = root / "results" / "phase5_gru" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Dense target: every row is a valid supervised point within the batch.
    # Sparse target: only assay rows are usable labels, and availability is
    # delayed; this reduces the labelled sample count sharply.
    fit_rows = fit if args.mode == "dense" else fit[fit[target].notna()]
    val_rows = val if args.mode == "dense" else val[val[target].notna()]
    test_rows = test if args.mode == "dense" else test[test[target].notna()]

    X_tr, y_tr, _ = build_windows(fit_rows, gc.get("lookback", 24), gc.get("horizon", 12),
                                  features, target)
    X_va, y_va, _ = build_windows(val_rows, gc.get("lookback", 24), gc.get("horizon", 12),
                                  features, target)
    X_te, y_te, meta_te = build_windows(test_rows, gc.get("lookback", 24),
                                        gc.get("horizon", 12), features, target)

    model, hist = train_forecaster(
        X_tr, y_tr, X_va, y_va,
        hidden_size=int(gc.get("hidden_size", 64)),
        num_layers=int(gc.get("num_layers", 1)),
        dropout=float(gc.get("dropout", 0.0)),
        batch_size=int(gc.get("batch_size", 64)),
        epochs=int(gc.get("epochs", 50)),
        lr=float(gc.get("lr", 1e-3)),
        weight_decay=float(gc.get("weight_decay", 1e-5)),
        grad_clip=float(gc.get("grad_clip", 1.0)),
        patience=int(gc.get("patience", 8)),
        seed=int(gc.get("seed", 0)),
    )
    y_gru = predict(model, X_te)

    # Baselines. Persistence applies directly; Ridge/RF (existing soft-sensor
    # models) are fit on the same training window features where target
    # availability makes the comparison fair.
    y_persist = _persistence_baseline(meta_te, test_rows, target)
    y_ridge = _baseline_regressor("ridge", X_tr, y_tr, X_te)
    y_rf = _baseline_regressor("random_forest", X_tr, y_tr, X_te)

    valid = np.isfinite(y_persist)
    reports = {
        "persistence": score_metrics(y_te[valid], y_persist[valid]),
        "ridge": score_metrics(y_te, y_ridge),
        "random_forest": score_metrics(y_te, y_rf),
        "gru": score_metrics(y_te, y_gru),
    }

    per_batch = {}
    bef = pd.DataFrame({"batch": meta_te[BATCH].to_numpy(),
                        "y_true": y_te, "y_gru": y_gru})
    for b, g in bef.groupby("batch"):
        per_batch[int(b)] = score_metrics(g["y_true"].to_numpy(), g["y_gru"].to_numpy())

    report = {
        "mode": args.mode,
        "target": str(target),
        "features": features,
        "lookback": gc.get("lookback", 24),
        "horizon": gc.get("horizon", 12),
        "seed": gc.get("seed", 0),
        "n_features": X_tr.shape[2],
        "n_train_windows": int(len(X_tr)),
        "n_val_windows": int(len(X_va)),
        "n_test_windows": int(len(X_te)),
        "target_scale_note": ("Metrics are MSE/RMSE/MAE in g/L and R2 on the "
                              "original target scale. MSE here is on the "
                              "original-scale target, so it is NOT comparable "
                              "to any scaled MSE (e.g. the 7.20e-4 in the "
                              "2026 paper) without matching target scaling."),
        "metrics": reports,
        "per_batch_gru": per_batch,
        "best_epoch": hist["best_epoch"],
        "best_val_loss_scaled": hist["best_val_loss"],
        "train_history": hist["history"],
        "paper_status": ("Paper-inspired reproduction. The 2026 GRU paper "
                         "hyperparameters were not verified from its full text "
                         "in this environment; all values above are "
                         "project-selected defaults, not claimed published "
                         "values."),
    }
    (out_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    pred_df = pd.DataFrame({"batch": meta_te[BATCH].to_numpy(),
                            "time_h": meta_te[TIME].to_numpy(),
                            "y_true": y_te, "y_persistence": y_persist,
                            "y_ridge": y_ridge, "y_rf": y_rf, "y_gru": y_gru})
    pred_df.to_csv(out_dir / "per_batch_predictions.csv", index=False)
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("train_history", "per_batch_gru")}, indent=2))
    print(f"\nWrote artifacts to {out_dir}")


def _baseline_regressor(name: str, X_tr: np.ndarray, y_tr: np.ndarray,
                        X_te: np.ndarray) -> np.ndarray:
    """Fit a Ridge or Random Forest on flattened window features.

    This reuses the existing soft-sensor models as a compatible baseline over
    the same windows and training batches, so the comparison is fair.
    """
    from bioreactor_monitoring.softsensor import _make_model
    x2 = X_tr.reshape(len(X_tr), -1)
    t2 = X_te.reshape(len(X_te), -1)
    model = _make_model(name, seed=0)
    model.fit(x2, y_tr)
    return model.predict(t2)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Data-dependent experiment not run: the processed cache or split "
              "file is unavailable in this environment.", file=sys.stderr)
        sys.exit(2)