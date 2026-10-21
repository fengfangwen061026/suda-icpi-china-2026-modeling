"""Build `Engineering.docx` from `ENGINEERING_DRAFT.md`.

Same single source as `build_engineering_html.py`; only the renderer differs.
Built out of the other two builders rather than beside them: the figure
placement comes from `build_engineering_html`, and every Word-specific fix --
the equations pandoc's OMML writer mangles, the equation numbers it drops, the
whitespace a renderer collapses -- comes from `build_wiki_docx`, which already
documents each one.

Two things differ from the Modeling document:

* This page's figures live in subdirectories (``outputs/figures/engineering/``
  and ``outputs/figures/video/``), which `build_wiki_docx.size_figures` does not
  match, so sizing is done here.
* `WORD_SAFE_EQUATIONS` covers equations from across the project; this page
  displays only some of them, and asking for a rewrite of one that is not here
  is not an error. Only the intersection is applied.

The editors' note is dropped, the same way the HTML build drops it.

Requires pandoc on PATH, or its location in $PANDOC. Without installing it:

    pip download pypandoc_binary --no-deps -d /tmp/pd \
      && python -c "import zipfile,glob; zipfile.ZipFile(glob.glob('/tmp/pd/*.whl')[0]).extractall('/tmp/pd/x')" \
      && chmod +x /tmp/pd/x/pypandoc/files/pandoc \
      && export PANDOC=/tmp/pd/x/pypandoc/files/pandoc

Run from the project root:

    PYTHONPATH=. .venv/bin/python build_engineering_docx.py
"""

from __future__ import annotations

import re
import subprocess
import zipfile
from pathlib import Path

import build_engineering_html as E
import build_wiki_docx as W
from src.docx_vector import attach_svg, vector_pairs

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "ENGINEERING_DRAFT.md"
OUTPUT = ROOT / "Engineering.docx"
BUILD = ROOT / ".docx-build"

TITLE = "Engineering — Modeling"

#: The supervisor's verdict is quoted in Chinese, so the reference document
#: still needs an East Asian typeface even though the page is in English.
HAN = "宋体"
HAN_BOLD = "黑体"


def prepared_markdown() -> str:
    """The published text, with figures placed and sized for the page."""
    markdown = SOURCE.read_text(encoding="utf-8")
    markdown = E.strip_editorial_note(markdown)
    markdown = E.resolve_figures(markdown)
    E.figures(markdown)  # same checks the HTML build runs

    # Pandoc sizes an image from its pixel count, which here is metres wide.
    # `build_wiki_docx.size_figures` only matches files directly in
    # outputs/figures; this page's are nested one level down.
    markdown = re.sub(
        r"(!\[[^\]]*\]\(outputs/figures/[\w./]+\.png\))(?!\{)",
        lambda m: f"{m.group(1)}{{width={W.FIGURE_WIDTH_IN}in}}",
        markdown,
    )

    # Only the rewrites for equations this page actually displays. Asking for
    # one that is not here would be a false alarm, not a stale rewrite.
    for tag, replacement in W.WORD_SAFE_EQUATIONS.items():
        if re.search(r"\\tag\{" + re.escape(tag) + r"\}", markdown) is None:
            continue
        match = W._equation(markdown, tag)
        body = f"$${replacement.strip()} \\tag{{{tag}}}$$"
        markdown = markdown[: match.start()] + body + markdown[match.end():]

    markdown = W.fix_accents_and_brackets(markdown)
    markdown = W.rewrite_equation_numbers(markdown)

    # The page's own H1 becomes the document title, so drop it from the body
    # or Word shows the same line twice.
    markdown, dropped = re.subn(r"\A# [^\n]*\n+", "", markdown, count=1)
    if not dropped:
        raise SystemExit(f"{SOURCE.name}: expected an H1 to use as the title")
    return markdown


def patched_reference(pandoc: str, destination: Path) -> Path:
    """Pandoc's reference document, with the East Asian typeface filled in.

    Lifted from `build_contribution_docx.py`: the default theme leaves
    `<a:ea typeface=""/>` empty, which leaves Word guessing for the Chinese
    quotation in Cycle 1.
    """
    base = W.build_reference(pandoc, BUILD / "engineering_reference_base.docx")
    source = zipfile.ZipFile(base)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as out:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == "word/theme/theme1.xml":
                theme = data.decode("utf-8")
                # Major (headings) first, then minor (body).
                theme, count = re.subn(
                    r'<a:ea typeface=""/>',
                    lambda m, box=[HAN_BOLD, HAN]: (
                        f'<a:ea typeface="{box.pop(0)}"/>' if box else m.group(0)
                    ),
                    theme,
                    count=2,
                )
                if count != 2:
                    raise SystemExit(
                        f"theme1.xml: expected 2 empty <a:ea> typefaces, found {count}"
                    )
                data = theme.encode("utf-8")
            out.writestr(item, data)
    return destination


def main() -> Path:
    pandoc = W.find_pandoc()
    BUILD.mkdir(exist_ok=True)

    prepared = BUILD / "engineering_prepared.md"
    prepared.write_text(prepared_markdown(), encoding="utf-8")
    reference = patched_reference(pandoc, BUILD / "engineering_reference.docx")

    subprocess.run(
        [
            pandoc,
            str(prepared),
            # See build_contribution_docx.py for why these two flags:
            # east_asian_line_breaks stops a soft wrap between two CJK
            # characters becoming a space; -smart keeps curly quotes out of
            # the East Asian font in the middle of English sentences.
            "--from=markdown+east_asian_line_breaks-smart",
            "--to=docx",
            f"--reference-doc={reference}",
            "--standalone",
            # No table of contents: this is a handover draft of five cycles,
            # not a document anyone navigates. The wiki has its own nav.
            f"--metadata=title:{TITLE}",
            f"--output={OUTPUT}",
        ],
        check=True,
        cwd=ROOT,
    )
    W.finish_docx(OUTPUT)
    # pandoc embeds the PNG; the SVG master goes on beside it so the figures
    # are vector in Word and WPS, with the raster as the fallback.
    attach_svg(OUTPUT, vector_pairs(ROOT / "outputs" / "figures"))
    return OUTPUT


if __name__ == "__main__":
    out = main()
    print(f"{out.relative_to(ROOT)}  {out.stat().st_size:,} bytes")
