"""Minimal Markdown -> .docx converter for the write-ups (headings, paragraphs, lists, quotes, tables, links)."""
import re
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))")


def hyperlink(par, text, url):
    part = par.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), r_id)
    r = OxmlElement("w:r"); rpr = OxmlElement("w:rPr")
    c = OxmlElement("w:color"); c.set(qn("w:val"), "1F4E79"); rpr.append(c)
    u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rpr.append(u)
    r.append(rpr); t = OxmlElement("w:t"); t.text = text; t.set(qn("xml:space"), "preserve"); r.append(t); h.append(r)
    par._p.append(h)


def add_inline(par, text, bold=False):
    for piece in INLINE.split(text):
        if not piece:
            continue
        if piece.startswith("**"):
            run = par.add_run(piece[2:-2]); run.bold = True
        elif piece.startswith("`"):
            run = par.add_run(piece[1:-1]); run.font.name = "Consolas"; run.font.size = Pt(9.5)
        elif piece.startswith("[") and "](" in piece:
            t, u = re.match(r"\[([^\]]+)\]\(([^)]+)\)", piece).groups()
            hyperlink(par, t, u)
        elif piece.startswith("*") and piece.endswith("*") and len(piece) > 2:
            run = par.add_run(piece[1:-1]); run.italic = True
        else:
            run = par.add_run(piece)
        if bold:
            run.bold = True


def convert(src, dst):
    lines = open(src, encoding="utf-8").read().splitlines()
    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    for side in ("left_margin", "right_margin"):
        setattr(sec, side, Cm(2.2))
    sec.top_margin = sec.bottom_margin = Cm(2.0)
    st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)
    st.paragraph_format.space_after = Pt(5)
    for h, size in (("Title", 18), ("Heading 1", 14), ("Heading 2", 12), ("Heading 3", 11)):
        doc.styles[h].font.name = "Calibri"; doc.styles[h].font.size = Pt(size); doc.styles[h].font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(0); p.paragraph_format.left_indent = Cm(0.5)
                r = p.add_run(lines[i].rstrip() or " "); r.font.name = "Consolas"; r.font.size = Pt(8.5)
                i += 1
            i += 1; doc.add_paragraph(); continue
        if not ln.strip():
            i += 1; continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Light Grid Accent 1"
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    cell = t.cell(r, c); cell.text = ""
                    p = cell.paragraphs[0]; add_inline(p, val, bold=(r == 0))
                    for run in p.runs:
                        run.font.size = Pt(9)
            doc.add_paragraph()
            continue
        im = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", ln)
        if im:
            import os
            path = os.path.join(os.path.dirname(os.path.abspath(src)), im.group(2))
            doc.add_picture(path, width=Cm(13.5)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap = doc.add_paragraph(); add_inline(cap, "*" + im.group(1) + "*"); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            i += 1; continue
        m = re.match(r"^(#{1,3}) (.*)", ln)
        if m:
            level = len(m.group(1))
            if level == 1:
                p = doc.add_paragraph(style="Title"); add_inline(p, m.group(2))
            else:
                p = doc.add_heading(level=level - 1); add_inline(p, m.group(2))
        elif ln.startswith("> "):
            p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.8)
            add_inline(p, ln[2:]); [setattr(r, "italic", True) for r in p.runs]
        elif re.match(r"^\s*- ", ln):
            p = doc.add_paragraph(style="List Bullet"); add_inline(p, re.sub(r"^\s*- ", "", ln))
        elif re.match(r"^\d+\. ", ln):
            num = re.match(r"^(\d+)\. ", ln).group(1)
            p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.63); p.paragraph_format.first_line_indent = Cm(-0.63)
            p.add_run(f"{num}.\t"); add_inline(p, re.sub(r"^\d+\. ", "", ln))
        else:
            p = doc.add_paragraph(); add_inline(p, ln)
        i += 1
    doc.save(dst)


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
