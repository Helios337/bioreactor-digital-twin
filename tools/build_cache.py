#!/usr/bin/env python3
"""Split the main IndPenSim CSV into per-batch parquet files with canonical names.

One pass over the 2.5 GB CSV. Process columns go to data/IndPenSim/parquet/batch_XX.parquet.
Raman channels are stored separately per batch under data/IndPenSim/parquet_raman/
because of their size (2200 channels). Both directories are gitignored.
"""
import os

import pandas as pd

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from indpenmon.data import CANON, PROCESS_COLS, CACHE  # noqa: E402

RAMAN_CACHE = os.path.join(os.path.dirname(CACHE), "parquet_raman")


def main():
    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(RAMAN_CACHE, exist_ok=True)
    df = pd.read_csv(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "IndPenSim", "extracted", "Mendeley_data",
        "100_Batches_IndPenSim_V3.csv"), low_memory=False)
    rename = {}
    for c in df.columns:
        if c in CANON:
            rename[c] = CANON[c]
        elif c.isdigit():
            rename[c] = "raman_" + c
    df = df.rename(columns=rename)
    raman = [c for c in df.columns if c.startswith("raman_") and c[6:].isdigit()]
    proc = [c for c in PROCESS_COLS]
    print("process cols:", len(proc), "raman cols:", len(raman))
    for b, g in df.groupby("batch"):
        b = int(b)
        g = g.sort_values("time").reset_index(drop=True)
        g[proc].to_parquet(os.path.join(CACHE, "batch_%03d.parquet" % b))
        if raman:
            g[["time"] + raman].to_parquet(
                os.path.join(RAMAN_CACHE, "batch_%03d.parquet" % b))
        if b % 10 == 0:
            print("cached batch", b)
    print("done. process cache:", CACHE, "raman cache:", RAMAN_CACHE)


if __name__ == "__main__":
    main()
