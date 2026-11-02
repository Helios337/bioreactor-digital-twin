# Bioreactor Digital Twin - Monitoring Prototype

> **Working title:** From Prediction to Trustworthy Closed-Loop Control: A Fault-Aware Digital-Twin Framework for Fed-Batch Fermentation.  
> **Status:** Research prototype (empirical Track B active; architecture proposal Track A ongoing).  
> **Data:** IndPenSim simulated benchmark (CC BY 4.0, DOI 10.17632/pdnjz7zz5x.2) — not real plant measurements.

---

## Table of Contents

- [Overview](#overview)
- [What this repository contains](#what-this-repository-contains)
- [Quick start](#quick-start)
- [Project structure](#project-structure)
- [Key results and evidence](#key-results-and-evidence)
- [Scientific claims boundary](#scientific-claims-boundary)
- [Data and reproducibility](#data-and-reproducibility)
- [References and literature review](#references-and-literature-review)
- [License and citation](#license-and-citation)

---

## Overview

This repository supports a reliability-oriented digital-twin framework for fed-batch penicillin fermentation. The research question is:

> What sensing, state-estimation, hybrid-modelling, uncertainty-management, fault-handling and control methods are needed to develop a reliable digital twin for fed-batch fermentation when observations are delayed, sensors fail, and process conditions change?

The work is structured in two parallel tracks:

| Track | Focus | Status |
|---|---|---|
| **A** | Critical literature review + proposed reference architecture | Active (19 priority sources tracked, 7 full-text verified) |
| **B** | Empirical monitoring prototype on IndPenSim benchmark | Completed through Phase 4 (data, monitoring, soft-sensor, estimated-trajectory monitoring); Phase 6–7 (control) implemented; Phase 8 (figures) available |

---

## What this repository contains

### Track A — Literature and architecture
- `references/`: verified source registry, BibTeX file, literature matrix, metadata logs, abstracts collection
- `review/`: scope documents, screening protocol, synthesis notes, manuscript outline
- `manuscript/`: draft paper sections
- `references/indpensim_labels.csv`: verified batch-level label sets (reproduce Luo 2024: 33/33 below-target batches)

### Track B — Monitoring-to-control prototype (`src/bioreactor_monitoring/`)
- `preprocess.py`: canonical schema mapping, regime/fault labels, assay-delay emulation, batch splitting
- `loader.py`: dataset discovery, SHA-256 verification, statistics loading
- `monitor.py`: golden-batch reference bands (3-sigma), deviation scores, alarm-event detection
- `softsensor.py`: Ridge and Random Forest baselines for penicillin concentration estimation
- `simulator.py`: Bajpai-Reuss kinetic simulator for control-arm comparison
- `control.py`: rule-based and constrained nonlinear MPC controllers
- `config.py`: typed, validated YAML configuration (paths resolve relative to repo root)
- `dashboard/app.py`: Streamlit view over recorded experiment results

### Scripts and results (`scripts/` and `results/`)
- `scripts/0_run_all.py` — full reproducible pipeline
- `scripts/1_inspect_data.py` — dataset inspection and validation
- `scripts/2_monitoring.py` — golden-batch monitoring
- `scripts/3_soft_sensor.py` — soft-sensor training and evaluation
- `scripts/4_monitoring_estimated.py` — monitoring with estimated (not true) penicillin trajectory
- `scripts/6_control_rule_based.py` and `7_control_mpc.py` — matched control arms
- `scripts/8_project_figures.py` — result visualisations
- `results/phase1/` through `results/phase8/`: JSON reports, CSV tables, PNG plots per phase

### Additional outputs
- `eda_results/`: exploratory data analysis (6 PNG graphs, 1 CSV summary, 1 JSON statistics file, readme) — generated from the IndPenSim dataset
- `docs/REPOSITORY_AUDIT.md`: repository audit notes

---

## Quick start

### Environment setup

```bash
git clone https://github.com/Helios337/bioreactor-digital-twin.git
cd bioreactor-digital-twin
python -m venv .venv
source .venv/bin/activate
pip install -e . streamlit pyarrow
```

### Verify the dataset

```bash
.venv/bin/python scripts/1_inspect_data.py
```

Expected output: archive SHA-256 verified, 100 batches, 113,935 records, 33 below-target batches (endpoint penicillin < 20 g/L), 4-hour assay delay emulated.

### Run the full pipeline

```bash
PYTHONPATH=src .venv/bin/python scripts/0_run_all.py
```

This executes phases 1–4 sequentially and writes results to `results/`.

### Launch the dashboard

```bash
.venv/bin/streamlit run dashboard/app.py
```

The dashboard reads from `results/phase2/` through `results/phase7/` and clearly labels simulated values versus estimated predictions.

---

## Project structure

```
bioreactor-digital-twin/
├── config/                  # YAML config (paths, thresholds, seeds, split fractions)
├── dashboard/                # Streamlit application (read-only over results/)
├── data/                     # IndPenSim dataset (gitignored, ~2.5 GB)
│   └── IndPenSim/
│       ├── 100_Batches_IndPenSim.zip
│       ├── extracted/Mendeley_data/
│       ├── parquet/          # processed batch caches
│       └── parquet_raman/
├── docs/                     # Audit notes, methodology documentation
├── eda_results/              # Exploratory analysis outputs (6 PNG + CSV + JSON)
├── indpenmon/                # Legacy data layer (not actively imported by scripts)
├── manuscript/               # Draft paper sections
├── references/               # Verified sources, BibTeX, matrix, metadata
├── report/                   # Project report (PDF and Markdown)
├── results/                  # Phase outputs (phase1–phase8)
├── review/                   # Scope, screening, synthesis
├── scripts/                  # Reproducible pipeline steps (0–8)
├── src/bioreactor_monitoring/
│   ├── __init__.py
│   ├── config.py             # Typed config loader
│   ├── loader.py             # Dataset discovery and verification
│   ├── preprocess.py         # Schema, labels, splits, assay delay
│   ├── monitor.py            # Golden-batch deviation monitoring
│   ├── softsensor.py         # Ridge / Random Forest estimation
│   ├── simulator.py          # Bajpai-Reuss kinetic model
│   └── control.py            # Rule-based and MPC controllers
└── tests/                    # Unit tests (39 pass; covers loader, preprocess,
                              # monitoring, softsensor, simulator, MPC, config)
```

---

## Key results and evidence

All results below are from recorded runs on the simulated IndPenSim benchmark. They are not predictions or simulated outputs unless explicitly labelled as such.

### Data layer (Phase 1)
- 100 batches (batches 1–30: recipe; 31–60: operator; 61–90: APC; 91–100: fault)
- 113,935 process-data rows plus 2,200 Raman spectral channels (wavenumbers 201–2400)
- Offline penicillin assay: ~21 samples per batch at 12-hour intervals, 4-hour emulated delay
- Label verification: endpoint penicillin < 20 g/L reproduces 33 below-target batches (matches Luo et al. 2024)

### Monitoring (Phase 2)
- Golden-batch reference profiles constructed from healthy training batches (recipe, operator, APC regimes separated)
- 3-sigma deviation bands per variable; sustained-alarm rule: threshold + minimum duration
- Detection performance (recorded in `results/phase2/monitoring_report.json`):
  - Below-target batches detected: 25 / 26
  - Detection with lead over delayed assay: 23 / 26
  - Median lead time: 9.2 h
  - False-alarm rate on healthy batches: 4.7%

### Soft-sensor (Phase 3)
- Features: feed rate, agitator RPM, temperature, pH, dissolved oxygen, vessel volume, CO2%, O2% (online variables only)
- Target: sparse offline penicillin concentration (`P_offline`)
- Baseline results (recorded in `results/phase3/softsensor_report.json`):
  - Random Forest: MAE 2.48 g/L, RMSE 4.13 g/L, R² 0.82 (pooled held-out)
  - Ridge: MAE 4.63 g/L, RMSE 6.82 g/L, R² 0.52
- Per-batch evaluation preserved; fault batches (91–100) evaluated separately

### Estimated-trajectory monitoring (Phase 4)
- Monitoring repeated using soft-sensor-estimated penicillin trajectories (not simulated truth)
- Result (`results/phase4/monitoring_estimated_report.json`):
  - Estimated trajectory MAE vs true: 2.58 g/L (held-out)
  - Oracle comparison: 25/26 below-target batches detected with true trajectory; 21/26 with estimated trajectory
  - Estimated trajectory retains useful early-warning capability compared to the oracle, but with reduced lead-time reliability

### Control arms (Phase 6 and 7)
- Rule-based feed controller and constrained nonlinear MPC implemented using the same simulator seed (seed 7) and initial conditions
- Matched comparison framework documented; results in `results/phase6/` and `results/phase7/`
- Note: control results demonstrate simulator behaviour and estimation-error sensitivity; they are not validated industrial control performance claims

### Dashboard
- `dashboard/app.py` reads from phases 2–7 and clearly distinguishes measured, predicted and simulated quantities
- Launch command: `.venv/bin/streamlit run dashboard/app.py`

---

## Scientific claims boundary

Every claim in this repository is separated into:

1. **Established evidence** — verified dataset properties, published methods, reproduced label counts, executed test results
2. **Author interpretation** — method design choices (e.g., OUR-based phase segmentation is heuristic, not a validated biological classifier)
3. **Proposed / to be evaluated** — architecture elements, control extensions, reliability claims

Specific boundaries observed:

- The IndPenSim dataset is a simulated benchmark (not physical plant measurements). All process trajectories and assay values are simulated.
- Dense true-state columns (`P_true`, `S_true`) are evaluation ground truth only. They are never used as soft-sensor inputs.
- Offline columns represent realistic sparse assays with a 4-hour delay. The delay is emulated explicitly; it is not a physical laboratory integration.
- The phase-segmentation method (`segment_phases()`) is an OUR-based heuristic. It is exploratory and not validated against expert-labelled phase annotations.
- The control arms (Phase 6 and 7) operate on the Bajpai-Reuss simulator. They are matched experimental comparisons, not validated industrial control systems.
- The dashboard is read-only. No actuator commands are issued to any physical bioreactor.
- Test counts (e.g., 10/10 data-layer tests, 39/39 full suite) refer to implementation verification, not model accuracy or control performance validation.

---

## Data and reproducibility

### Dataset
- Source: Mendeley Data, IndPenSim V2 (CC BY 4.0)
- DOI: `10.17632/pdnjz7zz5x.2`
- Files: `100_Batches_IndPenSim_V3.csv` (2.3 GB), `100_Batches_IndPenSim_Statistics.csv`
- Archive SHA-256 verified: `bc434c6cf96444fee3c915d434ac84e2a9c6492be4daebcfa4aed9cdff181f00`
- The dataset is gitignored (~2.5 GB); only result artifacts and scripts are committed

### Reproducibility
- All pipeline steps are deterministic when `seed` (default 42) is fixed in `config/config.yaml`
- Batch splits are saved to `results/splits.json` and reused across phases to prevent data leakage
- Each phase writes JSON reports with configuration snapshot, metric definitions and exclusion notes
- Scripts must not overwrite historical results without preserving them; use `results/` subdirectories by phase
- The `.venv/` environment is pinned via `pyproject.toml`; install with `pip install -e .`

---

## References and literature review

The literature review (Track A) follows a structured protocol:

- Source verification via Crossref, OpenAlex, PubMed
- Evidence level tracked per source: metadata-verified, abstract-read, full-text-read
- Citation-verification and scientific-writing skills registered in `.opencode/skills/`
- Reference matrix: `references/literature_matrix.csv`
- Verified BibTeX: `references/references.bib` (generated by `tools/build_bib.py`)

No fabricated citations, results, numbers, equations, data-availability claims or limitations appear in any file. Candidate gaps in the architecture remain labelled as hypotheses until citation chaining confirms them.

---

## License and citation

This repository is licensed under the same terms as the underlying dataset (CC BY 4.0) for data-related artifacts. Source code and original analysis are provided as-is for research transparency.

When citing or building on this work, distinguish clearly between:
- The IndPenSim benchmark (simulated) and any physical bioreactor measurements
- Completed implementation evidence (tests, recorded results) and proposed future work (architecture, validated control)

---

## Integrity summary

- No fabricated citations, results, numerical improvements, equations, data-availability claims or limitations
- Simulated benchmark data is never presented as plant data
- The proposed architecture is described as proposed and reliability-oriented, never as validated, safe or perfect
- Candidate gaps (e.g., uncertainty quantification integration, real-time streaming validation) are tracked as hypotheses pending further evidence
- Dashboard and scripts distinguish measured, estimated and simulated values explicitly
