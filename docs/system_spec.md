# System Specification

Date: 2026-10-29. Status: specification for the minimal monitoring-to-control prototype (Deliverable 3).

## 1. Purpose and scope

This document fixes the data contract, modules, control logic, failure handling, and evaluation design of the prototype.

The prototype is research software. It is not an industrial control product.

It operates on recorded simulated batches and on a simulator. It never sends a command to physical equipment.

## 2. Data inputs and expected schema

Primary dataset: IndPenSim version 2, DOI 10.17632/pdnjz7zz5x.2, licence CC BY 4.0.

Archive: 100_Batches_IndPenSim.zip, SHA256 bc434c6cf96444fee3c915d434ac84e2a9c6492be4daebcfa4aed9cdff181f00.

The archive contains a process-data summary CSV, a batch statistics CSV, and per-batch data files.

The exact file names and column names are confirmed during Phase 1 inspection; the schema below is provisional and is amended by an inspection report before models are trained.

Provisional process-data columns from the released summary file include: time in hours, aeration rate, agitator RPM, sugar feed rate, acid flow rate, base flow rate, heating and cooling water flow rates, water for injection, and air head pressure.

Additional online channels documented in the benchmark paper are dissolved oxygen, pH, temperature, vessel weight, and off-gas CO2 and O2.

Offline assay variables documented in the benchmark paper are penicillin, biomass, phenylacetic acid, nitrogen, and viscosity, sampled every 12 hours with a 4 hour delay.

Raman spectra are documented at 30 minute cadence and are not required by the initial prototype.

Batch statistics columns include penicillin harvested during the batch and at end of batch, total yield, and a fault indicator.

Control regime assignment is fixed by batch number: 1 to 30 recipe, 31 to 60 operator, 61 to 90 advanced process control, 91 to 100 faults.

### 2.1 Simulation input schema

The control plant is the Bajpai-Reuss penicillin model with states biomass, substrate, penicillin, and volume, plus a mass balance consistent feed model.

Simulator inputs: initial conditions, feed policy, kinetic parameters from published parameter sets, process-noise seed, measurement-noise seed, harvest time, and control interval.

Simulator outputs: time series of all states, measured variables, feed profile, and summary outcomes.

## 3. Model input and prediction target

Soft-sensor features: online variables available at the prediction time, batch age, and derived features such as oxygen uptake rate and respiratory quotient where computable.

Soft-sensor target: penicillin concentration in gram per litre from the offline assay label.

Inference rule: features use only information available at time t; offline labels available at time t are at least 12 hours old and arrive with a 4 hour delay.

Training labels are the recorded offline assays; the model is evaluated on the same assay schedule.

Preprocessing: alignment to a common time grid, handling of missing values by forward fill with flags, scaling fit on training batches only.

## 4. Monitoring logic

Golden-batch bands: per-time-point mean and upper and lower bounds computed from healthy training batches within the same control regime.

Deviation score: symmetric mean absolute percentage error of the running batch against the golden profile, following Luo et al. 2024.

Alarm rule: deviation score above a calibrated threshold, sustained for at least a minimum duration.

Alarm output: onset time, contributing variables ranked by contribution, and the evidence level of each input.

Monitoring operates on recorded batches in replay order and on simulator outputs in real time.

## 5. Control algorithm and constraints

Manipulated variable: substrate feed rate.

Controlled output for evaluation: penicillin trajectory and final penicillin yield at harvest time.

### 5.1 Recipe baseline

A fixed or scheduled feed profile that reproduces the published recipe-driven behaviour.

### 5.2 Rule-based feedback

A deterministic feed policy that reacts to the current estimated state within configured bounds.

### 5.3 Constrained MPC

A receding-horizon controller using a linearised model of the simulator about a nominal trajectory.

The controller minimises squared tracking error of the penicillin reference plus a move-suppression term.

The controller respects input limits on the feed rate and move limits per step.

### 5.4 Constraints

Feed-rate bounds: configured minimum and maximum, consistent with the benchmark operating range.

Substrate limit: maximum substrate concentration before inhibition, from the mechanistic parameters.

Volume limit: maximum working volume consistent with the mass-balance window in the benchmark (70,000 to 110,000 kg nominal range).

Control interval: fixed and configurable; the default is consistent with the benchmark's 12 minute online cadence.

### 5.5 Oracle arm

An oracle feedback arm that uses the true simulated state, providing the upper bound of achievable control quality.

The gap between oracle and soft-sensor outcomes quantifies the cost of estimation error.

## 6. Data flow and module interfaces

Modules and responsibilities.

loader: reads the dataset archive, validates hashes and licence note, returns canonical tables.

preprocess: aligns time grids, merges online and offline streams, creates batch-level splits, fits and stores scalers.

monitor: builds golden bands, computes deviation scores and alarms.

softsensor: trains and applies the penicillin estimator, returns predictions and residuals.

simulator: integrates the Bajpai-Reuss model under a feed policy.

recommender: given the current estimated state and constraints, returns a feed command and its justification.

gates: validates every command against configured bounds and triggers fallback.

evaluate: computes the protocol metrics for prediction, monitoring, and control.

dashboard: renders batch replay, predictions, alarms, recommendations, simulated outcomes, and metrics.

Interfaces are pure functions or classes with typed signatures and no hidden global state.

Configuration is read from YAML files in config/; paths, seeds, thresholds, and model choices are never hard-coded in source.

## 7. Failure handling

Missing values: flagged, forward-filled with a flag column, and never used as ground truth.

Stale data: a measurement older than the configured maximum age is treated as invalid.

Invalid inputs: rejected with an explicit error and a logged no-action fallback.

Out-of-bounds commands: clamped or rejected by the gates; the recommendation log records the rejection reason.

Alarms are labelled as alarms, not verified faults; a separate fault flag exists where the label set supports it.

Every measured, predicted, estimated, simulated, and user-configured value is labelled in outputs and in the dashboard.

## 8. Evaluation design

Prediction metrics: MAE, RMSE, R-squared per held-out batch and pooled; separate reporting for normal and fault batches.

Monitoring metrics: detection delay in hours, false-alarm rate, missed-event rate, per control regime.

Control metrics: final penicillin yield, tracking error, constraint-violation frequency, feed consumption, and variance across seeds.

System metrics: inference latency and control-decision time on a reference machine.

Comparisons: controllers are compared under identical initial conditions, disturbances, limits, and evaluation criteria.

Results are written to results/ with pinned seeds, input hashes, and the configuration used.

## 9. Non-goals

No hardware connection, no deployment to a plant, no real-time operating-system guarantees, no multi-user authentication, no production monitoring stack.

No digital-twin platform, no reinforcement learning, no deep-learning hybrid as the primary model, and no uncertainty-calibration subsystem.

The initial LSTM arm is optional and is added only if the Phase 3 evidence justifies it.
