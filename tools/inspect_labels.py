#!/usr/bin/env python3
"""Deep inspection of IndPenSim: batch grouping, flags, assay cadence, labels.

Reconciles three label definitions:
- fault_ref from the statistics CSV (batches 91-100 per dataset description).
- mass-based below-target: total penicillin yield < 2,000,000 g (2,000 kg).
- concentration-based below-target: final offline penicillin assay < 20 g/L.

Also verifies the concentration-based labels against the 33 unhealthy batches
published by Luo et al. 2024 (Front. Manuf. Technol. 4:1392038).
Output: data/IndPenSim/deep_summary.json
"""
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "IndPenSim", "extracted", "Mendeley_data")
MAIN = os.path.join(DATA, "100_Batches_IndPenSim_V3.csv")
STATS = os.path.join(DATA, "100_Batches_IndPenSim_Statistics.csv")

BID = "Batch ID"
TCOL = "Time (h)"
P_OFF = "Offline Penicillin concentration(P_offline:P(g L^{-1}))"
X_OFF = "Offline Biomass concentratio(X_offline:X(g L^{-1}))"
FAULT_MAIN = "Fault flag"
CTRL = "0 - Recipe driven 1 - Operator controlled(Control_ref:Control ref)"
PAT = "2-PAT control(PAT_ref:PAT ref)"
RAMAN_FLAG = " 1-Raman spec recorded"

LUO_UNHEALTHY = [3, 4, 6, 9, 10, 18, 19, 24, 25, 28, 30, 33, 34, 36, 37, 40,
                 42, 43, 44, 45, 47, 49, 51, 54, 59, 60, 91, 92, 94, 95, 97, 99, 100]


def main():
    stats = pd.read_csv(STATS)
    usecols = [BID, TCOL, P_OFF, X_OFF, FAULT_MAIN, CTRL, PAT, RAMAN_FLAG,
               "Fault reference(Fault_ref:Fault ref)"]
    df = pd.read_csv(MAIN, usecols=usecols, low_memory=False)
    print("loaded", df.shape)

    out = {}

    # batch grouping
    print("Batch ID uniques:", df[BID].nunique())
    counts = df.groupby(BID).size()
    out["batch_row_counts"] = {int(k): int(v) for k, v in counts.items()}
    tr = df.groupby(BID)[TCOL].agg(["min", "max"])
    out["batch_time_max"] = {int(k): float(v) for k, v in tr["max"].items()}
    print("rows/batch min max:", int(counts.min()), int(counts.max()))
    print("batch time max range:", float(tr["max"].min()), float(tr["max"].max()))

    # flag distributions
    for c in [FAULT_MAIN, CTRL, PAT, RAMAN_FLAG,
              "Fault reference(Fault_ref:Fault ref)"]:
        out["flag_" + c[:40]] = {str(k): int(v) for k, v in df[c].value_counts(dropna=False).items()}
        print(c, "->", df[c].value_counts(dropna=False).to_dict())

    # per-batch assay structure and labels
    rows = []
    for b, g in df.groupby(BID):
        g = g.sort_values(TCOL)
        p = g[P_OFF].dropna()
        x = g[X_OFF].dropna()
        final_p = float(p.iloc[-1]) if len(p) else np.nan
        final_x = float(x.iloc[-1]) if len(x) else np.nan
        rows.append(dict(
            batch=int(b), n_assays=int(len(p)), n_x_assays=int(len(x)),
            t_first_assay=float(p.index[0]) if len(p) else np.nan,
            t_final_assay=float(g.loc[p.index[-1], TCOL]) if len(p) else np.nan,
            final_p_offline=final_p, final_x_offline=final_x,
            final_true_p=float(g[P_OFF.replace("P_offline:P(g L^{-1})", "")].iloc[-1])
            if False else np.nan))
    lab = pd.DataFrame(rows).set_index("batch").sort_index()
    # true final P (dense column) at final assay time
    true_col = [c for c in pd.read_csv(MAIN, nrows=0).columns if c.startswith("Penicillin concentration(")][0]
    print("true P column:", true_col)

    conc_below = sorted(lab.index[lab.final_p_offline < 20.0].tolist())
    mass_below = sorted(stats.loc[stats["Penicllin_yield_total (kg)"] < 2_000_000, "Batch ref"].tolist())
    fault = sorted(stats.loc[stats["Fault ref(0-NoFault 1-Fault)"] == 1, "Batch ref"].tolist())
    print("\nconcentration-based below-target (<20 g/L final assay):", len(conc_below), conc_below)
    print("mass-based below-target (<2e6 g):", len(mass_below), mass_below)
    print("fault batches:", fault)
    print("Luo 33 match conc-based:", set(conc_below) == set(LUO_UNHEALTHY))
    print("diff conc vs Luo:", sorted(set(conc_below) ^ set(LUO_UNHEALTHY)))

    out["labels"] = dict(
        conc_below_target=conc_below, mass_below_target=mass_below,
        fault_batches=fault, luo_unhealthy=LUO_UNHEALTHY,
        conc_matches_luo=set(conc_below) == set(LUO_UNHEALTHY))
    out["assays_per_batch_min_max"] = [int(lab.n_assays.min()), int(lab.n_assays.max())]
    out["final_assay_time_range"] = [float(lab.t_final_assay.min()), float(lab.t_final_assay.max())]
    lab.to_json(os.path.join(os.path.dirname(DATA), "deep_summary.json"), orient="index")
    with open(os.path.join(os.path.dirname(DATA), "deep_summary.json"), "w") as f:
        json.dump(out, f, indent=1)

    # raman health
    ram = [c for c in pd.read_csv(MAIN, nrows=0).columns if c.isdigit()]
    print("\nraman channels:", len(ram))
    sample = df[ram].iloc[::5000]
    nan_cols = sample.isna().all()
    print("raman cols all-NaN in sample:", int(nan_cols.sum()))
    print("raman value range sample:", float(np.nanmin(sample.values)), float(np.nanmax(sample.values)))

    print("\nwrote deep_summary.json")


if __name__ == "__main__":
    main()
