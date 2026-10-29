"""Fed-batch penicillin plant model (Bajpai-Reuss structure).

This is a project implementation of the classic unstructured penicillin
kinetics of Bajpai and Reuss (1980), used here only as a transparent plant for
matched, relative control experiments. It is not claimed to reproduce
IndPenSim or any industrial process.

States (per litre basis): X biomass (g/L), S substrate (g/L),
P penicillin (g/L), V liquid volume (L).

Kinetics:
    mu  = mu_max * S / (Kx * X + S)
    pi  = pi_max * S / (Kp + S * (1 + S / Ki))
    dX/dt = mu * X - (F/V) * X
    dP/dt = pi * X - k_h * P - (F/V) * P
    dS/dt = -(mu / Yxs) * X - (pi / Yps) * X - m * X + (F/V) * (Sf - S)
    dV/dt = F

The parameter values below are documented implementation choices consistent
with the classical penicillin fed-batch control testbed literature (Bajpai and
Reuss 1980; Bajpai and Reuss 1981; San and Stephanopoulos 1989).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

STATE_NAMES = ("X", "S", "P", "V")


@dataclass
class BajpaiReussParams:
    mu_max: float = 0.092      # maximum specific growth rate, 1/h
    Kx: float = 0.006          # growth saturation constant (dimensionless with X)
    pi_max: float = 0.01       # maximum specific production rate, 1/h
    Kp: float = 0.0001         # production saturation constant, g/L
    Ki: float = 0.1            # substrate inhibition constant, g/L
    Yxs: float = 0.45          # biomass yield on substrate, g/g
    Yps: float = 1.2           # product yield on substrate, g/g
    m: float = 0.014           # maintenance coefficient, 1/h
    k_h: float = 0.01          # penicillin hydrolysis rate, 1/h
    Sf: float = 500.0          # substrate feed concentration, g/L
    X0: float = 1.5            # initial biomass, g/L
    S0: float = 0.0            # initial substrate, g/L
    P0: float = 0.0            # initial penicillin, g/L
    V0: float = 100.0          # initial volume, L


def rhs(t: float, y: np.ndarray, params: BajpaiReussParams,
        feed: float) -> np.ndarray:
    """Right-hand side of the fed-batch model for a given feed rate F.

    Substrate enters the kinetics as ``max(S, 0)`` so that numeric dips below
    zero cannot produce negative growth or production rates that destabilize
    the integrator.
    """
    X, S, P, V = y
    V = max(V, 1e-6)
    S_eff = max(S, 0.0)
    mu = params.mu_max * S_eff / (params.Kx * X + S_eff + 1e-12)
    pi = params.pi_max * S_eff / (params.Kp + S_eff * (1.0 + S_eff / params.Ki) + 1e-12)
    # Substrate consumption scales with available substrate, so it vanishes
    # when the substrate is exhausted and can never drive S below zero.
    cons = S_eff / (S_eff + 1e-3)
    F = feed
    dX = mu * X - (F / V) * X
    dP = pi * X - params.k_h * P - (F / V) * P
    dS = -(mu / params.Yxs) * X * cons - (pi / params.Yps) * X * cons \
        - params.m * X * cons + (F / V) * (params.Sf - S)
    dV = F
    # derivative order must match the state order [X, S, P, V]
    return np.array([dX, dS, dP, dV])


def simulate(policy, params: BajpaiReussParams, tf_h: float = 220.0,
             dt_control_h: float = 1.0, dt_max_h: float = 0.05,
             seed: int | None = None, process_sigma: float = 0.0,
             sensor=None, sensor_rng=None) -> dict:
    """Closed-loop simulation of the plant under a feed policy.

    ``policy`` must be callable: policy(t, y_true, measurement) -> feed rate,
    where ``measurement`` is a Measurement produced by ``sensor``.
    ``sensor`` must be callable: sensor(t, y_true, rng) -> Measurement, and may
    be an oracle (true state), a noisy estimator, or a delayed assay layer.
    The feed is held constant over each control interval.

    Returns a dict with "trajectory" DataFrame (time, X, S, P, V, F) and
    "summary" outcome metrics.
    """
    from bioreactor_monitoring.control import IdentitySensor

    rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng()
    srng = sensor_rng if sensor_rng is not None else rng
    sensor = sensor if sensor is not None else IdentitySensor()
    y0 = np.array([params.X0, params.S0, params.P0, params.V0])

    t_control = 0.0
    times = [0.0]
    states = [y0.copy()]
    feeds = [0.0]
    measurement = sensor(0.0, y0, srng)

    while t_control < tf_h - 1e-9:
        feed = float(np.clip(policy(t_control, states[-1], measurement), 0.0, None))
        sol = solve_ivp(
            rhs, (t_control, min(t_control + dt_control_h, tf_h)), states[-1],
            args=(params, feed), method="LSODA", rtol=1e-7, atol=1e-9,
            max_step=dt_max_h,
        )
        t_end = float(sol.t[-1])
        y_end = sol.y[:, -1].copy()
        if not np.all(np.isfinite(y_end)):
            raise FloatingPointError(
                f"non-finite plant state at t={t_end:.1f} under feed {feed:.4f}; "
                "last finite state " + str(np.round(states[-1], 6)))
        if process_sigma > 0:
            y_end = y_end + rng.normal(0.0, process_sigma * np.abs(y_end))
            y_end = np.maximum(y_end, 0.0)
        times.append(t_end)
        states.append(y_end)
        feeds.append(feed)
        measurement = sensor(t_end, y_end, srng)
        t_control = t_end

    arr = np.array(states)
    t = np.array(times)
    dt = np.concatenate([[0.0], np.diff(t)])
    out = pd.DataFrame({
        "time_h": t,
        "X": arr[:, 0], "S": arr[:, 1], "P": arr[:, 2], "V": arr[:, 3],
        "F": np.array(feeds),
    })
    summary = {
        "P_final_g_l": float(out["P"].iloc[-1]),
        "P_mass_g": float(out["P"].iloc[-1] * out["V"].iloc[-1]),
        "X_final_g_l": float(out["X"].iloc[-1]),
        "V_final_l": float(out["V"].iloc[-1]),
        "feed_total_l": float(np.sum(feeds[1:] * dt[1:])),
        "S_max_g_l": float(out["S"].max()),
        "S_rmse_g_l": float(np.sqrt(np.mean(out["S"] ** 2))),
        "constraint_violations": int((out["V"].to_numpy() > 1.35 * params.V0).sum()),
        "max_feed_l_h": float(np.max(feeds)),
    }
    return {"trajectory": out, "summary": summary}
