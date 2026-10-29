# Synthesis Notes

Status: scaffold with seed-corpus evidence pre-filled. Database-search evidence and citation chaining are pending (Phase 2 to Phase 4).

Rule: established evidence is cited. Reviewer interpretation is marked [INTERPRETATION]. Proposals are marked [PROPOSAL]. Nothing here is a novelty claim yet.

## Capability matrix

Scores: yes, partial, no, unknown (pending full text).

| Source | Delayed sensing | Sensor faults | Drift | Uncertainty | Closed-loop control | Fallback | Validation type |
|---|---|---|---|---|---|---|---|
| B1 Bajpai 1980 | no | no | no | no | no | no | model formulation |
| B2 Menezes 1994 | no | no | no | no | no | no | pilot-plant data (abstract) |
| B3 Zangirolami 1997 | no | no | no | no | no | no | simulation |
| B4 Birol 2002 | partial | partial | no | no | no | no | software package with monitoring/fault-diagnosis use case |
| B5 Montague 1985 | no | no | partial (parameter adaptation) | partial (EKF) | yes (adaptive GPC) | no | real-time 20-L pilot experiments |
| B6 Goldrick 2015 | no | partial (batch variation modelled) | partial (campaign variation) | no | no | no | simulation validated on industrial data |
| B7 Goldrick 2019 | yes (4-h assay delay modelled) | yes (agitator, aeration, substrate, sensor faults) | partial (batch-to-batch and campaign variation) | no | partial (PID plus recipe only, no APC) | no | simulation benchmark plus released dataset |
| B8 Metcalfe 2025 | partial | partial (deviation batches) | yes (PSI concept-drift alert) | no | no | no | proof of concept on simulated benchmark |
| B9 Zheng 2022 | unknown | unknown | unknown | no | no | no | industrial case studies (abstract) |
| B10 Hermann 2025 | unknown | unknown | unknown | partial (UKF) | no | no | bioprocess case study (abstract) |
| B11 Shukla 2026 | review | review | partial (biological variability) | review | review (adaptive control discussed) | review | n/a |
| B12 Page 2021 | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| S1 Luo 2024 | partial (delay inherent in dataset) | partial (anomaly and deviation detection) | no | no | no | no | IndPenSim 100 batches versus PCA baseline |
| S3 Rashedi 2022 | partial (daily sampling) | no | no | no | yes (MPC plus real experiment) | no | 35 historical batches plus real bioreactor validation |
| S4 Kwon 2024 | no | yes (noisy, malfunctioning, corrupt sensors) | no | partial (variability reduction) | no | no | 11 lab-scale cycles with resampled testing |
| S5 Zhu 2020 | review | review | review | review | review | review | review of 70+ studies, mostly simulation |
| S6 Mondal 2023 | review | review | review | review | review | review | review |
| S7 Gil 2026 | no | partial (disturbances, partial observability) | partial (nightly fine-tuning) | no | yes (RL deployed on real facility) | no | simulation plus 8-day real deployment |

Reading of the matrix [INTERPRETATION, to be verified by chaining]:

- Delayed sensing is modelled explicitly only in B7. B8 inherits it through IndPenSim. No source handles assay delay as a first-class monitoring problem.
- Sensor faults appear as benchmark scenarios (B7) or as data-quality problems (S4). No source fuses fault detection with estimation quality gating.
- Drift is addressed by B8 (PSI retraining alert) and partially by S7 (nightly fine-tuning). The two are not connected.
- Uncertainty appears only as EKF/UKF estimation error (B5, B10) or variability reduction (S4). Calibrated prediction uncertainty that constrains decisions is absent.
- Closed-loop control exists in B5, S3 and S7. None of them consumes a monitoring layer output.
- Fallback supervision is absent across all sources.
- Validation is dominated by simulation (B6, B7, B8, S1, S3 pre-deployment) with one real 8-day RL deployment (S7) and one real MPC experiment (S3).

## RQ1: measurements and soft sensors

Established evidence:

- Online variables at 12-minute cadence plus Raman spectra every 30 minutes versus 12-hour off-line assays with a 4-hour delay (B7, full-text).
- PLS on Raman spectra predicts penicillin comparably to off-line assays (B7, full-text).
- Soft sensing taxonomy: SVM, LS-SVM, neural networks, deep learning, fuzzy logic, probabilistic latent variable models, with metaheuristic optimization (S5, full-text).
- CNN-LSTM hybrid soft sensors for nonlinear dynamics (B9, abstract).
- LSTM soft sensor with 8-hour forecast horizon on IndPenSim (B8, abstract).
- VAE-generated synthetic time series improve soft sensor R-squared by 34% and cut variability by 82% on ethanol fermentation (S4, full-text).
- PLS plus UKF fusion for state estimation (B10, abstract; L-phenylalanine process, transferable only).

[INTERPRETATION] The estimation stack is mature at the level of single-variable accuracy. What is missing is the consumption of estimation uncertainty downstream.

## RQ2: model class appropriateness

Established evidence:

- Mechanistic models: B1, B2, B3, B4, B6.
- Hybrid mechanistic plus data-driven: S3 (mass balance plus regression inside MPC; linear beat NN on normalized RMSE).
- Pure data-driven: B8, B9, S4.
- Observer-based: B5 (EKF), B10 (UKF).
- Reviews recommend hybrid models (S5, S6, full-text).

[INTERPRETATION] S3 is the strongest caution against complexity: the linear hybrid won. Model choice should be justified by control objective and data sparsity, not accuracy alone.

## RQ3: latency, faults, drift, uncertainty

Established evidence:

- 4-hour off-line delay and 12-hour assay cadence are simulated explicitly (B7, full-text).
- Fault scenarios: agitator trip, aeration faults, substrate faults, sensor errors (B7, full-text).
- Corrupt, missing and malfunctioning sensor data handled by augmentation (S4, full-text).
- Concept drift via PSI threshold with automated retraining alert on deviation batches 91-100 (B8, abstract).
- Nightly policy fine-tuning against evolving dynamics (S7, full-text).

[INTERPRETATION] Each phenomenon is handled in isolation by a different community. No source in the current corpus handles latency, faults, drift and uncertainty jointly in one monitoring stack. This is candidate gap 1, pending chaining.

## RQ4: predictions to constrained MPC and fallback

Established evidence:

- Hybrid model inside constrained MPC maximizing VCD with metabolite constraints (S3, full-text).
- Adaptive Generalised Predictive Control with EKF biomass estimation from CO2 on a 20-L pilot plant (B5, abstract).
- Offline DDPG with behavior cloning from PID trajectories, POMDP formulation, logarithmic reward, anti-windup clipping, nightly fine-tuning (S7, full-text).
- IndPenSim control objectives: manipulate Fs, FN, FPAA; optimal harvest time; enhanced pH and temperature control (B7, full-text).

[INTERPRETATION] Control evidence exists but is decoupled from monitoring evidence. Fallback supervision is unaddressed (candidate gaps 2 and 3).

## RQ5: validation evidence beyond offline accuracy

Established evidence:

- Real bioreactor MPC experiment with over 2% protein improvement (S3, full-text).
- 8-day real photobioreactor RL deployment (S7, full-text).
- Released 100-batch benchmark dataset with Raman spectra (B7, full-text).
- Reviews note the simulation-only evidence base and few industrial deployments (S5, S6, full-text).

[INTERPRETATION] The field validates accuracy far more often than it validates decision quality, safety, or fallback behaviour. Candidate gap 4 and 5 live here.

## Gap register (hypotheses, chaining pending)

1. Joint handling of delayed observations, sensor faults and prediction uncertainty in fed-batch fermentation. Status: pending chaining.
2. Calibrated uncertainty that changes or constrains MPC decisions, not just reported as a metric. Status: pending chaining.
3. Explicit fallback or supervisory control on poor sensor health or model reliability, with validated fallback behaviour. Status: pending chaining.
4. Reproducible matched-scenario comparison of conventional, ML-MPC, hybrid MPC and reliability-aware MPC. Status: pending chaining.
5. Transfer limits of simulated IndPenSim evidence to real processes and across scales. Status: pending chaining.

## Cross-paper synthesis leads for Phase 4 chaining

- Metcalfe 2025 (B8) cites IndPenSim lineage; chain its references for drift-detection predecessors.
- Shukla 2026 (B11) reference list includes Goldrick 2019, Kwon 2024, Hermann 2025, Cheng 2024 (semi-supervised VAE soft sensor), Appl 2020 bioprocess digital twins, Hassan 2024 VR bioreactor twin. Chain these for the digital-twin and VAE threads.
- Gil 2026 (S7) cites Espinel-Rios 2025, Sass 2022, Monteiro 2026, Petsagkourakis 2020 for RL in bioprocesses. Chain for the control thread.
- Luo 2024 (S1) cites PCA/MSPC and doWhy causal tooling. Chain for the RCA thread.
