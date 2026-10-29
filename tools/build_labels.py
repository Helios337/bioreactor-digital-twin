#!/usr/bin/env python3
"""Build per-batch label table from the IndPenSim statistics CSV and main CSV.

Label definitions (all three kept, they are different things):
- fault: Fault ref = 1 in statistics CSV (batches 91-100).
- below_target_conc: final offline penicillin assay < 20 g/L. Reproduces the
  33 unhealthy batches of Luo et al. 2024 exactly (verified 2026-10-29).
- below_target_mass: total penicillin yield < 2,000,000 g (2,000 kg) from the
  statistics CSV (note: the CSV column is labelled kg but values are grams).

Outputs:
- references/indpensim_labels.csv (committed, 100 rows)
- data/IndPenSim/labels.json (local detail)
"""
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "IndPenSim")
EXTRACTED = os.path.join(DATA, "extracted", "Mendeley_data")
MAIN = os.path.join(EXTRACTED, "100_Batches_IndPenSim_V3.csv")
STATS = os.path.join(EXTRACTED, "100_Batches_IndPenSim_Statistics.csv")

PAT = "2-PAT control(PAT_ref:PAT ref)"
TCOL = "Time (h)"
P_OFF = "Offline Penicillin concentration(P_offline:P(g L^{-1}))"
X_OFF = "Offline Biomass concentratio(X_offline:X(g L^{-1}))"
TRUEP = "Penicillin concentration(P:g/L)"
FAULTR = "Fault reference(Fault_ref:Fault ref)"


def main():
    stats = pd.read_csv(STATS)
    stats = stats.rename(columns={stats.columns[0]: "batch"})
    use = [PAT, TCOL, P_OFF, X_OFF, TRUEP, FAULTR]
    df = pd.read_csv(MAIN, usecols=use, low_memory=False)

    rows = []
    for b, g in df.groupby(PAT):
        g = g.sort_values(TCOL)
        p = g[P_OFF].dropna()
        x = g[X_OFF].dropna()
        rows.append(dict(
            batch=int(b),
            rows=int(len(g)),
            t_max=float(g[TCOL].max()),
            n_assays=int(len(p)),
            final_p_off=float(p.iloc[-1]) if len(p) else np.nan,
            final_true_p=float(g[TRUEP].iloc[-1]),
            final_x_off=float(x.iloc[-1]) if len(x) else np.nan,
            fault_rows=int(g[FAULTR].sum()),
        ))
    lab = pd.DataFrame(rows).sort_values("batch").set_index("batch")

    # join statistics CSV (yields in grams despite kg label, fault ref)
    y = stats.set_index("batch")
    lab["yield_total_g"] = y["Penicllin_yield_total (kg)"].astype(float)
    lab["fault_stat"] = y["Fault ref(0-NoFault 1-Fault)"].astype(int)

    lab["regime"] = [("recipe" if b <= 30 else "operator" if b <= 60 else
                      "apc" if b <= 90 else "fault") for b in lab.index]
    lab["below_target_conc"] = (lab.final_p_off < 20.0).astype(int)
    lab["below_target_mass"] = (lab.yield_total_g < 2_000_000).astype(int)
    lab["fault_any"] = ((lab.fault_stat == 1) | (lab.fault_rows > 0)).astype(int)

    out = lab.reset_index()
    out.to_csv(os.path.join(ROOT, "references", "indpensim_labels.csv"), index=False)
    with open(os.path.join(DATA, "labels.json"), "w") as f:
        json.dump(dict(
            conc_below=sorted(lab.index[lab.below_target_conc == 1].tolist()),
            mass_below=sorted(lab.index[lab.below_target_mass == 1].tolist()),
            fault=sorted(lab.index[lab.fault_any == 1].tolist()),
            healthy_conc=sorted(lab.index[lab.below_target_conc == 0].tolist()),
        ), f, indent=1)

    print("batches:", len(lab))
    print("below-target concentration (<20 g/L):", int(lab.below_target_conc.sum()))
    print("below-target mass (<2000 kg):", int(lab.below_target_mass.sum()))
    print("fault batches:", sorted(lab.index[lab.fault_any == 1].tolist()))
    print("assays per batch:", int(lab.n_assays.min()), "-", int(lab.n_assays.max()))
    print("t_max range:", float(lab.t_max.min()), "-", float(lab.t_max.max()))
    # integrity checks
    luo = [3, 4, 6, 9, 10, 18, 19, 24, 25, 28, 30, 33, 34, 36, 37, 40, 42, 43,
           44, 45, 47, 49, 51, 54, 59, 60, 91, 92, 94, 95, 97, 99, 100]
    got = sorted(lab.index[lab.below_target_conc == 1].tolist())
    assert got == luo, "concentration labels do not reproduce Luo 2024"
    print("VERIFIED: concentration labels reproduce Luo et al. 2024 (33/33).")
    assert sorted(lab.index[lab.fault_stat == 1].tolist()) == list(range(91, 101))
    print("VERIFIED: statistics fault ref = batches 91-100.")
    print("wrote references/indpensim_labels.csv and data/IndPenSim/labels.json")


if __name__ == "__main__":
    main()
