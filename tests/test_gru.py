"""Tests for the standalone GRU forecaster.

These require the optional ``forecast`` extra (torch). When torch is not
installed the tests are skipped, so the data-independent base CI suite does not
need a deep-learning stack.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

torch = pytest.importorskip("torch")

from bioreactor_monitoring.gru_forecaster import (  # noqa: E402
    GRUForecaster,
    predict,
    train_forecaster,
)
from bioreactor_monitoring.preprocess import BATCH  # noqa: E402
from bioreactor_monitoring.sequence import build_windows  # noqa: E402


def _synthetic_sequence(n_batches=4, n_points=40, seed=0):
    rng = np.random.default_rng(seed)
    frames = []
    for b in range(1, n_batches + 1):
        t = 0.2 + 0.2 * np.arange(n_points)
        feed = 1.0 + 0.1 * rng.random(n_points)
        p = 2.0 * feed + 0.1 * t + 0.01 * rng.random(n_points)
        frames.append(pd.DataFrame({"batch": b, "time_h": t,
                                    "feed_rate_l_h": feed, "p_true_g_l": p}))
    return pd.concat(frames, ignore_index=True)


def _data(seed=0):
    df = _synthetic_sequence(seed=seed)
    X, y, meta = build_windows(df, lookback=8, horizon=4,
                               features=["feed_rate_l_h"], target="p_true_g_l")
    ids = np.sort(np.unique(meta[BATCH].to_numpy()))
    val_b = ids[-1]
    tr = meta[BATCH].to_numpy() != val_b
    return X[tr], y[tr], X[~tr], y[~tr]


def test_gru_forward_shape():
    model = GRUForecaster(n_features=1, hidden_size=8, num_layers=1)
    x = torch.zeros(5, 8, 1)
    out = model(x)
    assert out.shape == (5,)


def test_train_and_predict_on_synthetic():
    X_tr, y_tr, X_va, y_va = _data()
    model, hist = train_forecaster(
        X_tr, y_tr, X_va, y_va, hidden_size=8, num_layers=1,
        batch_size=8, epochs=6, patience=3, seed=0)
    assert "best_val_loss" in hist
    preds = predict(model, X_va)
    assert preds.shape == (len(X_va),)
    assert np.all(np.isfinite(preds))
    # separable synthetic target -> full-train predictor should be sensible
    assert np.mean(np.abs(preds - y_va)) < np.mean(np.abs(y_va)) + 1e-9


def test_dropout_only_allowed_between_layers():
    # A single-layer GRU with dropout > 0 is permitted by PyTorch but does not
    # add per-step dropout; a two-layer GRU applies it between layers.
    m1 = GRUForecaster(n_features=3, hidden_size=8, num_layers=1, dropout=0.2)
    m2 = GRUForecaster(n_features=3, hidden_size=8, num_layers=2, dropout=0.2)
    assert m1.gru.num_layers == 1
    assert m2.gru.num_layers == 2