---
name: literature-review
description: Runs reproducible scoping searches, applies eligibility rules, extracts evidence into a matrix, synthesizes across papers, and documents uncertainty and limitations. Never infers a research gap from absence of search results alone.
---

# Literature Review Skill

## Purpose

Produce an auditable, reproducible literature review for the fed-batch fermentation digital twin project.

## Workflow

1. Define exact search strings per research question before searching. Record them in review/search_protocol.md.
2. Run each string against the configured databases (OpenAlex, Crossref, PubMed, Semantic Scholar). Record hit counts and dates.
3. Deduplicate by DOI.
4. Screen titles and abstracts against the inclusion and exclusion criteria. Log every decision with a reason in review/screening_log.csv.
5. Screen full texts of survivors. Log access failures as excluded-access.
6. Extract evidence into references/literature_matrix.csv using the fixed column set.
7. Build the cross-paper capability matrix with dimensions: delayed sensing, sensor faults, drift, uncertainty, closed-loop control, fallback, validation type.
8. Synthesize per research question. Separate established evidence, authors' interpretation, and reviewer proposal.
9. Test every candidate gap by citation chaining (references and cited-by). Classify gaps as confirmed, partially covered, or refuted.

## Integrity rules

- Never infer a gap from absence of search results alone.
- Record access status per source: metadata-verified, abstract-read, full-text-read.
- Never fabricate a citation, result, number, equation or limitation.
- Distinguish what authors report from reviewer interpretation.
- If searches are incomplete, say so. Do not claim a systematic review unless the log supports it.

## Outputs

- review/search_protocol.md
- review/screening_log.csv
- references/literature_matrix.csv
- review/synthesis_notes.md
- review/gap_register.md (or section inside synthesis notes)
