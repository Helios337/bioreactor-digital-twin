#!/usr/bin/env python3
"""Verify reference metadata against Crossref, OpenAlex and PubMed.

Research-integrity rule: every recorded field comes from the API response.
Expected values from the brief or the seed PDFs are used only to flag
mismatches, never to fill gaps. Discrepancies are reported, not resolved
by guessing.
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "references", "metadata_raw.json")

UA = {"User-Agent": "bioreactor-fedbatch-review/1.0 (mailto:research@example.org)"}

SOURCES = [
    dict(id="B1", group="A. Foundational mechanistic models",
         label="Bajpai & Reuss, mechanistic model for penicillin production",
         doi="10.1002/jctb.503300140", exp_year=1980, exp_first="Bajpai",
         exp_title=["mechanistic", "model", "penicillin"]),
    dict(id="B2", group="A. Foundational mechanistic models",
         label="Menezes et al., pilot-plant penicillin-G fed-batch modelling",
         doi="10.1002/jctb.280610207", exp_year=1994, exp_first="Menezes",
         exp_title=["mathematical", "modelling", "penicillin"], pmid="7765415"),
    dict(id="B3", group="A. Foundational mechanistic models",
         label="Zangirolami et al., morphologically structured model",
         doi="10.1002/(SICI)1097-0290(19971220)56:6%3C593::AID-BIT1%3E3.0.CO;2-I",
         exp_year=1997, exp_first="Zangirolami",
         exp_title=["simulation", "penicillin", "morphologically"], pmid="18642330"),
    dict(id="B4", group="A. Foundational mechanistic models",
         label="Birol, Undey & Cinar, modular simulation package",
         doi="10.1016/S0098-1354(02)00127-8", exp_year=2002, exp_first="Birol",
         exp_title=["modular", "simulation", "penicillin"]),
    dict(id="B5", group="A. Foundational mechanistic models",
         label="Parameter adaptive control of fed-batch penicillin fermentation (1985 IFAC)",
         doi="10.1016/S1474-6670(17)59895-X", exp_year=1985, exp_first=None,
         exp_title=["parameter", "adaptive", "control", "penicillin"]),
    dict(id="B6", group="A. Foundational mechanistic models",
         label="Goldrick et al. 2015, industrial-scale fed-batch fermentation simulation",
         doi="10.1016/j.jbiotec.2014.10.029", exp_year=2015, exp_first="Goldrick",
         exp_title=["industrial-scale", "fed-batch", "fermentation"], pmid="25449107"),
    dict(id="B7", group="B. Monitoring, faults, benchmark data",
         label="Goldrick et al. 2019, IndPenSim benchmark",
         doi="10.1016/j.compchemeng.2019.05.037", exp_year=2019, exp_first="Goldrick",
         exp_title=["modern day monitoring", "benchmark", "fermentation"]),
    dict(id="B8", group="B. Monitoring, faults, benchmark data",
         label="Metcalfe et al. 2025, MLOps soft sensor",
         doi="10.1016/j.compchemeng.2024.108991", exp_year=2025, exp_first="Metcalfe",
         exp_title=["soft sensor", "fed-batch", "fermentation"]),
    dict(id="B9", group="B. Monitoring, faults, benchmark data",
         label="Zheng et al. 2022, supervised hybrid CNN-LSTM soft sensor",
         doi="10.1021/acsomega.2c01108", exp_year=2022, exp_first="Zheng",
         exp_title=["cnn-lstm", "soft sensor"], pmid="35601320"),
    dict(id="B10", group="C. Transferable state-estimation and digital-twin methods",
         label="Hermann & Kremling 2025, PLS plus unscented Kalman filter",
         doi="10.3390/bioengineering12060654", exp_year=2025, exp_first="Hermann",
         exp_title=["partial least", "unscented kalman", "bioprocesses"]),
    dict(id="B11", group="C. Transferable state-estimation and digital-twin methods",
         label="Shukla, Nagpal & Vyas 2026, digital twin in food fermentation",
         doi="10.1007/s43393-026-00454-8", exp_year=2026, exp_first="Shukla",
         exp_title=["digital twin", "fermentation"]),
    dict(id="B12", group="C. Transferable state-estimation and digital-twin methods",
         label="PRISMA 2020 statement",
         doi="10.1371/journal.pmed.1003583", exp_year=2021, exp_first="Page",
         exp_title=["prisma", "2020"]),
    dict(id="S1", group="Seed corpus (full text in hand)",
         label="Luo et al. 2024, golden batch root cause analysis",
         doi="10.3389/fmtec.2024.1392038", exp_year=2024, exp_first="Luo",
         exp_title=["golden batch", "root cause", "bioreactor"]),
    dict(id="S3", group="Seed corpus (full text in hand)",
         label="Rashedi et al. 2022, MPC with machine learning",
         doi="10.1016/j.ifacol.2022.07.420", exp_year=2022, exp_first="Rashedi",
         exp_title=["model predictive controller", "machine learning"]),
    dict(id="S4", group="Seed corpus (full text in hand)",
         label="Kwon et al. 2024, VAE synthetic time series for soft sensors",
         doi="10.3390/bioengineering11080803", exp_year=2024, exp_first="Kwon",
         exp_title=["fermentation", "synthetic", "time series"]),
    dict(id="S5", group="Seed corpus (full text in hand)",
         label="Zhu et al. 2020, soft-sensing methods review",
         doi="10.3390/s20061771", exp_year=2020, exp_first="Zhu",
         exp_title=["soft-sensing", "fermentation"]),
    dict(id="S6", group="Seed corpus (full text in hand)",
         label="Mondal et al. 2023, ML bioprocess review",
         doi="10.1016/j.biortech.2022.128523", exp_year=2023, exp_first="Mondal",
         exp_title=["machine learning", "bioprocess"]),
    dict(id="S7", group="Seed corpus (full text in hand)",
         label="Gil et al. 2026, RL behavior cloning in photobioreactor",
         doi="10.1016/j.engappai.2025.113326", exp_year=2026, exp_first="Gil",
         exp_title=["reinforcement learning", "behavior cloning", "photobioreactor"]),
]


def get(url, timeout=25, retries=2):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if attempt == retries:
                return {"_error": str(e)}
            time.sleep(1.5)


def norm_title(t):
    return re.sub(r"[^a-z0-9 ]", "", (t or "").lower()).split()


def title_similarity(a, b):
    ta, tb = set(norm_title(a)), set(norm_title(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def crossref_fields(m):
    authors = m.get("author") or []
    first = authors[0].get("family") if authors else None
    year = None
    for key in ("issued", "published-print", "published-online"):
        dp = (m.get(key) or {}).get("date-parts")
        if dp and dp[0]:
            year = dp[0][0]
            break
    return dict(
        title=(m.get("title") or [""])[0],
        container=(m.get("container-title") or [""])[0],
        year=year,
        first_author=first,
        authors=[(a.get("family", ""), a.get("given", "")) for a in authors],
        volume=m.get("volume"), issue=m.get("issue"),
        page=m.get("page"), article_number=m.get("article-number"),
        publisher=m.get("publisher"), type=m.get("type"),
        reference_count=m.get("reference-count"),
        doi=m.get("DOI"), url=m.get("URL"),
    )


results = []
for s in SOURCES:
    rec = dict(id=s["id"], group=s["group"], label=s["label"], doi=s["doi"],
               expected_year=s["exp_year"], expected_first=s["exp_first"])
    enc = urllib.parse.quote(s["doi"], safe="")
    cr = get("https://api.crossref.org/works/" + enc)
    if "message" in cr and cr.get("status") == "ok":
        rec["crossref"] = crossref_fields(cr["message"])
        rec["crossref_ok"] = True
    else:
        rec["crossref_ok"] = False
        rec["crossref_error"] = str(cr.get("_error") or cr.get("message"))
    oa = get("https://api.openalex.org/works/doi:" + enc)
    if "id" in oa:
        rec["openalex"] = dict(
            cited_by=oa.get("cited_by_count"),
            oa_status=(oa.get("open_access") or {}).get("oa_status"),
            type=oa.get("type"),
            year=(oa.get("publication_year")))
    if s.get("pmid"):
        pm = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                 "?db=pubmed&id=" + s["pmid"] + "&retmode=json")
        try:
            p = pm["result"][s["pmid"]]
            rec["pubmed"] = dict(title=p.get("title"), year=p.get("pubdate"),
                                 source=p.get("source"))
        except Exception:
            rec["pubmed"] = {"_error": "lookup failed"}
        time.sleep(0.4)
    # verdict
    c = rec.get("crossref", {})
    flags = []
    if not rec.get("crossref_ok"):
        flags.append("CROSSREF-MISS")
    else:
        if c.get("year") != s["exp_year"]:
            flags.append("YEAR:%s!=%s" % (c.get("year"), s["exp_year"]))
        if s["exp_first"] and (c.get("first_author") or "").lower() != s["exp_first"].lower():
            flags.append("FIRST-AUTHOR:%s!=%s" % (c.get("first_author"), s["exp_first"]))
        if s["exp_title"]:
            sim = title_similarity(" ".join(s["exp_title"]), c.get("title", ""))
            if sim < 0.35:
                flags.append("TITLE-LOW-MATCH:%.2f" % sim)
    rec["flags"] = flags
    results.append(rec)
    time.sleep(0.3)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(results, f, indent=1)

print("%-4s %-9s %-6s %-28s %-38s %s" % ("id", "xref", "year", "first author", "container", "flags"))
for r in results:
    c = r.get("crossref") or {}
    print("%-4s %-9s %-6s %-28s %-38s %s" % (
        r["id"], "ok" if r.get("crossref_ok") else "MISS",
        c.get("year"), (c.get("first_author") or "-")[:28],
        (c.get("container") or "-")[:38], ";".join(r["flags"]) or "-"))
print("\nWrote", OUT)
