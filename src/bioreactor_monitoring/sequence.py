"""Sliding-window sequence construction for time-series forecasting.

The builder keeps every window fully inside one batch, requires strictly
ordered timestamps within each batch, and produces a direct-horizon target
``P(t + h)`` from input rows up to and including ``t`` so no future data leaks
into the predictors.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from bioreactor_monitoring.preprocess import BATCH, TIME


def build_windows(df: pd.DataFrame, lookback: int, horizon: int,
                  features: list[str], target: str,
                  batch_col: str = BATCH, time_col: str = TIME) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build sliding windows with a direct-horizon target.

    Each input window is the last ``lookback`` rows ending at row ``i`` and the
    target is the ``target`` value at row ``i + horizon``. Windows never cross a
    batch boundary: a window whose end would overlap the next batch is dropped.
    Timestamps within a batch must be strictly increasing.

    Returns ``(X, y, meta)`` where ``X`` has shape
    ``(samples, lookback, n_features)``, ``y`` has shape ``(samples,)``, and
    ``meta`` is a DataFrame of batch / time anchors for the sample rows.
    """
    lookback = int(lookback)
    horizon = int(horizon)
    if lookback < 1 or horizon < 1:
        raise ValueError("lookback and horizon must be positive integers")

    windows: list[np.ndarray] = []
    targets: list[float] = []
    meta: list[dict] = []
    for batch_id, sub in df.groupby(batch_col, sort=True):
        sub = sub.sort_values(time_col)
        t = sub[time_col].to_numpy(dtype=float)
        if not np.all(np.diff(t) > 0):
            raise ValueError(
                f"timestamps in batch {batch_id} are not strictly increasing")
        # The target for the last possible window must still be inside this
        # batch, so the last start index is len - lookback - horizon.
        n = len(sub)
        last_start = n - lookback - horizon
        if last_start < 0:
            continue
        feats = sub[features].to_numpy(dtype=float)
        tgt = sub[target].to_numpy(dtype=float)
        for start in range(0, last_start + 1):
            i = start + lookback - 1        # last input row index
            j = i + horizon                 # target row index
            windows.append(feats[start:i + 1])
            targets.append(float(tgt[j]))
            meta.append({
                batch_col: int(batch_id),
                time_col: float(t[i]),
                f"target_time_h": float(t[j]),
            })

    if not windows:
        raise ValueError(
            "no windows could be built; increase rows or reduce lookback/horizon")
    X = np.stack(windows)
    y = np.asarray(targets, dtype=float)
    meta_df = pd.DataFrame(meta)
    return X, y, meta_df