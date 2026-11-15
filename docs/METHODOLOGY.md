# Methodology

Status: methodology reference. This document records the data definitions,
features, targets, phase segmentation, assay delay and experiment design used
across the repository, so claims are traceable to definitions.

## 1. Data definitions

Source: IndPenSim version 2 (Mendeley Data, DOI 10.17632/pdnjz7zz5x.2,
CC BY 4.0). This is a simulated benchmark, not physical plant data.

Canonical per-row schema (created by `src/bioreactor_monitoring/preprocess.py`):

- `batch`: integer batch id, 1 to 100.
- `time_h`: elapsed batch time in hours.
- Online process variables: aeration, agitator RPM, feed rate, acid/base/
  cooling/heating/water flows, head pressure, dumped flow, substrate `substrate_g_l`,
  dissolved oxygen `do2_mg_l`, vessel volume `volume_l`, weight, pH, temperature,
  heat, CO2 and O2 off-gas %, PAA flow, oil flow, OUR, CER, ammonia shots.
- `p_true_g_l`: dense simulated (true) penicillin trajectory, present on every row.
- `p_offline_g_l`: sparse offline assay label, present on roughly 12-hour rows.
- `x_offline_g_l`: sparse offline biomass label.
- `fault`: 1 for batches 91 to 100.
- `regime`: recipe (1-30), operator (31-60), apc (61-90), fault (91-100).
- `below_target`: 1 when the batch endpoint `p_true_g_l < 20 g/L`.

## 2. Targets

- Soft-sensor baseline (Phase 3): sparse offline penicillin `p_offline_g_l`.
- Monitoring (Phases 2 and 4): the penicillin trajectory; Phase 2 uses the dense
  true trajectory (oracle), Phase 4 uses an estimated trajectory.
- GRU forecasting (Phase 5): Mode 1 target is the dense `p_true_g_l`; Mode 2
  target is the sparse offline assay `p_offline_g_l`.
- Control (Phases 6 and 7): outcomes on the separate Bajpai-Reuss simulator.

## 3. Assay delay

Offline assays are revealed only `delta = 4 h` after sampling
(`assay_available` in preprocess). The soft-sensor and monitoring evaluations
respect this: an assay sampled at time `t` is known to the downstream system at
`t + 4`. For online forecasting, inputs available at time `t` are used to
predict a target at `t + horizon`.

## 4. Batch splits

`results/splits.json` records a deterministic whole-batch split (seed 42):
72 training batches and 28 test + deviation batches (including fault batches
91-100). Every batch stays in a single partition. Preprocessing is fit on the
training batches only and applied to the rest.

## 5. Phase segmentation and monitoring

Monitoring follows a golden-batch deviation approach (Luo et al. 2024),
rebuilt per control regime from healthy training batches and applied to each
held-out batch. A batch is flagged when its trajectory drops below the lower
band, with a minimum-alarm-duration rule for the false-alarm assessment.

## 6. Experiment design notes

- Phase 2 uses the dense simulated true trajectory as an oracle reference. It
  is not a deployable sensor.
- Phase 4 uses estimated trajectories and, after the correctness repair, only
  causal (past-only) smoothing for online and lead-time claims.
- Phase 5 GRU is a standalone component; it does not depend on the dashboard,
  monitoring, or control code.
- Phases 6 and 7 run the Bajpai-Reuss simulator only; results must not be read
  as IndPenSim or industrial validation.