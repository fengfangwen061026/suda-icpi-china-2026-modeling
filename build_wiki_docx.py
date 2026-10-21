"""Build a Word version of the wiki from WIKI_DRAFT.md.

Same single source as `build_wiki_html.py`; only the renderer differs. Pandoc
turns the LaTeX into native Word equation objects (OMML), so the formulas stay
selectable and editable rather than becoming pictures.

Pandoc's OMML writer does not carry everything KaTeX does. Three constructs come
out wrong, silently:

* ``\\tag{...}``          -- dropped entirely, so every equation loses its number
* ``&`` alignment         -- emitted as a literal "&" inside the equation
* ``\\underbrace{}_{...}`` -- the label is lost
* parens inside ``\\text{}`` -- rendered as ``\\(...\\)``

The first is handled for every equation by :func:`rewrite_equation_numbers`. The
other three affect six equations, which get an explicit Word-safe rewrite in
:data:`WORD_SAFE_EQUATIONS` -- keyed by equation number, and the build fails if a
key no longer matches the source, so the Word file cannot quietly go stale
against the Markdown.

Requires pandoc on PATH, or its location in $PANDOC. Run from the project root:

    .venv/bin/python build_wiki_docx.py
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from src import equation_numbers as E
from src.docx_vector import attach_svg, vector_pairs
from src import references as R
from src import parameters as P

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "WIKI_DRAFT.md"
OUT = ROOT / "Modeling.docx"

#: Text width of an A4 page at the margins set below, in inches.
FIGURE_WIDTH_IN = 6.3

#: Equations pandoc cannot carry faithfully, rewritten so Word renders them.
#: `\underbrace{x}_{label}` becomes `\overset{label}{x}`, which keeps the label
#: (above the term rather than below it); `&` alignment becomes a plain
#: `array{l}`; parens inside `\text{}` become commas.
WORD_SAFE_EQUATIONS: dict[str, str] = {
    "3.1-4": r"""
R_{\text{margin}}(\text{site})=
\overset{\text{lactate arm}}{\left(\frac{f_L(L_t)}{f_L(L_s)}\right)}
\cdot
\overset{\text{hypoxia arm}}{\left(\frac{f_O(C_t)}{f_O(C_s)}\right)}
\cdot
\overset{\text{quorum arm}}{\left(\frac{f_O(C_t)/f_O(C_s)}{N_s/N_t}\right)^{n_Q}}
\cdot
\overset{\text{native repression}}{\left(\rho_{\text{anox}}\rho_{\text{glu}}\right)}
""",
    "3.2-4": r"""
\overset{\text{hypoxic volume}}{\left(\frac{\overline{f}_O(R_2)}{\overline{f}_O(R_1)}\right)}\times
\overset{\text{AHL integration}}{\left(\frac{\Psi_{\text{centre}}(R_2)}{\Psi_{\text{centre}}(R_1)}\right)}
=\frac{Q(R_2)}{Q(R_1)}
""",
    "3.4-1": r"""
\frac{\text{delivery, tagged}}{\text{delivery, untagged}}
=\frac{1}{r_{\text{biomass}}\,r_{\text{potency}}}>1
\quad\Longleftrightarrow\quad
r_{\text{potency}}<r^{*}\equiv\frac{1}{r_{\text{biomass}}}
""",
    "4.3-3": r"""
\begin{array}{l}
\text{total off-target reduction}=\rho_{\text{pool}}\times\dfrac{E_{\text{untagged}}}{E_{\text{tagged}}}\\[6pt]
\text{confinement share}=\dfrac{\ln(\text{confinement})}{\ln(\text{total})}
\end{array}
""",
    "4.4-8": r"""
\overset{\text{own},\ \propto R^2}{\left(\Psi_{\text{centre}}\sim\frac{\alpha^2}{2}\right)}
\qquad\text{vs}\qquad
\overset{\text{neighbour},\ \propto R^3/d}{\left(\Psi_{\text{out}}\sim\frac{R^3}{3\lambda^2 d}\right)}
""",
    "6-1": r"""
\begin{array}{l}
\dot A = \Phi-\delta_A A \qquad \text{antigen + IL-1β/IL-18 signal}\\[4pt]
\dot D = a_D\dfrac{A}{K_A+A}-\delta_D D \qquad \text{DC maturation, saturating}\\[4pt]
\dot T = a_T\,\varepsilon\,D-\delta_T T \qquad \text{CTL priming, suppressed by }\varepsilon\\[4pt]
\dot M = rM\Big(1-\dfrac MK\Big)-\dfrac{kTM}{h+M} \qquad \text{distant lesion}
\end{array}
""",
}


def find_pandoc() -> str:
    """Pandoc from $PANDOC or PATH."""
    candidate = os.environ.get("PANDOC") or shutil.which("pandoc")
    if not candidate or not Path(candidate).is_file():
        raise SystemExit(
            "pandoc not found. Install it, or point $PANDOC at the binary.\n"
            "Without installing: pip download pypandoc_binary --no-deps -d /tmp/pd "
            "&& unzip -o /tmp/pd/*.whl -d /tmp/pd "
            "&& export PANDOC=/tmp/pd/pypandoc/files/pandoc"
        )
    return candidate


def _equation(markdown: str, tag: str) -> re.Match[str]:
    match = re.search(
        r"\$\$((?:(?!\$\$).)*?\\tag\{" + re.escape(tag) + r"\}\s*)\$\$", markdown, re.S
    )
    if match is None:
        raise SystemExit(
            f"equation ({tag}) is no longer in {SOURCE.name}, but build_wiki_docx.py "
            "still carries a Word-safe rewrite for it. Update WORD_SAFE_EQUATIONS."
        )
    return match


def apply_word_safe_equations(markdown: str) -> str:
    """Swap in the rewrites, keeping each equation's number."""
    for tag, replacement in WORD_SAFE_EQUATIONS.items():
        match = _equation(markdown, tag)
        body = f"$${replacement.strip()} \\tag{{{tag}}}$$"
        markdown = markdown[: match.start()] + body + markdown[match.end() :]
    return markdown


EM = "\u2003"  # em space; the only gap LibreOffice keeps inside an equation


def _map_math(markdown: str, fix) -> str:
    """Apply `fix` to the body of every display and inline equation."""
    markdown = re.sub(r"\$\$(.+?)\$\$", lambda m: f"$${fix(m.group(1))}$$",
                      markdown, flags=re.S)
    return re.sub(r"(?<![\$\\])\$([^\$\n]+?)\$(?!\$)",
                  lambda m: f"${fix(m.group(1))}$", markdown)


def fix_accents_and_brackets(markdown: str) -> str:
    """Two constructs pandoc's OMML gets wrong, both silently.

    ``\\bar x`` comes out as an acute accent rather than a macron. A square
    bracket survives only as ``\\left[ ... \\right]``: ``[``, ``\\big[`` and
    ``\\Big[`` all render the whole equation as a single error glyph.

    The line-spacing argument of ``\\\\`` inside an array -- ``\\\\[4pt]`` -- is not a
    bracket, so it is masked out before the rewrite and restored after.
    """
    guard = "\x00ROWSPACE\x00"

    def fix(body: str) -> str:
        spacings: list[str] = []

        def mask(match: re.Match[str]) -> str:
            spacings.append(match.group(0))
            return guard

        body = re.sub(r"\\\\\[[^\]]*\]", mask, body)
        # an accent takes one token: a control sequence or a single
        # character. \w would swallow the subscript in "\bar f_O".
        body = re.sub(r"\\bar\s*(\\[A-Za-z]+|[A-Za-z0-9])",
                      r"\\overline{\1}", body)
        body = re.sub(r"\\(?:bigg?|Bigg?)\[", r"\\left[", body)
        body = re.sub(r"\\(?:bigg?|Bigg?)\]", r"\\right]", body)
        body = re.sub(r"(?<!\\left)\[", r"\\left[", body)
        body = re.sub(r"(?<!\\right)\]", r"\\right]", body)
        for spacing in spacings:
            body = body.replace(guard, spacing, 1)
        return body

    return _map_math(markdown, fix)


def rewrite_equation_numbers(markdown: str) -> str:
    """``\\tag{3.1-4}`` -> a trailing ``(3.1-4)`` inside the equation.

    Pandoc drops ``\\tag`` on the floor, so the number has to live inside the
    maths to survive at all. The hyphen has to be ``\\text{-}`` or it is typeset
    as a minus with binary-operator spacing, and the gap in front has to be em
    spaces inside ``\\text{}`` -- every maths spacing command (``\\qquad``,
    ``\\hspace``, ``\\mspace``, ``\\phantom``) is collapsed on render.
    :func:`preserve_math_spaces` then stops Word collapsing those em spaces too.
    """
    def replace(match: re.Match[str]) -> str:
        number = match.group(1).replace("-", r"\text{-}")
        return r"\text{" + EM * 3 + r"}\mathrm{(" + number + ")}"

    return re.sub(r"\\tag\*?\{([^}]*)\}", replace, markdown)


def _pandoc_escape(text: str) -> str:
    """Bibliographic fields are data, not Markdown: one title has brackets."""
    return text.replace("[", r"\[").replace("]", r"\]")


def anchor_sections(markdown: str) -> str:
    """Give every numbered heading the id its section marks point at.

    Pandoc would otherwise slug the heading text, which drops the leading
    number and suffixes the repeated "Model" / "Results" headings -- neither is
    something a mark written as ``(§2.3)`` can compute.
    """
    seen: set[str] = set()

    def attach(match: re.Match[str]) -> str:
        number = match.group(2)
        if number in seen:
            return match.group(0)
        seen.add(number)
        return f"{match.group(0).rstrip()} {{#{R.section_anchor(number)}}}"

    return re.sub(
        r"^#{1,6}[ \t]+((\d+(?:\.\d+)*)\.?[ \t]+.*?)[ \t]*$",
        attach, markdown, flags=re.MULTILINE,
    )


def apply_sections(markdown: str) -> str:
    """``(§2.1)`` -> a raised, linked mark, and a bookmark on every heading."""
    markdown, _ = R.apply_sections(
        markdown,
        mark=lambda numbers: "^" + ",".join(
            f"[§{n}](#{R.section_anchor(n)})" for n in numbers
        ) + "^",
    )
    return anchor_sections(markdown)


def citation_markup(markers: list[R.Marker]) -> str:
    """The raised, linked numbers that stand in the text.

    ``^...^`` is pandoc's superscript, which the Word writer turns into a run
    with ``vertAlign=superscript`` -- a real raised number, not a smaller font.
    It cannot contain a literal space, which is why the numbers are joined by a
    bare comma.
    """
    links = []
    for marker in markers:
        link = f"[{marker.number}](#{R.entry_anchor(marker.number)})"
        if marker.first:
            # The bookmark §8's own number links back to.
            link = f"[{link}]{{#{R.citation_anchor(marker.number)}}}"
        links.append(link)
    return "^" + ",".join(links) + "^"


def reference_list(entries: list[R.Entry]) -> str:
    """§8's list: the number is written out, so that it can be the link back.

    One paragraph per entry rather than a Markdown ordered list -- Word would
    generate that list's numbers itself, and a generated number cannot carry a
    bookmark or a link.
    """
    blocks = []
    for entry in entries:
        number = f"[[{R.numbered(entry)}](#{R.citation_anchor(entry.number)})]"
        body = R.format_entry(entry.reference, ("*", "*"), _pandoc_escape)
        blocks.append(f"{number}{{#{R.entry_anchor(entry.number)}}} {body}")
    return "\n\n".join(blocks)


def check_anchors(body: str) -> None:
    """A Word link to a bookmark that is not there fails silently on the click."""
    bookmarks = set(re.findall(r'w:bookmarkStart[^>]*w:name="([^"]+)"', body))
    dangling = sorted(
        set(re.findall(r'w:hyperlink w:anchor="([^"]+)"', body)) - bookmarks
    )
    if dangling:
        raise SystemExit(
            "internal links with no bookmark behind them: " + ", ".join(dangling)
        )


def apply_references(markdown: str) -> str:
    """``[@key]`` -> a raised, linked number, and the reference list into §8."""
    markdown, entries = R.apply(markdown, marker=citation_markup, tighten=True)
    if "<!--REFERENCES-->" not in markdown:
        raise SystemExit(f"{SOURCE.name} has lost its <!--REFERENCES--> marker.")
    return markdown.replace("<!--REFERENCES-->", reference_list(entries))


def apply_equation_numbers(markdown: str) -> str:
    """Repository tags out, (1)…(N) in, mapping out to the repo.

    Shared with `build_wiki_html.py` so the Word file and the published page
    carry the same numbers; the Markdown source keeps the repository tags.
    """
    markdown, index, unknown = E.renumber(markdown)
    if unknown:
        raise SystemExit(
            f"{SOURCE.name} refers to equation(s) it never displays: "
            + ", ".join(unknown)
        )
    E.write_index(index)
    return markdown


def size_figures(markdown: str) -> str:
    """Pandoc sizes images from their pixel count, which here is metres wide."""
    return re.sub(
        r"(!\[[^\]]*\]\(outputs/figures/[\w.]+\.png\))(?!\{)",
        lambda m: f"{m.group(1)}{{width={FIGURE_WIDTH_IN}in}}",
        markdown,
    )


def build_reference(pandoc: str, path: Path) -> Path:
    """Pandoc's default reference, set to A4 with ruled tables."""
    default = path.parent / "reference-default.docx"
    default.write_bytes(
        subprocess.run(
            [pandoc, "--print-default-data-file", "reference.docx"],
            check=True, capture_output=True,
        ).stdout
    )

    borders = (
        "<w:tblBorders>"
        + "".join(
            f'<w:{edge} w:val="single" w:sz="4" w:space="0" w:color="BFBFBF" />'
            for edge in ("top", "left", "bottom", "right", "insideH", "insideV")
        )
        + "</w:tblBorders>"
    )
    page = (
        '<w:pgSz w:w="11906" w:h="16838" />'
        '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" '
        'w:header="709" w:footer="709" w:gutter="0" />'
    )

    with zipfile.ZipFile(default) as src, zipfile.ZipFile(
        path, "w", zipfile.ZIP_DEFLATED
    ) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "word/styles.xml":
                text = data.decode("utf-8")
                text = text.replace(
                    '<w:style w:type="table" w:default="1" w:styleId="Table">\n'
                    "    <w:name w:val=\"Table\" />",
                    '<w:style w:type="table" w:default="1" w:styleId="Table">\n'
                    "    <w:name w:val=\"Table\" />",
                )
                text = re.sub(
                    r'(<w:style w:type="table"[^>]*w:styleId="Table">.*?<w:tblPr>)',
                    r"\1" + borders,
                    text,
                    count=1,
                    flags=re.S,
                )
                data = text.encode("utf-8")
            elif item.filename == "word/document.xml":
                text = data.decode("utf-8")
                text = text.replace("<w:sectPr>", "<w:sectPr>" + page, 1)
                data = text.encode("utf-8")
            dst.writestr(item, data)
    return path


def finish_docx(path: Path) -> int:
    """Two things pandoc leaves for the reader to fix by hand.

    ``<m:t>`` is written without ``xml:space``, so a renderer may collapse the
    run's whitespace -- which it does, closing the gap before every equation
    number. And the table of contents is a field, which Word shows empty until
    somebody refreshes it; ``updateFields`` makes Word fill it in on open.
    """
    with zipfile.ZipFile(path) as doc:
        items = [(i, doc.read(i.filename)) for i in doc.infolist()]

    patched = 0
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as doc:
        for info, data in items:
            if info.filename == "word/document.xml":
                text = data.decode("utf-8")
                patched = text.count("<m:t>")
                data = text.replace("<m:t>", '<m:t xml:space="preserve">').encode("utf-8")
            elif info.filename == "word/settings.xml":
                text = data.decode("utf-8")
                if "updateFields" not in text:
                    text = text.replace(
                        "</w:settings>", '<w:updateFields w:val="true" /></w:settings>'
                    )
                data = text.encode("utf-8")
            doc.writestr(info, data)
    return patched


def main() -> Path:
    pandoc = find_pandoc()
    markdown = SOURCE.read_text(encoding="utf-8")

    stale = P.markdown_table()
    missing = [
        row.strip()
        for row in stale.splitlines()
        if row.strip().startswith("| `") and row.strip() not in markdown
    ]
    if missing:
        raise SystemExit(
            f"{SOURCE.name} parameter table is stale against config/parameters.csv "
            f"({len(missing)} row(s) differ). Fix the Markdown first."
        )

    markdown = re.sub(r"\A#\s+Modeling\s*\n", "", markdown)
    markdown = apply_word_safe_equations(markdown)
    markdown = apply_equation_numbers(markdown)
    markdown = apply_sections(markdown)
    markdown = apply_references(markdown)
    markdown = fix_accents_and_brackets(markdown)
    markdown = rewrite_equation_numbers(markdown)
    markdown = size_figures(markdown)

    work = ROOT / ".docx-build"
    work.mkdir(exist_ok=True)
    prepared = work / "prepared.md"
    prepared.write_text(markdown, encoding="utf-8")
    reference = build_reference(pandoc, work / "reference.docx")

    result = subprocess.run(
        [
            pandoc,
            str(prepared),
            "-f", "markdown-implicit_figures",
            "-o", str(OUT),
            "--reference-doc", str(reference),
            "--resource-path", str(ROOT),
            "--toc", "--toc-depth=2",
            "--metadata", "title=Modeling",
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    for line in result.stderr.splitlines():
        print(f"  pandoc: {line}", file=sys.stderr)

    runs = finish_docx(OUT)
    # Same two-layer picture as the other builds: the PNG pandoc embedded, with
    # the SVG master attached so Word and WPS draw the figure as vector.
    attach_svg(OUT, vector_pairs(ROOT / "outputs" / "figures"))

    with zipfile.ZipFile(OUT) as doc:
        body = doc.read("word/document.xml").decode("utf-8")
    check_anchors(body)
    equations = body.count("<m:oMath")
    images = len([n for n in zipfile.ZipFile(OUT).namelist() if n.startswith("word/media/")])
    print(f"{OUT}  ({OUT.stat().st_size // 1024} KB)")
    print(f"  {equations} native equations, {body.count('<w:tbl>')} tables, {images} images")
    print(f"  {runs} equation text runs marked space-preserving")
    if "&amp;" in body and "<m:t>&amp;</m:t>" in body:
        print("  WARNING: a literal & survived inside an equation", file=sys.stderr)
    return OUT


if __name__ == "__main__":
    main()
