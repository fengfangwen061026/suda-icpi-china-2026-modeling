"""Build a self-contained wiki page from WIKI_DRAFT.md.

`WIKI_DRAFT.md` is the single source of the page's text. This script renders it
into `wiki_template.html` (head, CSS, masthead, footer) and embeds every figure
as a data URI, so the output opens anywhere with no assets beside it.

It also checks that the parameter table in the Markdown still matches the table
generated from `config/parameters.csv`, and refuses to build if it does not —
`src/parameters.py` already checks that CSV against the live code, so the chain
from code to published page cannot hold a stale number.

Run from the project root:

    .venv/bin/python build_wiki_html.py
"""

from __future__ import annotations

import base64
import html
import re
import sys
from pathlib import Path

from src import equation_numbers as E
from src import references as R
from src import md2html
from src import parameters as P

ROOT = Path(__file__).resolve().parent
FIGURES = ROOT / "outputs" / "figures"
SOURCE = ROOT / "WIKI_DRAFT.md"
TEMPLATE = ROOT / "wiki_template.html"
OUT = ROOT / "modeling_wiki.html"

#: The template carries the stylesheet for both pages, so its masthead and
#: footer are placeholders. These are this page's; `build_engineering_html.py`
#: fills the same four with its own.
EYEBROW = "iGEM &middot; Dry lab"
TITLE = "Modeling"
STANDFIRST = (
    "An engineered <em>E.&nbsp;coli</em> Nissle 1917 circuit for pMMR/MSS colorectal\n"
    "  cancer, gated on hypoxia, lactate and quorum. Two questions: where other than a tumour does it\n"
    "  switch on, and what dose would a therapeutic effect require."
)
FOOTER = (
    "Figures generated from the model code in <code>src/</code>; every figure on this page is\n"
    "  reproducible with <code>python -m src.plots</code>."
)


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def check_parameter_table(markdown: str) -> list[str]:
    """Rows present in the generated table but missing from the Markdown."""
    generated = [
        line.strip()
        for line in P.markdown_table().splitlines()
        if line.strip().startswith("| `")
    ]
    return [row for row in generated if row not in markdown]


#: Citation markers and the §8 list are placed as tokens, not as markup: the
#: Markdown converter escapes raw HTML, so the anchors go in after conversion.
#: A token carries the whole group -- ``@@CITE:1*,2@@`` -- because the raised
#: numbers share one ``<sup>``; the star marks a reference's first appearance.
LIST_TOKEN = "@@REFERENCES@@"
_CITE_TOKEN_RE = re.compile(r"@@CITE:([\d*,]+)@@")
_SEC_TOKEN_RE = re.compile(r"@@SEC:([\d.,]+)@@")


def apply_sections(markdown: str) -> tuple[str, dict[str, str]]:
    """``(§2.1)`` -> a token, plus the id `md2html` will give each heading.

    The converter derives a heading id from its text, so the marks have to
    derive them the same way; `link_sections` then refuses to write a page
    where any of them missed.
    """
    markdown, used = R.apply_sections(
        markdown, mark=lambda numbers: "@@SEC:" + ",".join(numbers) + "@@"
    )
    found = R.headings(markdown)
    return markdown, {number: md2html.slug(found[number]) for number in used}


def apply_references(markdown: str) -> tuple[str, list[R.Entry]]:
    """``[@key]`` -> a token per group, and a token where §8's list goes."""
    markdown, entries = R.apply(
        markdown,
        marker=lambda markers: "@@CITE:" + ",".join(
            f"{m.number}*" if m.first else str(m.number) for m in markers
        ) + "@@",
        tighten=True,
    )
    if "<!--REFERENCES-->" not in markdown:
        raise SystemExit(f"{SOURCE.name} has lost its <!--REFERENCES--> marker.")
    return markdown.replace("<!--REFERENCES-->", LIST_TOKEN), entries


def citation_markup(group: str) -> str:
    """``1*,2`` -> the raised, linked numbers that stand in the text."""
    links = []
    for item in group.split(","):
        number = int(item.rstrip("*"))
        # The first appearance is also the target §8's own number links back to.
        ident = f' id="{R.citation_anchor(number)}"' if item.endswith("*") else ""
        links.append(
            f'<a{ident} href="#{R.entry_anchor(number)}">{number}</a>'
        )
    return '<sup class="cite">' + ",".join(links) + "</sup>"


def reference_list(entries: list[R.Entry]) -> str:
    """§8's list: the number is written out, so that it can be the link back."""
    def escape(text: str) -> str:
        return html.escape(text, quote=False)

    items = [
        '<p class="reference" id="{}"><a class="refnum" href="#{}">{}</a> {}</p>'
        .format(
            R.entry_anchor(entry.number),
            R.citation_anchor(entry.number),
            R.numbered(entry),
            R.format_entry(entry.reference, ("<em>", "</em>"), escape),
        )
        for entry in entries
    ]
    return '<div class="references">\n' + "\n".join(items) + "\n</div>"


def section_markup(group: str, sections: dict[str, str]) -> str:
    """``1.1,4.1`` -> the raised, linked section marks that stand in the text."""
    links = [
        f'<a href="#{sections[number]}">§{number}</a>' for number in group.split(",")
    ]
    return '<sup class="xref">' + ",".join(links) + "</sup>"


def link_citations(body: str, entries: list[R.Entry], sections: dict[str, str]) -> str:
    """Turn the tokens into markup, and refuse to ship a page missing any."""
    if f"<p>{LIST_TOKEN}</p>" not in body:
        raise SystemExit("the reference-list token did not survive conversion.")
    body = body.replace(f"<p>{LIST_TOKEN}</p>", reference_list(entries))
    body = _CITE_TOKEN_RE.sub(lambda m: citation_markup(m.group(1)), body)
    body = _SEC_TOKEN_RE.sub(lambda m: section_markup(m.group(1), sections), body)
    if "@@CITE" in body or "@@SEC" in body or LIST_TOKEN in body:
        raise SystemExit("a cross-reference token survived into the page.")

    dangling = [
        f"§{number} -> #{ident}"
        for number, ident in sorted(sections.items())
        if f'id="{ident}"' not in body
    ]
    if dangling:
        raise SystemExit(
            "section marks point at ids the page does not have: "
            + ", ".join(dangling)
        )

    # Every number in §8 links back somewhere; the target is an id only the
    # first marker carries, so a dropped marker has to be loud.
    dangling = [
        entry.number
        for entry in entries
        if f'id="{R.citation_anchor(entry.number)}"' not in body
    ]
    if dangling:
        raise SystemExit(
            "§8 numbers link back to markers the page does not have: "
            + ", ".join(str(n) for n in dangling)
        )
    return body


def apply_equation_numbers(markdown: str) -> str:
    """Repository tags out, (1)…(N) in, mapping out to the repo."""
    markdown, index, unknown = E.renumber(markdown)
    if unknown:
        raise SystemExit(
            f"{SOURCE.name} refers to equation(s) it never displays: "
            + ", ".join(unknown)
        )
    E.write_index(index)
    return markdown


def fill_template(
    html: str,
    content: str,
    *,
    eyebrow: str = EYEBROW,
    title: str = TITLE,
    standfirst: str = STANDFIRST,
    footer: str = FOOTER,
) -> str:
    """Put a page's masthead, footer and body into the shared shell.

    Shared because the stylesheet is: two templates would be two copies of 350
    lines of CSS, and the second copy goes stale the first time anyone touches
    the first. Refuses to return a page with a placeholder still in it.
    """
    for token, value in (
        ("{{EYEBROW}}", eyebrow),
        ("{{TITLE}}", title),
        ("{{STANDFIRST}}", standfirst),
        ("{{FOOTER}}", footer),
        ("{{CONTENT}}", content),
    ):
        html = html.replace(token, value)
    leftover = re.findall(r"\{\{[A-Z]+\}\}", html)
    if leftover:
        raise SystemExit("template placeholder not filled: " + ", ".join(leftover))
    return html


def embed_figures(html: str) -> str:
    """Replace every outputs/figures reference with an inline data URI."""
    for figure in sorted(FIGURES.glob("*.png")):
        html = html.replace(f'src="outputs/figures/{figure.name}"',
                            f'src="{data_uri(figure)}"')
    return html


def main() -> Path:
    markdown = SOURCE.read_text(encoding="utf-8")

    missing = check_parameter_table(markdown)
    if missing:
        print(
            f"{SOURCE.name} parameter table is stale: {len(missing)} row(s) differ "
            f"from config/parameters.csv. First:\n  {missing[0]}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    markdown = apply_equation_numbers(markdown)
    markdown, sections = apply_sections(markdown)
    markdown, entries = apply_references(markdown)

    body, contents = md2html.convert(markdown)

    # The page's own <h1> lives in the masthead, so drop the document title.
    body = body.split("\n", 1)[1] if body.startswith("<h1") else body

    body = link_citations(body, entries, sections)

    html = TEMPLATE.read_text(encoding="utf-8")
    html = fill_template(html, f"{contents}\n\n<main>\n{body}\n</main>")
    html = embed_figures(html)

    OUT.write_text(html, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    out = main()
    print(f"{out}  ({out.stat().st_size // 1024} KB)")
