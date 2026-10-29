# Search Protocol

Purpose: make the literature search reproducible and auditable. This protocol follows the brief's integrity rules. No systematic-review claim is made unless the log supports it.

## Review type

Scoped critical literature review with a reproducible search protocol. The review is narrative and evidence-matrix driven. PRISMA 2020 vocabulary is used only for the search and screening log structure.

## Databases and sources

1. OpenAlex API (metadata, abstracts, citation counts, cited-by chaining).
2. Crossref REST API (DOI metadata verification).
3. PubMed and PubMed Central (biomedical records, full text where open access).
4. Semantic Scholar API (optional, citation graph cross-check).
5. Publisher pages (access status and full text where permitted).
6. Citation chaining: reference lists and cited-by lists of all included studies.
7. IndPenSim dataset record (Mendeley Data V2) and the community simulator repository (implementation understanding only, not cited as authority).

## Search dates

- Initial search: 2026-10-29.
- Re-run before submission: required. Record the new date here.

## Date window

1980-01-01 to search date. Foundational mechanistic models (Bajpai and Reuss 1980) are in scope deliberately.

## Language

English only. Record any excluded non-English record in the screening log.

## Exact search strings

OpenAlex syntax: `search=<string>`. Crossref syntax: `query.bibliographic=<string>`. PubMed syntax: title/abstract field search as shown.

- S1 (soft sensing and state estimation): ("fed-batch" OR "fed batch") AND fermentation AND ("soft sensor" OR "soft-sensor" OR "state estimation")
- S2 (control): ("penicillin fermentation") AND ("model predictive control" OR MPC OR "reinforcement learning")
- S3 (digital twin): (bioprocess OR fermentation) AND ("digital twin") AND (monitoring OR control)
- S4 (faults): (fermentation OR bioprocess) AND ("fault detection" OR "fault diagnosis" OR "sensor fault")
- S5 (PAT and spectroscopy): ("process analytical technology" OR PAT) AND (Raman OR spectroscopy) AND fermentation
- S6 (drift and maintenance): (fermentation OR bioprocess) AND ("concept drift" OR "model drift" OR "model maintenance") AND ("machine learning" OR "soft sensor")
- S7 (golden batch and RCA): ("golden batch" OR "deviation analysis") AND (fermentation OR bioprocess) AND (anomaly OR "root cause")
- S8 (uncertainty): (bioprocess OR fermentation) AND ("uncertainty quantification" OR "conformal prediction") AND ("soft sensor" OR "state estimation")
- S9 (fallback and safety): (bioprocess OR fermentation) AND ("fault-tolerant control" OR "supervisory control" OR fallback) AND (MPC OR "model predictive")

RQ mapping: S1 and S5 serve RQ1. S1 and S3 serve RQ2. S4, S6, S8 serve RQ3. S2 and S9 serve RQ4. S3, S6 and S9 serve RQ5.

## Inclusion criteria

- Batch or fed-batch fermentation process.
- Addresses monitoring, state estimation, soft sensing, fault handling, drift, uncertainty, or control.
- English language.
- Verifiable metadata (DOI or PubMed ID resolvable).
- Full text or at minimum abstract accessible for evidence extraction.

## Exclusion criteria

- Continuous-only processes with no batch relevance.
- Pure metabolic engineering or strain development without a monitoring or control component.
- Records with unverifiable metadata.
- Duplicate records of the same study (keep the publisher version).

## Screening procedure

1. Run each string against OpenAlex and Crossref. Record hit counts in the counts table below.
2. Deduplicate by DOI.
3. Title and abstract screen against inclusion and exclusion criteria. Log every decision with a reason.
4. Full-text screen of survivors. Log access failures as excluded-access with the reason.
5. Citation chaining on included studies (references and cited-by). Add newly found candidates through the same pipeline.
6. Single-reviewer screening with a second pass on a 10 percent random sample for consistency. Record the sample result in the log.

## Search counts (to be filled as searches run)

| Query | Database | Date | Hits | After dedup | Included | Excluded | Notes |
|---|---|---|---|---|---|---|---|
| S1 | OpenAlex | 2026-10-29 | 1014 | 25 screened | 1 | 0 | pilot run 2026-10-29; top 25 returned; 1 already in corpus; candidates logged pending-screen |
| S1 | Crossref | 2026-10-29 | | | | | |
| S2 | OpenAlex | 2026-10-29 | | | | | |
| S2 | Crossref | 2026-10-29 | | | | | |
| S3 | OpenAlex | 2026-10-29 | | | | | |
| S4 | OpenAlex | 2026-10-29 | 2435 | 25 screened | 0 | 0 | pilot run 2026-10-29; top 25 returned; 0 already in corpus; candidates logged pending-screen |
| S5 | OpenAlex | 2026-10-29 | | | | | |
| S6 | OpenAlex | 2026-10-29 | 245 | 25 screened | 2 | 0 | pilot run 2026-10-29; top 25 returned; 2 already in corpus; candidates logged pending-screen |
| S7 | OpenAlex | 2026-10-29 | 37 | 25 screened | 1 | 0 | pilot run 2026-10-29; top 25 returned; 1 already in corpus; candidates logged pending-screen |
| S8 | OpenAlex | 2026-10-29 | | | | | |
| S9 | OpenAlex | 2026-10-29 | | | | | |

## Screening log

All decisions are recorded in review/screening_log.csv. Columns: record_id, source_db, query_id, title, authors, year, venue, doi, pmid, access_status, decision, decision_reason, screener, date.

## Honesty rules

- A gap is a hypothesis until citation chaining supports it. Absence of search results alone never establishes a gap.
- If the searches are not run to completion, the paper must not claim a systematic review. It is a scoped critical review with a reproducible protocol.
- Every excluded full text is logged with its reason.
