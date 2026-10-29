"""Tests for the soft-sensor module."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from bioreactor_monitoring.softsensor import (
    build_feature_frame,
    fit_predict,
    score_metrics,
)


def test_score_metrics_hand_values():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.0, 2.5, 3.0])
    m = score_metrics(y_true, y_pred)
    assert m["mae"] == pytest_approx(0.1666667)
    assert m["rmse"] == pytest_approx(0.2886751)
    assert m["r2"] == pytest_approx(0.875)


def pytest_approx(x):
    import pytest
    return pytest.approx(x, abs=1e-5)


def _synthetic(n_batches=6, seed=0):
    rng = np.random.default_rng(seed)
    frames = []
    for b in range(1, n_batches + 1):
        t = rng.uniform(20, 200, 20)
        y = 2.0 + 0.08 * t + rng.normal(0, 0.1, 20)
        x1 = 0.5 * y + rng.normal(0, 0.2, 20)
        frames.append(pd.DataFrame({
            "batch": b,
            "time_h": t,
            "feed_rate_l_h": x1,
            "temperature_k": 300.0 + 0.01 * t,
            "p_offline_g_l": y,
        }))
    return pd.concat(frames).reset_index(drop=True)


def test_build_feature_frame_keeps_labelled_rows():
    df = _synthetic()
    out = build_feature_frame(df, ["feed_rate_l_h", "temperature_k"])
    assert len(out) == len(df)
    assert set(["batch", "time_h", "p_offline_g_l"]).issubset(out.columns)


def test_fit_predict_runs_for_ridge_and_forest():
    df = _synthetic(n_batches=8)
    train = df[df["batch"] <= 6]
    test = df[df["batch"] > 6]
    for name in ("ridge", "random_forest"):
        res = fit_predict(train, test, ["feed_rate_l_h", "temperature_k"], name, seed=0)
        assert res.metrics["mae"] >= 0
        assert res.metrics["rmse"] >= 0
        assert np.isfinite(res.metrics["r2"])
        assert len(res.predictions) == len(test[test["p_offline_g_l"].notna()])


def test_fit_predict_rejects_unknown_model():
    df = _synthetic()
    train = df[df["batch"] <= 4]
    test = df[df["batch"] > 4]
    try:
        fit_predict(train, test, ["feed_rate_l_h"], "nope", seed=0)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_predict_trajectories_covers_all_training_rows():
    from bioreactor_monitoring.preprocess import P_OFFLINE
    from bioreactor_monitoring.softsensor import predict_trajectories

    df = _synthetic(n_batches=8, seed=1)
    train = df[df["batch"] <= 5]
    eval_df = df[df["batch"] > 5]
    out = predict_trajectories(train, eval_df, ["feed_rate_l_h", "temperature_k"],
                               "ridge", seed=0, oof_folds=3)
    assert out["p_est"].notna().all()          # no unfilled rows
    tr_out = out[out["batch"].isin(train["batch"].unique())]
    ev_out = out[out["batch"].isin(eval_df["batch"].unique())]
    assert len(tr_out) == len(train)            # every training row covered
    assert len(ev_out) == len(eval_df)
    assert out[P_OFFLINE].isna().sum() == (len(train) + len(eval_df) - int(df[P_OFFLINE].notna().sum()))
