# Reproducibility

This document records the environment, data checksum, seeds, splits, run
commands and artifacts needed to reproduce the repository.

## 1. Environment

- Python 3.10, 3.11, or 3.12 (per `pyproject.toml`, `requires-python = ">=3.10"`).
- Core dependencies: numpy, pandas, scipy, scikit-learn, matplotlib,
  statsmodels, PyYAML, pyarrow.
- Dev extras: pytest, streamlit.
- Forecasting extras (optional, for the GRU experiment only): torch, xgboost.

Setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"          # base monitoring workflow + tests
pip install -e ".[forecast]"     # additionally for the GRU experiment
```

## 2. Dataset

Source: Mendeley Data, IndPenSim V2. DOI 10.17632/pdnjz7zz5x.2. License CC BY 4.0.

Place the archive at `data/IndPenSim/100_Batches_IndPenSim.zip` (gitignored).
Recorded SHA-256 of the archive:

```
bc434c6cf96444fee3c915d434ac84e2a9c6492be4daebcfa4aed9cdff181f00
```

Run `scripts/1_inspect_data.py` to verify the hash, apply the canonical schema,
and write the processed parquet cache to `data/processed/process_named.parquet`.

## 3. Determinism

- A fixed random seed (default 42) controls the batch split and shuffle in
  `results/splits.json`.
- The split is written once and reused across phases to prevent leakage.
- The GRU training uses a fixed seed and PyTorch manual seed where supported;
  CUDA availability is detected without being required.
- Each phase writes a `config` snapshot into its report.

## 4. Run commands

All commands run from the repository root.

Inspect and prepare data:

```bash
PYTHONPATH=src .venv/bin/python scripts/1_inspect_data.py
```

Monitoring, soft sensor, estimated monitoring, and control (sequential):

```bash
PYTHONPATH=src .venv/bin/python scripts/0_run_all.py
```

GRU forecasting (separate; requires the forecast extra):

```bash
PYTHONPATH=src .venv/bin/python scripts/5_gru_forecasting.py --mode dense
PYTHONPATH=src .venv/bin/python scripts/5_gru_forecasting.py --mode sparse
```

Tests:

```bash
.venv/bin/python -m pytest tests/ -q
```

Dashboard:

```bash
.venv/bin/streamlit run dashboard/app.py
```

## 5. Artifacts

- `results/phase1/` inspection report and processed cache.
- `results/phase2/`, `results/phase3/`, `results/phase4/`, `results/phase6/`,
  `results/phase7/` recorded experiment outputs.
- `results/phase5_gru/` GRU run directories (each holds `metrics.json`, per-batch
  CSV, feature-selection data, and training history once a real run completes).
- `results/splits.json` the shared batch split.
- Reruns write to versioned run directories and never overwrite historical
  outputs (for example `results/phase4/<run_name>/`).

## 6. What is reproducible here

The full data-independent test suite is reproducible in a clean environment and
reported green (49 tests passing). The data-dependent experiments require the
2.5 GB IndPenSim dataset, which is not present in the agent environment; they
must be run locally with the commands above.