"""Sequential equation numbers for the published page.

`WIKI_DRAFT.md` tags every equation with its `EQUATIONS.md` number -- `3.1-4`,
`V-2` -- so the Markdown source stays traceable to the function that evaluates
it. A reader of the page has no use for that scheme: it starts at 2.2, skips,
and carries the chapter numbering of a repository they cannot see.

So the source keeps the repository tags and the *build* renumbers them, 1..N in
reading order, rewriting every ``Eq. 3.1-4`` in the prose to match. The mapping
is not thrown away -- :func:`index_table` emits it as an appendix table, so the
page still says which repository equation each number is.

One display gets one number, even when it carries several repository tags:
``\\tag{3.1-1,2}`` is a single numbered display, and both `3.1-1` and `3.1-2`
resolve to it.

Used by `build_wiki_html.py` and `build_wiki_docx.py`, which must agree.
"""

from __future__ import annotations

import re
from pathlib import Path

#: A repository tag: `3.1-4`, `6-3`, `V-2`.
TAG = r"[0-9]+(?:\.[0-9]+)?-[0-9]+|V-[0-9]+"

_TAG_RE = re.compile(r"\\tag\*?\{([^}]*)\}")
_REF_RE = re.compile(
    rf"\bEqs?\.\s*(?P<tags>(?:{TAG})(?:\s*,\s*(?:{TAG}))*)(?P<trail>\.?)"
)
ROOT = Path(__file__).resolve().parent.parent

_PART_RE = re.compile(rf"^(?P<prefix>[0-9]+(?:\.[0-9]+)?|V)-(?P<number>[0-9]+)$")


def expand(tag_text: str) -> list[str]:
    """`"3.4-2 - 3.4-4"` -> `["3.4-2", "3.4-3", "3.4-4"]`.

    Three shorthands appear in the source: a comma list (`6-6, 6-7`), a bare
    continuation that inherits the prefix (`3.1-1,2`), and an en-dash range
    (`3.4-2 - 3.4-4`). Anything else comes back as a single opaque tag, which
    is what we want -- an unrecognised tag still gets a number, it just does not
    resolve a cross-reference.
    """
    tags: list[str] = []
    prefix = ""
    for piece in (p.strip() for p in tag_text.split(",")):
        if not piece:
            continue
        bounds = re.split(r"\s*[-\u2013\u2014]\s+", piece)
        if len(bounds) == 2 and all(_PART_RE.match(b) for b in bounds):
            start, end = (_PART_RE.match(b) for b in bounds)
            if start["prefix"] == end["prefix"]:
                prefix = start["prefix"]
                tags += [
                    f"{prefix}-{n}"
                    for n in range(int(start["number"]), int(end["number"]) + 1)
                ]
                continue
        match = _PART_RE.match(piece)
        if match:
            prefix = match["prefix"]
            tags.append(piece)
        elif piece.isdigit() and prefix:
            tags.append(f"{prefix}-{piece}")
        else:
            tags.append(piece)
    return tags


def collect(markdown: str) -> tuple[dict[str, int], list[tuple[int, list[str]]]]:
    """Walk the tags in reading order; return tag -> number, and the index."""
    numbers: dict[str, int] = {}
    index: list[tuple[int, list[str]]] = []
    for position, match in enumerate(_TAG_RE.finditer(markdown), start=1):
        tags = expand(match.group(1))
        index.append((position, tags))
        for tag in tags:
            numbers.setdefault(tag, position)
    return numbers, index


def _rewrite_references(markdown: str, numbers: dict[str, int]) -> tuple[str, list[str]]:
    """``Eq. 3.1-4`` -> ``Eq. (12)``; several tags collapse or list."""
    unknown: list[str] = []

    def replace(match: re.Match[str]) -> str:
        tags = [t.strip() for t in match["tags"].split(",")]
        missing = [t for t in tags if t not in numbers]
        if missing:
            unknown.extend(missing)
            return match.group(0)
        seen: list[int] = []
        for tag in tags:
            if numbers[tag] not in seen:
                seen.append(numbers[tag])
        word = "Eq." if len(seen) == 1 else "Eqs."
        if len(seen) == 1:
            body = f"({seen[0]})"
        elif len(seen) == 2:
            body = f"({seen[0]}) and ({seen[1]})"
        else:
            body = ", ".join(f"({n})" for n in seen[:-1]) + f" and ({seen[-1]})"
        return f"{word} {body}{match['trail']}"

    return _REF_RE.sub(replace, markdown), unknown


def renumber(markdown: str) -> tuple[str, list[tuple[int, list[str]]], list[str]]:
    """Return the markdown with sequential numbers, the index, and any misses."""
    numbers, index = collect(markdown)
    markdown, unknown = _rewrite_references(markdown, numbers)
    counter = iter(n for n, _ in index)
    markdown = _TAG_RE.sub(lambda _: f"\\tag{{{next(counter)}}}", markdown)
    return markdown, index, sorted(set(unknown))


#: Where the page-number -> repository-tag mapping is written.
INDEX_PATH = ROOT / "outputs" / "equation_index.md"


def index_table(index: list[tuple[int, list[str]]]) -> str:
    """The mapping table: page number against repository tag."""
    rows = "\n".join(
        f"| ({number}) | {', '.join(tags)} |" for number, tags in index
    )
    return (
        "| Page | `EQUATIONS.md` |\n|---|---|\n" + rows
    )


def write_index(index: list[tuple[int, list[str]]], path: Path | None = None) -> Path:
    """Write the mapping to the repository rather than into the page.

    The repository tag is only meaningful to somebody holding `EQUATIONS.md`,
    which a reader of the published page is not. Printing 57 rows of it in the
    deliverable cost two pages and told that reader nothing; the people who
    need it are us, and we have the repo. So the build emits it here and the
    page carries one sentence pointing at it.
    """
    path = path or INDEX_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Equation index (generated -- do not edit)\n\n"
        "`WIKI_DRAFT.md` tags each equation with its `EQUATIONS.md` number; the\n"
        "build renumbers them (1)...(N) in reading order. This is the mapping, so\n"
        "a number on the published page can still be traced to the function that\n"
        "evaluates it. Regenerated by `build_wiki_html.py` and\n"
        "`build_wiki_docx.py`.\n\n" + index_table(index) + "\n",
        encoding="utf-8",
    )
    return path
