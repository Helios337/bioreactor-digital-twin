"""Golden-batch monitoring: reference bands, deviation scores, alarms.

The method follows the golden-batch deviation approach of Luo et al. 2024,
adapted to streaming operation: reference bands are built per time point
from healthy training batches of the same control regime, and each running
batch is scored against those bands at the current time.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

GRID_STEP_H = 0.2


def reference_grid(train_batches: pd.DataFrame, time_col: str = "time_h",
                   max_h: float | None = None, step_h: float = GRID_STEP_H) -> np.ndarray:
    """Interpolation grid for building golden bands.

    The grid runs from the step to the mean training-batch span, rounded down
    to a multiple of the step.
    """
    spans = train_batches.groupby("batch")[time_col].max()
    end = float(spans.mean()) if max_h is None else float(max_h)
    grid = np.arange(step_h, end + 1e-9, step_h)
    if len(grid) == 0:
        raise ValueError("empty reference grid: no training data")
    return grid


def _interp_batch(batch_df: pd.DataFrame, grid: np.ndarray, var: str, time_col: str) -> np.ndarray:
    t = batch_df[time_col].to_numpy(dtype=float)
    x = batch_df[var].to_numpy(dtype=float)
    return np.interp(grid, t, x)


def build_golden_bands(train_batches: pd.DataFrame, variables: list[str],
                       k: float = 3.0, time_col: str = "time_h",
                       grid: np.ndarray | None = None) -> dict[str, np.ndarray]:
    """Per-variable, per-time-point mean and upper/lower bands.

    Returns a dict with keys "grid", "mean" (array of per-variable means),
    "upper", and "lower", each of shape (len(grid), n_variables).
    """
    if grid is None:
        grid = reference_grid(train_batches, time_col)
    n_t = len(grid)
    n_v = len(variables)
    means = np.zeros((n_t, n_v))
    upper = np.zeros((n_t, n_v))
    lower = np.zeros((n_t, n_v))
    for j, var in enumerate(variables):
        mat = np.stack(
            [_interp_batch(b, grid, var, time_col) for _, b in train_batches.groupby("batch")]
        )
        m = mat.mean(axis=0)
        s = mat.std(axis=0)
        band = k * np.where(np.isfinite(s), s, 0.0)
        means[:, j] = m
        upper[:, j] = m + band
        lower[:, j] = m - band
    return {"grid": grid, "variables": list(variables), "mean": means,
            "upper": upper, "lower": lower}


def deviation_series(batch_df: pd.DataFrame, bands: dict, variables: list[str] | None = None,
                     time_col: str = "time_h", eps: float = 1e-9,
                     std_rel_floor: float = 0.02, std_abs_floor: float = 0.05) -> pd.DataFrame:
    """Per-variable deviation of a batch vs the golden bands.

    Two scalings are provided.

    ``zscore`` is the dimensionless standardized deviation of each variable at
    each time point, (x - mean) / (k * std), clipped at zero in sign. The
    aggregate columns ``z_mean`` and ``z_max`` are the mean and the maximum
    across variables. The standard deviation is floored by a relative fraction
    of the absolute mean plus an absolute floor, so that variables at the
    physical zero of their range do not produce infinitesimal denominators.

    ``deviation_pct`` is the symmetric mean absolute percentage deviation for
    interpretive reporting and is floored by ``eps`` to avoid division blow-up.

    Returns a DataFrame with time_h, per-variable zscore and pct columns, and
    the aggregates ``z_mean``, ``z_max``, and ``deviation_pct``.
    """
    grid = bands["grid"]
    variables = list(variables or bands["variables"])
    means = bands["mean"]
    std_raw = np.maximum((bands["upper"] - bands["lower"]) / 2.0, eps)
    std_based = np.maximum(std_raw, std_rel_floor * np.abs(means) + std_abs_floor)
    out: dict[str, np.ndarray] = {"time_h": grid}
    z_all: list[np.ndarray] = []
    pct_all: list[np.ndarray] = []
    for j, var in enumerate(variables):
        x = _interp_batch(batch_df, grid, var, time_col)
        m = means[:, j]
        s = std_based[:, j]
        z = (x - m) / s
        out[f"z_{var}"] = z
        z_all.append(np.abs(z))
        denom = np.maximum((np.abs(x) + np.abs(m)) / 2.0, eps)
        pct = 100.0 * np.abs(x - m) / denom
        out[f"pct_{var}"] = pct
        pct_all.append(pct)
    out["z_mean"] = np.mean(z_all, axis=0)
    out["z_max"] = np.max(z_all, axis=0)
    out["deviation_pct"] = np.mean(pct_all, axis=0)
    return pd.DataFrame(out)


def alarm_events(dev: np.ndarray, grid: np.ndarray, threshold: float,
                 min_duration_h: float) -> list[dict]:
    """Contiguous alarm episodes from a deviation series.

    An alarm begins when deviation exceeds ``threshold`` and ends when it drops
    back below it. Episodes shorter than ``min_duration_h`` are discarded.
    Returns a list of dicts with onset, offset, peak, and duration.
    """
    step = grid[1] - grid[0] if len(grid) > 1 else 1.0
    min_samples = max(1, int(round(min_duration_h / step)))
    above = dev > threshold
    events: list[dict] = []
    start = None
    for i, flag in enumerate(above):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            if i - start >= min_samples:
                events.append(_episode(grid, dev, start, i))
            start = None
    if start is not None and len(above) - start >= min_samples:
        events.append(_episode(grid, dev, start, len(above)))
    return events


def select_monitor_variables(train_batches: pd.DataFrame, variables: list[str],
                             time_col: str = "time_h",
                             rel_floor: float = 1e-4, abs_floor: float = 1e-6,
                             grid: np.ndarray | None = None) -> list[str]:
    """Keep monitor variables that actually vary across healthy batches.

    Constant or near-constant variables (for example a fixed recipe feed rate)
    have near-zero golden-band width, so any small deviation explodes in the
    standardized score. A variable is kept when its median across-time,
    across-batch standard deviation exceeds both an absolute floor and a
    fraction of its median absolute mean.
    """
    if grid is None:
        grid = reference_grid(train_batches, time_col)
    kept: list[str] = []
    for var in variables:
        mat = np.stack(
            [_interp_batch(b, grid, var, time_col) for _, b in train_batches.groupby("batch")]
        )
        med_std = float(np.median(mat.std(axis=0)))
        med_abs_mean = float(np.median(np.abs(mat.mean(axis=0))))
        threshold = max(rel_floor * med_abs_mean, abs_floor)
        if med_std >= threshold:
            kept.append(var)
    return kept


def _episode(grid: np.ndarray, dev: np.ndarray, i0: int, i1: int) -> dict:
    seg = dev[i0:i1]
    return {
        "onset_h": float(grid[i0]),
        "offset_h": float(grid[min(i1, len(grid) - 1)]),
        "peak": float(seg.max()),
        "duration_h": float(grid[min(i1, len(grid) - 1)] - grid[i0]),
    }
