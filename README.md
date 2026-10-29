# Bioreactor Digital Twin Literature Review and Reference Architecture

Working title: From Prediction to Trustworthy Closed-Loop Control: A Fault-Aware Digital-Twin Framework for Fed-Batch Fermentation.

Primary question: What sensing, state-estimation, hybrid-modelling, uncertainty-management, fault-handling and control methods are needed to develop a reliable digital twin for fed-batch fermentation when observations are delayed, sensors fail, and process conditions change?

## Scope

Track A (active): critical literature review plus a proposed reliability-oriented reference architecture. This is the research paper deliverable.

Track B (gated): an end-to-end empirical monitoring prototype on the IndPenSim benchmark. It starts only after an explicit trigger following gap verification. No model training and no experimental performance claims exist in this repository until then.

## Status

- 19 priority sources tracked (18 unique; B7 and S2 are the same paper).
- Metadata verified for all 19 via Crossref, OpenAlex and PubMed.
- Abstracts read for 17 of 18 unique sources.
- Full text read for 7 sources (the seed corpus).
- Search protocol defined and piloted. Screening of database searches in progress.
- Architecture, synthesis and manuscript are scaffolds pending Phase 4 to 7 evidence work.

## Repository structure

- references/: source_register.md, references.bib, literature_matrix.csv, metadata_raw.json, abstracts.json.
- review/: scope_and_questions.md, search_protocol.md, screening_log.csv, synthesis_notes.md, paper_outline.md.
- manuscript/: draft.md.
- figures/: proposed_architecture.mmd.
- tools/: verify_references.py, build_bib.py, build_matrix.py.
- .opencode/skills/: literature-review, citation-verification, scientific-writing, bioprocess-control-review.

## Quickstart

Verify reference metadata and rebuild artifacts:

```bash
python3 tools/verify_references.py   # queries Crossref, OpenAlex, PubMed; writes references/metadata_raw.json
python3 tools/build_bib.py           # writes references/references.bib from verified fields only
python3 tools/build_matrix.py        # writes references/literature_matrix.csv
```

## Governing documents

- Research brief: /Users/adi/Downloads/Bioreactor Research Brief.md.
- Approved plan: /Users/adi/.opencode/plan/bioreactor-fedbatch-monitoring-plan.md.
- Seed corpus (7 PDFs, full text read): /Users/adi/Documents/RP Project.

## Data note

The IndPenSim dataset (Mendeley Data V2, about 2.5 GB) is deliberately not downloaded during the review phase. The community GitHub implementation is used for understanding only and is never cited as authority.

## Integrity summary

No fabricated citations, results, numbers, equations, data-availability claims or limitations. Candidate gaps are hypotheses until citation chaining confirms them. Simulated benchmark data is never presented as plant data. The architecture is proposed and to be evaluated, never described as validated or safe.
