#!/usr/bin/env python3
"""Inspect the downloaded IndPenSim dataset and write a machine-readable summary.

Run after data/IndPenSim/100_Batches_IndPenSim.zip is present.
Extracts the zip (if needed), loads the main and statistics CSVs, and reports
shapes, columns, batch structure, labels, missingness, and time coverage.
Output: data/IndPenSim/inspection_summary.json plus a printed report.
"""
import json
import os
import zipfile

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "IndPenSim")
ZIP = os.path.join(DATA, "100_Batches_IndPenSim.zip")
EXTRACT = os.path.join(DATA, "extracted")


def ensure_extracted():
    if os.path.isdir(os.path.join(EXTRACT, "Mendeley_data")):
        print("already extracted")
        return
    os.makedirs(EXTRACT, exist_ok=True)
    with zipfile.ZipFile(ZIP) as z:
        names = z.namelist()
        print("zip entries:", len(names))
        for n in names[:40]:
            print("  ", n, z.getinfo(n).file_size)
        z.extractall(EXTRACT)
    print("extracted to", EXTRACT)


def main():
    ensure_extracted()
    base = os.path.join(EXTRACT, "Mendeley_data")
    files = os.listdir(base) if os.path.isdir(base) else os.listdir(EXTRACT)
    print("files:", files)

    main_csv = None
    stats_csv = None
    for root, _, names in os.walk(EXTRACT):
        for n in names:
            low = n.lower()
            if low.endswith(".csv") and "statistic" in low:
                stats_csv = os.path.join(root, n)
            elif low.endswith(".csv"):
                main_csv = os.path.join(root, n)
    print("main_csv:", main_csv)
    print("stats_csv:", stats_csv)

    summary = dict(zip=str(ZIP), main_csv=main_csv, stats_csv=stats_csv)

    # statistics CSV: small, load fully
    if stats_csv:
        st = pd.read_csv(stats_csv)
        print("\n== statistics CSV ==")
        print("shape:", st.shape)
        print("columns:", list(st.columns))
        print(st.head(3).to_string())
        fault_col = [c for c in st.columns if "fault" in c.lower()]
        if fault_col:
            fc = fault_col[0]
            print("fault counts:", st[fc].value_counts().to_dict())
            summary["fault_batches"] = sorted(st.loc[st[fc] == 1].iloc[:, 0].tolist())
        yield_cols = [c for c in st.columns if "yield" in c.lower() or "total" in c.lower()]
        if yield_cols:
            yc = yield_cols[0]
            summary["yield_stats"] = dict(
                min=float(st[yc].min()), max=float(st[yc].max()),
                mean=float(st[yc].mean()), median=float(st[yc].median()))
            below = st[st[yc] < 2000]
            print("batches below 2000 kg:", len(below))
            summary["below_target_batches"] = below.iloc[:, 0].tolist()

    # main CSV: sniff with small read, then full
    if main_csv:
        sniff = pd.read_csv(main_csv, nrows=5)
        cols = list(sniff.columns)
        print("\n== main CSV ==")
        print("columns:", len(cols))
        print("first 40:", cols[:40])
        print("last 40:", cols[-40:])
        summary["main_columns"] = cols
        df = pd.read_csv(main_csv)
        print("shape:", df.shape)
        time_cols = [c for c in cols if "time" in c.lower()]
        batch_cols = [c for c in cols if "batch" in c.lower()]
        print("time cols:", time_cols, "| batch cols:", batch_cols)
        if time_cols:
            tc = time_cols[0]
            summary["time_range"] = [float(df[tc].min()), float(df[tc].max())]
            print("time range:", summary["time_range"])
        if batch_cols:
            bc = batch_cols[0]
            counts = df[bc].value_counts().sort_index()
            summary["batch_row_counts"] = {str(k): int(v) for k, v in counts.items()}
            print("batches:", len(counts), "rows per batch min/max:",
                  int(counts.min()), int(counts.max()))
        nan = df.isna().sum()
        top_nan = nan[nan > 0].sort_values(ascending=False).head(20)
        summary["top_nan_columns"] = {k: int(v) for k, v in top_nan.items()}
        print("top NaN columns:", summary["top_nan_columns"])
        summary["dtypes"] = {c: str(t) for c, t in df.dtypes.items() if c in cols[:50]}

    out = os.path.join(DATA, "inspection_summary.json")
    with open(out, "w") as f:
        json.dump(summary, f, indent=1)
    print("\nwrote", out)


if __name__ == "__main__":
    main()
