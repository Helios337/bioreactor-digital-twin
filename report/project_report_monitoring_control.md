# Project Report

## Does Soft-Sensor Accuracy Matter for Monitoring and Control in Fed-Batch Penicillin Fermentation?

### A reproducible monitoring-to-control evaluation on the IndPenSim benchmark and a Bajpai-Reuss plant

| Field | Value |
|---|---|
| Date | 29 October 2026 |
| Prepared with | OpenCode research workspace |
| Covering | Deliverables 1 to 5 of the monitoring-to-control research workflow |
| Code and data | Repository `bioreactor-digital-twin`, `src/`, `scripts/`, `results/` |
| Companion review | `review/decision_report_2026-10-29.md`, `review/research_protocol.md` |

### Abstract

Fed-batch fermentation is monitored through sparse, delayed offline assays, and soft sensors are the standard route to online estimates of unmeasured quality variables.

This project builds the smallest defensible monitoring-to-control pipeline for fed-batch penicillin fermentation and uses it to answer one question quantitatively: does soft-sensor estimation accuracy actually change early-warning performance and closed-loop control outcome?

Monitoring and soft sensing are evaluated on the released IndPenSim benchmark (100 simulated batches, CC BY 4.0), and closed-loop feed control is evaluated under matched conditions on a self-implemented Bajpai-Reuss plant.

A random-forest soft sensor matches published IndPenSim baselines on held-out batches (MAE 2.13 g/L, R-squared 0.85 on normal batches).

A golden-band monitor on the true penicillin trajectory detects 23 of 26 below-target held-out batches earlier than the delayed 12 h plus 4 h assay stream, with a median lead of 9.2 h and a false-alarm rate of 4.7 percent.

When the monitor is fed the soft-sensor estimate instead of the true trajectory, the number of below-target batches caught early drops to 11 of 26 and the median lead falls to 5.0 h, at a trajectory MAE of 2.58 g/L.

In matched control experiments, a substrate-PI loop driven by online estimates (oracle or soft-sensor-like) far outperforms the same loop driven by delayed assays (final penicillin 6 to 7.4 g/L versus 0.01 g/L), while a constrained model-predictive controller keeps the delayed-assay arm healthy (9.7 g/L) because the model propagates state between sparse updates.

Estimator noise over a hundredfold range has only a modest effect on final product for either controller, while per-seed process variance dominates.

The headline conclusion: soft-sensor point accuracy buys early-warning ability, not closed-loop outcome, and a process model makes the control loop robust to slow measurements.

### 1. Introduction

#### 1.1 Background

Fed-batch fermentation is a central operation in biopharmaceutical manufacturing, and penicillin fermentation is the reference process for which an open industrial-scale benchmark exists.

Critical quality variables such as product concentration are typically measured offline every 12 hours and the results arrive with an additional 4 hour laboratory delay [B7].

Substrate concentration has no offline measurement at all in the benchmark [B7].

Soft sensors estimate such unmeasured variables from online process variables [S5].

#### 1.2 Problem statement

A soft-sensor estimate is usually evaluated by prediction error on held-out batches.

It is rarely evaluated by what it does downstream: whether it preserves the early-warning signal that a monitoring layer needs, and whether it degrades the feedback loop that a controller runs on.

The project therefore asks one primary question: for fed-batch penicillin fermentation, does soft-sensor estimation accuracy measurably influence monitoring early-warning performance and the quality of constrained substrate-feed control?

#### 1.3 Objectives

1. Build a reproducible monitoring-to-control pipeline on the IndPenSim benchmark and a small documented plant simulator.
2. Evaluate a simple soft sensor on held-out batches against published baselines.
3. Measure early-warning performance of a golden-band monitor on the true and the estimated trajectory, relative to the delayed assay stream.
4. Compare control outcome under oracle, soft-sensor-like, delayed-assay, and recipe sensing in matched simulation experiments.
5. Report conclusions honestly, including negative or null results.

Whole system workflow: measurements, process monitoring, state estimation, control decision, simulated action, updated process state, all in software.

#### 1.4 Non-goals and safety

The prototype never connects to physical equipment.

Control commands are recommendations evaluated in simulation.

Real-time means accelerated replay with documented cadence.

### 2. Literature context and prior work

The integrated monitoring-estimation-control idea is not new.

Zhang and Lennox 2004 combined a PLS biomass soft sensor with a moving-horizon feed controller and SPE/T-squared model monitoring on the penicillin Pensim simulator [Z1].

Montague et al. 1985 combined an extended Kalman filter biomass estimate from carbon dioxide with adaptive predictive control on a 20 litre pilot plant [B5].

On the modern IndPenSim benchmark, published work is soft-sensor-only: Acosta-Pavas et al. 2024 compare interpretable learners for penicillin prediction [Z2], Metcalfe et al. 2025 build an LSTM penicillin soft sensor with drift monitoring [Z3], and Luo et al. 2024 build an offline golden-batch deviation and root-cause method [S1].

Rashedi et al. 2022 put a hybrid linear model inside constrained MPC and found the linear model beat a neural network, a recurring simplicity-wins result [S3].

No peer-reviewed study found in this project closes the substrate-feed loop on the released IndPenSim data or quantifies the estimation-to-control coupling on this benchmark.

That absence is treated as a gap hypothesis, re-verified by targeted searches in this project rather than asserted globally.

### 3. Materials and methods

#### 3.1 Dataset

IndPenSim, Mendeley Data version 2, DOI 10.17632/pdnjz7zz5x.2, licence CC BY 4.0.

Archive hash verified: SHA256 bc434c6cf96444fee3c915d434ac84e2a9c6492be4daebcfa4aed9cdff181f00.

The release contains one process table with 113,935 rows and 2,239 columns, of which 2,200 are Raman wavenumber columns, and one statistics table for 100 batches.

The release header is malformed; the batch identifier lives in the column documented by the record as `2-PAT control(PAT_ref:PAT ref)`.

Control regimes are declared by batch number: 1 to 30 recipe driven, 31 to 60 operator controlled, 61 to 90 advanced process control, 91 to 100 faulted.

All data are simulated and are not plant measurements.

#### 3.2 Preprocessing and labels

Columns were mapped to a canonical schema.

The below-target label uses the endpoint penicillin concentration below 20 g/L, which reproduces the published count of 33 below-target batches [S1].

A yield-in-kilograms rule instead yields 13 and is volume-confounded, so it is not used.

Online assay cadence was confirmed at 12 hours with a 4 hour delay.

All splits are by complete batch, stratified by regime and label, with seed 42, and were persisted before any model selection.

#### 3.3 Soft sensor

Features are the eight online variables of the published baseline: substrate feed rate, agitation, temperature, pH, dissolved oxygen, vessel volume, and off-gas CO2 and O2 [Z2].

Target is the offline penicillin assay label at its 12 hour schedule.

Models: linear ridge regression and random forest with 300 trees.

Trajectory-level out-of-fold predictions were used whenever estimates fed monitoring bands, to avoid in-sample optimism.

#### 3.4 Monitoring

Golden bands are per-time-point means and standard deviation bounds of the penicillin trajectory across healthy training batches of the same control regime.

The monitor alarms at the first time the trajectory drops below the band; a matched assay baseline applies the identical rule to the delayed assay stream.

Lead time is the difference between the two alarming times.

Band width has a physical floor so that near-zero early values do not dominate.

#### 3.5 Control plant and policies

The plant is a Bajpai-Reuss structured penicillin model implemented for this project with documented parameters [B1, Z4].

Policies: constant-feed recipe, substrate-PI feedback, and constrained nonlinear MPC with receding horizon 5, move suppression, and a soft volume limit.

Sensing layers: oracle, noisy estimator with relative noise sigma, and delayed assay (12 h cadence, 4 h delay, zero-order hold).

All arms share initial conditions, seeds, process noise, and limits.

### 4. Results

#### 4.1 Dataset and labels

Table: dataset structure.

| Item | Value |
|---|---|
| Batches | 100 |
| Rows | 113,935 |
| Time cadence | 12 minutes |
| Offline assay cadence | 12 hours plus 4 hours |
| Fault batches | 91 to 100 |
| Below-target batches (endpoint P below 20 g/L) | 33 |
| Held-out batches (test and deviation) | 28 |

#### 4.2 Soft-sensor estimation

Table: held-out-batch prediction results.

| Model | Split | MAE (g/L) | RMSE (g/L) | R-squared |
|---|---|---|---|---|
| Ridge | normal | 4.241 | 6.004 | 0.647 |
| Ridge | fault | 5.296 | 8.058 | 0.145 |
| Random forest | normal | 2.129 | 3.875 | 0.853 |
| Random forest | fault | 3.092 | 4.549 | 0.727 |

Published numbers for context only, because splits differ: Acosta-Pavas Cubist MAE 1.920, R-squared 0.908 [Z2]; Metcalfe LSTM MAE 2.39 to 2.68 on deviation batches [Z3].

A simple random forest is competitive with the published soft sensors, and the LSTM arm was therefore not justified at this stage.

Figure 1: predicted versus offline penicillin, random forest and ridge (results/phase3/softsensor_random_forest.png, results/phase3/softsensor_ridge.png).

#### 4.3 Monitoring

Table: golden-band early warning, oracle versus soft-sensor-estimated trajectory, 26 below-target held-out batches.

| Metric | True trajectory | RF-estimated trajectory |
|---|---|---|
| Detected by monitor | 25 | 21 |
| With lead over the assay stream | 23 | 11 |
| Median lead time (h) | 9.2 | 5.0 |
| False-alarm rate on healthy batches | 4.7 percent | 7.8 percent |

Trajectory estimation error on held-out batches: MAE 2.58 g/L, RMSE 4.18 g/L, R-squared 0.806.

Estimation error roughly halves the fraction of below-target batches with early-warning lead and cuts the median lead close to the assay timeline.

Figure 2: monitoring KPI comparison (results/phase8/monitoring_oracle_vs_estimated.png).

Figure 3: representative fault batch 99 versus the golden band and assay samples (results/phase8/representative_batch_99.png).

#### 4.4 Control

Table: final penicillin by arm, 5 matched seeds, mean and standard deviation.

| Arm | Rule-based PI (g/L) | Constrained MPC (g/L) |
|---|---|---|
| Oracle | 7.36 (3.46) | 9.15 (8.43) |
| Soft-sensor sigma 0.005 | 7.39 (3.13) | 9.13 (8.39) |
| Soft-sensor sigma 0.02 | 6.62 (3.01) | 8.89 (8.07) |
| Soft-sensor sigma 0.05 | 6.32 (2.28) | 9.22 (7.41) |
| Soft-sensor sigma 0.1 | 6.62 (1.73) | 10.03 (6.36) |
| Soft-sensor sigma 0.2 | 6.02 (1.79) | 10.55 (4.62) |
| Soft-sensor sigma 0.5 | 6.28 (1.91) | 8.48 (2.48) |
| Delayed assay | 0.01 (0.00) | 9.74 (9.10) |
| Recipe (no feedback) | 10.89 (0.87) | not applicable |

Three findings follow.

First, a pure measurement-feedback loop driven by delayed assays collapses the batch, while the model-based controller keeps it healthy.

Secondly, estimator noise over a hundredfold range changes final product by only a modest amount for either controller, and per-seed variance dominates.

Thirdly, a well-tuned constant-feed recipe is hard to beat at this operating point, consistent with simplicity-wins results in the literature [S3].

Figure 4: control outcome versus estimator noise for both controllers (results/phase8/control_p_vs_sigma.png).

### 5. Discussion

The results separate two things that are often conflated: the accuracy of a soft-sensor estimate and the value of that estimate downstream.

Prediction accuracy transfers to monitoring: a trajectory MAE of 2.58 g/L halves the early-warning yield and nearly halves the median lead.

Prediction accuracy does not transfer to rule-based or model-based control outcome at this operating point, because both controllers are robust to substrate-estimate noise and because outcome variance is dominated by process disturbances.

Sensing cadence is the controlling factor for control: delayed assay feedback is catastrophic for a feedback-only loop but not for a model-based controller.

This suggests that for control quality, investing in a process model matters more than polishing a point estimator, while for early-warning monitoring, estimator quality directly determines lead time.

These are quantitative, matched, reproducible statements about a simulated benchmark, evaluated with the same seeds, initial conditions, and limits across all arms.

### 6. Limitations

The IndPenSim data are simulated, and the control plant is a self-implemented Bajpai-Reuss model, so absolute values are not transferable to any physical process.

Published soft-sensor baselines use different data splits; comparisons are contextual only.

The monitoring lead definition and the band-width floor are documented choices that affect the absolute numbers.

The MPC volume limit is a soft penalty, and volume-limit crossings remain frequent in all MPC arms.

The estimator is a point predictor; shrinkage toward the training envelope is a known limitation for deviation detection.

No physical validation was performed, and deployment would require process-specific checks, fail-safe engineering, and authorization.

### 7. Conclusion

The smallest defensible monitoring-to-control system for fed-batch penicillin fermentation was built, tested, and evaluated end to end.

Soft-sensor point accuracy strongly affects early-warning monitoring performance but weakly affects closed-loop control outcome at the studied operating point.

Delayed offline assay feedback breaks a feedback-only controller and is rescued by a model-based controller.

Simplicity wins: a tuned constant-feed recipe outperforms the tuned rule-based controller, and a random forest matches deep-learning baselines.

The project delivers the decision report, research protocol, system specification, working reproducible implementation, and paper plan that were requested, with all recorded numbers tied to reproducible runs.

### 8. References

The following references were verified against Crossref, OpenAlex, or full text.

[B1] Bajpai RK, Reuss M. A mechanistic model for penicillin production. Journal of Chemical Technology and Biotechnology, 1980, 30:332-344. DOI 10.1002/jctb.503300140.

[B5] Montague GA, Morris AJ, Wright AR, Aynsley M, Ward A. Parameter adaptive control of the fed-batch penicillin fermentation. IFAC Proceedings Volumes, 1985, 18(17):69-74. DOI 10.1016/S1474-6670(17)59895-X.

[B7] Goldrick S, Duran-Villalobos CA, Jankauskas K, Lovett D, Farid SS, Lennox B. Modern day monitoring and control challenges outlined on an industrial-scale benchmark fermentation process. Computers and Chemical Engineering, 2019, 130:106471. DOI 10.1016/j.compchemeng.2019.05.037.

[S1] Luo D, He M, Darko J, Ly Seymour F, Maturana F. The golden batch-driven root cause analysis for anomalies in bioreactor fermentation process. Frontiers in Manufacturing Technology, 2024, 4:1392038. DOI 10.3389/fmtec.2024.1392038.

[S3] Rashedi M, Khodabandehlou H, Demers M, Wang T, Garvin C. Model predictive controller design for bioprocesses based on machine learning algorithms. IFAC-PapersOnLine, 2022, 55(7):45-50. DOI 10.1016/j.ifacol.2022.07.420.

[S5] Zhu X, Rehman KU, Wang B, Shahzad M. Modern soft-sensing modeling methods for fermentation processes. Sensors, 2020, 20(6):1771. DOI 10.3390/s20061771.

[Z1] Zhang H, Lennox B. Integrated condition monitoring and control of fed-batch fermentation processes. Journal of Process Control, 2004, 14(1):41-50. DOI 10.1016/S0959-1524(03)00044-1.

[Z2] Acosta-Pavas JC, Robles-Rodriguez CE, Griol D, Daboussi F, Aceves-Lara CA, Corrales DC. Soft sensors based on interpretable learners for industrial-scale fed-batch fermentation: Learning from simulations. Computers and Chemical Engineering, 2024, 187:108736. DOI 10.1016/j.compchemeng.2024.108736.

[Z3] Metcalfe B, Acosta-Pavas JC, Robles-Rodriguez CE, Georgakilas GK, Dalamagas T, Aceves-Lara CA, Daboussi F, Koehorst JJ, Corrales DC. Towards a machine learning operations (MLOps) soft sensor for real-time predictions in industrial-scale fed-batch fermentation. Computers and Chemical Engineering, 2025, 194:108991. DOI 10.1016/j.compchemeng.2024.108991.

[Z4] San KY, Stephanopoulos G. Optimization of fed-batch penicillin fermentation: a case of singular optimal control with state constraints. Biotechnology and Bioengineering, 1989, 34(1):72-78. DOI 10.1002/bit.260340110.

The full verified bibliography is in references/references.bib.

### Appendix A. Reproducibility

Environment: Python 3.12, numpy, pandas, scipy, scikit-learn, matplotlib, pytest, streamlit.

Pipeline: `PYTHONPATH=src .venv/bin/python scripts/0_run_all.py`.

Dashboard: `.venv/bin/streamlit run dashboard/app.py`.

All random processes use pinned seeds recorded in each report.

Configuration is separated from source in config/config.yaml.

### Appendix B. Result files

- results/phase1/inspection_report.json and .md.
- results/phase2/monitoring_report.json and per_batch_monitoring.csv.
- results/phase3/softsensor_report.json and model figures.
- results/phase4/monitoring_estimated_report.json and per_batch_monitoring_estimated.csv.
- results/phase6/control_report.json, per_run_control.csv, control_by_arm.png.
- results/phase7/mpc_report.json, per_run_mpc.csv, mpc_report.md.
- results/phase8 project figures.
