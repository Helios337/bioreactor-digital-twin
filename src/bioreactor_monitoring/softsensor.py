"""Penicillin soft-sensor baselines.

Trains interpretable regression models (linear ridge and random forest) to
predict the sparse offline penicillin label from online variables, evaluated
on complete held-out batches. The feature set matches the published IndPenSim
baseline (Acosta-Pavas et al. 2024) so that numbers are comparable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from bioreactor_monitoring.preprocess import BATCH


@dataclass
class SoftSensorResult:
    model_name: str
    fitted: Pipeline | None
    predictions: pd.DataFrame  # batch, time_h, y_true, y_pred
    metrics: dict[str, float]


def build_feature_frame(df: pd.DataFrame, features: list[str],
                        time_col: str = "time_h") -> pd.DataFrame:
    """Assemble the feature matrix for labelled rows.

    Only rows with a non-null offline penicillin label are used as training and
    evaluation targets; features come from the same row's online variables.
    """
    labelled = df[df["p_offline_g_l"].notna()].copy()
    return labelled[[ "batch", time_col, *features, "p_offline_g_l"]]


def fit_predict(train_df: pd.DataFrame, test_df: pd.DataFrame,
                features: list[str], model_name: str, seed: int) -> SoftSensorResult:
    """Fit a model on training batches and predict on held-out batches."""
    tr = build_feature_frame(train_df, features)
    te = build_feature_frame(test_df, features)
    X_tr = tr[features].to_numpy(dtype=float)
    y_tr = tr["p_offline_g_l"].to_numpy(dtype=float)
    X_te = te[features].to_numpy(dtype=float)
    y_te = te["p_offline_g_l"].to_numpy(dtype=float)

    model = _make_model(model_name, seed)
    model.fit(X_tr, y_tr)
    y_pred = model.predict(X_te)
    predictions = pd.DataFrame({
        "batch": te["batch"].to_numpy(),
        "time_h": te["time_h"].to_numpy(),
        "y_true": y_te,
        "y_pred": y_pred,
    })
    metrics = score_metrics(y_te, y_pred)
    return SoftSensorResult(model_name=model_name, fitted=model,
                            predictions=predictions, metrics=metrics)


def predict_trajectories(train_df: pd.DataFrame, eval_df: pd.DataFrame,
                         features: list[str], model_name: str, seed: int,
                         oof_folds: int = 5) -> pd.DataFrame:
    """Leak-free trajectory-level predictions for monitoring.

    Returns a frame with columns batch, time_h, p_offline_g_l (label where
    present), and p_est.

    For training batches, predictions are out-of-fold at the trajectory level:
    in each GroupKFold split over batches, a model fitted on the other folds'
    labelled rows predicts every row of the current fold's batches. This keeps
    every training trajectory honest while covering the whole batch.

    For all other batches, a model fitted on the full training set predicts
    every row.
    """
    from sklearn.model_selection import GroupKFold

    tr = build_feature_frame(train_df, features)

    # Trajectory-level out-of-fold predictions for training batches.
    oof = np.full(len(train_df), np.nan)
    n_splits = min(oof_folds, train_df[BATCH].nunique())
    gkf = GroupKFold(n_splits=n_splits)
    for tr_idx, va_idx in gkf.split(tr[features].to_numpy(dtype=float),
                                    tr["p_offline_g_l"].to_numpy(dtype=float),
                                    tr["batch"].to_numpy()):
        va_batches = set(int(b) for b in tr.iloc[va_idx]["batch"].unique())
        model = _make_model(model_name, seed)
        model.fit(tr.iloc[tr_idx][features].to_numpy(dtype=float),
                  tr.iloc[tr_idx]["p_offline_g_l"].to_numpy(dtype=float))
        mask = train_df[BATCH].isin(list(va_batches)).to_numpy()
        oof[mask] = model.predict(train_df.loc[mask, features].to_numpy(dtype=float))
    tr_full = train_df.copy()
    tr_full["p_est"] = oof

    # Held-out predictions for every remaining row.
    model = _make_model(model_name, seed)
    model.fit(tr[features].to_numpy(dtype=float), tr["p_offline_g_l"].to_numpy(dtype=float))
    ev = eval_df.copy()
    ev["p_est"] = model.predict(ev[features].to_numpy(dtype=float))

    out = pd.concat([
        tr_full[["batch", "time_h", "p_offline_g_l", "p_est"]],
        ev[["batch", "time_h", "p_offline_g_l", "p_est"]],
    ], ignore_index=True)
    out["batch"] = out["batch"].astype(int)
    return out.sort_values(["batch", "time_h"]).reset_index(drop=True)


def _make_model(model_name: str, seed: int) -> Pipeline:
    if model_name == "ridge":
        return Pipeline([
            ("scale", StandardScaler()),
            ("reg", Ridge(alpha=1.0)),
        ])
    if model_name == "random_forest":
        return Pipeline([
            ("reg", RandomForestRegressor(n_estimators=300, min_samples_leaf=2,
                                          random_state=seed, n_jobs=-1)),
        ])
    raise ValueError(f"unknown model: {model_name}")


def score_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """MAE, RMSE, and R-squared."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"mae": mae, "rmse": rmse, "r2": r2}
