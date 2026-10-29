# Source Register

Purpose: single source of truth for the 19 priority sources, their verification status, access status, and discrepancies.

Date searched: 2026-10-29.

Verification method: DOI metadata queried against the Crossref REST API. Citation counts and open-access status queried against OpenAlex. Biomedical records cross-checked against PubMed E-utilities (esummary/efetch). Seed PDFs (S1, S3, S4, S5, S6, S7 and B7) were read in full text locally.

Access status vocabulary: metadata-verified (API fields confirmed, full text not yet obtained), abstract-read, full-text-read.

## Verification summary

- 19 priority sources tracked (12 brief sources B1-B12, 7 seed sources S1-S7; B7 and S2 are the same paper).
- 18 unique DOIs. 17 resolved via Crossref. B3 resolved via PubMed and OpenAlex after Crossref failed on its SICI-format DOI.
- All 19 sources have verified title, venue, year, and DOI.
- 7 sources are full-text read (the seed corpus). 12 are metadata-verified with full text pending.

## Discrepancy and verification log

- D1: B3 Zangirolami 1997. Crossref API does not resolve the SICI-format DOI. Resolved independently via PubMed PMID 18642330 and OpenAlex. Pages 593-604 confirmed by both. The brief's DOI and PMID are correct.
- D2: B5 1985 IFAC paper. The brief listed no authors. Crossref gives Montague, Morris, Wright, Aynsley, Ward. Registered accordingly.
- D3: B1 Bajpai and Reuss. Brief states 1980. Crossref confirms 1980, volume 30, issue 1, pages 332-344. Some secondary sources cite 1981. Crossref record is treated as authoritative and the mismatch is noted here.
- D4: B11 Shukla et al. is dated 2026 in Crossref (Systems Microbiology and Biomanufacturing, volume 6, issue 3, article 56). It is a real ahead-of-print record, not a fabrication. Re-verify at submission time.
- D5: Automated title-similarity flags raised on B2, B4, B8, B9, B10, B12, S1, S4, S5, S6 were inspected and are false positives caused by hyphenation and tokenization. All titles were confirmed manually against API responses.
- D6: Crossref container titles arrived HTML-escaped (for example "Computers &amp; Chemical Engineering"). Normalized to plain text in the register and BibTeX.

## Per-source register

### B1 - Bajpai and Reuss 1980

- Citation: Bajpai, R. K., Reuss, M. (1980). A mechanistic model for penicillin production. Journal of Chemical Technology and Biotechnology, 30(1), 332-344.
- DOI: 10.1002/jctb.503300140
- Verified via: Crossref.
- Access: metadata-verified. OpenAlex OA status: closed. Cited by 190.
- Relevance: foundational mechanistic penicillin model. Defines what first-principles kinetics represent and where assumptions enter. Baseline for the hybrid digital twin component.
- Next action: obtain full text.

### B2 - Menezes et al. 1994

- Citation: Menezes, J. C., Alves, S. S., Lemos, J. M., de Azevedo, S. F. (1994). Mathematical modelling of industrial pilot-plant penicillin-G fed-batch fermentations. Journal of Chemical Technology and Biotechnology, 61(2), 123-138.
- DOI: 10.1002/jctb.280610207. PMID 7765415.
- Verified via: Crossref and PubMed (title, year, venue match).
- Access: metadata-verified. OpenAlex OA status: closed. Cited by 52.
- Relevance: evidence that model assumptions and parameters must be revised when moving between process settings and scales.
- Next action: obtain full text.

### B3 - Zangirolami et al. 1997

- Citation: Zangirolami, T. C., Johansen, C. L., Nielsen, J., Jorgensen, S. B. (1997). Simulation of penicillin production in fed-batch cultivations using a morphologically structured model. Biotechnology and Bioengineering, 56(6), 593-604.
- DOI: 10.1002/(SICI)1097-0290(19971220)56:6<593::AID-BIT1>3.0.CO;2-I. PMID 18642330.
- Verified via: PubMed efetch and OpenAlex (Crossref unresolved, see D1).
- Access: metadata-verified. OpenAlex OA status: closed. Cited by 37.
- Relevance: morphology-based structured model. Evidence for the cost and value of representing biological mechanism in digital twins.
- Next action: obtain full text.

### B4 - Birol, Undey and Cinar 2002

- Citation: Birol, G., Undey, C., Cinar, A. (2002). A modular simulation package for fed-batch fermentation: penicillin production. Computers and Chemical Engineering, 26(11), 1553-1565.
- DOI: 10.1016/S0098-1354(02)00127-8.
- Verified via: Crossref.
- Access: metadata-verified. OpenAlex OA status: closed. Cited by 658.
- Relevance: modular simulator extending to pH, temperature, aeration, agitation, feed and CO2 evolution. Discusses monitoring and fault diagnosis. Direct ancestor of the IndPenSim benchmark.
- Next action: obtain full text.

### B5 - Montague et al. 1985

- Citation: Montague, G. A., Morris, A. J., Wright, A. R., Aynsley, M., Ward, A. (1985). Parameter adaptive control of the fed-batch penicillin fermentation. IFAC Proceedings Volumes, 18(17), 69-74.
- DOI: 10.1016/S1474-6670(17)59895-X.
- Verified via: Crossref.
- Access: metadata-verified. OpenAlex OA status: closed. Cited by 11.
- Relevance: historical model-based adaptive control of penicillin with biomass estimation from CO2 via extended Kalman filter. Establishes that predictive control of penicillin fermentation is not new.
- Next action: obtain full text.

### B6 - Goldrick et al. 2015

- Citation: Goldrick, S., Stefan, A., Lovett, D., Montague, G., Lennox, B. (2015). The development of an industrial-scale fed-batch fermentation simulation. Journal of Biotechnology, 193, 70-82.
- DOI: 10.1016/j.jbiotec.2014.10.029. PMID 25449107.
- Verified via: Crossref and PubMed.
- Access: metadata-verified. OpenAlex OA status: green (repository manuscript likely available). Cited by 143.
- Relevance: the 100,000 L penicillin simulation validated against industrial data. Core reference for the IndPenSim benchmark.
- Next action: obtain full text from the green-OA repository copy.

### B7 / S2 - Goldrick et al. 2019

- Citation: Goldrick, S., Duran-Villalobos, C. A., Jankauskas, K., Lovett, D., Farid, S. S., Lennox, B. (2019). Modern day monitoring and control challenges outlined on an industrial-scale benchmark fermentation process. Computers and Chemical Engineering, 130, 106471.
- DOI: 10.1016/j.compchemeng.2019.05.037.
- Verified via: Crossref and full-text PDF in seed corpus.
- Access: full-text-read. OpenAlex OA status: hybrid. Cited by 78.
- Relevance: defines the IndPenSim benchmark, its variables, Raman simulation, fault scenarios, QbD/PAT demonstration and control objectives. Source of the 100-batch dataset description.
- Next action: none for access. Use as benchmark authority.

### B8 - Metcalfe et al. 2025

- Citation: Metcalfe, B., Acosta-Pavas, J. C., Robles-Rodriguez, C. E., Georgakilas, G. K., Dalamagas, T., Aceves-Lara, C. A., et al. (2025). Towards a machine learning operations (MLOps) soft sensor for real-time predictions in industrial-scale fed-batch fermentation. Computers and Chemical Engineering, 194, 108991.
- DOI: 10.1016/j.compchemeng.2024.108991.
- Verified via: Crossref.
- Access: metadata-verified. OpenAlex OA status: bronze (free to read on publisher site). Cited by 40.
- Relevance: LSTM penicillin prediction on IndPenSim with an 8-hour forecast horizon plus concept-drift monitoring and model-maintenance workflow. Closest prior work on reliability over changing process data.
- Next action: obtain full text (bronze OA).

### B9 - Zheng et al. 2022

- Citation: Zheng, J., Ma, L., Wu, Y., Ye, L., Shen, F. (2022). Nonlinear dynamic soft sensor development with a supervised hybrid CNN-LSTM network for industrial processes. ACS Omega, 7(19), 16653-16664.
- DOI: 10.1021/acsomega.2c01108. PMID 35601320.
- Verified via: Crossref and PubMed.
- Access: metadata-verified. OpenAlex OA status: gold (PMC full text available). Cited by 44.
- Relevance: hybrid CNN-LSTM soft sensor including penicillin fermentation. Example of predictive soft sensing only, not closed-loop safe control.
- Next action: obtain full text from PMC.

### B10 - Hermann and Kremling 2025

- Citation: Hermann, L., Kremling, A. (2025). A hybrid soft sensor approach combining partial least-squares regression and an unscented Kalman filter for state estimation in bioprocesses. Bioengineering, 12(6), 654.
- DOI: 10.3390/bioengineering12060654.
- Verified via: Crossref.
- Access: metadata-verified. OpenAlex OA status: gold (PMC full text available). Cited by 10.
- Relevance: data-driven estimate fused with a state estimator. Transferable observer evidence from an L-phenylalanine process, not penicillin.
- Next action: obtain full text from PMC.

### B11 - Shukla, Nagpal and Vyas 2026

- Citation: Shukla, K., Nagpal, S., Vyas, A. (2026). Opportunities of digital twin in controlling and monitoring microbial processes in food fermentation. Systems Microbiology and Biomanufacturing, 6(3), 56.
- DOI: 10.1007/s43393-026-00454-8.
- Verified via: Crossref.
- Access: metadata-verified. OpenAlex OA status: closed. Cited by 5.
- Relevance: recent adjacent review of digital twins, AI, sensing and control in microbial fermentation. Scope must be distinguished from penicillin-focused work.
- Next action: obtain full text. Re-verify metadata at submission (ahead-of-print record).

### B12 - Page et al. 2021 (PRISMA 2020)

- Citation: Page, M. J., McKenzie, J. E., Bossuyt, P. M., Boutron, I., Hoffmann, T. C., Mulrow, C. D., et al. (2021). The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. PLOS Medicine, 18(3), e1003583.
- DOI: 10.1371/journal.pmed.1003583.
- Verified via: Crossref.
- Access: metadata-verified. OpenAlex OA status: gold. Cited by 5138.
- Relevance: reporting guideline for the review methodology. Not a bioprocess evidence source.
- Next action: obtain full text (open access).

### S1 - Luo et al. 2024

- Citation: Luo, D., He, M., Darko, J., Ly Seymour, F., Maturana, F. (2024). The golden batch-driven root cause analysis for anomalies in bioreactor fermentation process. Frontiers in Manufacturing Technology, 4, 1392038.
- DOI: 10.3389/fmtec.2024.1392038.
- Verified via: Crossref and full-text PDF in seed corpus.
- Access: full-text-read. OpenAlex OA status: gold. Cited by 1.
- Relevance: offline golden-batch deviation and contribution-based root cause analysis on IndPenSim. Provides the 33 below-target versus 67 healthy batch labels and the RCA method to extend to streaming.
- Next action: none for access.

### S3 - Rashedi et al. 2022

- Citation: Rashedi, M., Khodabandehlou, H., Demers, M., Wang, T., Garvin, C. (2022). Model predictive controller design for bioprocesses based on machine learning algorithms. IFAC-PapersOnLine, 55(7), 45-50.
- DOI: 10.1016/j.ifacol.2022.07.420.
- Verified via: Crossref and full-text PDF in seed corpus.
- Access: full-text-read. OpenAlex OA status: diamond. Cited by 21.
- Relevance: hybrid mass-balance plus regression/NN model inside MPC for fed-batch feed optimization. Evidence that a linear model can outperform a neural network for control.
- Next action: none for access.

### S4 - Kwon et al. 2024

- Citation: Kwon, H. J., Shiu, J. H., Yamakawa, C. K., Rivera, E. C. (2024). Enhancing fermentation process monitoring through data-driven modeling and synthetic time series generation. Bioengineering, 11(8), 803.
- DOI: 10.3390/bioengineering11080803.
- Verified via: Crossref and full-text PDF in seed corpus.
- Access: full-text-read. OpenAlex OA status: gold. Cited by 22.
- Relevance: convolutional VAE synthetic augmentation improves soft-sensor R-squared by 34 percent and cuts variability by 82 percent on ethanol fermentation. Portable small-data remedy.
- Next action: none for access.

### S5 - Zhu et al. 2020

- Citation: Zhu, X., Rehman, K. U., Wang, B., Shahzad, M. (2020). Modern soft-sensing modeling methods for fermentation processes. Sensors, 20(6), 1771.
- DOI: 10.3390/s20061771.
- Verified via: Crossref and full-text PDF in seed corpus.
- Access: full-text-read. OpenAlex OA status: gold. Cited by 140.
- Relevance: taxonomy of soft-sensing methods and optimizers. Notes the simulation-only evidence base and few industrial deployments.
- Next action: none for access.

### S6 - Mondal et al. 2023

- Citation: Mondal, P. P., Galodha, A., Verma, V. K., Singh, V., Show, P. L., Awasthi, M. K., Lall, B., Anees, S., Pollmann, K., Jain, R. (2023). Review on machine learning-based bioprocess optimization, monitoring, and control systems. Bioresource Technology, 370, 128523.
- DOI: 10.1016/j.biortech.2022.128523.
- Verified via: Crossref and full-text PDF in seed corpus.
- Access: full-text-read. OpenAlex OA status: closed. Cited by 177.
- Relevance: ML landscape across pharmaceuticals, biofuels and wastewater. Identifies hybrid models, IoT integration and the industrial deployment gap as needs.
- Next action: none for access.

### S7 - Gil et al. 2026

- Citation: Gil, J. D., Del Rio Chanona, E. A., Guzman, J. L., Berenguel, M. (2026). Reinforcement learning meets bioprocess control through behavior cloning: Real-world deployment in an industrial photobioreactor. Engineering Applications of Artificial Intelligence, 164, 113326.
- DOI: 10.1016/j.engappai.2025.113326.
- Verified via: Crossref and full-text PDF in seed corpus.
- Access: full-text-read. OpenAlex OA status: hybrid. Cited by 12.
- Relevance: offline DDPG with behavior cloning from PID trajectories, POMDP formulation, nightly fine-tuning. First industrial RL validation in a bioprocess. Control-side evidence for the adaptive layer.
- Next action: none for access.

## Access acquisition plan

1. B9, B10, B12: open access (gold). Download from publisher or PMC.
2. B8: bronze OA on ScienceDirect. Download.
3. B6: green OA. Check the University of Manchester repository.
4. B1, B2, B3, B4, B5, B11: closed. Use institutional access or interlibrary loan.
5. Record access status changes in this register as they happen.

## IndPenSim dataset record (added 2026-10-29, Track B triggered)

- Name: 100 batches IndPenSim (Mendeley Data, Version 2).
- DOI: 10.17632/pdnjz7zz5x.2. Page: https://data.mendeley.com/datasets/pdnjz7zz5x/2
- Licence: CC BY 4.0 (verified on the dataset page, 2026-10-29).
- File: 100_Batches_IndPenSim.zip, 503.8 MB, content id e7007dff-4061-494f-a9f5-16c20f457d1d.
- Download route: public files API, no authentication required.
- Contents (per the authors' notebook): Mendeley_data/100_Batches_IndPenSim_V3.csv (main time-series, about 113,918 rows and about 212 columns including Raman channels) and Mendeley_data/100_Batches_IndPenSim_Statistics.csv (per-batch penicillin yield totals plus Fault ref 0/1 labels).
- Batch groups: 1-30 recipe-driven, 31-60 operator controlled, 61-90 APC with Raman, 91-100 faults resulting in process deviations.
- Caveat: simulated data generated by IndPenSim, not plant measurements (per B7).
- Local location: data/IndPenSim/ (gitignored, not committed). Both V2 archives verified identical (SHA256 bc434c6cf96444fee3c915d434ac84e2a9c6492be4daebcfa4aed9cdff181f00).
- Status: downloaded and processed 2026-10-29. Processed cache: data/processed/process_named.parquet. Canonical inspector: scripts/1_inspect_data.py.
