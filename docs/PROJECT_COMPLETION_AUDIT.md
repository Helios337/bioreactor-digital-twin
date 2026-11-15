# Project Completion Audit

Status: Milestone 1 baseline audit on branch `research/project-completion`.

Baseline commit audited: `4e4827697ad0e8d82e127953665a46f7194a9b9b` (origin/main).

Date: 2026-11-16.

This document records the real current state of the repository, the issues found,
and a proposed file-by-file change plan. It is evidence-based. Nothing in this
document is a substituted experiment result.

## 1. Scope and evidence levels

The brief asks for a complete, strengthened, reproducible research repository.

Evidence in this audit is limited by two hard facts:

1. The raw IndPenSim dataset is not present in this execution environment.
   There is no `data/` directory, no archive, and no `data/processed/` parquet
   cache. Consequently every data-dependent action is blocked here: the
   inspection, monitoring, soft-sensor, estimated-monitoring run, and the new
   GRU training run cannot be executed. They are recorded as "not run" with the
   exact commands the user must run locally.
2. The 2026 GRU publication by Rekkas-Ventiris and Benardos has not been verified
   here. It is therefore treated as paper-inspired, not an exact reproduction,
   until full methods are available.

What can be done here, and is done: verify project integrity, run the full
data-independent test suite, audit the code for scientific-validity bugs,
implement the correctness repairs, add the standalone GRU component, add tests,
and update documentation. These are real and reproducible.

## 2. Baseline test run

Environment: Python 3.12.5, clean venv at a temporary path, package installed
editable via `pip install -e ".[dev]"`.

Exact command:

```bash
python -m pytest tests/ -q
```

Result: 39 passed, 0 failed, 0 skipped. This matches the README claim of 39
tests. The suite covers config, loader, preprocess, monitor, softsensor,
simulator, MPC, and control.

No CI workflow exists in the repository (there is no `.github/` tracked in the
repo tree), so this passing state is not currently verified automatically on
push.

## 3. What is already correct and should be preserved

The following science and engineering choices are sound and must not be
regressed:

- Batch-level splits. `results/splits.json` records a whole-batch train/test
  split (72 train, 28 test+deviation) that keeps every batch in one partition.
  The split is deterministic and reused across phases.
- Fault batches 91 to 100 are excluded from training. This matches the brief.
- Leak-free soft-sensor evaluation. `predict_trajectories()` uses trajectory-
  level out-of-fold predictions for training batches and a full-train fit for
  held-out batches. Features are online-only; dense `p_true_g_l` is never a
  predictor.
- Assay delay handling. `assay_available()` reveals an assay only at
  `sample_time + delay_h`, correctly modelling the four-hour reporting delay.
- The endpoint rule `P_final < 20 g/L`. Verified against the code and recorded
  results; reproduces the published below-target count.
- Clear simulated-data boundary. The README and AGENTS.md repeatedly state that
  IndPenSim is simulated benchmark data and that Bajpai-Reuss control results
  are simulator results only.
- No fabricated results. Recorded result files are internally consistent with
  the code that generated them.
- `pyproject.toml` keeps mathtplotlib, statsmodels, pyarrow as core; dev extras
  hold pytest and streamlit.

## 4. Issues found (ordered by severity)

### I1. Non-causal (centred) smoothing in Phase 4 estimated-monitoring

File: `scripts/4_monitoring_estimated.py`, line 98.

The estimated trajectory is smoothed with:

```python
x.rolling(int(round(win / step)), center=True, min_periods=1).median()
```

With `center=True`, a rolling window of width 1.0 h uses up to 0.5 h of future
samples to smooth the current time point. The README and the phase report use
this smoothed estimate for online-style early-warning and lead-time claims.

Impact: for any online monitoring claim the smoothed value at time `t` may
reflect data available only after `t`. This is a causal-leakage flaw in the
Monitoring workstream.

Required change: switch to a trailing / past-only smoother (`center=False`)
for online claims, and re-run Phase 4 to a new versioned result directory.
Optionally expose a separately named retrospective (centred) smoothing only for
research plots, never for lead-time claims.

### I2. Oracle state fallback in non-oracle controller arms

File: `src/bioreactor_monitoring/control.py`, class `NonLinearMPC.__call__`,
lines 161-167.

When any measurement component is `None`, MPC substitutes the true state from
`y_true`:

```python
measurement.X if measurement.X is not None else y_true[0]
```

For a delayed-assay or partially observed sensor, this silently gives the
controller access to the hidden true state for the missing components, i.e. an
oracle leak.

Required change: the source of each controller state estimate must be explicit.
Oracle fallback is allowed only in a named oracle arm. For non-oracle arms,
declare a state estimator, hold-last-value policy, or stop with a clear error
when required states are unavailable. Add a test proving a non-oracle sensor
cannot read true-state values through the controller interface.

### I3. Monitoring evaluation excludes fault batches entirely

Files: `scripts/2_monitoring.py`, `scripts/4_monitoring_estimated.py`.

Both loop only over `("recipe", "operator", "apc")` regimes. Batches 91 to 100
(fault regime) are never scored by the monitor. The brief explicitly asks to
report fault-batch outcomes separately where possible. This is a coverage gap,
not necessarily a bug, but the reports should state that fault batches are
excluded and the reason.

### I4. README references a non-existent file

File: `README.md`, line 68 references `docs/REPOSITORY_AUDIT.md`. That file does
not exist. The README project tree lists `docs/` as "Audit notes, methodology
documentation" but the directory contains only `paper_plan.md` and
`system_spec.md`.

### I5. No CI workflow

The brief requires a CI workflow that installs the project and runs the
data-independent tests without the large dataset. None exists. `pyproject.toml`
has no such configuration and there is no `.github/workflows/`.

### I6. Pipeline/documentation command mismatches

- `README.md` "Run the full pipeline" says `scripts/0_run_all.py` executes
  phases 1 to 4. The orchestrator actually runs phases 1, 2, 3, 4, 6, 7
  (inspection, monitoring, soft sensor, estimated monitoring, rule-based
  control, MPC). Phases 5 (GRU) and 8 (figures) are not in the orchestrator.
  The written scope and actual scope disagree; the README must be corrected.
- `scripts/0_run_all.py` will fail hard on any phase that raises, which is
  correct, but the README claim must match.

### I7. Missing optional-dependency extras for GRU

`pyproject.toml` has no optional extra for PyTorch or XGBoost. The brief wants
PyTorch and XGBoost in an optional forecasting extra so the base install and
full pipeline do not require them. This must be added so `0_run_all.py` does
not unexpectedly need a deep-learning stack.

### I8. No scalar-feature window builder or sequence-boundary safety tests

The preprocess layer has no sliding-window sequence builder and no test proving
that sequences never cross batch boundaries. Workstream C needs a tested
sliding-window builder, and Workstream B needs a batch-boundary regression test.

### I9. Minor documentation / hygiene

- README "Data" section says the process CSV is 2.3 GB; the config and brief
  say "about 2.5 GB" for the full dataset. Numbers should be reconciled after
  the local data is available.
- `config/config.yaml` `data.dir` is `data/IndPenSim` but `scripts/1_inspect_data.py`
  and `scripts/4_monitoring_estimated.py` read from `data/processed/`. The
  processed-cache location is not declared in config; it is hard-coded. Paths
  should be centralised.
- No GRU phase, no `results/phase5_gru/`, no forecasting config, no `phase5`
  directory exists yet; the brief's proposed names are free.

## 5. Proposed file-by-file change plan

The plan adds no scope beyond the brief. It is ordered so scientific-correctness
repairs and tests land before any new model code.

| Workstream | File | Change |
|---|---|---|
| B / D | `scripts/4_monitoring_estimated.py` | Make smoothing causal (`center=False`) for online claims; write to a new versioned result folder; label retrospective smoothing separately if kept. |
| B / E | `src/bioreactor_monitoring/control.py` / `simulator.py` | Make non-oracle controllers raise instead of falling back to `y_true`; add a `HoldLastStateEstimator` and use it where appropriate; keep oracle fallback only in a named oracle arm. |
| B | `tests/test_monitor.py` | Add a regression test proving future observations do not change earlier smoothed values (causality). |
| B | `tests/test_preprocess.py` | Add a test proving sequences/windows never cross batch boundaries. |
| B / E | `tests/test_mpc.py` / `tests/test_simulator.py` | Add a test that a non-oracle controller cannot read true-state values through the sensor interface. |
| A | `.github/workflows/ci.yml` | Data-independent CI: install package, run pytest. |
| C | `src/bioreactor_monitoring/gru.py` | Standalone GRU forecaster (configurable lookback/horizon, GRU layers, Adamax, MSE, early stopping, gradient clipping), no dashboard/control dependency. |
| C | `src/bioreactor_monitoring/sequence.py` | Tested sliding-window sequence builder with batch-boundary and ordering safety. |
| C | `scripts/5_gru_forecasting.py` | Standalone runnable GRU experiment, Mode 1 (dense target) and Mode 2 (sparse assay) with separate reports. |
| C | `config/gru_forecasting.yaml` | GRU defaults, clearly marked as project-selected until the paper is verified. |
| C | `tests/test_gru.py` | Tests for sequence builder, in-/out-of-batch windows, and GRU forward shapes on synthetic data. |
| C | `results/phase5_gru/` | Artifact directory (run outputs). Not created until a real run lands. |
| A / F | `scripts/0_run_all.py` | Make stated scope and actual steps agree; add GRU as optional/separate. |
| F | `dashboard/app.py` | Add a GRU section labelled "planned / not yet run" until a real run exists. |
| G | `README.md` | Fix tree, tests count, pipeline scope, dataset size, remove the dangling audit reference; add status and results only from traceable runs. |
| G | `docs/METHODOLOGY.md`, `docs/REPRODUCIBILITY.md`, `docs/EXPERIMENT_STATUS.md`, `docs/GRU_METHODS.md` | New/updated research documentation. |
| A | `config/config.yaml` | Centralise processed-cache paths and GRU defaults without absolute paths. |

## 6. Known blockers

- Raw dataset absent. All steps that consume `data/processed/process_named.parquet`
  or the archive are blocked and recorded as "not run". Exact user commands are
  given in the final report.
- The 2026 GRU paper full text is not verified. GRU hyperparameters are
  project-selected defaults, not claimed as published.

## 7. Milestone exit criteria

- Audit report exists: yes (this file).
- No files destructively modified: commits on the new branch only.
- Current tests and known issues recorded: yes above.