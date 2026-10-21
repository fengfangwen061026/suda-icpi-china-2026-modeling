"""Build the bilingual review copy from ENGINEERING_DRAFT_ZH.md.

This one is **not** a wiki page. It is the artefact the team reviews against:
every English block of the Engineering page followed by its Chinese rendering,
so a reviewer can read the Chinese and still point at the English sentence they
want changed. It keeps the 审稿说明 block that the published build strips,
because that block is instructions to the reviewer.

Built from the same parts as the other two pages -- `wiki_template.html` for the
shell, `src/md2html.py` for the conversion, and `build_engineering_html.py` for
figure placement -- so the three cannot drift into three different renderings of
the same Markdown.

The one thing specific to this page: a line beginning ``◆ `` is a translation,
and becomes a ``<p class="zh">`` so it reads as a second voice. The marker is
consumed; the stylesheet replaces it.

Run from the project root:

    .venv/bin/python build_bilingual_html.py
"""

from __future__ import annotations

import re
from pathlib import Path

import build_engineering_html as E
import build_wiki_html as W
from src import md2html

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "ENGINEERING_DRAFT_ZH.md"
TEMPLATE = ROOT / "wiki_template.html"
OUT = ROOT / "engineering_bilingual.html"

EYEBROW = "iGEM &middot; Engineering &middot; 审稿版"
TITLE = "Engineering 中英对照"
STANDFIRST = (
    "Engineering 页的中英对照审稿版：英文段落在上，中文译文紧随其下。\n"
    "  <strong>上线的是英文稿</strong>，中文只是帮你快速读懂——要改的是英文那一句。"
)
FOOTER = (
    "审稿版，不上线。英文源 <code>ENGINEERING_DRAFT.md</code>，对照源\n"
    "  <code>ENGINEERING_DRAFT_ZH.md</code>；重建用 <code>python build_bilingual_html.py</code>。"
)

#: A translation line. Continuation lines do not carry the marker, so a new
#: marker is what starts a new one.
MARKER = "◆ "
_SPLIT_RE = re.compile(r"\n(?=◆ )")


def split_translations(markdown: str) -> str:
    """Give every ``◆`` line its own block.

    In the source a run of them sits in one paragraph, which is how it should
    be read in a text editor. The converter needs one block each, or the run
    becomes a single ``<p>`` with the markers stranded inside it.
    """
    blocks = []
    for block in markdown.split("\n\n"):
        blocks.append("\n\n".join(_SPLIT_RE.split(block)) if MARKER in block else block)
    return "\n\n".join(blocks)


def mark_translations(html: str) -> str:
    """``<p>◆ …</p>`` -> ``<p class="zh">…</p>``, and no marker may survive.

    The note block documents the marker inside backticks, so a ``◆`` in a code
    span is a mention, not a stranded marker; everything else is a line that
    did not get its own paragraph and would render with the marker showing.
    """
    html = re.sub(r"<p>◆\s*", '<p class="zh">', html)
    stranded = re.sub(r"<code>.*?</code>", "", html, flags=re.S)
    if "◆" in stranded:
        context = stranded[max(0, stranded.index("◆") - 60):][:140]
        raise SystemExit(
            "a ◆ marker is not at the start of its own paragraph, so it would "
            f"render as text:\n  …{context}…"
        )
    return html


def main() -> Path:
    markdown = SOURCE.read_text(encoding="utf-8")
    # The review copy keeps its own note block; only figures are placed.
    markdown, placed = E.place_figures(markdown)
    E.check_figures(placed)
    markdown = split_translations(markdown)

    body, contents = md2html.convert(markdown)
    body = body.split("\n", 1)[1] if body.startswith("<h1") else body
    body = mark_translations(body)

    html = TEMPLATE.read_text(encoding="utf-8")
    html = W.fill_template(
        html,
        f"{contents}\n\n<main>\n{body}\n</main>",
        eyebrow=EYEBROW,
        title=TITLE,
        standfirst=STANDFIRST,
        footer=FOOTER,
    )
    html = E.embed_figures(html, placed)

    OUT.write_text(html, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    out = main()
    print(f"{out}  ({out.stat().st_size // 1024} KB)")
