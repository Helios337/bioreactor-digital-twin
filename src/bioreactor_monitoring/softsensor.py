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

    if model_name == "ridge":
        model: Pipeline = Pipeline([
            ("scale", StandardScaler()),
            ("reg", Ridge(alpha=1.0)),
        ])
    elif model_name == "random_forest":
        model = Pipeline([
            ("reg", RandomForestRegressor(n_estimators=300, min_samples_leaf=2,
                                          random_state=seed, n_jobs=-1)),
        ])
    else:
        raise ValueError(f"unknown model: {model_name}")

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
