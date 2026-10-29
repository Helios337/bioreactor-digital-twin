"""IndPenSim data layer for the bioreactor monitoring prototype.

Canonical column registry, batch loading with parquet cache, label construction,
off-line assay delay emulation, Raman preprocessing, phase segmentation, and
golden-batch profile building.

Integrity rules:
- The dense true-state columns (S_true, P_true) are simulation truth. They are
  NEVER soft-sensor inputs. They are evaluation ground truth only.
- Off-line columns are sparse assays. The 4-hour laboratory delay is emulated
  explicitly (B7: predefined 4 h delay).
- Batch key is the PAT_ref column per the dataset documentation.
"""
import os

import numpy as np
import pandas as pd
from scipy.signal import medfilt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "IndPenSim")
EXTRACTED = os.path.join(DATA, "extracted", "Mendeley_data")
MAIN_CSV = os.path.join(EXTRACTED, "100_Batches_IndPenSim_V3.csv")
STATS_CSV = os.path.join(EXTRACTED, "100_Batches_IndPenSim_Statistics.csv")
CACHE = os.path.join(DATA, "parquet")
RAMAN_CACHE = os.path.join(DATA, "parquet_raman")
LABELS_CSV = os.path.join(ROOT, "references", "indpensim_labels.csv")

# Canonical names for the 39 named columns of the main CSV.
CANON = {
    "Time (h)": "time",
    "Aeration rate(Fg:L/h)": "Fg",
    "Agitator RPM(RPM:RPM)": "RPM",
    "Sugar feed rate(Fs:L/h)": "Fs",
    "Acid flow rate(Fa:L/h)": "Fa",
    "Base flow rate(Fb:L/h)": "Fb",
    "Heating/cooling water flow rate(Fc:L/h)": "Fc",
    "Heating water flow rate(Fh:L/h)": "Fh",
    "Water for injection/dilution(Fw:L/h)": "Fw",
    "Air head pressure(pressure:bar)": "Pair",
    "Dumped broth flow(Fremoved:L/h)": "Fremoved",
    "Substrate concentration(S:g/L)": "S_true",
    "Dissolved oxygen concentration(DO2:mg/L)": "DO2",
    "Penicillin concentration(P:g/L)": "P_true",
    "Vessel Volume(V:L)": "V",
    "Vessel Weight(Wt:Kg)": "W",
    "pH(pH:pH)": "pH",
    "Temperature(T:K)": "T",
    "Generated heat(Q:kJ)": "Q",
    "carbon dioxide percent in off-gas(CO2outgas:%)": "CO2out",
    "PAA flow(Fpaa:PAA flow (L/h))": "Fpaa",
    "PAA concentration offline(PAA_offline:PAA (g L^{-1}))": "PAA_off",
    "Oil flow(Foil:L/hr)": "Foil",
    "NH_3 concentration off-line(NH3_offline:NH3 (g L^{-1}))": "NH3_off",
    "Oxygen Uptake Rate(OUR:(g min^{-1}))": "OUR",
    "Oxygen in percent in off-gas(O2:O2  (%))": "O2out",
    "Offline Penicillin concentration(P_offline:P(g L^{-1}))": "P_off",
    "Offline Biomass concentratio(X_offline:X(g L^{-1}))": "X_off",
    "Carbon evolution rate(CER:g/h)": "CER",
    "Ammonia shots(NH3_shots:kgs)": "NH3_shots",
    "Viscosity(Viscosity_offline:centPoise)": "visc_off",
    "Fault reference(Fault_ref:Fault ref)": "fault_row",
    "0 - Recipe driven 1 - Operator controlled(Control_ref:Control ref)": "ctrl_ref",
    "1- No Raman spec": "no_raman",
    " 1-Raman spec recorded": "raman_rec",
    "2-PAT control(PAT_ref:PAT ref)": "batch",
    "Batch reference(Batch_ref:Batch ref)": "row_ref",
    "Batch ID": "batch_id_str",
    "Fault flag": "fault_flag",
}

PROCESS_COLS = list(CANON.values())
OFFLINE_COLS = ["P_off", "X_off", "PAA_off", "NH3_off", "visc_off"]
ASSAY_DELAY_H = 4.0
ONLINE_COLS = ["Fg", "RPM", "Fs", "Fa", "Fb", "Fc", "Fh", "Fw", "Pair",
               "Fremoved", "DO2", "V", "W", "pH", "T", "Q", "CO2out", "Fpaa",
               "Foil", "OUR", "O2out", "CER", "NH3_shots"]
RAMAN_MIN, RAMAN_MAX = 201, 2400

# Verified label sets (tools/build_labels.py; concentration-based matches Luo 2024).
CONC_BELOW = [3, 4, 6, 9, 10, 18, 19, 24, 25, 28, 30, 33, 34, 36, 37, 40,
              42, 43, 44, 45, 47, 49, 51, 54, 59, 60, 91, 92, 94, 95, 97, 99, 100]
FAULT_BATCHES = list(range(91, 101))


def regime_of(batch):
    """Control regime per the dataset documentation."""
    b = int(batch)
    if b <= 30:
        return "recipe"
    if b <= 60:
        return "operator"
    if b <= 90:
        return "apc"
    return "fault"


def load_main(usecols=None):
    """Load the main CSV with canonical renaming. Raman channels become raman_NNN."""
    df = pd.read_csv(MAIN_CSV, usecols=usecols, low_memory=False)
    rename = {}
    for c in df.columns:
        if c in CANON:
            rename[c] = CANON[c]
        elif c.isdigit():
            rename[c] = "raman_" + c
    return df.rename(columns=rename)


def load_labels():
    """Per-batch label table built by tools/build_labels.py."""
    return pd.read_csv(LABELS_CSV).set_index("batch").sort_index()


def load_batches(process_only=True, cache=True):
    """Return {batch_id: DataFrame sorted by time} with canonical columns.

    Uses per-batch parquet cache when present (built by tools/build_cache.py).
    """
    if cache and os.path.isdir(CACHE) and len(os.listdir(CACHE)) >= 100:
        out = {}
        for f in sorted(os.listdir(CACHE)):
            if f.endswith(".parquet"):
                d = pd.read_parquet(os.path.join(CACHE, f))
                out[int(f.split("_")[1].split(".")[0])] = d.sort_values("time")
        return out
    cols = PROCESS_COLS if process_only else None
    df = load_main(usecols=cols)
    out = {}
    for b, g in df.groupby("batch"):
        out[int(b)] = g.sort_values("time").reset_index(drop=True)
    return out


def load_raman_batch(batch):
    """Load one batch: process columns joined with Raman channels."""
    proc = load_batches().get(int(batch))
    rpath = os.path.join(RAMAN_CACHE, "batch_%03d.parquet" % int(batch))
    if proc is None or not os.path.exists(rpath):
        raise FileNotFoundError(rpath)
    r = pd.read_parquet(rpath)
    r = r.drop(columns=["time"] + [c for c in r.columns if c in ("raman_rec", "no_raman")])
    return pd.concat(
        [proc.reset_index(drop=True), r.reset_index(drop=True)], axis=1)


def raman_cols(df):
    """Only true spectral channels (digit suffix). Excludes flag columns like raman_rec."""
    return [c for c in df.columns if c.startswith("raman_") and c[6:].isdigit()]


def prepare_raman(spec):
    """SNV, linear detrend, and median-filter spike removal on a spectra frame.

    spec: DataFrame with raman_NNN columns. Returns processed frame with
    channels sorted by ascending wavenumber.
    """
    spec = spec.copy()
    keep = [c for c in spec.columns if not spec[c].isna().all()]
    spec = spec[keep]
    x = spec.values.astype(float)
    mu = x.mean(axis=1, keepdims=True)
    sd = x.std(axis=1, keepdims=True)
    sd[sd == 0] = 1.0
    x = (x - mu) / sd                      # SNV per spectrum
    wavenumbers = np.array([float(c.split("_")[1]) for c in spec.columns])
    order = np.argsort(wavenumbers)
    x = x[:, order]
    t = wavenumbers[order].astype(float)
    coef = np.polyfit(t, x.T, 1)           # linear baseline per spectrum
    x = x - (coef[0] * t + coef[1]).T
    x = medfilt(x, kernel_size=(1, 5))     # cosmic-spike suppression
    return pd.DataFrame(x, index=spec.index,
                        columns=["raman_" + str(int(v)) for v in t])


def available_offline(g, cols=OFFLINE_COLS, delay_h=ASSAY_DELAY_H):
    """Emulate the laboratory pipeline: an assay taken at ta is visible at ta+delay.

    Returns a frame with one column per input: col_avail, forward-filled from
    assays whose availability time is <= row time. NaN before the first visible assay.
    """
    g = g.sort_values("time")
    out = pd.DataFrame(index=g.index)
    for c in cols:
        assays = g[["time", c]].dropna().copy()
        if assays.empty:
            out[c + "_avail"] = np.nan
            continue
        assays = assays.rename(columns={c: "val"})
        assays["avail_time"] = assays["time"] + delay_h
        merged = pd.merge_asof(
            g[["time"]], assays[["avail_time", "val"]],
            left_on="time", right_on="avail_time", direction="backward")
        out[c + "_avail"] = merged["val"].values
    return out


def segment_phases(g):
    """Heuristic phase segmentation from the OUR trajectory.

    lag: OUR below 10% of batch max.
    growth: rising OUR through the peak.
    production: after OUR falls below 50% of peak post-peak (or peak time + 20 h).
    """
    our = g["OUR"].rolling(int(5 / 0.2), center=True, min_periods=1).mean()
    thr_hi = 0.10 * our.max()
    gt = our.gt(thr_hi)
    lag_end_idx = gt.idxmax() if gt.any() else g.index[0]
    peak_idx = our.idxmax()
    t_peak = float(g["time"].loc[peak_idx])
    post = our.loc[peak_idx:]
    prod_candidates = post.index[post < 0.5 * our.max()]
    if len(prod_candidates):
        prod_start = float(g["time"].loc[prod_candidates[0]])
    else:
        prod_start = t_peak + 20.0
    phases = pd.Series("growth", index=g.index)
    phases[g.index <= lag_end_idx] = "lag"
    phases[g["time"] >= prod_start] = "production"
    return phases


def resample_relative(g, var, grid_pct=np.arange(0, 1.01, 0.01)):
    """Interpolate one variable onto a percent-of-batch-duration grid."""
    t = g["time"].values
    y = g[var].values
    t0, t1 = t[0], t[-1]
    rel = (t - t0) / (t1 - t0)
    yy = np.interp(grid_pct, rel, y)
    return pd.Series(yy, index=grid_pct)


def golden_profile(batches, healthy_ids, variables, method="relative"):
    """Per-grid-point mean and 3-sigma bands over healthy batches.

    Returns {var: DataFrame indexed by relative grid 0..1 with mean, std, upper, lower}.
    """
    frames = {}
    grid = np.arange(0, 1.01, 0.01)
    for v in variables:
        rows = [resample_relative(batches[b], v).values for b in healthy_ids]
        arr = np.vstack(rows)
        mean = arr.mean(axis=0)
        std = arr.std(axis=0)
        frames[v] = pd.DataFrame(
            dict(mean=mean, std=std, upper=mean + 3 * std, lower=mean - 3 * std),
            index=grid)
    return frames


def smape(actual, pred):
    """Symmetric mean absolute percentage error, Luo et al. 2024 deviation measure."""
    a = np.asarray(actual, float)
    p = np.asarray(pred, float)
    denom = (np.abs(a) + np.abs(p)) / 2.0
    denom = np.where(denom == 0, 1e-9, denom)
    return float(np.mean(np.abs(a - p) / denom))
