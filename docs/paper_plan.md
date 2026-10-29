# Research Paper Plan

Status: plan. Numerical results in this document are copied from actual runs
where they exist, and marked as placeholder otherwise.

## Working title

Does Soft-Sensor Accuracy Matter for Control in Fed-Batch Penicillin Fermentation? A Reproducible Monitoring-to-Control Evaluation on IndPenSim and a Bajpai-Reuss Plant.

## Abstract outline

1. Motivation: delayed offline assays, soft sensors, and the open question of
whether point-prediction accuracy translates into closed-loop benefit.
2. Method: golden-batch monitoring on the released IndPenSim benchmark compared
against a delayed-assay baseline; random-forest soft sensor with leak-free
held-out evaluation; matched closed-loop feed-control experiments on a
self-implemented Bajpai-Reuss plant under oracle, noisy-estimator, and delayed-assay
sensing.
3. Results (summary bullets, from results/ runs only).
4. Conclusion: estimation error erodes early-warning ability more than it
erodes rule-based control outcome; delayed assay feedback is much worse than
online feedback; simpler controllers can match or beat tuned rule-based loops.

## Introduction and related work

Structure: (1) the measurement problem in fed-batch fermentation (B7); (2)
soft sensors and their evaluation (Acosta-Pavas 2024, Metcalfe 2025, Zhu 2020);
(3) monitoring and root cause analysis (Luo 2024); (4) control with estimated
states (Zhang and Lennox 2004, Montague 1985, Rashedi 2022); (5) the gap: no
matched quantification on the modern benchmark of how estimator accuracy shapes
monitoring lead time and control outcome.

## Research questions

RQ1: Can a simple soft sensor match published IndPenSim penicillin baselines on
held-out batches?
RQ2: Does a golden-band monitor using the true and the estimated trajectory
detect below-target batches earlier than the delayed assay stream, and at what
false-alarm rate?
RQ3: Under matched conditions in a penicillin simulator, how does control
outcome depend on feedback sensing (oracle, noisy estimator, delayed assay,
recipe)?

## Methodology

- Dataset: IndPenSim Mendeley V2, CC BY 4.0, SHA256 verified.
- Preprocessing: canonical schema, per-batch keys from the PAT_ref column,
regimes, fault flags, endpoint < 20 g/L below-target label (reproduces the
published count of 33).
- Soft sensor: random forest on the published 8-variable online feature set;
complete-batch splits, chronological ordering, out-of-fold trajectory
predictions for band construction.
- Monitoring: per-regime golden bands on the CQA trajectory; first below-band
crossing; matched delayed-assay baseline (12 h cadence, 4 h delay).
- Control: Bajpai-Reuss plant implemented for this project (documented
parameters); policy arms recipe, substrate-PI, constrained nonlinear MPC;
sensing arms oracle, noisy estimator at sigma levels, delayed assay; matched
seeds and limits.
- Reproducibility: pinned seeds, config separated from code, result JSON with
settings, tests in the repository.

## Experimental design

Contrasts and metrics tables as in the research protocol. No test-batch data
touches any fitting decision.

## Results to generate (figures and tables)

1. Table: soft-sensor per-model metrics on held-out normal and fault batches,
with published baselines quoted for context.
   - Actual (scripts/3): random forest MAE 2.13 g/L, RMSE 3.88, R2 0.85 on
     normal held-out batches; fault batches MAE 3.09, R2 0.73. Ridge clearly
     worse. Context: Acosta-Pavas Cubist MAE 1.92, R2 0.908 on their own
     split; Metcalfe LSTM MAE 2.39-2.68 on deviation batches.
2. Figure: predicted vs offline penicillin scatter per model.
3. Table: monitoring oracle vs estimated: detected, lead-over-assay counts,
median lead, false-alarm rate.
   - Actual (scripts/2, scripts/4): true trajectory 25/26 detected, 23 with
     lead, median lead 9.2 h, FAR 4.7%. Estimated trajectory 25/26 detected,
     21 with lead, median lead 5.0 h, FAR 7.8%, at trajectory MAE 2.58 g/L.
4. Figure: per-batch deviation traces for representative batches (healthy,
below-target, fault).
5. Figure: monitoring degradation from true to estimated trajectory.
6. Table: control arms (recipe, PI-oracle, PI-noisy, PI-assay, MPC-oracle,
MPC-noisy, MPC-assay): final P mean and std, feed use, violations.
   - Actual (scripts/6, scripts/7): see the Phase 6 and Phase 7 reports;
     headline numbers in the Results summary below.
7. Figure: final P versus estimator noise sigma for PI and MPC.
8. Figure: coverage diagram of the full pipeline.

## Results summary (actual runs, 2026-10-29)

Monitoring (26 below-target held-out batches):
- Oracle trajectory: 23/26 with early-warning lead over the delayed assay
  stream, median 9.2 h, false-alarm rate 4.7 %.
- Random-forest-estimated trajectory (MAE 2.58 g/L): 21/26 with lead,
  median lead 5.0 h, false-alarm rate 7.8 %.

Control (matched seeds, 5 seeds per arm, Bajpai-Reuss plant):
- Rule-based substrate-PI with oracle or noisy estimator feedback: final P
  6.0 to 7.4 g/L; with delayed-assay feedback the batch collapses (0.01 g/L).
- Constrained MPC: final P 8.5 to 10.6 g/L across the same sensing layers,
  including the delayed-assay arm (9.7 g/L), because the model propagates
  state between sparse updates.
- Tuned constant-feed recipe: 10.9 g/L.
- Final P is only modestly sensitive to estimator noise over a 100x range for
  both controllers; per-seed process-disturbance variance dominates.

Headline conclusions:
1. Soft-sensor point accuracy strongly affects monitoring early-warning ability
   (H2), even when it weakly affects control outcome (H3).
2. Delayed off-line feedback is catastrophic for a pure measurement-feedback
   loop but not for a model-based controller.
3. A well-tuned conventional recipe is hard to beat at one operating point:
   simplicity wins, consistent with earlier findings.

## Discussion and limitations

- Simulated benchmark data and self-implemented plant; absolute values not
transferable.
- Published baselines use different splits; only contextual comparison.
- Monitoring lead definition and band width floor choices.
- The estimator was point-predictive; shrinkage toward the training envelope.
- No physical validation; deployment requires process-specific checks.

## Claim-level citations

Every result claim is tied to a specific row of results/*/ and a protocol
section. Literature claims are tied to references.bib entries with verified
metadata.
