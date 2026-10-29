"""Tests for the nonlinear MPC controller."""

from __future__ import annotations

import numpy as np
import pytest

from bioreactor_monitoring.control import (
    IdentitySensor,
    Measurement,
    NonLinearMPC,
    run_batch,
)
from bioreactor_monitoring.simulator import BajpaiReussParams


def test_mpc_runs_and_respects_volume_limit():
    params = BajpaiReussParams()
    policy = NonLinearMPC(params=params, N=5, Sref=0.05, v_limit=130.0,
                          Fmax=0.3, wV=1000.0)
    res = run_batch(policy, IdentitySensor(), params, seed=0)
    summary = res["summary"]
    tr = res["trajectory"]
    assert summary["P_final_g_l"] > 0.0
    assert tr["V"].max() < 140.0          # volume constrained
    assert np.isfinite(summary["feed_total_l"])


def test_mpc_measurement_driven():
    policy = NonLinearMPC(params=BajpaiReussParams(), N=3, Sref=0.05)
    # low measured substrate should raise the feed
    f1 = policy(1.0, np.array([10.0, 0.01, 5.0, 100.0]),
                Measurement(X=10.0, S=0.01, P=5.0, V=100.0))
    assert f1 > 0.0


def test_mpc_robust_to_heavy_estimator_noise():
    from bioreactor_monitoring.control import NoisyEstimatorSensor
    params = BajpaiReussParams()
    policy = NonLinearMPC(params=params, N=5, Sref=0.05, wV=100.0)
    sensor = NoisyEstimatorSensor(sigma=0.5, seed=0)     # very noisy estimates
    res = run_batch(policy, sensor, params, seed=0, process_sigma=0.01)
    assert np.isfinite(res["summary"]["P_final_g_l"])
    assert res["summary"]["P_final_g_l"] >= 0.0
