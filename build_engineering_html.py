"""Build the Engineering page from ENGINEERING_DRAFT.md.

Same shape as `build_wiki_html.py`, and deliberately built out of its parts
rather than beside them: the shared `wiki_template.html` carries the stylesheet,
`src/md2html.py` does the conversion, and `fill_template` / `data_uri` come from
the modelling build. A second converter would be a second set of bugs.

Two things are specific to this page:

* the draft opens with an editorial note block marked 不上线 ("not for the
  published page"), which is stripped here rather than deleted from the source,
  so the source stays the thing the team edits;
* the draft references figures with ordinary Markdown images, so it reads
  correctly anywhere it is opened; this build only checks that each file
  exists and then inlines it.

Run from the project root:

    .venv/bin/python build_engineering_html.py
"""

from __future__ import annotations

import re
from pathlib import Path

import build_wiki_html as W
from src import md2html

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "ENGINEERING_DRAFT.md"
TEMPLATE = ROOT / "wiki_template.html"
OUT = ROOT / "engineering_wiki.html"

EYEBROW = "iGEM &middot; Engineering &middot; Model"
TITLE = "Engineering"
STANDFIRST = (
    "The modelling team's Design&ndash;Build&ndash;Test&ndash;Learn record for an engineered\n"
    "  <em>E.&nbsp;coli</em> Nissle 1917 circuit that releases GSDMD-NT in a colorectal tumour.\n"
    "  Five cycles; two of them ran v1&nbsp;&rarr;&nbsp;v2, and in both the v1 had returned an\n"
    "  answer that looked fine. One is still open, and says so."
)
FOOTER = (
    "Every figure is generated from the frozen workbook by <code>src/plots.py</code>; rebuild\n"
    "  this page with <code>python build_engineering_html.py</code>."
)

#: Images the draft may reference, and nothing else: a path outside this set
#: is a typo rather than a new figure, and should stop the build.
#:
#: This page is the modelling group's record, so its evidence is the modelling
#: figures themselves, referenced where they already live.
ALLOWED_FIGURES = {
    "outputs/figures/video/fig2_2_gate_holdout.png",
    "outputs/figures/fig3_3_arm_direction.png",
    "outputs/figures/fig4_4_cluster.png",
    "outputs/figures/fig4_6_dose_requirement.png",
}

_NOTE_RE = re.compile(r"^> \*\*交接说明.*?^---$\n+", re.S | re.M)
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

#: This page is its own wiki page, so its figures start at 1. (The Description
#: insert starts at 2 because the wet lab's own schematic is its Fig. 1.)
FIRST_FIGURE = 1
FIGURE_REF = re.compile(r"\{#(?P<key>[a-z0-9_-]+)\}")


def resolve_figures(page: str) -> str:
    """``{#key}`` -> a figure number, assigned in order of the legends.

    The house rule the wiki follows is that every figure is numbered in reading
    order and named in the prose, so both failures stop the build: a legend the
    text never points at, and a pointer with no legend. Same rule, same
    implementation, as `build_description_docx.resolve_figures`.
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
        raise SystemExit(f"{SOURCE.name}: pointed at but never captioned: {dangling}")
    if unmentioned := sorted(set(numbers) - mentioned):
        raise SystemExit(
            f"{SOURCE.name}: captioned but never named in the text: {unmentioned}"
        )
    return FIGURE_REF.sub(lambda m: str(numbers[m.group("key")]), page)


def strip_editorial_note(markdown: str) -> str:
    """Drop the leading 不上线 block. Absent is fine; half-present is not."""
    if "交接说明" not in markdown:
        return markdown
    stripped = _NOTE_RE.sub("", markdown, count=1)
    if "交接说明" in stripped:
        raise SystemExit(
            f"{SOURCE.name}: the 交接说明 block is there but does not end in a "
            "'---' rule, so it cannot be stripped safely."
        )
    return stripped.lstrip("\n")


def figures(markdown: str) -> list[str]:
    """Every image the draft references, in order, checked and on disk."""
    found = _IMAGE_RE.findall(markdown)
    unknown = [p for p in found if p not in ALLOWED_FIGURES]
    if unknown:
        raise SystemExit(
            f"{SOURCE.name} references figure(s) that are not in ALLOWED_FIGURES:\n  "
            + "\n  ".join(unknown)
        )
    missing = [p for p in found if not (ROOT / p).is_file()]
    if missing:
        raise SystemExit(
            "figure file(s) not on disk:\n  " + "\n  ".join(missing)
        )

    captions = [int(n) for n in re.findall(r"^\*\*Figure (\d+)\. ", markdown, re.M)]
    if captions != list(range(1, len(captions) + 1)):
        raise SystemExit(f"{SOURCE.name}: figure captions are {captions}, not 1…N in order.")
    if len(captions) != len(found):
        raise SystemExit(
            f"{SOURCE.name}: {len(found)} image(s) but {len(captions)} caption(s)."
        )
    return found


def embed_figures(html: str, placed: list[str]) -> str:
    """Inline every figure, so the page opens with no assets beside it."""
    for reference in placed:
        html = html.replace(
            f'src="{reference}"', f'src="{W.data_uri(ROOT / reference)}"'
        )
    return html


def main() -> Path:
    markdown = SOURCE.read_text(encoding="utf-8")
    markdown = strip_editorial_note(markdown)
    markdown = resolve_figures(markdown)
    placed = figures(markdown)

    body, contents = md2html.convert(markdown)

    # The page's own <h1> lives in the masthead, so drop the document title.
    body = body.split("\n", 1)[1] if body.startswith("<h1") else body

    html = TEMPLATE.read_text(encoding="utf-8")
    html = W.fill_template(
        html,
        f"{contents}\n\n<main>\n{body}\n</main>",
        eyebrow=EYEBROW,
        title=TITLE,
        standfirst=STANDFIRST,
        footer=FOOTER,
    )
    html = embed_figures(html, placed)

    OUT.write_text(html, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    out = main()
    print(f"{out}  ({out.stat().st_size // 1024} KB)")
