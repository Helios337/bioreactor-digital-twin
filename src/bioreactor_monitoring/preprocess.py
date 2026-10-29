"""Preprocessing and feature selection for the IndPenSim release.

Key data-quality facts established in Phase 1 inspection:

- The release CSV has a malformed two-row header; ``pandas`` preserved 39
  named columns plus 2200 numeric Raman wavenumber columns.
- The batch identifier lives in the column ``2-PAT control(PAT_ref:PAT ref)``
  (the dataset record states this explicitly). Values are 1 to 100.
- ``Penicillin concentration(P:g/L)`` is populated at every row and is the
  simulated (true) product trajectory.
- ``Offline Penicillin concentration(P_offline:...)`` is populated on
  approximately 20 rows per batch (12-hourly offsets) and is the realistic
  sparse assay label used as the soft-sensor target.
- ``Fault reference(Fault_ref:Fault ref)`` is 1 exactly for batches 91 to 100.
- The statistics file labels the yield columns "(kg)" but values are grams;
  dividing by 1000 reproduces the per-batch kilogram-scale yields in the
  benchmark paper.

All quantity columns are renamed to canonical short names here.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TIME = "time_h"
BATCH = "batch"
P_TRUE = "p_true_g_l"
P_OFFLINE = "p_offline_g_l"
X_OFFLINE = "x_offline_g_l"
FAULT = "fault"
REGIME = "regime"
BELOW_TARGET = "below_target"

# Reliable batch identifier per the dataset record.
BATCH_REFERENCE_COL = "2-PAT control(PAT_ref:PAT ref)"

# Canonical renaming for the named columns we use.
COLUMN_MAP = {
    "Time (h)": "time_h",
    "Aeration rate(Fg:L/h)": "aeration_l_h",
    "Agitator RPM(RPM:RPM)": "agitator_rpm",
    "Sugar feed rate(Fs:L/h)": "feed_rate_l_h",
    "Acid flow rate(Fa:L/h)": "acid_flow_l_h",
    "Base flow rate(Fb:L/h)": "base_flow_l_h",
    "Heating/cooling water flow rate(Fc:L/h)": "cooling_flow_l_h",
    "Heating water flow rate(Fh:L/h)": "heating_flow_l_h",
    "Water for injection/dilution(Fw:L/h)": "water_flow_l_h",
    "Air head pressure(pressure:bar)": "head_pressure_bar",
    "Dumped broth flow(Fremoved:L/h)": "dumped_flow_l_h",
    "Substrate concentration(S:g/L)": "substrate_g_l",
    "Dissolved oxygen concentration(DO2:mg/L)": "do2_mg_l",
    "Penicillin concentration(P:g/L)": "p_true_g_l",
    "Vessel Volume(V:L)": "volume_l",
    "Vessel Weight(Wt:Kg)": "weight_kg",
    "pH(pH:pH)": "ph",
    "Temperature(T:K)": "temperature_k",
    "Generated heat(Q:kJ)": "heat_kj",
    "carbon dioxide percent in off-gas(CO2outgas:%)": "co2_out_pct",
    "PAA flow(Fpaa:PAA flow (L/h))": "paa_flow_l_h",
    "PAA concentration offline(PAA_offline:PAA (g L^{-1}))": "paa_offline_g_l",
    "Oil flow(Foil:L/hr)": "oil_flow_l_h",
    "NH_3 concentration off-line(NH3_offline:NH3 (g L^{-1}))": "nh3_offline_g_l",
    "Oxygen Uptake Rate(OUR:(g min^{-1}))": "our_g_min",
    "Oxygen in percent in off-gas(O2:O2  (%))": "o2_out_pct",
    "Offline Penicillin concentration(P_offline:P(g L^{-1}))": "p_offline_g_l",
    "Offline Biomass concentratio(X_offline:X(g L^{-1}))": "x_offline_g_l",
    "Carbon evolution rate(CER:g/h)": "cer_g_h",
    "Ammonia shots(NH3_shots:kgs)": "nh3_shots_kg",
    "Viscosity(Viscosity_offline:centPoise)": "viscosity_cp",
    "Fault reference(Fault_ref:Fault ref)": "fault_ref",
    "0 - Recipe driven 1 - Operator controlled(Control_ref:Control ref)": "control_ref",
}

# Soft-sensor predictor set matching the published IndPenSim baseline
# (Acosta-Pavas et al. 2024 used feed rate, agitation, temperature, pH,
# dissolved oxygen, vessel volume, CO2 percent, and O2 percent).
SOFT_SENSOR_FEATURES = [
    "feed_rate_l_h",
    "agitator_rpm",
    "temperature_k",
    "ph",
    "do2_mg_l",
    "volume_l",
    "co2_out_pct",
    "o2_out_pct",
]

# Online-only variables that are safe soft-sensor features.
ONLINE_FEATURES = [
    "aeration_l_h",
    "agitator_rpm",
    "feed_rate_l_h",
    "acid_flow_l_h",
    "base_flow_l_h",
    "cooling_flow_l_h",
    "heating_flow_l_h",
    "water_flow_l_h",
    "head_pressure_bar",
    "dumped_flow_l_h",
    "substrate_g_l",
    "do2_mg_l",
    "volume_l",
    "weight_kg",
    "ph",
    "temperature_k",
    "heat_kj",
    "co2_out_pct",
    "paa_flow_l_h",
    "oil_flow_l_h",
    "our_g_min",
    "o2_out_pct",
    "cer_g_h",
    "nh3_shots_kg",
]


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the canonical column renaming and drop unrecognized columns."""
    renamed = df.rename(columns=COLUMN_MAP)
    keep = [c for c in renamed.columns if c in set(COLUMN_MAP.values()) or c == BATCH_REFERENCE_COL]
    out = renamed[keep].copy()
    out = out.rename(columns={BATCH_REFERENCE_COL: BATCH})
    out[BATCH] = out[BATCH].astype(int)
    return out


def add_regime_and_fault(df: pd.DataFrame) -> pd.DataFrame:
    """Assign the declared control regime and the fault flag by batch number."""
    out = df.copy()
    out[REGIME] = np.select(
        [
            out[BATCH].between(1, 30),
            out[BATCH].between(31, 60),
            out[BATCH].between(61, 90),
        ],
        ["recipe", "operator", "apc"],
        default="fault",
    )
    out[FAULT] = out[BATCH].between(91, 100).astype(int)
    return out


def add_below_target(df: pd.DataFrame) -> pd.DataFrame:
    """Label batches whose endpoint penicillin concentration is below 20 g/L.

    This reproduces the published count of 33 below-target batches in the
    Luo et al. 2024 analysis of this dataset. The alternative yield-in-kg
    rule is volume-confounded (a high-volume batch can have a large total
    mass yet a low concentration) and is not used as the quality label.
    """
    out = df.copy()
    endpoint = (
        df.sort_values("time_h").groupby(BATCH)[P_TRUE].last()
    )
    below = (endpoint < 20.0).astype(int)
    out[BELOW_TARGET] = out[BATCH].map(below).fillna(0).astype(int)
    return out


def assay_available(assay_times: np.ndarray, assay_values: np.ndarray, query_times: np.ndarray,
                    delay_h: float) -> tuple[np.ndarray, np.ndarray]:
    """Availability of delayed sparse assay values at query times.

    ``assay_times`` and ``assay_values`` carry the recorded sample times and
    values. An assay taken at time t becomes known to the downstream system at
    t + delay_h. For each query time, return the most recent assay value known
    at that time, or NaN when none is known yet, together with the age of that
    value in hours.

    Both input arrays must be sorted by assay time.
    """
    assay_times = np.asarray(assay_times, dtype=float)
    assay_values = np.asarray(assay_values, dtype=float)
    query_times = np.asarray(query_times, dtype=float)
    known_times = assay_times + delay_h
    # candidates = assays whose known time <= query time
    values = np.full(query_times.shape, np.nan)
    ages = np.full(query_times.shape, np.nan)
    idx = np.searchsorted(known_times, query_times, side="right") - 1
    valid = idx >= 0
    values[valid] = assay_values[np.clip(idx[valid], 0, len(assay_values) - 1)]
    ages[valid] = query_times[valid] - known_times[np.clip(idx[valid], 0, len(known_times) - 1)]
    return values, ages


def split_batches(batch_ids: np.ndarray, seed: int, test_fraction: float) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic stratified-by-regime split of batch ids into train and test.

    Batches 91 to 100 are excluded and returned separately as the deviation
    set, because faults are the deviation evaluation set, not normal-operation
    training data.
    """
    rng = np.random.default_rng(seed)
    normal = np.array(sorted(set(int(b) for b in batch_ids) - set(range(91, 101))))
    dev = np.array(sorted(set(range(91, 101)) & set(int(b) for b in batch_ids)))
    regimes = np.array([
        "recipe" if b <= 30 else "operator" if b <= 60 else "apc" for b in normal
    ])
    test_idx: list[int] = []
    for reg in ("recipe", "operator", "apc"):
        members = np.where(regimes == reg)[0]
        rng.shuffle(members)
        n_test = max(1, round(len(members) * test_fraction))
        test_idx.extend(members[:n_test].tolist())
    test = np.array(sorted(int(normal[i]) for i in test_idx))
    train = np.array(sorted(int(b) for b in normal if b not in test))
    return train, np.concatenate([test, dev])


def write_processed_cache(df: pd.DataFrame, dest: Path) -> None:
    """Persist the canonical per-row table to parquet for fast reloads."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(dest, index=False)
