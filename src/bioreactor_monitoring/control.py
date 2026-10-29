"""Control layer for the fed-batch plant: sensors, feed policies, runner.

The experiments compare feed policies under matched conditions, with the only
difference being the sensing layer through which the controller observes the
plant: the true state (oracle), a noisy estimator of tunable accuracy
(soft-sensor-like), or the delayed off-line assay stream (12 h + 4 h delay).

The estimation-error sweep varies the noise level of the estimator sensor and
measures how final penicillin outcome degrades.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.integrate import solve_ivp

from bioreactor_monitoring.simulator import rhs, simulate, BajpaiReussParams


@dataclass
class Measurement:
    X: float | None = None
    S: float | None = None
    P: float | None = None
    V: float | None = None


@dataclass
class IdentitySensor:
    """Oracle: the controller sees the exact plant state."""

    def __call__(self, t: float, y: np.ndarray, rng) -> Measurement:
        return Measurement(*y)


@dataclass
class NoisyEstimatorSensor:
    """Soft-sensor-like estimator with relative accuracy sigma per state."""

    sigma: float = 0.0
    seed: int = 0

    def __post_init__(self):
        self._rng = np.random.default_rng(self.seed)

    def __call__(self, t: float, y: np.ndarray, rng) -> Measurement:
        noise = rng.normal(0.0, self.sigma, 4)
        m = np.maximum(y * (1.0 + noise), 0.0)
        return Measurement(*m)


@dataclass
class DelayedAssaySensor:
    """Off-line assay every interval_h, revealed delay_h later.

    Between revelations the controller holds the last revealed values
    (zero-order hold). Unknown states are None.
    """

    interval_h: float = 12.0
    delay_h: float = 4.0
    seed: int = 0
    noise: float = 0.01

    def __post_init__(self):
        self._rng = np.random.default_rng(self.seed)
        self._next_sample = 0.0
        self._pending: list[tuple[float, Measurement]] = []
        self._last_revealed: Measurement = Measurement()

    def __call__(self, t: float, y: np.ndarray, rng) -> Measurement:
        # Take a sample at the scheduled time.
        if t >= self._next_sample - 1e-9:
            vals = y * (
                1.0 + rng.normal(0.0, self.noise, 4) if self.noise > 0 else 1.0
            )
            self._pending.append((t + self.delay_h, Measurement(*np.maximum(vals, 0.0))))
            self._next_sample = t + self.interval_h
        while self._pending and self._pending[0][0] <= t + 1e-9:
            self._last_revealed = self._pending.pop(0)[1]
        return self._last_revealed


@dataclass
class SubstratePI:
    """Feed policy regulating estimated substrate to a setpoint.

    F = clip(ff + Kp * e + Ki * integral(e), Fmin, Fmax), e = Sref - S_hat.
    The controller ignores states the sensor does not provide, and stops
    feeding when the measured volume approaches the configured limit.
    """

    Sref: float = 0.05
    Kp: float = 20.0
    Ki: float = 2.0
    Fff: float = 0.05
    Fmin: float = 0.0
    Fmax: float = 0.3
    v_limit: float | None = None
    dt_h: float = 1.0

    def __post_init__(self):
        self._integral = 0.0
        self._last_t: float | None = None

    def __call__(self, t: float, y_true: np.ndarray, measurement: Measurement) -> float:
        if measurement.V is not None and self.v_limit is not None \
                and measurement.V >= self.v_limit:
            return 0.0
        if measurement.S is None:
            return self.Fff
        if self._last_t is not None:
            self._integral += (t - self._last_t) * (self.Sref - measurement.S)
        self._last_t = t
        e = self.Sref - measurement.S
        F = self.Fff + self.Kp * e + self.Ki * self._integral
        return float(np.clip(F, self.Fmin, self.Fmax))


@dataclass
class ConstantFeed:
    """Conventional recipe baseline: a fixed feed rate."""

    F: float = 0.10

    def __call__(self, t: float, y_true: np.ndarray, measurement: Measurement) -> float:
        return self.F


@dataclass
class NonLinearMPC:
    """Constrained nonlinear MPC on the plant model (receding horizon).

    The controller predicts with the plant model from its current state
    estimate, and solves for the feed sequence minimising squared substrate
    regulation error, a large penalty for violating the volume limit, and a
    move-suppression term. Only the first move is applied.

    The horizon is N control steps; the volume limit is enforced as an
    inequality constraint in the optimization.
    """

    params: BajpaiReussParams = field(default_factory=BajpaiReussParams)
    N: int = 5
    wS: float = 1.0
    wV: float = 100.0          # penalty on volume above the limit (soft)
    lam: float = 1e-3          # move suppression
    Sref: float = 0.03
    Fmax: float = 0.3
    v_limit: float = 130.0
    dt_h: float = 1.0

    def __post_init__(self):
        self._last_u: np.ndarray | None = None

    def __call__(self, t: float, y_true: np.ndarray, measurement: Measurement) -> float:
        from scipy.optimize import minimize

        state = np.array([
            measurement.X if measurement.X is not None else y_true[0],
            measurement.S if measurement.S is not None else y_true[1],
            measurement.P if measurement.P is not None else y_true[2],
            measurement.V if measurement.V is not None else y_true[3],
        ], dtype=float)
        dt = self.dt_h

        def rollout(u: np.ndarray) -> np.ndarray:
            y = state.copy()
            out = [y]
            for f in u:
                sol = solve_ivp(rhs, (0.0, dt), y, args=(self.params, float(f)),
                                method="LSODA", rtol=1e-6, atol=1e-8, max_step=dt / 5.0)
                y = sol.y[:, -1]
                out.append(y)
            return np.array(out[1:])          # states at steps 1..N

        def cost(u: np.ndarray) -> float:
            steps = rollout(u)
            s_trajectory = steps[:, 1]
            v_trajectory = steps[:, 3]
            j = self.wS * np.sum((s_trajectory - self.Sref) ** 2)
            j += self.wV * np.sum(np.maximum(v_trajectory - self.v_limit, 0.0) ** 2)
            if self._last_u is not None and len(self._last_u) == len(u):
                j += self.lam * np.sum((u - self._last_u) ** 2)
            return float(j)

        bounds = [(0.0, self.Fmax)] * self.N
        x0 = (self._last_u if self._last_u is not None else np.full(self.N, 0.05)).copy()
        res = minimize(cost, x0, method="SLSQP", bounds=bounds,
                       options={"maxiter": 100, "ftol": 1e-9})
        u = np.clip(res.x, 0.0, self.Fmax)
        self._last_u = u
        return float(u[0])


def run_batch(policy, sensor, params: BajpaiReussParams, tf_h: float = 220.0,
              dt_control_h: float = 1.0, seed: int = 0, process_sigma: float = 0.0) -> dict:
    """Run one closed-loop batch with the given policy and sensing layer."""
    rng = np.random.default_rng(seed)
    return simulate(policy, params, tf_h=tf_h, dt_control_h=dt_control_h,
                    seed=seed, process_sigma=process_sigma,
                    sensor=sensor, sensor_rng=rng)
