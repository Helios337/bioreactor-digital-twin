# Paper Outline

Working title: From Prediction to Trustworthy Closed-Loop Control: A Fault-Aware Digital-Twin Framework for Fed-Batch Fermentation.

Section plan follows the brief. Citation keys refer to references/references.bib.

## 1. Abstract

- Scoped critical review plus proposed architecture. No experimental claims.

## 2. Introduction and research questions

- Fed-batch fermentation monitoring and control problem: delayed assays, sensor faults, drift, living-cell variability.
- PAT and QbD context (B7).
- RQ1 to RQ5 from review/scope_and_questions.md.
- Monitoring emphasis: RQ3 carries the most weight.

## 3. Review protocol and search methodology

- Search protocol: databases, strings S1 to S9, date window, inclusion and exclusion criteria.
- Screening log and honest PRISMA-style flow.
- Verification method: Crossref, OpenAlex, PubMed, publisher records.
- Sources: B12 for reporting guidance.

## 4. Penicillin fermentation process and modelling foundations

- Mechanistic foundations: Bajpai and Reuss (B1), pilot-plant industrial media (B2), morphology-structured model (B3).
- Modular simulator lineage: B4 to B6 leading to IndPenSim (B7).
- Historical adaptive predictive control with EKF biomass estimation from CO2 (B5).

## 5. Sensors, PAT, soft sensors and state estimation

- Online versus off-line measurements and the 4-hour assay delay (B7).
- Raman spectroscopy and PLS calibration (B7).
- Soft sensing taxonomy and optimizers (S5).
- Deep and hybrid soft sensors: CNN-LSTM (B9), LSTM with MLOps lifecycle (B8).
- Observer-based estimation: PLS plus UKF (B10), transferable from L-phenylalanine.
- Small-data augmentation with VAEs (S4).

## 6. Hybrid digital twins and model maintenance under drift

- Hybrid modelling evidence: mass balance plus regression inside MPC (S3).
- Digital twin context and enablers (B11), scope-distinguished.
- Drift detection and model maintenance: PSI threshold with retraining alert (B8).
- ML landscape and deployment gaps (S6).

## 7. Faults, delayed observations and uncertainty calibration

- Fault scenarios in the benchmark: agitator trip, aeration, substrate, sensor errors (B7).
- Fault detection and anomaly detection evidence (B7, S1).
- Delayed off-line assays and their monitoring consequences (B7).
- Uncertainty calibration: hypothesis to verify by chaining. Candidate gap 1 and 3 live here.

## 8. Predictive control, operating constraints and fallback supervision

- MPC with hybrid models (S3); linear models can beat NNs for control.
- Historical adaptive predictive control (B5).
- Offline RL with behavior cloning and nightly fine-tuning (S7).
- Fallback and supervisory control: hypothesis to verify by chaining. Candidate gaps 2 and 4 live here.

## 9. Proposed reference architecture

- Mermaid diagram (figures/proposed_architecture.mmd) with components: sensing and data integrity, state estimation and soft sensors, hybrid digital twin, uncertainty and drift assessment, constrained MPC, safety supervisor and fallback, feedback to the process.
- Per-component rationale with citations; unproven elements marked as proposal.
- Monitoring emphasis mapping: golden-batch streaming monitor and contribution RCA (S1) integrated with soft sensor outputs.

## 10. Validation roadmap, benchmark design and metrics

- Staged roadmap: offline evidence review, software-in-the-loop, hardware-in-the-loop where appropriate, supervised physical validation.
- Comparison table: conventional control versus ML-MPC versus hybrid MPC versus reliability-aware MPC under matched nominal and disturbed scenarios.
- Proposed metrics: MAE/RMSE, prediction interval coverage and width, fault-detection delay, false-alarm rate, constraint-violation frequency and duration, titer/yield/productivity, resource use, fallback activations, control-computation latency.
- No results reported in this paper.

## 11. Research gaps and future directions

- Five candidate gaps from the brief, each classified confirmed, partially covered, or refuted after chaining.
- Transfer limits of simulated IndPenSim evidence to real processes and across scales (candidate gap 5).

## 12. Limitations of this review and conclusion

- Single-reviewer screening with sampled second pass.
- Access limitations for closed sources.
- Scoped review, not a systematic review unless the log supports it.
- Simulated benchmark limitations.

## Tables and figures

- T1: Literature evidence matrix (19 sources).
- T2: Mechanistic versus ML versus hybrid versus observer model comparison.
- T3: Capability matrix across delayed sensing, faults, drift, uncertainty, closed-loop control, fallback, validation type.
- T4: Proposed validation comparison table (no results).
- F1: Proposed reference architecture (Mermaid, editable).
- F2: PRISMA-style search and screening flow (only if the log supports it).
