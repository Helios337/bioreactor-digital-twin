# GRU Forecasting: Methods and Reproduction Status

This note is about the standalone GRU penicillin forecasting experiment
(Workstream C) and how it relates to the 2026 publication by Rekkas-Ventiris
and Benardos.

## 1. Status of the published method

The brief describes the accessible bibliographic / abstract information: Random
Forest and XGBoost feature selection, a GRU model, Adamax and tanh among the
reported best settings, and a reported MSE of `7.20e-4`.

In this environment the full paper and its supplementary material were not
accessible. The experiment is therefore a transparent **paper-inspired
reproduction**, not an exact reproduction.

Each architecture and training detail is treated in one of two ways:

1. If it is recorded in the accessible abstract, it is flagged as such.
2. Otherwise it is a **project-selected default** and is explicitly not claimed
   as a published value.

Unknowns that must be verified against the full text before any exact claim:
target definition, input variables, split method, sequence length, forecast
horizon, GRU depth, hidden dimensions, dropout, batch size, epochs, learning
rate, feature-selection protocol, and target scaling.

**MSE scale warning.** The reported `7.20e-4` MSE must not be compared with an
original-scale MSE from this repository. A scaled MSE and an original-scale MSE
are different quantities. This repository reports metrics on the original g/L
scale (see the `target_scale_note` in any phase5 metrics file). No claim of
matching the published MSE is made.

## 2. Project-selected settings (recorded in `config/config.yaml`)

Mode 1 (dense) is the primary GRU benchmark; Mode 2 (sparse) is a separate
secondary experiment and is never merged into one metric table.

- Lookback and horizon are configurable and stored in every report.
- GRU uses `tanh` (the standard GRU candidate activation). PyTorch does not
  expose a candidate-activation argument, so none is invented.
- `dropout` in PyTorch applies only between recurrent layers when
  `num_layers > 1`. A single-layer GRU gets no inter-layer dropout; no extra
  output dropout is added unless justified.
- Adamax optimiser, MSE loss, gradient clipping, and early stopping on a
  grouped validation split are used.
- Deterministic seed where practical; CPU execution is the default.

## 3. Causality and leakage safeguards

- A prediction at time `t` uses input data available at or before `t`; the
  target is at `t + horizon`. The sequence builder never includes the target
  row or later data in the input window.
- Windows never cross batch boundaries (tested).
- Feature selection fit on training batches only; target, batch, fault labels,
  and post-outcome fields are excluded from the predictor matrix.
- If XGBoost is requested but unavailable, the operation falls back to a
  Random Forest and records the substitution explicitly rather than silently.

## 4. Paper verification checklist

Before claiming exact reproduction, verify and record each item in the
repository's reference registry with an evidence status of full-text, abstract,
or unavailable:

- Title, authors, year, venue, DOI.
- Target definition and input variables.
- Split method and sequence length.
- Forecast horizon.
- GRU depth, hidden dimensions, dropout, batch size, epochs, learning rate.
- Feature-selection protocol.
- Target scaling and metric scale.

Do not infer missing architecture values from the reported MSE.