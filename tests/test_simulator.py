"""Tests for the Bajpai-Reuss simulator and control layer."""

from __future__ import annotations

import numpy as np
import pytest

from bioreactor_monitoring.control import (
    ConstantFeed,
    DelayedAssaySensor,
    IdentitySensor,
    Measurement,
    NoisyEstimatorSensor,
    SubstratePI,
    run_batch,
)
from bioreactor_monitoring.simulator import BajpaiReussParams, simulate


def test_constant_feed_batch_is_bounded_and_positive():
    params = BajpaiReussParams()
    res = run_batch(ConstantFeed(F=0.10), IdentitySensor(), params, seed=0)
    tr = res["trajectory"]
    assert (tr[["X", "S", "P", "V"]].to_numpy() >= 0).all()
    assert tr["P"].iloc[-1] > 1.0              # product is produced
    assert tr["X"].iloc[-1] > 5.0              # biomass grows
    assert tr["V"].iloc[-1] > params.V0        # volume rises with feed
    assert np.isfinite(res["summary"]["P_mass_g"])


def test_batch_mass_balance_without_feed():
    """With no feed, integrated substrate uptake equals integrated conversion."""
    params = BajpaiReussParams()
    params.S0 = 50.0
    res = run_batch(ConstantFeed(F=0.0), IdentitySensor(), params,
                    tf_h=50.0, seed=1)
    tr = res["trajectory"]
    X, S, P = tr["X"].to_numpy(), tr["S"].to_numpy(), tr["P"].to_numpy()
    t = tr["time_h"].to_numpy()

    # ODE-consistent uptake, including the substrate-saturation factor.
    Se = np.maximum(S, 0.0)
    cons = Se / (Se + 1e-3)
    mu = params.mu_max * Se / (params.Kx * X + Se)
    pi = params.pi_max * Se / (params.Kp + Se * (1.0 + Se / params.Ki))
    uptake = ((mu / params.Yxs + pi / params.Yps) + params.m) * X * cons
    consumed = np.trapezoid(uptake, t)
    # mass withdrawn from the free substrate pool (V constant, no feed)
    withdrawn = params.S0 - S[-1]
    assert S[-1] >= -1e-6                      # no negative substrate
    assert abs(consumed - withdrawn) < 0.02 * max(withdrawn, 1e-9)


def test_identical_sensor_and_zero_noise_are_identical():
    p1 = BajpaiReussParams()
    a = run_batch(SubstratePI(), IdentitySensor(), p1, seed=3)
    b = run_batch(SubstratePI(), NoisyEstimatorSensor(sigma=0.0, seed=3),
                  p1, seed=3)
    # harness-level float differences are at the 1e-4 scale
    assert a["trajectory"]["P"].iloc[-1] == pytest.approx(
        b["trajectory"]["P"].iloc[-1], rel=1e-4)


def test_reproducible_with_seed():
    p1 = BajpaiReussParams()
    a = run_batch(SubstratePI(), IdentitySensor(), p1, seed=5, process_sigma=0.02)
    b = run_batch(SubstratePI(), IdentitySensor(), p1, seed=5, process_sigma=0.02)
    assert all(a["trajectory"]["P"].to_numpy() == b["trajectory"]["P"].to_numpy())


def test_delayed_assay_sensor_reveal_schedule():
    sensor = DelayedAssaySensor(interval_h=12.0, delay_h=4.0, seed=0, noise=0.0)
    y = np.array([10.0, 0.05, 5.0, 100.0])
    rng = np.random.default_rng(0)
    # before the first reveal, S is unknown
    assert sensor(0.0, y, rng).S is None
    m1 = sensor(1.0, y, rng).S      # sample at t=0, revealed at t=4
    assert m1 is None
    m4 = sensor(4.0, y, rng).S      # reveal at t=4
    assert m4 == pytest.approx(0.05)
    # sensor then holds the last revealed value until the next reveal
    m6 = sensor(6.0, y, rng).S
    assert m6 == pytest.approx(0.05)
    m13 = sensor(13.0, y, rng).S    # sample at t=12 revealed at t=16
    assert m13 == pytest.approx(0.05)
    m17 = sensor(17.0, y, rng).S
    assert m17 == pytest.approx(0.05)


def test_substrate_pi_respects_volume_limit():
    policy = SubstratePI(Sref=0.05, v_limit=130.0)
    meas = Measurement(S=0.05, X=10.0, P=5.0, V=131.0)
    f = policy(1.0, np.array([10.0, 0.05, 5.0, 131.0]), meas)
    assert f == 0.0
    policy = SubstratePI(Sref=0.05, Kp=20.0)
    meas = Measurement(S=0.02, X=10.0, P=5.0, V=100.0)
    f = policy(1.0, np.array([10.0, 0.02, 5.0, 100.0]), meas)
def test_substrate_pi_respects_volume_limit():
    policy = SubstratePI(Sref=0.05, v_limit=130.0)
    meas = Measurement(S=0.05, X=10.0, P=5.0, V=131.0)
    f = policy(1.0, np.array([10.0, 0.05, 5.0, 131.0]), meas)
    assert f == 0.0


def test_substrate_pi_uses_measured_substrate_only():
    policy = SubstratePI(Sref=0.05, Kp=20.0)
    meas = Measurement(S=0.02, X=10.0, P=5.0, V=100.0)
    f = policy(1.0, np.array([10.0, 0.02, 5.0, 100.0]), meas)
    assert f > policy.Fff                # substrate below ref -> feed up
    meas_low = Measurement(S=0.2, X=10.0, P=5.0, V=100.0)
    f2 = policy(2.0, np.array([10.0, 0.2, 5.0, 100.0]), meas_low)
    assert f2 <= policy.Fff + 1e-12      # substrate above ref -> feed down
