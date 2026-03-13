#!/usr/bin/env python3
"""
Generate a well-formatted PDF from docs/DOCUMENTATION.md.

Usage:
    python docs/generate_pdf.py

Output:
    docs/DOCUMENTATION.pdf

Requirements (auto-installed -- pure Python, no system packages needed):
    pip install fpdf2
"""

import os
import re
import sys
import html as html_module

DOCS_DIR   = os.path.dirname(os.path.abspath(__file__))
SOURCE_MD  = os.path.join(DOCS_DIR, "DOCUMENTATION.md")
OUTPUT_PDF = os.path.join(DOCS_DIR, "DOCUMENTATION.pdf")


# ---- Auto-install if missing --------------------------------------------------
def _ensure(*packages):
    import importlib, subprocess
    for pkg, import_name in packages:
        try:
            importlib.import_module(import_name)
        except ImportError:
            print(f"  Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])


_ensure(("fpdf2", "fpdf"))

from fpdf import FPDF, XPos, YPos   # noqa: E402


# ---- Colours (RGB tuples) -----------------------------------------------------
C_INDIGO  = (99,  102, 241)
C_DARK    = (15,  23,  42)
C_BODY    = (30,  41,  59)
C_MUTED   = (100, 116, 139)
C_WHITE   = (255, 255, 255)
C_BORDER  = (226, 232, 240)
C_CODEBG  = (30,  41,  59)
C_CODEFG  = (200, 210, 230)
C_THBG    = C_INDIGO
C_THFG    = C_WHITE
C_TDALT   = (241, 245, 249)


# ---- Text sanitisation --------------------------------------------------------
_REPLACEMENTS = [
    ("\u2014", "--"),   # em dash
    ("\u2013", "-"),    # en dash
    ("\u2018", "'"),
    ("\u2019", "'"),
    ("\u201c", '"'),
    ("\u201d", '"'),
    ("\u2026", "..."),
    ("\u2022", "*"),
     ("\u2713", "[OK]"),
    ("\u2714", "[OK]"),
    ("\u00a0", " "),
    ("\u2192", "->"),
    ("\u2190", "<-"),
    ("\u2550", "="),
    ("\u2500", "-"),
    ("\u2502", "|"),
    ("\u251c", "+"),
    ("\u2514", "+"),
    ("\u2518", "+"),
    ("\u250c", "+"),
    ("\u252c", "+"),
    ("\u2524", "+"),
    ("\u27a4", "->"),
    # Emoji shorthand
    ("\U0001f6e1", "[Shield]"),
    ("\U0001f4ca", "[Chart]"),
    ("\U0001f5a5", "[PC]"),
    ("\U0001f514", "[Bell]"),
    ("\U0001f4c8", "[Graph]"),
    ("\u2705", "[OK]"),
    ("\u274c", "[X]"),
    ("\u26a0", "[!]"),
]

def _sanitise(text: str) -> str:
    """Map known special chars and strip remaining non-Latin-1 characters."""
    for src, dst in _REPLACEMENTS:
        text = text.replace(src, dst)
    # Strip anything still outside Latin-1
    return "".join(ch if ord(ch) < 256 else "?" for ch in text)


def _strip_html(t: str) -> str:
    return re.sub(r"<[^>]+>", "", t)


def _clean(t: str) -> str:
    return _sanitise(html_module.unescape(_strip_html(t)))


# ---- PDF class ----------------------------------------------------------------
class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=24)
        self.add_page()
        self.set_font("Helvetica", size=10)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*C_MUTED)
        self.cell(0, 5, "RansomGuard -- Complete Documentation",
                  align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*C_BORDER)
        self.line(20, self.get_y(), self.w - 20, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*C_MUTED)
        self.cell(0, 5, f"Page {self.page_no()}", align="C")

    def hline(self, color=C_INDIGO, width=0.5):
        self.set_draw_color(*color)
        self.set_line_width(width)
        self.line(20, self.get_y(), self.w - 20, self.get_y())
        self.set_line_width(0.2)
        self.ln(3)

    def h1(self, text):
        self.ln(2)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*C_DARK)
        self.multi_cell(0, 10, _clean(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.hline(C_INDIGO, 0.8)

    def h2(self, text):
        self.ln(5)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*C_INDIGO)
        self.multi_cell(0, 8, _clean(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.hline(C_BORDER, 0.3)

    def h3(self, text):
        self.ln(4)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*C_DARK)
        self.multi_cell(0, 7, _clean(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def h4(self, text):
        self.ln(3)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*C_BODY)
        self.multi_cell(0, 6, _clean(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def body(self, text):
        cleaned = _clean(text)
        if not cleaned.strip():
            return
        self.set_font("Helvetica", size=10)
        self.set_text_color(*C_BODY)
        self.multi_cell(0, 6, cleaned, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def code_block(self, code_lines):
        self.ln(1)
        lh      = 4.5
        pad     = 3
        total_h = len(code_lines) * lh + pad * 2 + 2
        x, y    = self.get_x(), self.get_y()
        if y + total_h > self.h - 28:
            self.add_page()
            x, y = self.get_x(), self.get_y()
        self.set_fill_color(*C_CODEBG)
        self.rect(x, y, self.w - 40, total_h, style="F")
        self.set_xy(x + pad, y + pad)
        self.set_font("Courier", size=7.5)
        self.set_text_color(*C_CODEFG)
        for ln_text in code_lines:
            cleaned = _clean(ln_text)[:120]
            self.cell(self.w - 40 - pad * 2, lh, cleaned,
                      new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_x(x + pad)
        self.set_xy(x, y + total_h + 1)
        self.set_text_color(*C_BODY)
        self.ln(2)

    def table(self, rows):
        if not rows:
            return
        # Remove separator rows (---|---)
        rows = [r for r in rows
                if not all(re.match(r"^:?-+:?$", c.strip()) for c in r)]
        if not rows:
            return
        col_n = len(rows[0])
        col_w = (self.w - 40) / col_n
        rh    = 6.5

        # Header row
        self.set_fill_color(*C_THBG)
        self.set_text_color(*C_THFG)
        self.set_font("Helvetica", "B", 8)
        for cell in rows[0]:
            self.cell(col_w, rh, _clean(cell)[:50], border=0, fill=True)
        self.ln()

        # Data rows
        self.set_font("Helvetica", size=8)
        for i, row in enumerate(rows[1:]):
            if self.get_y() > self.h - 35:
                self.add_page()
            fill = (i % 2 == 1)
            self.set_fill_color(*(C_TDALT if fill else C_WHITE))
            self.set_text_color(*C_BODY)
            for cell in row:
                self.multi_cell(col_w, rh, _clean(cell)[:80], border=0,
                                fill=fill, new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.ln(rh)
        self.ln(3)

    def bullet(self, text, depth=0):
        indent = 4 + depth * 6
        sym    = "*" if depth == 0 else "-"
        self.set_font("Helvetica", size=10)
        self.set_text_color(*C_BODY)
        self.set_x(20 + indent)
        self.multi_cell(0, 6, f"{sym}  {_clean(text)}",
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def blockquote(self, text):
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(*C_BODY)
        self.set_fill_color(240, 240, 255)
        self.set_draw_color(*C_INDIGO)
        self.set_line_width(0.8)
        x, y = self.get_x(), self.get_y()
        self.line(x, y, x, y + 7)
        self.set_line_width(0.2)
        self.set_x(x + 4)
        self.multi_cell(0, 6, f"  {_clean(text)}",
                        fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*C_BORDER)


# ---- Markdown parser ----------------------------------------------------------
def render(pdf: PDF, md_text: str):
    lines     = md_text.split("\n")
    in_code   = False
    code_buf  = []
    table_buf = []
    in_table  = False

    def flush_table():
        nonlocal table_buf, in_table
        if table_buf:
            pdf.table(table_buf)
        table_buf.clear()
        in_table = False

    for raw in lines:
        line = raw.rstrip()

        # Fenced code block
        if line.startswith("```"):
            if not in_code:
                in_code  = True
                code_buf = []
            else:
                pdf.code_block(code_buf)
                in_code  = False
                code_buf = []
            continue
        if in_code:
            code_buf.append(line)
            continue

        # Table
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            table_buf.append(cells)
            in_table = True
            continue
        elif in_table:
            flush_table()

        # Headings
        if line.startswith("#### "):
            pdf.h4(line[5:])
        elif line.startswith("### "):
            pdf.h3(line[4:])
        elif line.startswith("## "):
            pdf.h2(line[3:])
        elif line.startswith("# "):
            pdf.h1(line[2:])
        # Horizontal rule
        elif re.match(r"^-{3,}$", line) or re.match(r"^\*{3,}$", line):
            pdf.hline(C_BORDER, 0.3)
        # Blockquote
        elif line.startswith("> "):
            pdf.blockquote(line[2:])
        # Bullet list
        elif re.match(r"^\s*[-*+] ", line):
            depth = (len(line) - len(line.lstrip())) // 2
            text  = re.sub(r"^\s*[-*+] ", "", line)
            pdf.bullet(text, depth)
        # Numbered list
        elif re.match(r"^\s*\d+\. ", line):
            depth = (len(line) - len(line.lstrip())) // 2
            text  = re.sub(r"^\s*\d+\. ", "", line)
            pdf.bullet(text, depth)
        # Empty line
        elif not line.strip():
            pdf.ln(2)
        # Normal paragraph
        else:
            pdf.body(line)

    if in_table:
        flush_table()
    if in_code and code_buf:
        pdf.code_block(code_buf)


# ---- Entry point --------------------------------------------------------------
def build_pdf():
    if not os.path.exists(SOURCE_MD):
        print(f"[ERROR] Source not found: {SOURCE_MD}")
        sys.exit(1)

    print("\n  Ransomware Detector -- PDF Generator")
    print(f"  Source : {SOURCE_MD}")
    print(f"  Output : {OUTPUT_PDF}\n")

    with open(SOURCE_MD, "r", encoding="utf-8") as f:
        md_text = f.read()

    pdf = PDF()
    print("  Rendering PDF...", end="", flush=True)
    render(pdf, md_text)
    pdf.output(OUTPUT_PDF)
    print(" done.")

    size_kb = os.path.getsize(OUTPUT_PDF) // 1024
    print(f"\n  PDF saved: {OUTPUT_PDF}  ({size_kb} KB)\n")


if __name__ == "__main__":
    build_pdf()
