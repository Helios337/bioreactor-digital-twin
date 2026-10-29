"""Tests for configuration handling."""

from __future__ import annotations

import pytest

from bioreactor_monitoring.config import Config, ConfigError

CONFIG_TEXT = """
regimes:
  recipe: [1, 30]
  operator: [31, 60]
  apc: [61, 90]
  fault: [91, 100]
splits:
  seed: 42
  test_batches: []
data:
  dir: data
"""


def make_config(tmp_path):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(CONFIG_TEXT, encoding="utf-8")
    return Config.from_yaml(cfg_file)


def test_from_yaml_parses(tmp_path):
    cfg = make_config(tmp_path)
    assert cfg.data["splits"]["seed"] == 42


def test_from_yaml_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError):
        Config.from_yaml(tmp_path / "nope.yaml")


def test_regime_for_batch(tmp_path):
    cfg = make_config(tmp_path)
    assert cfg.regime_for_batch(1) == "recipe"
    assert cfg.regime_for_batch(30) == "recipe"
    assert cfg.regime_for_batch(45) == "operator"
    assert cfg.regime_for_batch(61) == "apc"
    assert cfg.regime_for_batch(99) == "fault"


def test_regime_out_of_range_raises(tmp_path):
    cfg = make_config(tmp_path)
    with pytest.raises(ConfigError):
        cfg.regime_for_batch(101)


def test_resolve_absolute_and_relative(tmp_path, monkeypatch):
    cfg = make_config(tmp_path)
    monkeypatch.setattr(cfg, "root", tmp_path)
    assert cfg.resolve("data") == (tmp_path / "data").resolve()
    assert cfg.resolve(str(tmp_path / "abs")) == (tmp_path / "abs").resolve()
