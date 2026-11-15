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


def test_mpc_never_reads_true_state_from_missing_measurement():
    """A missing measurement component must not be filled from y_true.

    The MPC holds the last value from its sensor instead, so the controller has
    no oracle access to true state through a partially observed sensor.
    """
    from bioreactor_monitoring.control import Measurement
    policy = NonLinearMPC(params=BajpaiReussParams(), N=3, Sref=0.05,
                          initial_state=np.array([10.0, 0.05, 5.0, 100.0]))
    # Only substrate is observed; everything else missing.
    msg = Measurement(S=0.02)
    # True state says substrate = 0.99; the observed value must win, others hold.
    f1 = policy(1.0, np.array([50.0, 0.99, 99.0, 200.0]), msg)
    state_after = policy._last_state
    # The held state must reflect the measured S (0.02), not the true S (0.99).
    assert state_after[1] == pytest.approx(0.02, abs=1e-6)
    # Held components come from the declared initial conditions, not the true
    # hidden state (X=50, P=99, V=200 would leak if y_true were used).
    assert state_after[0] == pytest.approx(10.0, abs=1e-6)
    assert state_after[2] == pytest.approx(5.0, abs=1e-6)
    assert state_after[3] == pytest.approx(100.0, abs=1e-6)
    assert f1 is not None
