#!/usr/bin/env python3
"""Data-layer verification tests. Run after tools/build_labels.py and build_cache.py."""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from indpenmon.data import (ASSAY_DELAY_H, CONC_BELOW, FAULT_BATCHES,  # noqa: E402
                            available_offline, golden_profile, load_batches,
                            load_labels, raman_cols, segment_phases, smape)


def main():
    ok = []

    labels = load_labels()
    assert len(labels) == 100, "expected 100 batches"
    ok.append("labels: 100 batches")

    conc = sorted(labels.index[labels.below_target_conc == 1].tolist())
    assert conc == CONC_BELOW, "concentration labels mismatch"
    ok.append("labels: below-target concentration reproduces Luo 2024 (33/33)")

    fault = sorted(labels.index[labels.fault_any == 1].tolist())
    assert fault == FAULT_BATCHES, "fault labels mismatch"
    ok.append("labels: fault batches = 91-100")

    regimes = labels.regime.value_counts().to_dict()
    assert regimes.get("recipe") == 30 and regimes.get("operator") == 30
    assert regimes.get("apc") == 30 and regimes.get("fault") == 10
    ok.append("labels: regimes 30 recipe / 30 operator / 30 apc / 10 fault")

    batches = load_batches()
    assert len(batches) == 100, "expected 100 cached batches"
    b1 = batches[1]
    assert list(b1.columns[:5]) == ["time", "Fg", "RPM", "Fs", "Fa"]
    assert b1["time"].iloc[0] == 0.2 and b1["time"].is_monotonic_increasing
    ok.append("cache: 100 batches, canonical columns, time sorted from 0.2 h")

    # assay delay emulation on batch 1
    av = available_offline(b1)
    raw_assays = b1["P_off"].dropna()
    assay_times = b1.loc[raw_assays.index, "time"]
    first_assay_t = float(assay_times.iloc[0])
    avail = av["P_off_avail"].dropna()
    first_avail_t = float(b1.loc[avail.index[0], "time"])
    assert first_avail_t >= first_assay_t + ASSAY_DELAY_H - 0.21, (first_assay_t, first_avail_t)
    assert avail.nunique() <= len(raw_assays)
    t_check = avail.index[-1]
    t_check_h = float(b1.loc[t_check, "time"])
    visible = float(avail.loc[t_check])
    eligible = raw_assays[assay_times <= t_check_h - ASSAY_DELAY_H + 0.21]
    assert abs(visible - float(eligible.iloc[-1])) < 1e-9
    ok.append("delay: 4-h assay delay emulated (first visible at assay+4h, values match latest eligible assay)")

    # phase segmentation on a healthy recipe batch
    ph = segment_phases(batches[5])
    assert set(ph.unique()) == {"lag", "growth", "production"}
    ok.append("phases: lag/growth/production all present on batch 5")

    # golden profile on healthy recipe-regime batches 1-30
    healthy = [b for b in range(1, 31) if b not in CONC_BELOW]
    gp = golden_profile(batches, healthy, ["pH", "DO2", "P_true"])
    assert set(gp.keys()) == {"pH", "DO2", "P_true"}
    assert len(gp["pH"]) == 101
    assert (gp["pH"]["upper"] >= gp["pH"]["mean"]).all()
    ok.append("golden: profile on %d healthy recipe batches, 101 grid points, 3-sigma bands" % len(healthy))

    # symmetric MAPE
    assert abs(smape([10.0, 20.0], [10.0, 20.0])) < 1e-9
    assert smape([10.0], [11.0]) > 0.09
    ok.append("smape: exact match gives 0, 10% error gives >0.09")

    # raman channel filter excludes flag columns
    fake = pd.DataFrame({"raman_2400": [1.0], "raman_rec": [1.0], "no_raman": [0.0]})
    assert raman_cols(fake) == ["raman_2400"]
    ok.append("raman: digit-suffix filter excludes flag columns")

    print("\n".join("PASS " + s for s in ok))
    print("\nAll data-layer tests passed:", len(ok))


if __name__ == "__main__":
    main()
