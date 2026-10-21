"""Guard rails for the wiki page and the Markdown it is built from.

The point of these is drift. `WIKI_DRAFT.md` is prose, so nothing stops a number
in it from falling behind the code, a figure reference from pointing at a file
that was renamed, or an equation citation from naming a formula that no longer
exists. Each of those has a cheap mechanical check, so each of them gets one.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import build_wiki_html as B
from src import equation_numbers as E
from src import md2html
from src import parameters as P

ROOT = Path(__file__).resolve().parent.parent
DRAFT = ROOT / "WIKI_DRAFT.md"
EQUATIONS = ROOT / "EQUATIONS.md"
MODULES = sorted(ROOT.glob("MODULE_*.md"))


@pytest.fixture(scope="module")
def draft() -> str:
    return DRAFT.read_text(encoding="utf-8")


# -- the page cannot hold a stale parameter ------------------------------


def test_parameter_table_matches_the_generated_one(draft: str) -> None:
    """Every generated row appears verbatim in the draft.

    src/parameters.py already checks config/parameters.csv against the live
    code, so this closes the last link in the chain code -> CSV -> page.
    """
    assert B.check_parameter_table(draft) == []


def test_the_build_refuses_a_stale_parameter_table() -> None:
    """The check is load-bearing, so it has to actually fail when it should."""
    assert B.check_parameter_table("no table here at all")


# -- references resolve --------------------------------------------------


def test_every_referenced_figure_exists(draft: str) -> None:
    referenced = set(re.findall(r"outputs/figures/[\w.]+\.png", draft))
    assert referenced, "the page should carry figures"
    missing = [path for path in referenced if not (ROOT / path).is_file()]
    assert missing == []


def _equation_tags() -> set[str]:
    text = EQUATIONS.read_text(encoding="utf-8")
    tags: set[str] = set()
    for raw in re.findall(r"\\tag\{([^}]*)\}", text):
        # a tag may name several equations at once, e.g. "3.3-5,6" or "6-6, 6-7"
        head = raw.split("-")[0].strip()
        for part in raw.split(","):
            part = part.strip()
            tags.add(part if "-" in part else f"{head}-{part}")
    return tags


@pytest.mark.parametrize("source", [DRAFT, *MODULES], ids=lambda p: p.name)
def test_every_cited_equation_exists(source: Path) -> None:
    """A citation of Eq. (x.y-n) must name a formula EQUATIONS.md defines."""
    text = source.read_text(encoding="utf-8")
    cited: set[str] = set()
    for pattern in (r"式\(([\dV][\d.]*-[\d,\s]+)\)", r"Eq\.?\s+([\dV][\d.]*-[\d,\s]+)"):
        for raw in re.findall(pattern, text):
            head = raw.split("-")[0].strip()
            for part in raw.split(","):
                part = part.strip()
                if part:
                    cited.add(part if "-" in part else f"{head}-{part}")
    assert cited, f"{source.name} cites no equations"
    assert sorted(cited - _equation_tags()) == []


# -- the converter leaves maths and code alone ---------------------------


def test_display_math_survives_verbatim() -> None:
    body, _ = md2html.convert(r"$$a_\text{x} \cdot \frac{1}{2}$$")
    assert r"$$a_\text{x} \cdot \frac{1}{2}$$" in body
    assert "<em>" not in body


def test_an_equation_number_is_laid_out_beside_the_formula() -> None:
    """KaTeX's own \\tag is absolutely positioned against a box the width of the
    column, so a formula wider than the column scrolls out from under its own
    number. The number has to be a sibling in the flex row instead."""
    body, _ = md2html.convert(r"$$a = b \tag{3.1-4}$$")
    assert '<div class="eq-math">$$a = b$$</div>' in body
    assert '<span class="eq-tag">(3.1-4)</span>' in body
    assert r"\tag" not in body


def test_an_untagged_equation_gets_no_number() -> None:
    body, _ = md2html.convert(r"$$x = y$$")
    assert '<div class="eq"><div class="eq-math">$$x = y$$</div></div>' in body


def test_no_equation_on_the_page_still_carries_a_katex_tag() -> None:
    """Scoped to the equations themselves; the stylesheet mentions \\tag in a
    comment explaining why we do not use it."""
    html = (ROOT / "modeling_wiki.html").read_text(encoding="utf-8")
    formulas = re.findall(r'<div class="eq-math">(.*?)</div>', html, re.S)
    assert len(formulas) > 60
    assert [f for f in formulas if "\\tag" in f] == []
    assert html.count('class="eq-tag"') > 40


def test_inline_math_is_not_touched_by_emphasis_rules() -> None:
    body, _ = md2html.convert(r"before $x_*y^*z$ after")
    assert r"$x_*y^*z$" in body
    assert "<em>" not in body


def test_a_pipe_inside_maths_does_not_split_a_table_cell() -> None:
    body, _ = md2html.convert("| a | b |\n|---|---|\n| $\\{x \\mid x>0\\}$ | c |\n")
    assert body.count("<td>") == 2
    # the formula survives intact; > is HTML-escaped, which the browser hands
    # back to KaTeX as the original character
    assert r"$\{x \mid x&gt;0\}$" in body


def test_tables_blockquotes_and_lists_render() -> None:
    body, _ = md2html.convert(
        "| h |\n|---|\n| v |\n\n> quoted\n\n- one\n- two\n\n1. first\n"
    )
    assert "<table>" in body and "<th>h</th>" in body and "<td>v</td>" in body
    assert "<blockquote><p>quoted</p></blockquote>" in body
    assert "<ul><li>one</li><li>two</li></ul>" in body
    assert "<ol><li>first</li></ol>" in body


def test_a_blockquote_does_not_swallow_the_table_after_it() -> None:
    body, _ = md2html.convert("> quoted\n\n| h |\n|---|\n| v |\n")
    assert body.index("</blockquote>") < body.index("<table>")


def test_an_image_with_a_following_line_becomes_a_captioned_figure() -> None:
    body, _ = md2html.convert("![alt](a.png)\n**Figure 1.** What it shows.\n")
    assert '<figure><img src="a.png" alt="alt">' in body
    assert "<figcaption><strong>Figure 1.</strong> What it shows.</figcaption>" in body
    assert "<p><img" not in body


def test_an_image_without_a_caption_still_becomes_a_figure() -> None:
    body, _ = md2html.convert("![alt](a.png)\n\nA separate paragraph.\n")
    assert "<figure><img" in body and "<figcaption>" not in body
    assert "<p>A separate paragraph.</p>" in body


def test_an_image_does_not_absorb_the_heading_after_it() -> None:
    body, _ = md2html.convert("![alt](a.png)\n## Next section\n")
    assert "<figcaption>" not in body
    assert "<h2" in body


def test_the_template_lays_equation_numbers_out_as_siblings() -> None:
    """Checked here because the symptom is visual: if `.eq` ever goes back to
    sizing the formula box to the column, wide formulas scroll under their
    number and nothing in the markup looks wrong."""
    template = (ROOT / "wiki_template.html").read_text(encoding="utf-8")
    assert ".eq-math" in template and ".eq-tag" in template
    assert "min-width: 0" in template, "the formula box must be allowed to shrink"


def test_the_template_lets_prose_columns_wrap() -> None:
    """Cells are nowrap for numbers; the sentence columns have to wrap or the
    widest tables sit behind a horizontal scrollbar."""
    template = (ROOT / "wiki_template.html").read_text(encoding="utf-8")
    assert "td:last-child" in template and "white-space: normal" in template


def test_tables_use_the_class_the_template_styles() -> None:
    """The template's rule is `.tablewrap`; cells are nowrap, so a mismatch
    silently drops the horizontal scroll and wide tables run off the page."""
    body, _ = md2html.convert("| h |\n|---|\n| v |\n")
    assert 'class="tablewrap"' in body
    template = (ROOT / "wiki_template.html").read_text(encoding="utf-8")
    assert ".tablewrap" in template


def test_every_figure_on_the_page_is_captioned() -> None:
    html = (ROOT / "modeling_wiki.html").read_text(encoding="utf-8")
    figures = re.findall(r"<figure>.*?</figure>", html, re.S)
    assert len(figures) == len(list((ROOT / "outputs" / "figures").glob("*.png")))
    assert all("<figcaption>" in figure for figure in figures)


def test_figure_captions_are_numbered_in_reading_order() -> None:
    """A figure added mid-page renumbers the rest; the captions have to follow."""
    source = (ROOT / "WIKI_DRAFT.md").read_text(encoding="utf-8")
    numbers = [int(n) for n in re.findall(r"^\*\*Figure (\d+)\.\*\*", source, re.M)]
    assert numbers == list(range(1, len(numbers) + 1))


def test_headings_get_stable_slug_ids() -> None:
    body, contents = md2html.convert("## The $n_Q$ problem, part 2\n")
    assert 'id="the-n-q-problem-part-2"' in body
    assert 'href="#the-n-q-problem-part-2"' in contents


def test_repeated_subheadings_get_distinct_ids() -> None:
    """The page uses "Model" and "Results" in every section on purpose."""
    body, _ = md2html.convert("### Results\n\n### Results\n\n### Results\n")
    assert 'id="results"' in body
    assert 'id="results-2"' in body
    assert 'id="results-3"' in body


def test_two_headings_differing_only_in_maths_do_not_collide() -> None:
    body, _ = md2html.convert("## Bound on $n_Q$\n\n## Bound on $K_m$\n")
    assert 'id="bound-on-n-q"' in body
    assert 'id="bound-on-k-m"' in body


def test_html_in_prose_is_escaped_not_injected() -> None:
    body, _ = md2html.convert("a < b & c > d\n")
    assert "&lt; b &amp; c &gt;" in body


# -- the page builds -----------------------------------------------------


def test_the_built_page_is_self_contained() -> None:
    out = B.main()
    html = out.read_text(encoding="utf-8")
    assert "{{CONTENT}}" not in html
    assert 'src="outputs/figures/' not in html, "figures must be inlined"
    assert html.count("data:image/png;base64,") == len(
        set(re.findall(r"outputs/figures/[\w.]+\.png", DRAFT.read_text(encoding="utf-8")))
    )
    assert "katex" in html, "the page needs KaTeX to render its equations"
    assert html.rstrip().endswith("</html>")


# --- sequential equation numbering -----------------------------------------
#
# The source tags every equation with its `EQUATIONS.md` number and the build
# swaps in (1)…(N). Two things can go wrong silently: a cross-reference naming
# an equation the page never displays, and the Word and HTML builds disagreeing
# about which number is which.


def test_compound_tags_expand_to_their_parts() -> None:
    assert E.expand("3.1-1,2") == ["3.1-1", "3.1-2"]
    assert E.expand("6-6, 6-7") == ["6-6", "6-7"]
    assert E.expand("3.4-2 – 3.4-4") == ["3.4-2", "3.4-3", "3.4-4"]
    assert E.expand("V-2") == ["V-2"]


def test_one_display_gets_one_number() -> None:
    numbers, index = E.collect(r"$$a \tag{3.1-1,2}$$ $$b \tag{3.1-4}$$")
    assert [n for n, _ in index] == [1, 2]
    assert numbers == {"3.1-1": 1, "3.1-2": 1, "3.1-4": 2}


def test_references_follow_the_renumbering() -> None:
    source = r"See Eq. 3.1-4. $$a \tag{3.1-1,2}$$ $$b \tag{3.1-4}$$ and Eq. 3.1-1"
    out, _, unknown = E.renumber(source)
    assert unknown == []
    assert "See Eq. (2)." in out
    assert out.endswith("and Eq. (1)")


def test_a_reference_to_an_undisplayed_equation_is_reported() -> None:
    _, _, unknown = E.renumber(r"Eq. 9.9-9 $$a \tag{3.1-1}$$")
    assert unknown == ["9.9-9"]


def test_the_page_displays_every_equation_it_cites() -> None:
    source = (ROOT / "WIKI_DRAFT.md").read_text(encoding="utf-8")
    _, _, unknown = E.renumber(source)
    assert unknown == []


def test_no_repository_tag_survives_into_the_page() -> None:
    html = (ROOT / "modeling_wiki.html").read_text(encoding="utf-8")
    assert not re.search(r"Eqs?\.\s*\d+\.\d+-\d+", html)


def test_the_equation_index_is_written_to_the_repo_not_the_page() -> None:
    """The mapping belongs where EQUATIONS.md is, not in the deliverable.

    A repository tag means nothing to a reader of the published page, so the
    57-row table was moved out of 6.1 on 2026-10-14. What has to stay true is
    that the mapping still exists and still covers every equation -- otherwise
    the traceability claim in "How to read this page" is empty.
    """
    from src import equation_numbers as E

    source = (ROOT / "WIKI_DRAFT.md").read_text(encoding="utf-8")
    _, index, _ = E.renumber(source)

    written = E.INDEX_PATH.read_text(encoding="utf-8")
    assert written.count("\n| (") == len(index)
    assert f"| ({len(index)}) |" in written
    assert "3.1-4" in written, "the repository tags are the point of the file"

    assert "## 6.1 Equation index" not in source
    assert "outputs/equation_index.md" in source, "the page must say where it is"

    html = (ROOT / "modeling_wiki.html").read_text(encoding="utf-8")
    assert "EQUATIONS.md" in html


# --- §1.0, the wet lab's own data ------------------------------------------
#
# §1.0 is the only place on the page that counts the experiments themselves.
# A workbook change that moved a well count would leave it quietly wrong, so
# the counts are read back out of `src/data.py` rather than trusted.


def test_the_wet_lab_block_table_counts_the_measurements_that_exist() -> None:
    from src import data

    workbook = data.load()
    source = (ROOT / "WIKI_DRAFT.md").read_text(encoding="utf-8")
    killing = workbook.killing
    counts = {
        "growth": len(workbook.growth),
        "intensity": len(workbook.reporter_intensity),
        "positive": len(workbook.reporter_positive),
        "block5": int((killing.block == 5).sum()),
        "block6": int((killing.block == 6).sum()),
    }
    section = source.split("## 1.0 ", 1)[1].split("## 1.1 ", 1)[0]
    for name, count in counts.items():
        assert f"**{count}**" in section, f"{name}: {count} measurements is not in §1.0"
    assert f"**{sum(counts.values())} measurements" in section


# --- numbered citations ----------------------------------------------------
#
# The source writes `[@key]`; the build numbers them. Two failure modes matter:
# a marker with no reference behind it, and a reference nothing points at.


def test_citations_are_numbered_in_order_of_first_appearance() -> None:
    from src import references as R

    refs = {
        k: R.Reference(k, "A", "T", "V", "2000", "1", "2026-01-01")
        for k in ("alpha", "beta")
    }
    out, ordered = R.apply("sees [@beta] then [@alpha] then [@beta]", refs)
    assert out == "sees [1] then [2] then [1]"
    assert [entry.reference.key for entry in ordered] == ["beta", "alpha"]
    assert [entry.number for entry in ordered] == [1, 2]


def test_several_keys_in_one_marker_render_as_a_list() -> None:
    from src import references as R

    refs = {
        k: R.Reference(k, "A", "T", "V", "2000", "1", "2026-01-01")
        for k in ("alpha", "beta")
    }
    out, _ = R.apply("both [@alpha; @beta]", refs)
    assert out == "both [1, 2]"


def test_a_citation_group_split_across_lines_is_still_one_group() -> None:
    """§2.2 wraps `[@thomlinson1955; @worth2022]` over a line break."""
    from src import references as R

    refs = {
        k: R.Reference(k, "A", "T", "V", "2000", "1", "2026-01-01")
        for k in ("alpha", "beta")
    }
    out, entries = R.apply("text [@alpha;\n@beta].", refs)
    assert out == "text [1, 2]."
    assert [entry.number for entry in entries] == [1, 2]


def test_the_markers_a_build_emits_can_be_hyperlinks() -> None:
    from src import references as R

    refs = {"alpha": R.Reference("alpha", "A", "T", "V", "2000", "1", "2026-01-01")}
    out, _ = R.apply(
        "see [@alpha]",
        refs,
        marker=lambda ms: f"[{ms[0].number}](#{R.entry_anchor(ms[0].number)})",
    )
    assert out == "see [1](#ref-1)"


def test_only_the_first_appearance_is_the_one_section_8_links_back_to() -> None:
    from src import references as R

    refs = {
        k: R.Reference(k, "A", "T", "V", "2000", "1", "2026-01-01")
        for k in ("alpha", "beta")
    }
    out, _ = R.apply(
        "one [@alpha] two [@beta; @alpha] three [@beta]",
        refs,
        marker=lambda ms: "".join(
            f"{m.number}{'*' if m.first else ''}" for m in ms
        ),
    )
    assert out == "one 1* two 2*1 three 2"


def test_tighten_closes_the_gap_a_raised_number_hangs_off() -> None:
    """A superscript belongs on the word, not a space away from it."""
    from src import references as R

    refs = {"alpha": R.Reference("alpha", "A", "T", "V", "2000", "1", "2026-01-01")}
    marker = lambda ms: f"^{ms[0].number}^"  # noqa: E731

    out, _ = R.apply("resection [@alpha], and", refs, marker=marker, tighten=True)
    assert out == "resection^1^, and"

    # a line wrap in the source is the same gap, written differently
    out, _ = R.apply("standard\n[@alpha]: see", refs, marker=marker, tighten=True)
    assert out == "standard^1^: see"

    # but a marker that opens a block has nothing to hang off
    out, _ = R.apply("text\n\n[@alpha] opens", refs, marker=marker, tighten=True)
    assert out == "text\n\n^1^ opens"

    # and without it the source spacing is left exactly as written
    out, _ = R.apply("resection [@alpha], and", refs, marker=marker)
    assert out == "resection ^1^, and"


def test_a_parenthesised_section_aside_becomes_a_raised_mark() -> None:
    from src import references as R

    source = (
        "# 1. Calibration\n\n## 1.1 Gate\n\n## 4.1 Test\n\n"
        "it forbids extrapolating (§1.1, §4.1).\n"
    )
    out, used = R.apply_sections(source, mark=lambda ns: "^" + ",".join(ns) + "^")
    assert out.endswith("extrapolating^1.1,4.1^.\n")
    assert used == ["1.1", "4.1"]


def test_a_section_the_prose_uses_as_a_word_is_left_alone() -> None:
    """Only an aside can be raised; `§4.1 turns this` is the sentence itself."""
    from src import references as R

    source = (
        "## 1.3 Growth\n\n## 2.3 Lumen\n\n## 4.1 Test\n\n"
        "§4.1 turns this into a test, and §2.3 says the same. See (the shape "
        "§1.3 established) and (§2.3 says so).\n"
    )
    out, used = R.apply_sections(source, mark=lambda ns: "RAISED")
    assert "RAISED" not in out
    assert used == []


def test_a_section_mark_with_no_such_section_stops_the_build() -> None:
    from src import references as R

    with pytest.raises(R.ReferenceError, match="§9.9"):
        R.apply_sections("## 1.1 Gate\n\ntext (§9.9).\n", mark=lambda ns: "x")


def test_an_author_list_ending_in_et_al_keeps_one_full_stop() -> None:
    from src import references as R

    reference = R.Reference("k", "Smith J, et al.", "T", "V", "2000", "1", "2026-01-01")
    assert ".. " not in reference.rendered()
    assert reference.rendered().startswith("Smith J, et al. T. ")


def test_a_citation_with_no_reference_stops_the_build() -> None:
    from src import references as R

    with pytest.raises(R.ReferenceError, match="ghost"):
        R.apply("[@ghost]", {})


def test_a_reference_nothing_cites_stops_the_build() -> None:
    from src import references as R

    refs = {"idle": R.Reference("idle", "A", "T", "V", "2000", "1", "2026-01-01")}
    with pytest.raises(R.ReferenceError, match="idle"):
        R.apply("no citations here", refs)


def test_every_reference_is_cited_and_every_citation_resolves() -> None:
    from src import references as R

    source = (ROOT / "WIKI_DRAFT.md").read_text(encoding="utf-8")
    source += (ROOT / "config" / "parameters.csv").read_text(encoding="utf-8")
    _, ordered = R.apply(source)
    assert ordered, "the page cites nothing at all"


def test_every_reference_records_the_date_it_was_checked() -> None:
    from src import references as R

    for reference in R.load().values():
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", reference.checked), reference.key
        assert reference.locator, reference.key


def test_no_raw_citation_marker_survives_into_the_page() -> None:
    html = (ROOT / "modeling_wiki.html").read_text(encoding="utf-8")
    assert "[@" not in html
    assert "<h1" in html and "References" in html


# --- the page holds no retyped copy of a computed table ---------------------
#
# `WIKI_DRAFT.md` is prose, so every number in it is a hand-typed copy of
# something the code produced. The parameter census is already guarded that
# way; these two tables are the ones a parameter change silently invalidates,
# as the 2026-10-14 sensor-prior swap demonstrated.


def test_the_tissue_results_table_matches_the_code() -> None:
    from src import data as D, tissue

    source = (ROOT / "WIKI_DRAFT.md").read_text(encoding="utf-8")
    arms = tissue.TissueAxis(
        anoxic_repression=10.0, glucose_repression=10.0
    ).arms(D.load()).set_index("label")

    for label, printed in {
        "Colonic mucosa": "21.85×",
        "Tumour rim": "48.66×",
        "Colon lumen (dysbiosis/UC)": "23.1×",
    }.items():
        value = float(arms.loc[label, "total_ratio"])
        digits = len(printed.split(".")[1].rstrip("×"))
        assert f"{value:.{digits}f}×" == printed, (label, value)
        assert printed in source, f"{label}: {printed} is not on the page"


def test_the_escalation_table_matches_the_code() -> None:
    from src import data as D, dose

    source = (ROOT / "WIKI_DRAFT.md").read_text(encoding="utf-8")
    frame = dose.escalation_erodes_margin(D.load()).set_index("radius_um")

    for radius, (escalation, left) in {
        400.0: ("1.76×", "12.44×"),
        250.0: ("3.19×", "6.86×"),
        180.0: ("4.33×", "5.05×"),
        150.0: ("4.95×", "4.41×"),
    }.items():
        assert f"{float(frame.loc[radius, 'total_escalation']):.2f}×" == escalation
        assert f"{float(frame.loc[radius, 'mucosa_margin_left']):.2f}×" == left
        assert escalation in source and left in source, radius


def test_the_decisions_summary_agrees_with_the_sections_it_summarises() -> None:
    """The opening table is the only page a judge is certain to read.

    It restates six numbers that live in five different chapters, so it is the
    most likely place for the page to contradict itself after a parameter
    change. Recompute each from the code.
    """
    from src import data as D, dose, lesion_size as L, tissue, validation as V

    source = (ROOT / "WIKI_DRAFT.md").read_text(encoding="utf-8")
    # Split on the next heading: the table's own rule rows contain "---".
    summary = source.split("## What the model decided", 1)[1].split(
        "## What we set out to answer", 1
    )[0]
    workbook = D.load()

    bottleneck = tissue.weakest_link(
        workbook, anoxic_repression=10.0, glucose_repression=10.0
    )
    assert f"{float(bottleneck['total_ratio']):.2f}×" == "21.85×"
    assert "21.85×" in summary and "Colonic mucosa" in str(bottleneck["label"])

    assert L.OXYGEN_PENETRATION_UM == 178.0
    assert "178 µm" in summary

    holdout = V.gate_corner_holdout_table()
    worst_fail = float(holdout[~holdout["passed"]]["ratio"].max())
    assert f"{worst_fail:.1f}×" == "4.4×" and "4.4×" in summary

    escalation = dose.escalation_erodes_margin(workbook).set_index("radius_um")
    assert f"{float(escalation.loc[150.0, 'total_escalation']):.2f}×" == "4.95×"
    assert f"{float(escalation.loc[150.0, 'mucosa_margin_left']):.2f}×" == "4.41×"
    assert "4.95×" in summary and "4.41×" in summary
