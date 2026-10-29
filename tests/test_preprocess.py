"""Tests for preprocessing logic that does not require the full dataset."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from bioreactor_monitoring.preprocess import (
    BATCH,
    BELOW_TARGET,
    FAULT,
    REGIME,
    add_below_target,
    add_regime_and_fault,
    assay_available,
    rename_columns,
    split_batches,
)


def _mini_frame():
    return pd.DataFrame({
        "2-PAT control(PAT_ref:PAT ref)": [1, 1, 31, 61, 95],
        "Time (h)": [0.2, 0.4, 0.2, 0.2, 0.2],
        "pH(pH:pH)": [7.0, 7.1, 7.0, 7.0, 7.0],
    })


def test_rename_columns_and_batch():
    df = rename_columns(_mini_frame())
    assert BATCH in df.columns
    assert list(df[BATCH]) == [1, 1, 31, 61, 95]
    assert "ph" in df.columns
    assert "pH(pH:pH)" not in df.columns


def test_add_regime_and_fault():
    df = add_regime_and_fault(rename_columns(_mini_frame()))
    assert list(df[REGIME]) == ["recipe", "recipe", "operator", "apc", "fault"]
    assert list(df[FAULT]) == [0, 0, 0, 0, 1]


def test_add_below_target():
    df = rename_columns(_mini_frame())
    # endpoint penicillin concentration rule: add a proper P column
    df["p_true_g_l"] = [5.0, 12.0, 30.0, 25.0, 15.0]
    df["time_h"] = df["time_h"]  # already present
    out = add_below_target(df)
    flagged = out.groupby(BATCH)[BELOW_TARGET].first()
    assert flagged[1] == 1        # endpoint P = 12 < 20
    assert flagged[31] == 0       # endpoint P = 30 >= 20
    assert flagged[95] == 1       # endpoint P = 15 < 20


def test_assay_available_after_delay():
    assay_times = np.array([0.0, 12.0, 24.0])
    assay_values = np.array([0.5, 2.0, 4.0])
    query = np.array([3.0, 5.0, 13.0, 16.0, 24.0, 30.0])
    values, ages = assay_available(assay_times, assay_values, query, delay_h=4.0)
    assert np.isnan(values[0])                 # t=3 < 0+4
    assert values[1] == pytest.approx(0.5)      # t=5 >= 4
    assert ages[1] == pytest.approx(1.0)
    assert values[2] == pytest.approx(0.5)     # t=13 < 12+4=16
    assert values[3] == pytest.approx(2.0)     # t=16 >= 16
    assert values[4] == pytest.approx(2.0)     # t=24 >= 16, < 28
    assert values[5] == pytest.approx(4.0)     # t=30 >= 28


def test_assay_available_none_known():
    values, ages = assay_available(np.array([0.0]), np.array([1.0]), np.array([1.0]), 4.0)
    assert np.isnan(values[0])
    assert np.isnan(ages[0])


def test_split_batches_excludes_deviation_set():
    train, other = split_batches(np.arange(1, 101), seed=7, test_fraction=0.2)
    assert set(train) & set(range(91, 101)) == set()
    assert len(set(train) & set(other)) == 0
    # stratification: each regime keeps a test portion in `other`
    test_batches = [b for b in other if b <= 90]
    regs = {"recipe": 0, "operator": 0, "apc": 0}
    for b in test_batches:
        reg = "recipe" if b <= 30 else "operator" if b <= 60 else "apc"
        regs[reg] += 1
    assert all(v >= 1 for v in regs.values())


def test_split_batches_stratified_by_label():
    labels = {b: 1 if b in (4, 11, 21, 34, 44, 67, 78, 88, 89, 90, 5, 6, 7) else 0
              for b in range(1, 101)}
    train, other = split_batches(np.arange(1, 101), seed=3, test_fraction=0.25,
                                 labels=labels)
    test_normal = [b for b in other if b <= 90]
    train_set = set(int(b) for b in train)
    # at least one labelled batch per regime should land in the test set
    for lo, hi, reg in ((1, 30, "recipe"), (31, 60, "operator"), (61, 90, "apc")):
        labelled_in_regime = [b for b in range(lo, hi + 1) if labels[b] == 1]
        assert any(b in test_normal for b in labelled_in_regime), reg


def test_split_batches_deterministic():
    a, _ = split_batches(np.arange(1, 101), seed=7, test_fraction=0.2)
    b, _ = split_batches(np.arange(1, 101), seed=7, test_fraction=0.2)
    assert list(a) == list(b)
