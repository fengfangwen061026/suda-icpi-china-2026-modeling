"""Guard rails for the modelling section of the Description page.

Same worry as `test_wiki.py`, with one more: this section is not a page of our
own but an insert into the wet lab's Description page, so besides its figures
pointing at renamed files and its numbers drifting away from the Model page, it
can also start repeating what the surrounding sections already say, or restart
its reference numbering on top of theirs. Each of those gets a cheap check.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import build_description_docx as B
from src import references as R

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "DESCRIPTION_DRAFT.md"


def page_text() -> str:
    """What sits between the fences -- the part that goes on the wiki."""
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    opens = [i for i, line in enumerate(lines) if line.strip() == B.OPEN]
    closes = [i for i, line in enumerate(lines) if line.strip() == B.CLOSE]
    assert len(opens) == len(closes) == 1 and opens[0] < closes[0]
    return "\n".join(lines[opens[0] + 1 : closes[0]])


def legends() -> list[str]:
    """Each figure legend, joined back into the one paragraph it is."""
    found, block = [], None
    for line in page_text().splitlines() + [""]:
        if line.lstrip().startswith("**Figure "):
            block = [line.strip()]
        elif block is not None:
            if line.strip():
                block.append(line.strip())
            else:
                found.append(" ".join(block))
                block = None
    return found


def test_the_page_text_is_fenced_off_from_the_internal_notes() -> None:
    page = page_text()
    # An insert, not a page: it opens at the section level the host page uses.
    assert page.lstrip().startswith("## 1.5 ")
    # The handover note and the reference audit are both internal, and both
    # name the wiki editor; neither may end up inside the fences.
    assert "不要发布" not in page


@pytest.mark.parametrize(
    "theirs",
    [
        "Escherichia coli Nissle 1917",  # their 1.2 chooses the chassis
        "pyroptosis",                    # their 1.3/1.4 and Design 2.3
        "phosphatidylserine",            # their 1.4 and Design 2.3.2
        "quorum-sensing signal",         # their 1.3 and Design 2.2.1
    ],
)
def test_the_insert_does_not_restate_the_surrounding_sections(theirs: str) -> None:
    """The wet lab's 1.1-1.4 already carry the background, chassis and circuit."""
    assert theirs.lower() not in page_text().lower()


def test_every_figure_the_page_shows_exists() -> None:
    paths = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", page_text())
    assert paths, "the page shows no figures at all"
    for path in paths:
        assert (ROOT / path).exists(), path


def test_every_figure_is_followed_by_a_house_style_legend() -> None:
    """`Figure n. Title.` in bold, then the description unbolded."""
    lines = page_text().splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^!\[[^\]]*\]\([^)]+\)\s*$", line.strip()):
            # A legend that describes the whole figure wraps over several
            # source lines; it is one paragraph, down to the blank line.
            block = []
            for following in lines[index + 1 :]:
                if not following.strip():
                    break
                block.append(following.strip())
            legend = " ".join(block)
            assert legend.startswith("**Figure {#"), legend
            # The bold stops after the title sentence; the rest is plain.
            title, _, rest = legend.partition("**")[2].partition("**")
            assert title.rstrip().endswith("."), title
            assert "**" not in rest


def test_a_legend_stays_the_length_of_a_legend() -> None:
    """A legend explains how to read the figure; it does not retell the data.

    The cap is loose enough for a two-panel figure and tight enough to catch
    the failure we actually made once: listing every plotted value in prose.
    """
    for legend in legends():
        assert len(legend.split()) <= 130, legend[:80]


def test_each_figure_is_named_in_the_prose() -> None:
    page = page_text()
    prose = "\n".join(
        line for line in page.splitlines()
        if not line.lstrip().startswith(("**Figure ", "!["))
    )
    for key in re.findall(r"\*\*Figure \{#([a-z0-9_-]+)\}", page):
        assert f"(Fig. {{#{key}}})" in prose, key


def test_figure_numbers_continue_the_host_pages_own_figures() -> None:
    resolved = B.resolve_figures(page_text())
    assert "{#" not in resolved
    assert f"**Figure {B.FIRST_FIGURE}. " in resolved
    assert f"(Fig. {B.FIRST_FIGURE})" in resolved
    for taken in range(1, B.FIRST_FIGURE):
        assert f"(Fig. {taken})" not in resolved


def test_a_figure_the_prose_never_names_stops_the_build() -> None:
    with pytest.raises(SystemExit, match="orphan"):
        B.resolve_figures("**Figure {#orphan}. A title.** Described here.")


def test_a_pointer_with_no_legend_stops_the_build() -> None:
    with pytest.raises(SystemExit, match="ghost"):
        B.resolve_figures("as shown there (Fig. {#ghost})")


def test_citations_are_keys_and_not_hand_written_numbers() -> None:
    page = page_text()
    assert "[@" in page
    # `[1]` in the prose would renumber by hand the moment a citation moves.
    stripped = re.sub(r"\[@[^\]]+\]", "", page)
    assert not re.search(r"\[\d+(?:,\s*\d+)*\]", stripped)
    assert B.LIST_MARKER in page


def test_every_citation_resolves_and_the_list_is_generated() -> None:
    resolved = B.resolve_citations(page_text())
    assert B.LIST_MARKER not in resolved
    assert "[@" not in resolved


def test_the_numbering_continues_the_host_pages_own_references() -> None:
    """Their Description page ends at [5]; ours may not start again at [1]."""
    resolved = B.resolve_citations(page_text())
    first = B.FIRST_REFERENCE
    assert f"[{first}]" in resolved
    assert re.search(rf"^\[{first}\] ", resolved, re.M)
    for taken in range(1, first):
        assert f"[{taken}]" not in resolved


def test_a_row_only_one_page_cites_does_not_stop_another_pages_build(
    tmp_path, monkeypatch
) -> None:
    """The reference table is shared, so the uncited-row check must be too."""
    elsewhere = tmp_path / "OTHER_PAGE.md"
    elsewhere.write_text("as shown earlier [@solo]", encoding="utf-8")
    monkeypatch.setattr(R, "SOURCES", (elsewhere,))

    refs = {"solo": R.Reference("solo", "A", "T", "V", "2000", "1", "2026-01-01")}
    out, entries = R.apply("this page cites nothing", refs)
    assert out == "this page cites nothing" and entries == []


def test_a_row_no_page_cites_still_stops_the_build() -> None:
    refs = {"nobody": R.Reference("nobody", "A", "T", "V", "2000", "1", "2026-01-01")}
    with pytest.raises(R.ReferenceError, match="nobody"):
        R.apply("no citations here", refs)


@pytest.mark.parametrize(
    "number",
    ["21.85", "178", "2.2 %", "4.95", "4.41", "87–228", "0.87–2.28"],
)
def test_the_numbers_quoted_here_are_the_model_pages_numbers(number: str) -> None:
    """The Description page restates the Model page; it must not restate it wrong."""
    assert number in (ROOT / "WIKI_DRAFT.md").read_text(encoding="utf-8")
