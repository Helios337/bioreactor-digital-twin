# Research Protocol

Date: 2026-10-29. Status: approved basis for implementation (Deliverable 2).

This protocol governs the empirical phases of the project: monitoring, soft sensing, and simulated closed-loop feed control for fed-batch penicillin fermentation.

It extends the existing literature search and screening protocol in review/search_protocol.md and the evidence base in references/literature_matrix.csv.

## 1. Research questions and hypotheses

Primary research question: For fed-batch penicillin fermentation, does soft-sensor estimation accuracy measurably influence the quality of constrained substrate-feed control decisions, and can a simple monitoring layer flag process deviations early enough to inform those decisions?

Sub-question 1 (estimation): Can a simple soft sensor predict penicillin concentration on held-out IndPenSim batches with accuracy comparable to published baselines?

Sub-question 2 (monitoring): Does a golden-batch-style streaming monitor detect below-target IndPenSim batches earlier than the offline-assay timeline, and at what false-alarm rate?

Sub-question 3 (control): Under matched disturbances in a penicillin simulator, how does soft-sensor-informed feed control compare with a recipe baseline and with oracle state feedback, and does control quality degrade as estimation error increases?

Hypotheses.

H1: A simple soft sensor (linear ridge or random forest) predicts held-out batch penicillin with MAE and RMSE in the range of the published IndPenSim soft-sensor results.

Published reference values: Acosta-Pavas et al. 2024 report Cubist R-squared 0.908, RMSE 3.149, MAE 1.920 on their IndPenSim split; Metcalfe et al. 2025 report LSTM MAE about 2.39 to 2.68 gram per litre on deviation batches 94, 99 and 100.

H1 is compared against these numbers on our own fixed splits, with the split reported, because model comparisons are only meaningful on identical data partitions.

H2: The streaming monitor raises an alarm for at least the majority of the 33 below-target batches before the time at which the offline assay confirms the anomaly, with a false-alarm rate below a pre-specified threshold on healthy batches of the same control regime.

H3: In matched simulations, feedback control with a soft-sensor estimate changes final penicillin outcome relative to the fixed recipe baseline, and final outcome degrades monotonically as the injected estimation standard deviation increases.

Falsification statements.

H1 is falsified if the simple models underperform the published range on our splits by a large margin that cannot be explained by split differences.

H2 is falsified if detection delay is not better than the assay timeline on most below-target batches, or if the false-alarm rate is not acceptable.

H3 is falsified if feedback control does not change outcomes relative to the recipe baseline, or if control quality is insensitive to estimation error across the swept range.

A falsified hypothesis is a valid result and will be reported honestly rather than hidden.

## 2. Data source, licence, and provenance

Dataset: IndPenSim, version 2, Mendeley Data record pdnjz7zz5x, DOI 10.17632/pdnjz7zz5x.2.

Licence: CC BY 4.0, as recorded in the dataset snapshot on 2026-10-29.

Archive: 100_Batches_IndPenSim.zip, 503,792,426 bytes.

Archive SHA256: bc434c6cf96444fee3c915d434ac84e2a9c6492be4daebcfa4aed9cdff181f00.

Content description from the record: 100 simulated batches of an industrial-scale 100,000 litre penicillin fermentation.

Control regimes in the released data: batches 1 to 30 recipe driven, batches 31 to 60 operator controlled, batches 61 to 90 advanced process control with a Raman soft sensor, batches 91 to 100 containing process faults.

Process data are simulated and are not plant measurements.

The dataset record states that a target production yield is 2,000 kg penicillin per batch and that below-target batches trigger investigation.

Units and yield definitions in the release will be verified during dataset inspection because the summary file appears to report total penicillin in grams rather than kilograms.

Citation for any use: Goldrick et al. 2019 for the benchmark paper, and the dataset DOI for the data.

The Bajpai-Reuss simulator for the control experiments is implemented by this project from the published mechanistic model and published parameter sets, and is not part of the Mendeley dataset.

## 3. Search protocol for the implementation phase

The literature search protocol, exact strings S1 to S9, databases, and eligibility criteria are documented in review/search_protocol.md.

Additional targeted verification performed on 2026-10-29 for this protocol used Crossref bibliographic search and publisher full text.

Search strings used for the gap check in this phase: soft sensing combined with feedback or predictive control for penicillin fermentation; closed-loop control on the IndPenSim dataset; estimation-to-control sensitivity in fed-batch fermentation.

Inclusion criteria for this gap check: penicillin or fed-batch fermentation processes; soft sensors, monitoring, or feed-rate control; verifiable metadata.

Exclusion criteria: continuous-only processes without batch relevance; studies without any estimation, monitoring, or control component; unverifiable records.

Screening decisions.

Included as prior art limiting novelty: Zhang and Lennox 2004 (integrated PLS soft sensor plus predictive control plus model monitoring on the Pensim penicillin process).

Included as soft-sensor-only prior art on IndPenSim: Acosta-Pavas et al. 2024, Metcalfe et al. 2025, Luo et al. 2024, Liu et al. 2024.

Included as control prior art on the classic penicillin model: San and Stephanopoulos 1989, Lim et al. 1986, Rodrigues et al. 1996.

Included as adjacent recent work: Herrera-Contreras et al. 2026 (early warning and forecasting, no control).

No peer-reviewed study was found in this phase that closes the substrate-feed loop on the released IndPenSim data or quantifies the estimation-to-control coupling on this benchmark.

This absence is a gap hypothesis and will be re-verified by citation chaining of the included papers' reference lists and cited-by records before any novelty claim is made.

## 4. Citation verification status

Citation keys follow references/references.bib.

New sources verified on 2026-10-29 with Crossref records or full text: Zhang and Lennox 2004, Acosta-Pavas et al. 2024, Metcalfe et al. 2025, Liu et al. 2024, Herrera-Contreras et al. 2026, San and Stephanopoulos 1989, Lim et al. 1986.

The dataset record and licence were verified via the Mendeley public API snapshot endpoint.

Access level per source is recorded in references/source_register.md.

## 5. Experimental design

### 5.1 Soft-sensor experiment

Units of analysis: batches.

Splits: complete-batch splits only, never random assignment of adjacent time points.

The final test set is a fixed set of held-out batches selected before any model tuning and never used for selection.

Validation: chronological ordering preferred where the use case is future-time prediction.

Preprocessing, missing-value handling, and feature selection are fixed in advance and documented.

Metrics: MAE, RMSE, R-squared computed per held-out batch and pooled across batches.

Normal-operation batches and deviation batches are evaluated and reported separately.

### 5.2 Monitoring experiment

Golden-band profiles are built from healthy batches within the same control regime to avoid regime confounding.

Deviation score follows the symmetric MAPE approach of Luo et al. 2024.

Alarm threshold is calibrated on a within-regime validation set.

Metrics: detection delay in hours relative to the 12 hour plus 4 hour assay timeline, false-alarm rate, missed-event rate.

Evaluation uses the below-target labels of Luo et al. 2024 as the reference label set, with the control regime stated for every reported number.

### 5.3 Control experiment

Plant model: the published Bajpai-Reuss penicillin model implemented by this project.

Comparators: fixed recipe feed, rule-based feedback feed, constrained linearised MPC, oracle state feedback.

Matched conditions: identical initial states, identical disturbance vectors and seeds, identical operating constraints for all comparators.

Estimation-error sweep: feedback controllers are run with several injected estimation-error levels to measure the coupling between estimation accuracy and control outcome.

Metrics: final penicillin yield at harvest time, trajectory tracking error, constraint-violation frequency, feed consumption, and variability across seeds.

Repeated seeded runs provide variability estimates; per-seed results are retained for transparency.

### 5.4 System experiment

Latency and computation time of the inference and control decision steps are logged on a fixed reference machine.

The dashboard replays recorded batches and control simulations with a documented data-update cadence.

## 6. Leakage-prevention strategy

No training point from a test batch is used for any fitting decision, including scaling, imputation, or threshold calibration.

Scaling and imputation parameters are fit on the training batches only.

Monitoring bands and alarm thresholds are calibrated without the final test batches.

Control evaluation never uses test-batch recorded data to train the controller or the estimator.

All random processes use pinned seeds that are recorded with every result.

## 7. Reproducibility commitments

Every result is produced by a script with a recorded command line and pinned seeds.

Configuration, including paths, seeds, and thresholds, is separated from source code.

A makefile or equivalent orchestrates download, preprocessing, training, evaluation, and dashboard steps.

Test results and experiment outputs are written to results/ with timestamps and hashes of the input data version.

## 8. Ethics and integrity

Simulated data are never presented as plant data.

Prediction accuracy is never presented as control performance.

No real-time or closed-loop claim is made beyond the simulator and the replay harness.

All limitations identified in this protocol are carried into the manuscript.
