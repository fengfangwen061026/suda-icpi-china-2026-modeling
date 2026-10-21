"""Guard rails for the Engineering page (the modelling group's section).

Same concern as `test_wiki.py`: the draft is prose, so every number in it is a
hand-typed copy of something the code or the workbook says. These recompute the
ones the page's argument rests on. If a cycle's conclusion can be read off a
number, that number is pinned here.

The draft is handed to whoever builds the wiki, so the structural tests check
the things that would be invisible to them and wrong on the published page: a
missing stage heading, a figure path that does not exist, an equation number
pointing at a different formula.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import build_engineering_html as B
import build_wiki_html as W
from src import data as D
from src import validation as V

ROOT = Path(__file__).resolve().parent.parent
DRAFT = ROOT / "ENGINEERING_DRAFT.md"
PAGE = ROOT / "engineering_wiki.html"

CYCLES = 5


@pytest.fixture(scope="module")
def draft() -> str:
    return DRAFT.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def workbook():
    return D.load()


# -- scope: this is the modelling group's section -------------------------


def test_the_page_says_whose_engineering_record_it_is(draft: str) -> None:
    """The wet lab's own DBTL cycles are theirs. This page may use their data
    as evidence but must not present their cloning and assays as our work."""
    assert "modelling team" in draft
    for theirs in ("Golden Gate", "electroporation", "colony PCR"):
        assert theirs not in draft, f"{theirs} is a wet-lab build step"


def test_the_page_has_the_cycles_it_claims(draft: str) -> None:
    headings = re.findall(r"^## Cycle (\d+) — ", draft, re.M)
    assert [int(n) for n in headings] == list(range(1, CYCLES + 1))


# -- Cycle 1: the gate held out -------------------------------------------


def test_the_endpoint_corner_is_predicted_to_the_stated_accuracy(draft: str) -> None:
    table = V.gate_corner_holdout_table()
    endpoint = table[table.test.str.contains("24 h")]
    assert bool(endpoint.passed.all()), "all four endpoint corners should pass"

    full_on = endpoint[endpoint.held.str.startswith("D")].iloc[0]
    gap = abs(float(full_on.predicted) - float(full_on.observed))
    assert f"{gap:.2f}" == "0.05"
    assert "0.05 percentage points" in draft


def test_the_midcourse_failure_is_the_discriminating_power_check(draft: str) -> None:
    """A protocol that passes everything proves nothing, so the page leans on
    the 9 h failure. It has to still be a failure."""
    nine = V.gate_corner_holdout_table()
    nine = nine[nine.test.str.contains("9 h")]
    assert int(nine.passed.sum()) == 0
    assert f"{float(nine.ratio.max()):.3f}×" == "4.447×"
    assert "4.447×" in draft and "not one of the four corners passed" in draft


def test_the_six_hour_corners_separate_the_two_criteria(draft: str) -> None:
    """The page claims 6 h passes the SE bound while failing the ratio bound;
    that is the argument for having declared both."""
    six = V.gate_corner_holdout_table()
    six = six[six.test.str.contains("6 h")]
    assert int(six.passed.sum()) == 0
    assert (six.standard_errors.abs() <= V.SE_TOLERANCE).all()
    assert f"{float(six.ratio.max()):.3f}×" == "1.600×" and "1.600×" in draft


def test_the_held_out_total_matches_the_code(draft: str) -> None:
    summary = V.validation_layer_is_no_longer_empty()
    assert summary["held_out_predictions"] == 28
    assert "28 held-out predictions" in draft
    # The page must not call internal cross-validation external validation.
    assert summary["external_dataset"] is False
    assert "internal cross-validation" in draft


# -- Cycle 2: the tissue-site model ---------------------------------------


def test_the_lesion_floor_is_the_parameter_free_claim_the_page_says_it_is(
    draft: str,
) -> None:
    from src import lesion_size as L

    assert L.OXYGEN_PENETRATION_UM == 178.0
    assert "178 µm" in draft
    # The source is hard-wrapped, so a phrase may straddle a line break.
    flowed = re.sub(r"\s+", " ", draft)
    assert "Thomlinson & Gray" in flowed and "160–200 µm" in flowed
    # Presented as a consequence of the geometry, not of a fit.
    assert "3.2-1" in draft and "3.2-5" in draft


def test_the_withdrawn_index_and_the_one_that_replaced_it(draft: str, workbook) -> None:
    """Cycle 2 carries the reason the safety argument cannot lean on the
    effector's own selectivity, so both numbers have to be right."""
    shipped = D.selectivity_index(workbook, "GSDMD-SsrA")
    assert shipped.trustworthy
    assert f"{shipped.index:.2f}×" == "3.33×" and "3.33×" in draft
    assert f"{shipped.cancer.mean:.2f} ± {shipped.cancer.sd:.2f}" == "4.77 ± 0.80"
    assert f"{shipped.normal.mean:.2f} ± {shipped.normal.sd:.2f}" == "1.43 ± 0.49"
    assert "11.4×" in draft, "the page must name the index it withdrew"

    # ...and the detector that caught it still fires.
    assert set(D.block6_duplicated_constructs(workbook)) == {"GSDMD", "GSDMD-TAT"}


# -- Cycle 4: the dose model ----------------------------------------------


def test_the_dose_leave_one_out_matches_the_code(draft: str) -> None:
    frame = V.dose_curve_leave_one_out()
    assert len(frame) == 6 and int(frame.passed.sum()) == 6
    assert f"{float(frame.ratio.min()):.3f}×" == "0.835×"
    assert "**six**\nheld-out doses passed" in draft and "0.835×" in draft


def test_the_capacity_forecast_matches_the_code(draft: str) -> None:
    frame = V.capacity_forecast()
    assert len(frame) == 8 and int(frame.passed.sum()) == 8
    assert f"{V.capacity_forecast_bias():.4f}" == "1.0500"
    assert "**eight** 24 h" in draft and "1.0500" in draft


def test_the_lowest_dose_already_clears_the_clinical_requirement(
    draft: str, workbook
) -> None:
    """The half of Cycle 4 that does not depend on the fitted exponent."""
    at6 = workbook.killing_block(5)
    at6 = at6[at6.dose_od == 6.0]
    net = (float(at6[at6.construct == "GSDMD-SsrA"].percent.mean())
           - float(at6[at6.construct == "gfp"].percent.mean()))
    assert f"{net:.2f} %" == "2.97 %" and "2.97 %" in draft


# -- the maths is cited, never re-derived ---------------------------------


def test_every_displayed_equation_comes_from_the_equation_table(draft: str) -> None:
    """The page carries equation numbers from `EQUATIONS.md`, the project's
    single numbering source. A formula shown here must be that formula, or the
    number points at something else."""
    table = (ROOT / "EQUATIONS.md").read_text(encoding="utf-8")

    def formulas(text: str) -> dict[str, str]:
        """Tag -> the formula's structure.

        `\\text{...}` labels are annotation, and the table annotates in Chinese
        while this page is in English, so label *contents* are blanked before
        comparing. Everything else must match character for character.
        """
        out: dict[str, str] = {}
        for block in re.findall(r"\$\$(.*?)\$\$", text, re.S):
            tag = re.search(r"\\tag\{([^}]*)\}", block)
            if not tag:
                continue
            body = re.sub(r"\\text\{[^}]*\}", r"\\text{}", block[: tag.start()])
            out[tag.group(1).strip()] = re.sub(r"\s+", "", body)
        return out

    page, source = formulas(draft), formulas(table)
    assert page, "the page should display tagged equations"
    for tag, body in page.items():
        assert tag in source, f"Eq. ({tag}) is not in EQUATIONS.md"
        assert body == source[tag], f"Eq. ({tag}) does not match EQUATIONS.md"


# -- the four stages are visible, which is what the medal is scored on ----


def _cycle_bodies(draft: str) -> list[str]:
    return re.split(r"^## (?=Cycle \d+ — )", draft, flags=re.M)[1:]


def test_every_cycle_shows_design_build_test_and_learn(draft: str) -> None:
    for body in _cycle_bodies(draft):
        name = body.splitlines()[0]
        assert re.search(r"^### Design", body, re.M), name
        # The open cycle states Build/Test as one not-yet-run heading.
        assert re.search(r"^### Build", body, re.M), name
        assert re.search(r"^### (Test|Build / Test)", body, re.M), name
        assert re.search(r"^### Learn|^### Build / Test", body, re.M), name


def test_every_cycle_documents_its_next_iteration(draft: str) -> None:
    """The medal guidance asks for this by name: 'document what changes in
    design you would make for the next iteration(s)'."""
    bodies = _cycle_bodies(draft)
    assert len(bodies) == CYCLES
    missing = [b.splitlines()[0] for b in bodies if "### Next iteration" not in b]
    assert missing == []


def test_the_two_iterated_cycles_show_both_versions(draft: str) -> None:
    """At least one v1 -> v2 iteration is what the criterion asks for; the page
    claims two, and each has to actually carry both versions."""
    iterated = [b for b in _cycle_bodies(draft) if "(v2)" in b]
    assert len(iterated) == 2
    for body in iterated:
        name = body.splitlines()[0]
        assert re.search(r"^### Design \(v1\)", body, re.M), name
        assert re.search(r"^### Learn \(v1\)", body, re.M), name
        assert re.search(r"^### Design \(v2\)", body, re.M), name
        assert re.search(r"^### Learn \(v2\)", body, re.M), name


# -- the figures -----------------------------------------------------------


def _resolved(draft: str) -> str:
    """The draft as the build sees it: note stripped, figure numbers assigned."""
    return B.resolve_figures(B.strip_editorial_note(draft))


def test_every_figure_the_draft_references_exists(draft: str) -> None:
    placed = B.figures(_resolved(draft))
    assert len(placed) == 4
    assert all((ROOT / p).is_file() for p in placed)


def test_every_legend_is_named_in_the_prose_and_vice_versa(draft: str) -> None:
    """The wiki's house rule, and the one the build refuses to break: a legend
    the text never points at, or a pointer with no legend."""
    body = B.strip_editorial_note(draft)
    assert B.FIGURE_REF.search(body), "the draft should use {#key} placeholders"
    B.resolve_figures(body)  # raises if either side is dangling

    with pytest.raises(SystemExit, match="never captioned"):
        B.resolve_figures("text about (Fig. {#ghost}).\n")
    with pytest.raises(SystemExit, match="never named"):
        B.resolve_figures("**Figure {#lonely}. T.** d\n")


def test_legends_follow_the_house_format(draft: str) -> None:
    """`Figure n. Title.` bold, then a plain description: the format the wiki
    asked every page to use, matching Description_Modeling_Insert.docx."""
    # A legend sits in the same block as its image, directly under it, and the
    # source is hard-wrapped — so it is the block minus its first line.
    legends = []
    for block in _resolved(draft).split("\n\n"):
        lines = block.strip().splitlines()
        if len(lines) > 1 and lines[0].startswith("!["):
            legends.append(" ".join(" ".join(lines[1:]).split()))
    assert len(legends) == 4
    for legend in legends:
        head = re.match(r"^\*\*(Figure \d+\. .+?\.)\*\* (\S)", legend)
        assert head, f"not `**Figure n. Title.** description`: {legend[:70]}…"
        # A title, not a whole sentence of findings, and a real description.
        assert len(head.group(1).split()) <= 20, head.group(1)
        assert len(legend.split()) >= 40, "the legend should explain the figure"


def test_the_handover_note_lists_the_same_figures_the_draft_uses(draft: str) -> None:
    """The note is what the wiki builder reads to find the files, so it going
    stale would send them looking for images that are not there."""
    note = draft.split("---", 1)[0]
    for path in B.figures(_resolved(draft)):
        assert path.rsplit("outputs/figures/", 1)[-1] in note, path


def test_a_figure_path_outside_the_allowed_set_stops_the_build() -> None:
    with pytest.raises(SystemExit, match="ALLOWED_FIGURES"):
        B.figures("![x](outputs/figures/not_a_real_figure.png)\n**Figure 1.** c\n")


def test_out_of_order_captions_stop_the_build() -> None:
    body = (
        "![a](outputs/figures/fig4_4_cluster.png)\n**Figure 1. One.** d\n\n"
        "![b](outputs/figures/fig4_6_dose_requirement.png)\n**Figure 3. Three.** d\n"
    )
    with pytest.raises(SystemExit, match="not 1"):
        B.figures(body)


def test_an_uncaptioned_figure_stops_the_build() -> None:
    with pytest.raises(SystemExit, match="caption"):
        B.figures("![a](outputs/figures/fig4_4_cluster.png)\n\nprose\n")


# -- the build -------------------------------------------------------------


def test_the_handover_note_is_stripped(draft: str) -> None:
    assert "交接说明" in draft, "the note is still in the source"
    assert "交接说明" not in B.strip_editorial_note(draft)
    assert B.strip_editorial_note(draft).startswith("# Engineering")


def test_a_note_block_with_no_closing_rule_stops_the_build() -> None:
    with pytest.raises(SystemExit, match="交接说明"):
        B.strip_editorial_note("# T\n\n> **交接说明** no rule after this\n")


def test_an_unfilled_placeholder_stops_the_build() -> None:
    with pytest.raises(SystemExit, match="NEWTOKEN"):
        W.fill_template("<p>{{NEWTOKEN}}</p>", "body")


def test_the_standfirst_counts_the_cycles_the_page_actually_has() -> None:
    """The masthead lives in the build script, far from the draft, so it is the
    easiest thing to leave behind -- it survived one scope rewrite already."""
    assert "Five cycles" in B.STANDFIRST
    assert "modelling team" in B.STANDFIRST
    assert B.TITLE != W.TITLE, "the two pages must not share a masthead"


def test_the_built_page_is_self_contained(draft: str) -> None:
    out = B.main()
    html = out.read_text(encoding="utf-8")
    assert "{{" not in html
    assert "交接说明" not in html
    assert 'src="outputs/' not in html, "figures must be inlined"
    assert html.count("data:image/png;base64,") == len(B.figures(_resolved(draft)))
    assert "<title>Engineering</title>" in html
    assert html.rstrip().endswith("</html>")


def test_every_figure_on_the_page_is_captioned() -> None:
    html = PAGE.read_text(encoding="utf-8")
    figures = re.findall(r"<figure>.*?</figure>", html, re.S)
    assert len(figures) == 4
    assert all("<figcaption>" in figure for figure in figures)


def test_the_page_keeps_every_dbtl_stage_visible() -> None:
    """A judge has to be able to find all four stages on the rendered page."""
    html = PAGE.read_text(encoding="utf-8")
    for stage in ("Design", "Build", "Test", "Learn"):
        assert re.search(rf"<h3[^>]*>{stage}", html), f"{stage} is not a heading"


# -- the bilingual review copy --------------------------------------------
#
# ENGINEERING_DRAFT_ZH.md mirrors an older English draft and is not read by any
# build. A stale review copy is worse than none, so it must either still cover
# the English or say in its own first lines that it does not.

BILINGUAL = ROOT / "ENGINEERING_DRAFT_ZH.md"
STALE_BANNER = "⚠️ 本对照版已过期"


def test_the_review_copy_either_covers_the_english_or_declares_itself_stale() -> None:
    bilingual = BILINGUAL.read_text(encoding="utf-8")
    if STALE_BANNER in bilingual:
        pytest.skip("review copy is marked stale; retranslate to re-enable")

    note = re.compile(r"^> \*\*(交接|稿件|审稿)说明.*?^---$\n+", re.S | re.M)
    body = note.sub("", bilingual)
    missing = [
        block.strip()
        for block in note.sub("", DRAFT.read_text(encoding="utf-8")).split("\n\n")
        if block.strip()
        and not block.strip().startswith(("|", "```", "#", "$$", "!", ">"))
        and block.strip() not in body
    ]
    assert missing == [], missing[:2]


def test_the_build_never_reads_the_review_copy() -> None:
    source = Path(B.__file__).read_text(encoding="utf-8")
    assert "ENGINEERING_DRAFT_ZH" not in source
    assert B.SOURCE.name == "ENGINEERING_DRAFT.md"
