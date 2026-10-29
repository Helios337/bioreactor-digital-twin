# Manuscript Draft (Scaffold)

Working title: From Prediction to Trustworthy Closed-Loop Control: A Fault-Aware Digital-Twin Framework for Fed-Batch Fermentation.

Status: scaffold only. Sections contain structure, citation keys and markers. No results are claimed anywhere in this document.

Marker legend: [EVIDENCE] established, cited. [INTERPRETATION] reviewer reading of cited evidence. [PROPOSAL] this project's proposed element, to be evaluated.

## 1. Abstract

[TO WRITE after synthesis] Scoped critical review plus proposed architecture. No experimental claims.

## 2. Introduction and research questions

- Fed-batch fermentation monitoring problem: delayed off-line assays, sensor faults, drift, living-cell variability [EVIDENCE: B7, S6].
- PAT and QbD context [EVIDENCE: B7].
- Research questions RQ1 to RQ5 [EVIDENCE: review/scope_and_questions.md].
- Contribution: a reliability-oriented reference architecture proposal plus a verified evidence matrix. [PROPOSAL]

## 3. Review protocol and search methodology

- Databases, strings S1 to S9, date window 1980 to present, inclusion and exclusion criteria [EVIDENCE: review/search_protocol.md].
- Screening log and flow [EVIDENCE: review/screening_log.csv].
- Metadata verification method [EVIDENCE: references/source_register.md].
- Reporting guidance [EVIDENCE: B12].

## 4. Penicillin fermentation process and modelling foundations

- Mechanistic foundations [EVIDENCE: B1, B2, B3].
- Simulator lineage from modular package to IndPenSim [EVIDENCE: B4, B6, B7].
- Historical adaptive predictive control with EKF biomass estimation [EVIDENCE: B5].

## 5. Sensors, PAT, soft sensors and state estimation

- Measurement landscape and assay delay [EVIDENCE: B7].
- Raman plus PLS [EVIDENCE: B7].
- Soft sensing taxonomy [EVIDENCE: S5].
- CNN-LSTM and LSTM-MLOps soft sensors [EVIDENCE: B9, B8].
- Observer-based estimation [EVIDENCE: B10, B5].
- VAE augmentation for sparse data [EVIDENCE: S4].
- [INTERPRETATION] accuracy-focused, uncertainty-consumption absent.

## 6. Hybrid digital twins and model maintenance under drift

- Hybrid modelling evidence [EVIDENCE: S3].
- Digital twin context, scope-distinguished [EVIDENCE: B11].
- Drift detection and retraining alert [EVIDENCE: B8].
- Landscape and deployment gaps [EVIDENCE: S6].
- [PROPOSAL] twin maintenance policy triggered by monitoring health signals.

## 7. Faults, delayed observations and uncertainty calibration

- Benchmark fault scenarios [EVIDENCE: B7].
- Anomaly detection and golden-batch RCA [EVIDENCE: S1].
- Data-quality robustness via augmentation [EVIDENCE: S4].
- [PROPOSAL] fused alert logic combining golden-batch deviation, reconstruction residual, and estimation uncertainty.
- Candidate gaps 1 and 3 [INTERPRETATION pending chaining].

## 8. Predictive control, operating constraints and fallback supervision

- Hybrid MPC evidence [EVIDENCE: S3].
- Historical adaptive control [EVIDENCE: B5].
- Offline RL with behavior cloning [EVIDENCE: S7].
- [PROPOSAL] monitoring-informed control gating and recipe fallback.
- Candidate gaps 2 and 4 [INTERPRETATION pending chaining].

## 9. Proposed reference architecture

- Figure 1: proposed architecture (figures/proposed_architecture.mmd). Caption: proposed, to be evaluated.
- Component rationale with citations [EVIDENCE where available; PROPOSAL elsewhere].
- [PROPOSAL] the integration claims: streaming golden-batch monitor, uncertainty-gated alerts, fallback supervisor.

## 10. Validation roadmap, benchmark design and metrics

- Staged roadmap: offline review, software-in-the-loop, hardware-in-the-loop where appropriate, supervised physical validation [PROPOSAL].
- Comparison table structure [PROPOSAL: no results].
- Proposed metrics: MAE/RMSE, interval coverage and width, fault-detection delay, false-alarm rate, constraint violations, titer/yield/productivity, resource use, fallback activations, control-computation latency [PROPOSAL].

## 11. Research gaps and future directions

- Gap register with chaining outcomes [TO COMPLETE in Phase 4].
- Transfer limits of simulated evidence [INTERPRETATION pending chaining].

## 12. Limitations of this review and conclusion

- Single-reviewer screening with sampled second pass.
- Closed-access sources limited to abstract level.
- Scoped review, not a systematic review.
- Simulated benchmark limitations.

## Figures and tables

- T1 literature evidence matrix (references/literature_matrix.csv).
- T2 model class comparison.
- T3 capability matrix (review/synthesis_notes.md).
- T4 proposed validation comparison (no results).
- F1 proposed architecture (Mermaid).
- F2 search and screening flow (only if log supports).
