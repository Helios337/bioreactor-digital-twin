---
name: scientific-writing
description: Writes clear technical prose for the bioreactor review paper. Separates reported evidence from interpretation and proposals, keeps terminology consistent, avoids hype, attaches a citation to every non-trivial claim, and never overstates novelty.
---

# Scientific Writing Skill

## Purpose

Produce manuscript text that a skeptical reviewer can audit claim by claim.

## Core rules

1. Every non-trivial scientific claim carries a citation key from references/references.bib.
2. Separate three layers explicitly: established evidence (cited), authors' interpretation (attributed), reviewer proposal (marked as proposal).
3. Terminology discipline. Never use interchangeably: input-distribution drift, sensor fault, prediction uncertainty, unsafe control. They are related but distinct.
4. The proposed architecture is described as proposed, reliability-oriented, and to be evaluated. The words validated, safe, and perfect are prohibited for it.
5. No novelty claim until citation chaining supports it. Phrase gaps as hypotheses until then.
6. Avoid hype words: revolutionary, breakthrough, groundbreaking, state-of-the-art unless a source uses them and the citation is attached.
7. Report only results that exist. Proposed metrics are listed as proposed future evaluation, never as findings.

## Style

- One full sentence per line in long Markdown files.
- Plain hyphens instead of em dashes.
- Define every abbreviation at first use.
- Keep mechanistic modelling, soft sensing, state estimation, fault diagnosis, drift, uncertainty calibration, MPC, and fallback supervision conceptually distinct.
- Distinguish penicillin-specific evidence from transferable methods from other bioprocesses.

## Manuscript structure

Follow the 12-section outline in review/paper_outline.md. Draft sections live in manuscript/draft.md with [EVIDENCE], [INTERPRETATION], and [PROPOSAL] markers until finalized.

## Outputs

- manuscript/draft.md
- figures/proposed_architecture.mmd with caption
- review/synthesis_notes.md
