#!/usr/bin/env python3
"""Convert report/project_report.md to a paginated PDF.

Requires: pip install markdown weasyprint, and on macOS:
  brew install glib pango gdk-pixbuf
  DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib python3 tools/report_to_pdf.py

The PDF is a rendering of the Markdown report. The Markdown file remains
the source of truth. No content is added or removed by conversion.
"""
import os
import re

import markdown
from weasyprint import HTML

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(ROOT, "report", "project_report.md")
PDF = os.path.join(ROOT, "report", "project_report.pdf")

CSS = """
@page {
  size: A4;
  margin: 2.0cm 1.8cm 2.2cm 1.8cm;
  @top-center { content: "Project Report: Fault-Aware Digital Twin for Fed-Batch Fermentation"; font-size: 7.5pt; color: #666; }
  @bottom-right { content: "Page " counter(page) " of " counter(pages); font-size: 8pt; color: #666; }
  @bottom-left { content: "Research in progress - no experimental results claimed"; font-size: 7.5pt; color: #999; }
}
@page :first { @top-center { content: none; } }
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 21pt; color: #12365c; margin-bottom: 4pt; }
h2 { font-size: 14.5pt; color: #1f3a5f; border-bottom: 1pt solid #2c5f8a; padding-bottom: 2pt; margin-top: 16pt; margin-bottom: 6pt; }
h3 { font-size: 11.5pt; color: #2c5f8a; margin-top: 10pt; margin-bottom: 4pt; }
h4 { font-size: 10.5pt; color: #2c5f8a; }
p { margin: 4pt 0; text-align: justify; }
li { margin: 2pt 0; }
table { border-collapse: collapse; width: 100%; font-size: 8.5pt; margin: 8pt 0; }
th, td { border: 0.5pt solid #8a8a8a; padding: 3pt 4pt; vertical-align: top; word-wrap: break-word; overflow-wrap: break-word; }
th { background: #e8eef4; color: #12365c; }
tr { page-break-inside: avoid; }
code { font-family: "Menlo", "Consolas", monospace; font-size: 8.5pt; background: #f2f2f2; padding: 0 2pt; }
pre { font-family: "Menlo", "Consolas", monospace; font-size: 8pt; background: #f6f6f6; border: 0.5pt solid #ccc; padding: 6pt; white-space: pre-wrap; overflow-wrap: break-word; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
hr { border: none; border-top: 0.5pt solid #bbb; margin: 10pt 0; }
blockquote { border-left: 2pt solid #2c5f8a; margin-left: 0; padding-left: 8pt; color: #444; }
.pagebreak { page-break-before: always; }
strong { color: #10243a; }
"""


def main():
    text = open(MD).read()
    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
    )
    # Force page breaks before References and Appendix A for readability.
    body = body.replace("<h2>17. References</h2>", '<h2 class="pagebreak">17. References</h2>')
    body = body.replace("<h2>Appendix A.", '<h2 class="pagebreak">Appendix A.')
    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Project Report: Fault-Aware Digital Twin for Fed-Batch Fermentation</title>
<meta name="author" content="OpenCode-assisted research workspace">
<meta name="description" content="Critical literature review and proposed reference architecture for real-time bioreactor monitoring and control">
<style>%s</style></head><body>%s</body></html>""" % (CSS, body)
    HTML(string=html, base_url=ROOT).write_pdf(PDF)
    print("wrote", PDF)


if __name__ == "__main__":
    main()
