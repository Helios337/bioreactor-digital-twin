"""Tests for the golden-batch monitoring module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from bioreactor_monitoring.monitor import (
    alarm_events,
    build_golden_bands,
    deviation_series,
    reference_grid,
    select_monitor_variables,
)


def _healthy_batches(n_batches=5, n_points=50):
    frames = []
    grid = 0.2 + np.arange(n_points) * 0.2
    spreads = np.linspace(-0.002, 0.002, n_batches)
    for i, (b, delta) in enumerate(zip(range(1, n_batches + 1), spreads), start=1):
        frames.append(pd.DataFrame({
            "batch": b,
            "time_h": grid,
            "x": 1.0 + (0.05 + delta) * grid,
        }))
    return pd.concat(frames)


def _deviant_batch():
    grid = 0.2 + np.arange(50) * 0.2
    return pd.DataFrame({"batch": 99, "time_h": grid,
                         "x": 3.0 + grid * 0.05})


def test_reference_grid():
    df = _healthy_batches()
    grid = reference_grid(df, "time_h")
    assert grid[0] == pytest.approx(0.2)
    assert len(grid) == 50


def test_golden_bands_mean_and_width():
    df = _healthy_batches()
    bands = build_golden_bands(df, ["x"], k=3.0)
    grid_mean = 1.0 + bands["grid"] * 0.05
    assert np.allclose(bands["mean"][:, 0], grid_mean, atol=1e-6)
    # width must be strictly positive because slopes differ between batches
    assert np.all(bands["upper"][:, 0] > bands["lower"][:, 0])


def test_deviation_zero_for_identical_batch():
    df = _healthy_batches()
    bands = build_golden_bands(df, ["x"])
    # a new batch exactly on the golden mean line
    grid = bands["grid"]
    new = pd.DataFrame({"batch": 1, "time_h": grid,
                        "x": 1.0 + grid * 0.05})
    dev = deviation_series(new, bands, ["x"])
    assert dev["deviation_pct"].max() < 1e-9


def test_deviation_large_for_stray_batch():
    df = _healthy_batches()
    bands = build_golden_bands(df, ["x"])
    dev = deviation_series(_deviant_batch(), bands, ["x"])
    assert dev["deviation_pct"].max() > 20.0
    assert dev["z_mean"].max() > 1.0


def test_alarm_events_threshold_and_min_duration():
    grid = np.arange(0.0, 10.0, 0.2)
    dev = np.zeros_like(grid)
    dev[10:25] = 35.0            # exceeds threshold (30) for 3 h
    dev[40:42] = 35.0            # 0.4 h, must be discarded
    events = alarm_events(dev, grid, threshold=30.0, min_duration_h=1.0)
    assert len(events) == 1
    assert events[0]["onset_h"] == pytest.approx(2.0)
    assert events[0]["duration_h"] == pytest.approx(3.0)


def test_select_monitor_variables_drops_constants():
    grid = 0.2 + np.arange(50) * 0.2
    frames = []
    for b in range(1, 6):
        frames.append(pd.DataFrame({
            "batch": b,
            "time_h": grid,
            "varying": 1.0 + (0.05 + 0.001 * b) * grid,
            "constant": 8.0 * np.ones_like(grid),
        }))
    train = pd.concat(frames)
    kept = select_monitor_variables(train, ["varying", "constant"])
    assert kept == ["varying"]
