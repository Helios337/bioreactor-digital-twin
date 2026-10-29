"""Typed access to the YAML configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "config.yaml"


class ConfigError(ValueError):
    """Raised when configuration is missing or invalid."""


class Config:
    """Read-only, validated view over the YAML configuration.

    Attributes can be read as nested mappings through the ``data``
    attribute; thin helpers cover the most-used sections.
    """

    def __init__(self, data: dict[str, Any], root: Path = REPO_ROOT):
        self.data = data
        self.root = root

    @classmethod
    def from_yaml(cls, path: Path | str = DEFAULT_CONFIG_PATH) -> "Config":
        path = Path(path)
        if not path.exists():
            raise ConfigError(f"config file not found: {path}")
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return cls(data, root=path.parents[1])

    def resolve(self, rel_path: str) -> Path:
        """Resolve a config path relative to the repository root."""
        p = Path(rel_path)
        if p.is_absolute():
            return p
        return (self.root / p).resolve()

    def regime_for_batch(self, batch_no: int) -> str:
        """Return the control regime label for a batch number."""
        regimes = self.data.get("regimes", {})
        for name, (lo, hi) in regimes.items():
            if lo <= batch_no <= hi:
                return name
        raise ConfigError(f"batch {batch_no} not covered by any regime")

    def splits(self) -> dict[str, Any]:
        return self.data.get("splits", {})

    def softsensor(self) -> dict[str, Any]:
        return self.data.get("softsensor", {})

    def monitoring(self) -> dict[str, Any]:
        return self.data.get("monitoring", {})

    def control(self) -> dict[str, Any]:
        return self.data.get("control", {})

    def data_dir(self) -> Path:
        return self.resolve(self.data.get("data", {}).get("dir", "data"))
