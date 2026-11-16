#!/usr/bin/env python3
"""Phase 5: compact, observable GRU penicillin forecasting experiment.

Dense mode forecasts the simulated true-state trajectory. Sparse mode forecasts
the recorded offline assay values. The modes have separate output directories
and reports. All data splits are by complete batch.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from bioreactor_monitoring.config import Config
from bioreactor_monitoring.gru_forecaster import predict, select_features, train_forecaster
from bioreactor_monitoring.preprocess import (
    BATCH, P_OFFLINE, P_TRUE, SOFT_SENSOR_FEATURES, TIME,
)
from bioreactor_monitoring.sequence import build_windows
from bioreactor_monitoring.softsensor import score_metrics

TARGET_COL_DENSE = P_TRUE
TARGET_COL_SPARSE = P_OFFLINE


def log(message: str) -> None:
    """Print a timestamped progress message immediately (Colab-friendly)."""
    stamp = time.strftime("%H:%M:%S")
    print(f"[{stamp}] {message}", flush=True)


def _load_data(root: Path) -> pd.DataFrame:
    path = root / "data" / "processed" / "process_named.parquet"
    if not path.exists():
        raise FileNotFoundError(
            "Processed Parquet cache not found. Run scripts/1_inspect_data.py first: "
            f"{path}"
        )
    log(f"Loading processed data: {path}")
    df = pd.read_parquet(path)
    log(f"Loaded {len(df):,} rows across {df[BATCH].nunique()} batches")
    return df


def _partition(df: pd.DataFrame, root: Path):
    splits_path = root / "results" / "splits.json"
    if not splits_path.exists():
        raise FileNotFoundError(
            "results/splits.json not found; run scripts/2_monitoring.py first."
        )
    splits = json.loads(splits_path.read_text())
    train_batches = np.asarray(splits["train_batches"], dtype=int)
    test_batches = np.asarray(splits["test_batches"], dtype=int)

    if set(train_batches) & set(test_batches):
        raise ValueError("Batch leakage detected: train and test batches overlap.")

    train = df[df[BATCH].isin(train_batches)]
    test = df[df[BATCH].isin(test_batches)]
    rng = np.random.default_rng(int(splits["seed"]))
    train_ids = np.asarray(sorted(set(train_batches.tolist())), dtype=int)
    if len(train_ids) < 3:
        raise ValueError("At least three training batches are needed for train/validation.")
    n_val = max(1, int(round(0.15 * len(train_ids))))
    n_val = min(n_val, len(train_ids) - 1)
    val_ids = set(rng.choice(train_ids, size=n_val, replace=False).tolist())
    val = train[train[BATCH].isin(val_ids)]
    fit = train[~train[BATCH].isin(val_ids)]

    if set(fit[BATCH].unique()) & set(val[BATCH].unique()):
        raise ValueError("Batch leakage detected between fit and validation partitions.")
    log(
        f"Batch split: fit={fit[BATCH].nunique()} | "
        f"validation={val[BATCH].nunique()} | test={test[BATCH].nunique()} "
        "(complete batches; test remains untouched)"
    )
    return fit, val, test


def _clean_rows(frame: pd.DataFrame, features: list[str], target: str) -> pd.DataFrame:
    required = [BATCH, TIME, target, *features]
    clean = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=required)
    return clean.sort_values([BATCH, TIME]).reset_index(drop=True)


def _limit_training_windows(X, y, meta, max_windows: int, seed: int):
    """Bound GRU training time while retaining representation from each batch."""
    if max_windows <= 0 or len(X) <= max_windows:
        return X, y, meta

    rng = np.random.default_rng(seed)
    batch_indices = meta.groupby(BATCH, sort=True).indices
    if not batch_indices:
        raise ValueError("No training windows available.")

    # Allocate a proportional quota to each batch, then use spare capacity.
    selected = []
    all_indices = np.arange(len(meta))
    for _, indices in batch_indices.items():
        quota = max(1, int(round(max_windows * len(indices) / len(meta))))
        take = min(len(indices), quota)
        selected.extend(rng.choice(indices, size=take, replace=False).tolist())

    selected = np.asarray(sorted(set(selected)), dtype=int)
    if len(selected) > max_windows:
        selected = np.sort(rng.choice(selected, size=max_windows, replace=False))
    elif len(selected) < max_windows:
        remaining = np.setdiff1d(all_indices, selected, assume_unique=False)
        extra = rng.choice(
            remaining, size=min(max_windows - len(selected), len(remaining)),
            replace=False,
        )
        selected = np.sort(np.concatenate([selected, extra]))

    return X[selected], y[selected], meta.iloc[selected].reset_index(drop=True)


def _standardize_windows(X_train, X_val, X_test):
    """Fit per-feature standardization on training windows only."""
    mean = X_train.mean(axis=(0, 1), keepdims=True)
    scale = X_train.std(axis=(0, 1), keepdims=True)
    scale = np.where(scale < 1e-8, 1.0, scale)

    def transform(values):
        return np.asarray((values - mean) / scale, dtype=np.float32)

    return transform(X_train), transform(X_val), transform(X_test), mean, scale


def _persistence_baseline(meta_test: pd.DataFrame, df_test: pd.DataFrame,
                          target: str) -> np.ndarray:
    """Fast last-observed-value baseline, calculated independently per batch."""
    preds = np.full(len(meta_test), np.nan, dtype=float)
    for batch_id, positions in meta_test.groupby(BATCH, sort=False).indices.items():
        sub = df_test[df_test[BATCH] == batch_id].sort_values(TIME)
        times = sub[TIME].to_numpy(dtype=float)
        values = sub[target].to_numpy(dtype=float)
        anchors = meta_test.iloc[positions][TIME].to_numpy(dtype=float)
        loc = np.searchsorted(times, anchors, side="right") - 1
        valid = loc >= 0
        batch_preds = np.full(len(positions), np.nan, dtype=float)
        batch_preds[valid] = values[loc[valid]]
        preds[positions] = batch_preds
    return preds


def _baseline_regressor(name: str, X_train: np.ndarray, y_train: np.ndarray,
                        X_test: np.ndarray, seed: int) -> np.ndarray:
    """Fit fast classical baselines on exactly the same flattened windows."""
    x_train = X_train.reshape(len(X_train), -1)
    x_test = X_test.reshape(len(X_test), -1)
    if name == "ridge":
        model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    elif name == "random_forest":
        model = RandomForestRegressor(
            n_estimators=100, max_depth=16, min_samples_leaf=3,
            max_features=0.8, random_state=seed, n_jobs=-1,
        )
    else:
        raise ValueError(f"Unknown baseline: {name}")
    model.fit(x_train, y_train)
    return model.predict(x_test)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["dense", "sparse"], default="dense")
    parser.add_argument("--epochs", type=int, default=None,
                        help="Override the configured maximum number of epochs.")
    parser.add_argument("--max-train-windows", type=int, default=None,
                        help="Override the cap on GRU training windows; 0 means no cap.")
    parser.add_argument("--top-k-features", type=int, default=None,
                        help="Override the number of top-ranked input features.")
    args = parser.parse_args()

    started = time.perf_counter()
    cfg = Config.from_yaml()
    root = cfg.root
    gc = cfg.data.get("gru_forecasting", {})
    seed = int(gc.get("seed", 0))
    features = list(SOFT_SENSOR_FEATURES)
    target = TARGET_COL_DENSE if args.mode == "dense" else TARGET_COL_SPARSE
    lookback = int(gc.get("lookback", 24))
    horizon = int(gc.get("horizon", 12))
    epochs = int(args.epochs if args.epochs is not None else gc.get("epochs", 20))
    max_train_windows = int(
        args.max_train_windows if args.max_train_windows is not None
        else gc.get("max_train_windows", 20000)
    )
    top_k = int(
        args.top_k_features if args.top_k_features is not None
        else gc.get("top_k_features", 6)
    )
    run_label = str(gc.get("run_label", "quick_v1"))

    print("\n" + "=" * 68, flush=True)
    log(f"PHASE 5 — GRU PENICILLIN FORECASTING ({args.mode.upper()} MODE)")
    log(f"Target: {target} | lookback: {lookback} rows | horizon: {horizon} rows")
    log(f"PyTorch: {torch.__version__} | CUDA available: {torch.cuda.is_available()}")
    print("=" * 68, flush=True)

    df = _load_data(root)
    fit, val, test = _partition(df, root)

    fit_rows = fit if args.mode == "dense" else fit[fit[target].notna()]
    val_rows = val if args.mode == "dense" else val[val[target].notna()]
    test_rows = test if args.mode == "dense" else test[test[target].notna()]
    fit_rows = _clean_rows(fit_rows, features, target)
    val_rows = _clean_rows(val_rows, features, target)
    test_rows = _clean_rows(test_rows, features, target)
    log(
        f"Usable rows — fit: {len(fit_rows):,} | "
        f"validation: {len(val_rows):,} | test: {len(test_rows):,}"
    )

    # Feature ranking uses only fit batches and a bounded per-batch sample.
    log("Step 1/6: ranking input features on training batches only")
    fs = select_features(
        fit_rows, features, target, seed=seed,
        model_kind=str(gc.get("feature_selector", "random_forest")),
        n_splits=int(gc.get("feature_folds", 3)),
        n_estimators=int(gc.get("feature_trees", 60)),
        max_rows_per_batch=int(gc.get("feature_max_rows_per_batch", 500)),
        verbose=True,
    )
    selected_features = fs["ranking"][:max(1, min(top_k, len(fs["ranking"]))) ]
    log("Selected features: " + ", ".join(selected_features))

    # Build windows batch-by-batch; no window crosses a batch boundary.
    log("Step 2/6: creating temporal windows")
    X_tr, y_tr, meta_tr = build_windows(fit_rows, lookback, horizon,
                                         selected_features, target)
    X_va, y_va, _ = build_windows(val_rows, lookback, horizon,
                                   selected_features, target)
    X_te, y_te, meta_te = build_windows(test_rows, lookback, horizon,
                                         selected_features, target)
    windows_before_cap = len(X_tr)
    X_tr, y_tr, meta_tr = _limit_training_windows(
        X_tr, y_tr, meta_tr, max_train_windows, seed
    )
    log(
        f"Windows — train: {len(X_tr):,}/{windows_before_cap:,} "
        f"(cap={max_train_windows:,}) | validation: {len(X_va):,} | "
        f"test: {len(X_te):,}"
    )

    if not all(len(a) for a in (X_tr, X_va, X_te)):
        raise ValueError("At least one split produced zero windows; check lookback/horizon.")

    log("Step 3/6: standardizing inputs using training windows only")
    X_tr, X_va, X_te, feature_mean, feature_scale = _standardize_windows(
        X_tr.astype(np.float32), X_va.astype(np.float32), X_te.astype(np.float32)
    )
    if not all(np.isfinite(a).all() for a in (X_tr, X_va, X_te, y_tr, y_va, y_te)):
        raise ValueError("Non-finite values remain in the model arrays after cleaning.")

    log("Step 4/6: training the GRU (epoch-level progress follows)")
    model, hist = train_forecaster(
        X_tr, y_tr, X_va, y_va,
        hidden_size=int(gc.get("hidden_size", 32)),
        num_layers=int(gc.get("num_layers", 1)),
        dropout=float(gc.get("dropout", 0.0)),
        batch_size=int(gc.get("batch_size", 128)),
        epochs=epochs,
        lr=float(gc.get("lr", 1e-3)),
        weight_decay=float(gc.get("weight_decay", 1e-5)),
        grad_clip=float(gc.get("grad_clip", 1.0)),
        patience=int(gc.get("patience", 5)),
        seed=seed,
        verbose=True,
    )
    y_gru = predict(model, X_te)

    log("Step 5/6: fitting persistence, Ridge and Random Forest baselines")
    y_persist = _persistence_baseline(meta_te, test_rows, target)
    y_ridge = _baseline_regressor("ridge", X_tr, y_tr, X_te, seed)
    y_rf = _baseline_regressor("random_forest", X_tr, y_tr, X_te, seed)

    valid = np.isfinite(y_persist) & np.isfinite(y_te)
    reports = {
        "persistence": score_metrics(y_te[valid], y_persist[valid]),
        "ridge": score_metrics(y_te, y_ridge),
        "random_forest": score_metrics(y_te, y_rf),
        "gru": score_metrics(y_te, y_gru),
    }

    per_batch = {}
    batch_eval = pd.DataFrame({
        "batch": meta_te[BATCH].to_numpy(), "y_true": y_te, "y_gru": y_gru,
    })
    for batch_id, group in batch_eval.groupby("batch"):
        per_batch[int(batch_id)] = score_metrics(
            group["y_true"].to_numpy(), group["y_gru"].to_numpy()
        )

    run_id = f"{args.mode}_L{lookback}_h{horizon}_{run_label}"
    out_dir = root / "results" / "phase5_gru" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "mode": args.mode,
        "target": str(target),
        "features": selected_features,
        "candidate_features": features,
        "feature_selection": fs,
        "lookback": lookback,
        "horizon": horizon,
        "seed": seed,
        "n_features": int(X_tr.shape[2]),
        "n_train_windows_before_cap": int(windows_before_cap),
        "n_train_windows": int(len(X_tr)),
        "n_val_windows": int(len(X_va)),
        "n_test_windows": int(len(X_te)),
        "training_config": {
            "hidden_size": int(gc.get("hidden_size", 32)),
            "num_layers": int(gc.get("num_layers", 1)),
            "batch_size": int(gc.get("batch_size", 128)),
            "max_epochs": epochs,
            "early_stopping_patience": int(gc.get("patience", 5)),
            "max_train_windows": max_train_windows,
        },
        "feature_scaler": {
            "mean": feature_mean.reshape(-1).tolist(),
            "scale": feature_scale.reshape(-1).tolist(),
            "fit_on": "training windows only",
        },
        "target_scale_note": (
            "Feature inputs are standardized using training windows only. "
            "Penicillin targets and reported MAE/RMSE remain on the original g/L scale. "
            "Validation MSE is therefore in (g/L)^2."
        ),
        "metrics": reports,
        "per_batch_gru": per_batch,
        "best_epoch": hist["best_epoch"],
        "best_val_mse_g_l2": hist["best_val_loss"],
        "train_history": hist["history"],
        "paper_status": (
            "Paper-inspired experiment. Hyperparameters are project-selected "
            "defaults, not claimed published values; this is not an exact reproduction."
        ),
        "elapsed_seconds": round(time.perf_counter() - started, 2),
    }

    log("Step 6/6: saving metrics, predictions and model checkpoint")
    (out_dir / "metrics.json").write_text(
        json.dumps(report, indent=2, allow_nan=False), encoding="utf-8"
    )
    pred_df = pd.DataFrame({
        "batch": meta_te[BATCH].to_numpy(),
        "time_h": meta_te[TIME].to_numpy(),
        "target_time_h": meta_te["target_time_h"].to_numpy(),
        "y_true": y_te,
        "y_persistence": y_persist,
        "y_ridge": y_ridge,
        "y_rf": y_rf,
        "y_gru": y_gru,
    })
    pred_df.to_csv(out_dir / "per_batch_predictions.csv", index=False)
    torch.save({
        "model_state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
        "selected_features": selected_features,
        "feature_mean": feature_mean.reshape(-1),
        "feature_scale": feature_scale.reshape(-1),
        "lookback": lookback,
        "horizon": horizon,
        "mode": args.mode,
        "training_config": report["training_config"],
    }, out_dir / "gru_checkpoint.pt")

    print("\nMODEL COMPARISON (test batches; MAE/RMSE in g/L)", flush=True)
    print("-" * 68, flush=True)
    for name, values in reports.items():
        print(
            f"{name:16s} MAE={values['mae']:.4f} | "
            f"RMSE={values['rmse']:.4f} | R2={values['r2']:.4f}",
            flush=True,
        )
    print("-" * 68, flush=True)
    log(f"Best epoch: {hist['best_epoch']} | best validation MSE: {hist['best_val_loss']:.6f} (g/L)^2")
    log(f"Saved results to: {out_dir}")
    log(f"Total elapsed time: {report['elapsed_seconds']:.1f} seconds")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"PHASE 5 ERROR: {exc}", file=sys.stderr, flush=True)
        sys.exit(2)
