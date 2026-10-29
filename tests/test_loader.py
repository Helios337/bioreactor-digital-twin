"""Tests for the dataset loader."""

from __future__ import annotations

import pandas as pd
import pytest

from bioreactor_monitoring.loader import (
    DataError,
    find_file,
    load_process_data,
    load_statistics,
    sha256_of,
)


def test_find_file_recursive(tmp_path):
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    (nested / "100_Batches_IndPenSim_V3.csv").write_text("x", encoding="utf-8")
    assert find_file(tmp_path, "100_Batches_IndPenSim_V3.csv") == nested / "100_Batches_IndPenSim_V3.csv"


def test_find_file_missing_raises(tmp_path):
    with pytest.raises(DataError):
        find_file(tmp_path, "does-not-exist.csv")


def test_sha256(tmp_path):
    f = tmp_path / "f.bin"
    f.write_bytes(b"hello")
    assert sha256_of(f) == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


def test_load_statistics_roundtrip(tmp_path):
    f = tmp_path / "stat.csv"
    df_in = pd.DataFrame({"Batch ref": [1, 2], "Penicillin_yield": [10.0, 20.0]})
    df_in.to_csv(f, index=False)
    df = load_statistics(f)
    assert list(df.columns) == ["Batch ref", "Penicillin_yield"]
    assert df.shape[0] == 2


def test_load_process_data_roundtrip(tmp_path):
    f = tmp_path / "process.csv"
    df_in = pd.DataFrame({"Time (h)": [0.2, 0.4], "Fs": [8.0, 8.0]})
    df_in.to_csv(f, index=False)
    df = load_process_data(f)
    assert list(df.columns) == ["Time (h)", "Fs"]
