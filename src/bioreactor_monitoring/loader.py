"""Loading the IndPenSim dataset into canonical tables.

The dataset archive layout is verified during Phase 1 inspection.
All functions here search for files by name rather than assuming a
fixed directory structure, so the loader is robust to layout changes
between dataset versions.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

PROCESS_CSV = "100_Batches_IndPenSim_V3.csv"
STATISTICS_CSV = "100_Batches_IndPenSim_Statistics.csv"


class DataError(ValueError):
    """Raised when the dataset is missing or inconsistent."""


def find_file(base_dir: Path, filename: str) -> Path:
    """Recursively locate a file by exact name under base_dir."""
    base_dir = Path(base_dir)
    if not base_dir.exists():
        raise DataError(f"data directory not found: {base_dir}")
    hits = [p for p in base_dir.rglob(filename) if p.is_file()]
    if not hits:
        raise DataError(f"file not found under {base_dir}: {filename}")
    if len(hits) > 1:
        # Prefer the shallowest match, which is usually the canonical one.
        hits.sort(key=lambda p: len(p.parts))
    return hits[0]


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    """Streaming SHA256 of a file."""
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def load_statistics(path: Path) -> pd.DataFrame:
    """Load the batch statistics table with normalized column names."""
    df = pd.read_csv(Path(path))
    df.columns = [str(c).strip() for c in df.columns]
    return df


def load_process_data(path: Path) -> pd.DataFrame:
    """Load the process data summary table.

    The release contains a large CSV with all batches concatenated.
    Column names are preserved as-is for Phase 1 inspection.
    """
    df = pd.read_csv(Path(path))
    df.columns = [str(c).strip() for c in df.columns]
    return df


def discover_layout(base_dir: Path, max_depth: int = 3) -> list[str]:
    """Return a shallow inventory of files under base_dir for inspection."""
    base_dir = Path(base_dir)
    if not base_dir.exists():
        return []
    out: list[str] = []
    for p in sorted(base_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(base_dir)
        if len(rel.parts) > max_depth:
            continue
        out.append(f"{rel}\t{p.stat().st_size}")
    return out
