"""Cross-references for the published page: citations, and section marks.

Both are set the same way -- a small mark raised to the upper right of the word
it belongs to, linked to what it names -- so both live here, and both builds
render them from the same rules.

The source writes a citation as ``[@zuniga2021]``, keyed to a row of
`config/references.csv`. The *build* turns those keys into ``[1]``, ``[2]``, …
in order of first appearance and emits the matching reference list into §8.
Hand-written numbers are not allowed, for the same reason the equation numbers
are generated: inserting one citation would otherwise renumber the rest of the
page by hand.

A marker is set the way a journal sets one -- a small number raised to the
upper right, not a bracket in the line -- and the numbers are cross-linked in
both directions:

* the raised number in the text is a link down to its entry in §8;
* that entry's own leading number is a link back to the first place the page
  cited it.

Two failures are made loud rather than silent:

* a key the Markdown cites but `references.csv` does not define -- the build
  stops, because a dangling citation is worse than none;
* a row `references.csv` defines that *no page of the project* cites -- the
  build stops too, because an uncited reference usually means a citation was
  dropped in an edit. The check is made against every page in `SOURCES`, not
  only the one being built, since the table is shared between them.

Every row carries a ``checked`` date. That column is the claim that a human
opened the paper and confirmed the bibliographic details, not that a search
engine returned them.

A section mark is a parenthesis holding nothing but section numbers --
``(§2.1)``, ``(§1.1, §4.1)`` -- and it is raised the same way, which takes the
aside out of the line and makes it a link. The many ``§`` that the prose uses
as words ("§4.1 turns this from a fit into a test", "every dose number in
§3.4") are left exactly as written: they are parts of sentences, not asides.

Used by `build_wiki_html.py` and `build_wiki_docx.py`, which must agree on the
numbers and the citation format but render the links in their own markup.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / "config" / "references.csv"

#: Every source the project cites from. A row counts as used when *any* of
#: them cites it, so a reference only the Description page needs does not stop
#: the Model page's build -- while a row no page cites still stops both.
SOURCES = (
    ROOT / "WIKI_DRAFT.md",
    ROOT / "DESCRIPTION_DRAFT.md",
    ROOT / "config" / "parameters.csv",
)

#: ``[@key]``, or ``[@a; @b]`` for several at once. The source separates a
#: citation from the word it follows by a space, or by a line wrap; `tighten`
#: closes that gap, because a raised number hangs off its own word.
_CITE_RE = re.compile(
    r"(?P<gap>[ \t]*\n?[ \t]*)\[@(?P<keys>[A-Za-z0-9_]+(?:\s*;\s*@[A-Za-z0-9_]+)*)\]"
)

#: ``(§2.1)`` or ``(§1.1, §4.1)`` -- a parenthesis holding section numbers and
#: nothing else. ``(§2.3 says the same about the decay half)`` is a sentence in
#: brackets, not an aside, so it has to fall outside this.
_SECTION_REF_RE = re.compile(
    r"(?P<gap>[ \t]*\n?[ \t]*)"
    r"\((?P<sections>§\d+(?:\.\d+)*(?:,[ \t]*\n?[ \t]*§\d+(?:\.\d+)*)*)\)"
)

#: ``## 2.3 The colon lumen`` -> its number and the rest of the heading.
_HEADING_RE = re.compile(r"^#{1,6}[ \t]+((\d+(?:\.\d+)*)\.?[ \t]+.*?)[ \t]*$", re.M)


class ReferenceError(RuntimeError):
    """A citation key with no row, or a row nothing cites."""


@dataclass(frozen=True)
class Reference:
    key: str
    authors: str
    title: str
    venue: str
    year: str
    locator: str
    checked: str

    def rendered(self) -> str:
        """Author–title–venue, the way a wiki page prints it."""
        return format_entry(self)


@dataclass(frozen=True)
class Entry:
    """A reference and the number the page gives it."""

    number: int
    reference: Reference


@dataclass(frozen=True)
class Marker:
    """One number inside one in-text citation group.

    `first` marks the earliest appearance of that reference on the page. It is
    the one §8's leading number links back to, so a reader who has jumped down
    to an entry can get back to where the argument first leant on it.
    """

    number: int
    first: bool


def format_entry(
    reference: Reference,
    emphasis: tuple[str, str] = ("*", "*"),
    escape: Callable[[str], str] = lambda text: text,
) -> str:
    """The one citation format, shared by every renderer.

    `emphasis` is the pair that italicises the venue and `escape` makes a field
    safe for the target markup, so HTML and Word cannot drift apart in style.
    """
    opened, closed = emphasis

    def sentence(field: str) -> str:
        # "… et al." and "Smith J" must both end in exactly one full stop.
        return escape(field) + ("" if field.endswith(".") else ".")

    return (
        f"{sentence(reference.authors)} {sentence(reference.title)} "
        f"{opened}{escape(reference.venue)}{closed} {escape(reference.year)}; "
        f"{escape(reference.locator)}"
    )


def load(path: Path | None = None) -> dict[str, Reference]:
    with (path or DEFAULT_PATH).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    references = {row["key"]: Reference(**row) for row in rows}
    if len(references) != len(rows):
        raise ReferenceError("config/references.csv has a duplicate key")
    return references


def _keys(match: re.Match[str]) -> list[str]:
    return [piece.strip().lstrip("@") for piece in match.group("keys").split(";")]


def cited(markdown: str) -> set[str]:
    """Every key `markdown` cites, in no particular order."""
    return {key for match in _CITE_RE.finditer(markdown) for key in _keys(match)}


def cited_anywhere(sources: tuple[Path, ...] | None = None) -> set[str]:
    """Every key any page of the project cites.

    A source that is not there yet is skipped rather than failing: the check
    this feeds exists to catch a dropped citation, and a missing file would
    turn that into a stream of false alarms.
    """
    keys: set[str] = set()
    for path in SOURCES if sources is None else sources:
        if path.exists():
            keys |= cited(path.read_text(encoding="utf-8"))
    return keys


def _default_marker(markers: list[Marker]) -> str:
    return "[" + ", ".join(str(m.number) for m in markers) + "]"


def _gap(markdown: str, match: re.Match[str], tighten: bool) -> str:
    """The whitespace a raised mark keeps in front of itself.

    It keeps none where the gap separates the mark from a word on the same
    paragraph -- that is the whole point of raising it. A gap that begins a
    line is indentation, and a mark that opens a block has nothing in front of
    it to hang off, so both are left alone.
    """
    start = match.start("gap")
    if tighten and start > 0 and markdown[start - 1] != "\n":
        return ""
    return match.group("gap")


def apply(
    markdown: str,
    references: dict[str, Reference] | None = None,
    marker: Callable[[list[Marker]], str] = _default_marker,
    tighten: bool = False,
) -> tuple[str, list[Entry]]:
    """``[@key]`` -> ``[n]``; returns the markdown and the numbered entries.

    `marker` renders one citation group, so a build that can set the markers in
    superscript and link them says so here rather than patching the text
    afterwards. Each :class:`Marker` knows whether it is that reference's first
    appearance, which is the one §8's number links back to.

    `tighten` closes the space the source leaves in front of a citation, which
    is what a raised number wants and a bracketed one does not.
    """
    references = references if references is not None else load()

    order: list[str] = []
    missing: list[str] = []
    for match in _CITE_RE.finditer(markdown):
        for key in _keys(match):
            if key not in references:
                missing.append(key)
            elif key not in order:
                order.append(key)
    if missing:
        raise ReferenceError(
            "cited but not in config/references.csv: " + ", ".join(sorted(set(missing)))
        )

    elsewhere = cited_anywhere()
    unused = [key for key in references if key not in order and key not in elsewhere]
    if unused:
        raise ReferenceError(
            "in config/references.csv but never cited: " + ", ".join(unused)
        )

    numbers = {key: n for n, key in enumerate(order, start=1)}
    seen: set[int] = set()

    def replace(match: re.Match[str]) -> str:
        markers = []
        for key in _keys(match):
            number = numbers[key]
            markers.append(Marker(number, number not in seen))
            seen.add(number)
        return _gap(markdown, match, tighten) + marker(markers)

    entries = [Entry(numbers[key], references[key]) for key in order]
    return _CITE_RE.sub(replace, markdown), entries


def entry_anchor(number: int) -> str:
    """``2`` -> ``ref-2``, the id an in-text marker points at."""
    return f"ref-{number}"


def citation_anchor(number: int) -> str:
    """``2`` -> ``cite-2``, the id §8's leading number points back at."""
    return f"cite-{number}"


def numbered(entry: Entry) -> str:
    """``1.`` -- the leading number §8 prints, and links back from."""
    return f"{entry.number}."


# --- section marks ---------------------------------------------------------


def section_anchor(number: str) -> str:
    """``2.3`` -> ``sec-2-3``, the id a section mark points at."""
    return "sec-" + number.replace(".", "-")


def headings(markdown: str) -> dict[str, str]:
    """Section number -> the whole heading text, for the first of each number."""
    found: dict[str, str] = {}
    for match in _HEADING_RE.finditer(markdown):
        found.setdefault(match.group(2), match.group(1))
    return found


def apply_sections(
    markdown: str,
    mark: Callable[[list[str]], str],
    tighten: bool = True,
) -> tuple[str, list[str]]:
    """``(§2.1)`` -> a raised, linked mark; returns it and the sections used.

    A mark pointing at a section the page does not have is a dead link that no
    reader would report, so it stops the build instead.
    """
    known = headings(markdown)
    used: list[str] = []
    missing: list[str] = []

    def replace(match: re.Match[str]) -> str:
        numbers = re.findall(r"\d+(?:\.\d+)*", match.group("sections"))
        for number in numbers:
            if number not in known:
                missing.append(number)
            elif number not in used:
                used.append(number)
        return _gap(markdown, match, tighten) + mark(numbers)

    out = _SECTION_REF_RE.sub(replace, markdown)
    if missing:
        raise ReferenceError(
            "section marks with no such section: "
            + ", ".join("§" + n for n in sorted(set(missing)))
        )
    return out, used
