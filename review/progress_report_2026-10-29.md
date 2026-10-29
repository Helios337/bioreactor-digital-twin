# Progress Report 1

Date: 2026-10-29. Author: OpenCode build agent. Phase: 0 to 3 partial (scaffolding, verification, protocol, matrix seeded).

## Verified references

- 19 priority sources tracked; 18 unique because B7 and S2 are the same paper (Goldrick 2019).
- Metadata verified for 19 of 19. Crossref resolved 17 DOIs. B3 (Zangirolami 1997) resolved via PubMed PMID 18642330 and OpenAlex after Crossref failed on its SICI-format DOI.
- Abstracts read for 17 of 18 unique sources: OpenAlex supplied 12, PubMed supplied B2, B3, B6, B9, publisher pages supplied B4, B5, B8, B11.
- Full text read for 7 sources: the seed corpus S1, S3, S4, S5, S6, S7 and B7.
- Bibliography: 18 entries in references/references.bib, ASCII-clean, generated only from verified API fields by tools/build_bib.py.

## Unresolved metadata and access issues

- B11 Shukla 2026 is an ahead-of-print record. Metadata verified in Crossref and on the journal site. Re-verify at submission time.
- Full text pending, closed access: B1, B2, B3, B4, B5, B11. Full text pending, open access available: B6 (green), B8 (bronze), B9 (gold), B10 (gold), B12 (gold).
- B9 and B10 matrix cells remain abstract-level with pending-full-text markers.
- 94 pilot search candidates carry search-hit-unverified status and pending-screen decisions.
- S7 pilot query returned HTTP 504 on first attempt and succeeded on retry. Protocol robustness note: retry logic is required for complex OpenAlex queries.
- S6 Mondal has no OpenAlex abstract but is full-text read from the seed PDF. Its matrix evidence level full-text is correct.

## Project files created

- README.md, AGENTS.md, .gitignore
- references/: source_register.md, references.bib, literature_matrix.csv, metadata_raw.json, abstracts.json
- review/: scope_and_questions.md, search_protocol.md, screening_log.csv (112 rows), synthesis_notes.md, paper_outline.md, pilot_search.json
- manuscript/: draft.md (12-section scaffold with evidence-layer markers)
- figures/: proposed_architecture.mmd (draft, marked proposed)
- tools/: verify_references.py, build_bib.py, build_matrix.py
- .opencode/skills/: literature-review, citation-verification, scientific-writing, bioprocess-control-review
- Git: 7 atomic commits on main.

## MCP status

- context7 and exa registered via opencode mcp add (written to /Users/adi/opencode.json) and available in the tool catalog.
- Semantic Scholar MCP deferred per the brief's inspect-first rule. uvx is installed at /Users/adi/.local/bin/uvx if the user approves installation after repo inspection.

## Next research decisions needed

1. Execute the remaining pilot-to-full searches S2, S3, S5, S8, S9 and screen the 94 pending-screen candidates.
2. Download open-access full texts first (B9, B10, B12 gold; B8 bronze; B6 green), then pursue closed access (B1 to B5, B11) via institutional routes.
3. Run citation chaining on the five gap hypotheses. Leads already identified: STAMM soft sensor maintenance framework (2026), TwinOps biomanufacturing (2021), Raman plus MSPC fault detection (2025), Cheng 2024 semi-supervised VAE soft sensor, Appl 2020 bioprocess digital twins, Hassan 2024 VR bioreactor twin, Petsagkourakis 2020 RL bioprocess, Espinel-Rios 2025, Sass 2022, Monteiro 2026.
4. Complete capability matrix unknowns for B9 and B10 after full-text access.
5. Decide venue formatting: journal versus conference, LaTeX versus Markdown. The user confirmed a research paper but not the venue specifics.
6. Track B trigger decision after Gate G1 gap verification. The IndPenSim dataset download stays deferred until then.
