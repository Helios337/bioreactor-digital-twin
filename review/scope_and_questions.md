# Scope and Research Questions

Working title: From Prediction to Trustworthy Closed-Loop Control: A Fault-Aware Digital-Twin Framework for Fed-Batch Fermentation.

Primary question: What sensing, state-estimation, hybrid-modelling, uncertainty-management, fault-handling and control methods are needed to develop a reliable digital twin for fed-batch fermentation when observations are delayed, sensors fail, and process conditions change?

## Research questions

- RQ1: Which measurements and soft sensors are used to estimate critical process states in fed-batch fermentation?
- RQ2: When are mechanistic, data-driven, hybrid and observer-based models appropriate?
- RQ3: How do existing systems address measurement latency, sensor faults, distribution shift and predictive uncertainty?
- RQ4: How are model predictions linked to constrained MPC and safe fallback decisions?
- RQ5: What validation evidence is needed to demonstrate reliability beyond offline prediction accuracy?

Monitoring emphasis: RQ3 carries the most weight because the project interest is real-time monitoring. The capability matrix scores every included study on delayed sensing, sensor faults, drift, uncertainty, closed-loop control, fallback and validation type.

## In scope

- Batch and fed-batch fermentation, with penicillin as the benchmark process.
- Soft sensing and state estimation of critical quality attributes and critical process parameters.
- Measurement latency, off-line assay delay, sensor faults, sensor drift, and model or concept drift.
- Predictive uncertainty and its use in monitoring decisions.
- Fault detection, anomaly detection, deviation analysis and root cause analysis.
- Control linkage: constrained MPC, learning-based control, supervisory fallback.
- Validation evidence types: offline accuracy, simulation, software-in-the-loop, hardware-in-the-loop, supervised physical deployment.

## Out of scope

- Continuous-only bioprocessing without batch relevance.
- Strain engineering and upstream metabolic design.
- Downstream purification and formulation.
- Bioreactor hardware and sensor device design.
- Clinical and regulatory submission process detail beyond PAT and QbD context.

## Terminology discipline

The following are related but distinct and are never used interchangeably in this project:

- Input-distribution drift: the statistical distribution of process inputs changes over time.
- Sensor fault: a hardware or calibration failure producing wrong or missing measurements.
- Prediction uncertainty: the model's quantified confidence in its own output.
- Unsafe control: a control action that violates constraints or drives the process out of a safe envelope.

## Evidence separation rule

For every included study the review records three layers and never blends them:

1. Established evidence: what the authors explicitly report, with citation.
2. Authors' interpretation: the authors' own framing of their results.
3. Reviewer proposal: this project's interpretation or proposed extension, marked as such.

## Candidate gaps (hypotheses to verify, not facts)

From the brief section 6, to be tested by citation chaining in Phase 4:

1. Joint handling of delayed observations, sensor faults and model or prediction uncertainty in fed-batch fermentation.
2. Whether calibrated uncertainty actually changes or constrains MPC decisions, rather than being reported only as a prediction metric.
3. Explicit fallback or supervisory control when sensor health or model reliability is poor, with documented validation of fallback behaviour.
4. Reproducible comparison of conventional control, conventional ML-MPC, hybrid MPC and reliability-aware MPC under matched nominal and disturbed scenarios.
5. The limits of transferring results from simulated IndPenSim trajectories to real processes and across scales.

## Materials

- Governing brief: /Users/adi/Downloads/Bioreactor Research Brief.md.
- Seed corpus (7 PDFs, full text read): /Users/adi/Documents/RP Project.
- IndPenSim dataset (Mendeley Data V2): not downloaded in the review phase. Download only if the gated empirical phase is triggered.
- IndPenSim community repository: implementation understanding only, never cited as authority.
