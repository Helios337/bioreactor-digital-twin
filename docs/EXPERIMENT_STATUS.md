# Experiment Status

This file records what has actually been executed, what is code-complete but
not run, and what remains pending. It is updated as runs land.

Status vocabulary: **executed** (real run completed), **implemented** (code and
tests present), **blocked-not-run** (needs the dataset or compute unavailable in
this environment), **pending** (planned, not started).

## Data-dependent experiments

| Experiment | Status | Evidence |
|---|---|---|
| Phase 1 dataset inspection | blocked-not-run | Code present; needs `data/IndPenSim` archive. Earlier committed `results/phase1/` reflects a prior local run. |
| Phase 2 oracle monitoring | blocked-not-run | Code present; earlier committed `results/phase2/` reflects a prior local run. |
| Phase 3 soft sensor | blocked-not-run | Code present; earlier committed `results/phase3/` reflects a prior local run. |
| Phase 4 estimated monitoring (causal rerun) | blocked-not-run | Code updated to causal smoothing; rerun needs the dataset. Historical `results/phase4/` is the old centred-smoothing run. |
| Phase 5 GRU (dense and sparse) | blocked-not-run | Code, config, and tests present; smoke-run on synthetic data only in the agent environment. No real benchmark metric is reported. |
| Phase 6 rule-based control | executed | Re-run in the agent environment with the non-oracle estimator, written to `results/phase6/v1/` (Bajpai-Reuss simulator, no dataset needed). Historical `results/phase6/` preserved. |
| Phase 7 MPC control | executed | Re-run in the agent environment with the non-oracle estimator, written to `results/phase7/v1/` (Bajpai-Reuss simulator, no dataset needed). Historical `results/phase7/` preserved. |

## Data-independent work

| Item | Status | Evidence |
|---|---|---|
| Full test suite | executed | 49 tests pass in a clean Python 3.12 venv (`pytest tests/ -q`). |
| Phase 4 causal smoothing regression test | executed | `tests/test_monitor.py::test_causal_rolling_median_ignores_future`. |
| Sequence no-cross-batch-boundary tests | executed | `tests/test_preprocess.py` sequence tests. |
| Non-oracle controller observability test | executed | `tests/test_mpc.py::test_mpc_never_reads_true_state_from_missing_measurement`. |
| GRU module and feature-selection tests | executed | `tests/test_gru.py`. |
| CI workflow | executed | `.github/workflows/ci.yml` runs the data-independent suite on Python 3.10/3.11/3.12. |
| GRU script smoke run | executed | Ran `scripts/5_gru_forecasting.py --mode dense` and `--mode sparse` on synthetic data; both complete without error. Not a real benchmark result. |

## Pending

- A real Phase 5 GRU run on the IndPenSim benchmark, with per-batch plots,
  residual plots, and model checkpoint saved under `results/phase5_gru/`.
- Phase 4 causal rerun and its figures.
- Dashboard GRU section updates once a real run exists (the tab is currently
  labelled "planned / not yet run").