#!/usr/bin/env python3
"""Build references/references.bib from verified API metadata only.

Sources: references/metadata_raw.json (Crossref + OpenAlex + PubMed responses
saved by tools/verify_references.py). B3 is overridden with PubMed/OpenAlex
verified fields because Crossref does not resolve its SICI-format DOI.
No field is hand-invented; overrides carry their verification source in a comment.
Diacritics are ASCII-folded for classic BibTeX compatibility.
"""
import html
import json
import os
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "references", "metadata_raw.json")
OUT = os.path.join(ROOT, "references", "references.bib")

KEYS = {
    "B1": "Bajpai1980", "B2": "Menezes1994", "B3": "Zangirolami1997",
    "B4": "Birol2002", "B5": "Montague1985", "B6": "Goldrick2015",
    "B7": "Goldrick2019", "B8": "Metcalfe2025", "B9": "Zheng2022",
    "B10": "Hermann2025", "B11": "Shukla2026", "B12": "Page2021",
    "S1": "Luo2024", "S3": "Rashedi2022", "S4": "Kwon2024",
    "S5": "Zhu2020", "S6": "Mondal2023", "S7": "Gil2026",
}

# B3 override: verified via PubMed efetch PMID 18642330 and OpenAlex
# (Crossref API does not resolve the SICI-format DOI).
B3_OVERRIDE = dict(
    title="Simulation of penicillin production in fed-batch cultivations using a morphologically structured model",
    authors=[("Zangirolami", "Teresa Cristina"), ("Johansen", "Claus Lindvald"),
             ("Nielsen", "Jens"), ("Jorgensen", "Sten Bay")],
    container="Biotechnology and Bioengineering", year=1997,
    volume="56", issue="6", page="593-604",
)


def fold(s):
    """ASCII-fold diacritics and normalize unicode hyphens for bibtex compatibility."""
    s = (s or "").replace("‐", "-").replace("‑", "-").replace("–", "-").replace("—", "-")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.encode("ascii", "ignore").decode("ascii")


def unescape(s):
    return html.unescape(s or "")


def fmt_authors(authors):
    return " and ".join("%s, %s" % (fold(fam), fold(giv)) for fam, giv in authors)


def bib_entry(key, c, doi):
    fields = []
    fields.append('  title = {%s}' % fold(unescape(c.get("title", ""))))
    fields.append('  author = {%s}' % fmt_authors(c.get("authors") or []))
    if c.get("container"):
        fields.append('  journal = {%s}' % fold(unescape(c["container"])))
    if c.get("year"):
        fields.append('  year = {%s}' % c["year"])
    if c.get("volume"):
        fields.append('  volume = {%s}' % c["volume"])
    if c.get("issue"):
        fields.append('  number = {%s}' % c["issue"])
    if c.get("page"):
        fields.append('  pages = {%s}' % c["page"])
    elif c.get("article_number"):
        fields.append('  pages = {%s}' % c["article_number"])
    fields.append('  doi = {%s}' % doi)
    fields.append('  url = {https://doi.org/%s}' % doi)
    return "@article{%s,\n%s\n}\n" % (key, ",\n".join(fields))


recs = {r["id"]: r for r in json.load(open(RAW))}
entries = []
for sid, key in KEYS.items():
    r = recs[sid]
    doi = r["doi"]
    if sid == "B3":
        c = dict(B3_OVERRIDE)
    else:
        c = r["crossref"] or {}
    entries.append(bib_entry(key, c, doi))

with open(OUT, "w") as f:
    f.write("% Verified reference bibliography.\n")
    f.write("% All fields sourced from Crossref/OpenAlex/PubMed API responses on 2026-10-29.\n")
    f.write("% B3 (Zangirolami 1997) fields verified via PubMed PMID 18642330 and OpenAlex.\n")
    f.write("% Diacritics ASCII-folded for classic BibTeX compatibility.\n")
    f.write("% Do not add unverified entries.\n\n")
    f.write("\n\n".join(entries))
print("wrote", OUT, "entries:", len(entries))
