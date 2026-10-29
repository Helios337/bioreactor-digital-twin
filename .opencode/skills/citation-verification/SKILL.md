---
name: citation-verification
description: Verifies titles, authors, venue, year, DOI and access status against Crossref, OpenAlex, PubMed and publisher records before any source is cited. Flags unverified sources instead of silently filling missing data.
---

# Citation Verification Skill

## Purpose

Ensure every cited source has verified metadata and a known access status.

## Workflow

1. For each source, query the DOI against Crossref. Record title, authors, venue, year, volume, issue, pages.
2. Cross-check against OpenAlex (citation count, OA status) and PubMed where a PMID exists.
3. For SICI-format or special-character DOIs that Crossref cannot resolve, use PubMed and OpenAlex as independent resolvers and record that path.
4. Compare returned fields against the expected citation. Log every mismatch in the discrepancy log. Never resolve a mismatch by guessing.
5. Set access status: metadata-verified, abstract-read, or full-text-read.
6. Generate BibTeX only from verified API fields. ASCII-fold diacritics for classic BibTeX compatibility.

## Tools

- tools/verify_references.py queries Crossref, OpenAlex and PubMed and saves references/metadata_raw.json.
- tools/build_bib.py generates references/references.bib from verified fields only.

## Integrity rules

- A title or abstract page is not proof of full-text access. Track the difference.
- Unverifiable sources are excluded and recorded, not cited with guessed fields.
- Ahead-of-print or future-dated records are flagged for re-verification at submission.
- Publisher pages, PubMed and institutional repositories outrank secondary aggregators.

## Outputs

- references/source_register.md with per-source verification and access status.
- references/references.bib with verified entries only.
- Discrepancy log entries for every resolved or unresolved mismatch.
