"""Build `Description_Modeling_Insert.docx` from `DESCRIPTION_DRAFT.md`.

`DESCRIPTION_DRAFT.md` is the single source for the modelling team's section of
the Description page -- §1.5, which is inserted into the wet lab's own draft
rather than published on its own. The Word version exists so it can be handed
over as one file: the section first, then the internal handover note and the
reference audit as an appendix, visibly separated so nobody pastes the wrong
half into the merged document.

The renderer is deliberately narrow -- it understands exactly the constructs
that file uses (two heading levels, paragraphs, `- ` bullets, images with the
bold caption line under them, one pipe table, the `> ` note block and `---`)
and nothing else. There is no mathematics on this page, so unlike
`build_wiki_docx.py` it needs no pandoc.

Citations are the Model page's mechanism: the source writes ``[@key]`` against
`config/references.csv` and the build numbers them. It also writes the page
text out with those numbers resolved, as `outputs/description_page.md` -- that
file, not the draft, is what gets pasted onto the wiki.

    PYTHONPATH=. .venv/bin/python build_description_docx.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from src import references as R
from src.docx_vector import attach_svg, vector_pairs

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "DESCRIPTION_DRAFT.md"
OUT = ROOT / "Description_Modeling_Insert.docx"
#: The section with its citations resolved -- what actually gets pasted.
PAGE = ROOT / "outputs" / "description_modeling_section.md"

#: Where the generated reference list goes, as on the Model page.
LIST_MARKER = "<!--REFERENCES-->"

#: This section is inserted into the wet lab's Description page, whose own
#: reference list ends at [5]. Ours continues from there rather than starting
#: again at [1]. Change this if their list grows, and rebuild -- never edit a
#: number by hand.
FIRST_REFERENCE = 6

#: Figures are numbered per page, in reading order, and their page already
#: carries the design schematic in 1.3. Same rule as the references: change
#: this, rebuild, never renumber by hand.
FIRST_FIGURE = 2

#: ``{#tissue}`` -- a figure's place-holder, in its legend and in the prose
#: that points at it.
FIGURE_REF = re.compile(r"\{#(?P<key>[a-z0-9_-]+)\}")

#: Fences around the text that actually goes on the wiki.
OPEN = "=== PAGE TEXT ==="
CLOSE = "=== END ==="

HAN = "宋体"
HAN_BOLD = "黑体"
LATIN = "Calibri"
MONO = "Consolas"

INK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x5A, 0x5A, 0x5A)
ACCENT = RGBColor(0x1F, 0x5C, 0x3A)

#: Printable width of the page, less the margins set below.
TEXT_WIDTH = Cm(16.0)


# --------------------------------------------------------------------------- #
# low-level helpers
# --------------------------------------------------------------------------- #

def style_run(run, *, size=10.5, bold=False, italic=False, color=INK,
              latin=LATIN, han=HAN, mono=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = MONO if mono else latin
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    fonts.set(qn("w:ascii"), MONO if mono else latin)
    fonts.set(qn("w:hAnsi"), MONO if mono else latin)
    fonts.set(qn("w:eastAsia"), MONO if mono else han)
    return run


def shade(paragraph, hexcolor):
    pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hexcolor)
    pr.append(shd)


def left_bar(paragraph, hexcolor, size=18):
    pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), str(size))
    left.set(qn("w:space"), "8")
    left.set(qn("w:color"), hexcolor)
    borders.append(left)
    pr.append(borders)


def keep_with_next(paragraph):
    paragraph._p.get_or_add_pPr().append(OxmlElement("w:keepNext"))


INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|\*[^*\n]+\*)")

#: `Apc`^Min/+^ -- the only superscript the source uses.
SUPER = re.compile(r"\^([^^]+)\^")


def emit_inline(paragraph, text, **base):
    """Write `text` into `paragraph`, honouring bold / code / link / italic."""
    for piece in INLINE.split(text):
        if not piece:
            continue
        kw = dict(base)
        if piece.startswith("**") and piece.endswith("**"):
            kw["bold"] = True
            kw["han"] = HAN_BOLD
            piece = piece[2:-2]
            # A bold link -- `**[Model](#)**` -- arrives here whole.
            link = re.fullmatch(r"\[([^\]]+)\]\([^)]*\)", piece)
            if link:
                kw["color"] = ACCENT
                piece = link.group(1)
        elif piece.startswith("`") and piece.endswith("`"):
            kw["mono"] = True
            kw["size"] = kw.get("size", 10.5) - 0.5
            piece = piece[1:-1]
        elif piece.startswith("[") and "](" in piece:
            label, _url = piece[1:-1].split("](", 1)
            kw["color"] = ACCENT
            piece = label
        elif piece.startswith("*") and piece.endswith("*"):
            kw["italic"] = True
            piece = piece[1:-1]
        emit_superscripts(paragraph, piece, **kw)


def emit_superscripts(paragraph, text, **kw):
    parts = SUPER.split(text)
    for index, part in enumerate(parts):
        if not part:
            continue
        run = style_run(paragraph.add_run(part), **kw)
        if index % 2:  # the captured group
            run.font.superscript = True


# --------------------------------------------------------------------------- #
# block writers
# --------------------------------------------------------------------------- #

def strip_md(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.replace("**", "").replace("`", "")


def add_para(doc, *, space_before=0, space_after=7, left=0, line=1.35):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.left_indent = Cm(left)
    pf.line_spacing = line
    return p


def heading(doc, level, text):
    sizes = {1: 19, 2: 14, 3: 12}
    befores = {1: 20, 2: 17, 3: 12}
    p = add_para(doc, space_before=befores[level], space_after=7, line=1.2)
    keep_with_next(p)
    emit_inline(p, text, size=sizes[level], bold=True,
                color=INK if level == 1 else ACCENT, han=HAN_BOLD)
    return p


def bullet(doc, text):
    p = add_para(doc, left=0.7, space_after=5)
    p.paragraph_format.first_line_indent = Cm(-0.35)
    style_run(p.add_run("· "), size=10.5, bold=True, color=ACCENT)
    emit_inline(p, text, size=10.5)


def rule(doc):
    p = add_para(doc, space_before=10, space_after=10)
    pr = p._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "C8C8C8")
    borders.append(bottom)
    pr.append(borders)


def figure(doc, path: Path, width=TEXT_WIDTH):
    if not path.exists():
        sys.exit(f"missing figure: {path}")
    p = add_para(doc, space_before=8, space_after=4)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    keep_with_next(p)
    p.add_run().add_picture(str(path), width=width)


def caption(doc, text):
    """A journal legend: the bold "Figure n. Title." then plain description.

    It is set left-aligned and in the body colour rather than centred and
    grey, because a legend that has to describe everything in the figure runs
    to several lines and reads as text, not as a label.
    """
    p = add_para(doc, space_after=12, line=1.3)
    emit_inline(p, text, size=9.5, color=INK)


def note_line(doc, text, *, first):
    p = add_para(doc, left=0.3, space_before=4 if first else 0, space_after=4,
                 line=1.3)
    shade(p, "FBF3E7")
    left_bar(p, "D9A441")
    emit_inline(p, text, size=9.5, color=GREY)


def column_widths(rows):
    """Share the text width out by how much each column has to say.

    Word's autofit ignores the East Asian runs and leaves the last column
    squeezed, so the widths are set explicitly. A CJK character is counted
    double because it sets roughly twice as wide as a Latin one.
    """
    def weight(cell):
        return sum(2 if ord(ch) > 0x2E7F else 1 for ch in strip_md(cell))

    demand = [max(weight(row[i]) for row in rows) for i in range(len(rows[0]))]
    floor = 2.2  # cm, so a narrow column still fits a date or a header
    free = TEXT_WIDTH.cm - floor * len(demand)
    total = sum(demand) or 1
    return [Cm(floor + free * d / total) for d in demand]


def table(doc, rows):
    head, body = rows[0], rows[1:]
    widths = column_widths(rows)
    t = doc.add_table(rows=1, cols=len(head))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    # Without a fixed layout Word and LibreOffice re-fit the grid and the
    # widths set per cell below are ignored.
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    t._tbl.tblPr.append(layout)
    for cell, text in zip(t.rows[0].cells, head):
        cell.paragraphs[0].paragraph_format.space_after = Pt(2)
        emit_inline(cell.paragraphs[0], text, size=9, bold=True, han=HAN_BOLD)
        shade(cell.paragraphs[0], "EFEFEF")
    for row in body:
        cells = t.add_row().cells
        for cell, text in zip(cells, row):
            cell.paragraphs[0].paragraph_format.space_after = Pt(2)
            cell.paragraphs[0].paragraph_format.line_spacing = 1.2
            emit_inline(cell.paragraphs[0], text, size=9)
    for row in t.rows:  # a width set per cell is the one Word honours
        for cell, width in zip(row.cells, widths):
            cell.width = width
    # LibreOffice lays the fixed grid out from `tblGrid`, which python-docx
    # left at equal columns when the table was created.
    for col, width in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths):
        col.set(qn("w:w"), str(width.twips))
    add_para(doc, space_after=8)
    return t


# --------------------------------------------------------------------------- #
# the renderer
# --------------------------------------------------------------------------- #

IMAGE = re.compile(r"^!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)\s*$")


def render(doc, lines):
    """Render `lines` of the narrow Markdown dialect this file uses."""
    buffer: list[str] = []
    pending: list[list[str]] = []
    in_note = False
    note_started = False

    def flush_paragraph():
        nonlocal buffer
        if buffer:
            emit_inline(add_para(doc), " ".join(buffer), size=10.5)
            buffer = []

    def flush_table():
        nonlocal pending
        if pending:
            table(doc, pending)
            pending = []

    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        index += 1
        stripped = line.strip()

        if stripped == ">" or stripped.startswith("> "):
            flush_paragraph()
            flush_table()
            in_note = True
            text = stripped[1:].strip()
            if text.startswith("- "):
                text = "· " + text[2:]
            if text:
                note_line(doc, text, first=not note_started)
                note_started = True
            continue
        if in_note and not stripped:
            in_note = False
            add_para(doc, space_after=4)
            continue

        if stripped.startswith("|"):
            flush_paragraph()
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue  # the alignment row
            pending.append(cells)
            continue
        flush_table()

        if not stripped:
            flush_paragraph()
            continue

        match = IMAGE.match(stripped)
        if match:
            flush_paragraph()
            figure(doc, ROOT / match.group("path"))
            # The caption is the bold line immediately under the image.
            if index < len(lines) and lines[index].strip().startswith("**"):
                text = [lines[index].strip()]
                index += 1
                while index < len(lines) and lines[index].strip():
                    text.append(lines[index].strip())
                    index += 1
                caption(doc, " ".join(text))
            continue

        if stripped.startswith("#"):
            flush_paragraph()
            level = len(stripped) - len(stripped.lstrip("#"))
            heading(doc, min(level, 3), stripped[level:].strip())
            continue

        if stripped == "---":
            flush_paragraph()
            rule(doc)
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            text = [stripped[2:]]
            while index < len(lines) and lines[index].startswith("  ") \
                    and lines[index].strip():
                text.append(lines[index].strip())
                index += 1
            bullet(doc, " ".join(text))
            continue

        # `1. ` in the prose, `[6] ` in the generated reference list.
        if re.match(r"^(?:\d+\.|\[\d+\]) ", stripped):
            flush_paragraph()
            text = [stripped]
            while index < len(lines) and lines[index].startswith("   ") \
                    and lines[index].strip():
                text.append(lines[index].strip())
                index += 1
            p = add_para(doc, left=0.9, space_after=4, line=1.3)
            p.paragraph_format.first_line_indent = Cm(-0.9)
            emit_inline(p, " ".join(text), size=9.5)
            continue

        buffer.append(stripped)

    flush_paragraph()
    flush_table()


def resolve_citations(page: str) -> str:
    """``[@key]`` -> ``[1]``, and the marker -> the numbered reference list.

    Same table and same rules as the Model page, so a reference cannot say one
    thing there and another here; `src.references` is what enforces that a key
    exists and that no row goes uncited. The numbers are offset by
    `FIRST_REFERENCE`, because this section is pasted into a page that already
    has references of its own.
    """
    offset = FIRST_REFERENCE - 1
    page, entries = R.apply(
        page,
        marker=lambda markers: "["
        + ", ".join(str(m.number + offset) for m in markers)
        + "]",
    )
    if LIST_MARKER not in page:
        sys.exit(f"{SOURCE.name} has lost its {LIST_MARKER} marker")
    listing = "\n".join(
        f"[{entry.number + offset}] {entry.reference.rendered()}" for entry in entries
    )
    return page.replace(LIST_MARKER, listing)


def resolve_figures(page: str) -> str:
    """``{#key}`` -> a figure number, assigned in order of the legends.

    The wiki's house rule is that every figure is numbered in reading order
    and named in the prose, so both failures stop the build: a legend whose
    figure the text never points at, and a pointer with no legend.
    """
    legends = [
        match.group("key")
        for line in page.splitlines()
        if line.lstrip().startswith("**Figure ")
        for match in [FIGURE_REF.search(line)]
        if match
    ]
    numbers = {key: n for n, key in enumerate(legends, start=FIRST_FIGURE)}

    mentioned = {
        match.group("key")
        for line in page.splitlines()
        if not line.lstrip().startswith("**Figure ")
        for match in FIGURE_REF.finditer(line)
    }
    if dangling := sorted(mentioned - set(numbers)):
        sys.exit(f"{SOURCE.name}: pointed at but never captioned: {dangling}")
    if unmentioned := sorted(set(numbers) - mentioned):
        sys.exit(f"{SOURCE.name}: captioned but never named in the text: {unmentioned}")

    return FIGURE_REF.sub(lambda m: str(numbers[m.group("key")]), page)


def banner(doc, text, fill):
    p = add_para(doc, space_before=14, space_after=10, left=0.2)
    shade(p, fill)
    emit_inline(p, text, size=10, bold=True, han=HAN_BOLD, color=INK)


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    # The fences are matched as whole lines: the handover note above them talks
    # about the markers, so a substring search finds the wrong occurrence.
    fences = [i for i, line in enumerate(lines) if line.strip() in (OPEN, CLOSE)]
    opens = [i for i in fences if lines[i].strip() == OPEN]
    closes = [i for i in fences if lines[i].strip() == CLOSE]
    if len(opens) != 1 or len(closes) != 1 or opens[0] > closes[0]:
        sys.exit(f"{SOURCE.name}: expected one {OPEN} line then one {CLOSE} line")

    before = "\n".join(lines[: opens[0]])
    page = resolve_figures(resolve_citations("\n".join(lines[opens[0] + 1 : closes[0]])))
    after = "\n".join(lines[closes[0] + 1 :])

    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(page.strip("\n") + "\n", encoding="utf-8")

    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(2.2)
        section.bottom_margin = Cm(2.2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    normal = doc.styles["Normal"]
    normal.font.name = LATIN
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), HAN)

    banner(doc, "① 以下是插入 01 Description 的建模段（1.5），可直接贴", "E8F1EC")
    render(doc, page.strip("\n").splitlines())

    doc.add_page_break()
    banner(doc, "② 以下是内部交接说明与参考文献核查记录，不要并入正文", "FBF3E7")
    # The handover note sits above the fence in the source; the audit below it.
    note = before.split("\n", 1)[1] if "\n" in before else ""
    render(doc, (note.strip("\n") + "\n\n" + after.strip("\n")).splitlines())

    doc.save(OUT)
    attached = attach_svg(OUT, vector_pairs(ROOT / "outputs" / "figures"))
    print(f"wrote {OUT.relative_to(ROOT)} (vector: {', '.join(attached) or 'none'})")


if __name__ == "__main__":
    main()
