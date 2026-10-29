"""Dashboard for the fed-batch monitoring-to-control prototype.

Materialized views over results/ and data/processed/. All numbers are the
recorded experiment outputs; labels distinguish measured, predicted, and
simulated values.

Run: .venv/bin/streamlit run dashboard/app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PHASE2 = ROOT / "results" / "phase2"
PHASE3 = ROOT / "results" / "phase3"
PHASE4 = ROOT / "results" / "phase4"
PHASE6 = ROOT / "results" / "phase6"
PHASE7 = ROOT / "results" / "phase7"
SPLITS = ROOT / "results" / "splits.json"


def load_json(path: Path):
    if path.exists():
        return json.loads(path.read_text())
    return None


st.set_page_config(page_title="Penicillin monitoring-to-control", layout="wide")
st.title("Fed-batch penicillin monitoring-to-control prototype")
st.caption("Research prototype. Everything shown here is simulated or recorded "
           "simulated benchmark data; no physical plant is connected.")

tab_overview, tab_monitor, tab_soft, tab_control = st.tabs(
    ["Overview", "Monitoring", "Soft sensor", "Control"])

with tab_overview:
    splits = load_json(SPLITS)
    st.subheader("Data and splits")
    if splits:
        st.write(f"Seed {splits['seed']}: "
                 f"{len(splits['train_batches'])} train batches, "
                 f"{len(splits['test_batches'])} held-out (test + deviation) batches.")
    st.write("IndPenSim Mendeley DOI 10.17632/pdnjz7zz5x.2, CC BY 4.0. "
             "Follow the workflow: measurements, monitoring, state estimation, "
             "control recommendation, simulated action, updated state.")

with tab_monitor:
    st.subheader("Golden-batch CQA monitoring")
    p4 = load_json(PHASE4 / "monitoring_estimated_report.json")
    p2 = load_json(PHASE2 / "monitoring_report.json")
    if p4:
        a, b, c = st.columns(3)
        a.metric("Oracle: detected with lead", f"{p4['oracle_comparison'].get('true_trajectory_with_lead', 'n/a')} / 26")
        b.metric("Estimated: detected with lead", f"{p4['n_below_target_with_lead_over_assay']} / 26")
        c.metric("Estimated trajectory MAE", f"{p4['trajectory_estimation_error_heldout']['mae_g_l']} g/L")
        st.dataframe(
            pd.read_csv(PHASE4 / "per_batch_monitoring_estimated.csv"),
            height=320, use_container_width=True)
    elif p2:
        st.json(p2)

with tab_soft:
    st.subheader("Soft-sensor baselines")
    rep = load_json(PHASE3 / "softsensor_report.json")
    if rep:
        rows = []
        for name, blk in rep["results"].items():
            for split in ("pooled", "normal_test", "fault_test"):
                m = blk[split]
                rows.append({"model": name, "split": split, "MAE": m["mae"],
                             "RMSE": m["rmse"], "R2": m["r2"]})
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        st.caption("Published baselines (different splits) in "
                   "results/phase3/softsensor_report.json.")

with tab_control:
    st.subheader("Matched control arms")
    col1, col2 = st.columns(2)
    for col, path, title in ((col1, PHASE6 / "control_report.json", "Rule-based (Phase 6)"),
                              (col2, PHASE7 / "mpc_report.json", "Constrained MPC (Phase 7)")):
        rep = load_json(path)
        if rep:
            with col:
                st.markdown(f"#### {title}")
                st.dataframe(pd.DataFrame(rep["by_arm"]), use_container_width=True)
                st.caption("All arms share seeds, initial conditions, and limits. "
                           "Sensing layer differs only.")
