---
name: bioprocess-control-review
description: Keeps mechanistic modelling, soft sensing, state estimation, fault diagnosis, drift, uncertainty calibration, MPC, and fallback/safety supervision conceptually distinct when reviewing bioprocess papers. Distinguishes penicillin-specific evidence from transferable methods in other bioprocesses.
---

# Bioprocess Control Review Skill

## Purpose

Prevent concept blending when extracting evidence from bioprocess monitoring and control papers.

## Concept boundaries

When reading a paper, classify each contribution into exactly one bucket before synthesizing:

- Mechanistic modelling: first-principles kinetics, structured or unstructured models, parameter identification.
- Soft sensing: inference of hard-to-measure variables from auxiliary measurements.
- State estimation: observer-based correction of model states (Kalman filters, UKF, EKF).
- Fault diagnosis: detection, isolation, and identification of sensor or process faults.
- Drift: change in input distribution or process behaviour over time or across campaigns.
- Uncertainty calibration: prediction intervals, conformal methods, ensembles, Bayesian outputs.
- Predictive control: MPC and variants, constraints, objectives, feasibility.
- Fallback supervision: switching or gating logic when sensor health or model reliability degrades.
- Validation: offline accuracy, simulation, software-in-the-loop, hardware-in-the-loop, supervised physical deployment.

## Transferability test

For every paper ask:

1. Is the organism and process penicillin fed-batch, or another fermentation, or another process class?
2. Is the data plant-measured, pilot-plant, or simulated (for example IndPenSim)?
3. Does the method need online states that the benchmark does not provide?
4. Is the timescale compatible with batch monitoring (minutes) or control (seconds to hours)?

## Classification outputs

- Capability matrix row scores for one paper per dimension in review/synthesis_notes.md.
- Explicit transferability note in the relevance column of references/literature_matrix.csv.
- A paper is never cited as penicillin-specific evidence unless the process and dataset are penicillin.
