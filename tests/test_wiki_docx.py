"""Guard rails for the Word build.

Pandoc's OMML writer drops or mangles several LaTeX constructs **silently** --
no warning, just a wrong-looking equation. Each rule that compensates for one
of those is pinned here, because the failure mode is a formula that is quietly
wrong in a document going to a reviewer.

The transforms are pure functions, so these run without pandoc installed; the
one test that needs the binary skips when it is absent.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

import build_wiki_docx as B

ROOT = Path(__file__).resolve().parent.parent
DRAFT = ROOT / "WIKI_DRAFT.md"


@pytest.fixture(scope="module")
def draft() -> str:
    return DRAFT.read_text(encoding="utf-8")


# -- equation numbers ----------------------------------------------------


def test_every_equation_keeps_its_number() -> None:
    """Pandoc drops \\tag entirely, so the number has to move into the maths."""
    out = B.rewrite_equation_numbers(r"$$a = b \tag{3.1-4}$$")
    assert r"\tag" not in out
    assert r"\mathrm{(3.1\text{-}4)}" in out
    assert B.EM in out, "the gap before the number has to be an em space"


def test_the_number_hyphen_is_not_a_minus_sign() -> None:
    """Bare '-' inside maths is typeset as a binary operator: '3.1 - 4'."""
    out = B.rewrite_equation_numbers(r"$$a \tag{V-1}$$")
    assert r"\text{-}" in out
    assert r"(V-1)" not in out


def test_the_draft_has_no_tag_left_after_rewriting(draft: str) -> None:
    assert r"\tag" not in B.rewrite_equation_numbers(draft)


# -- accents and brackets ------------------------------------------------


@pytest.mark.parametrize(
    "source, expected",
    [
        # \bar renders as an acute accent, not a macron
        (r"$\bar z$", r"$\overline{z}$"),
        (r"$$K=\bar y_{24}$$", r"$$K=\overline{y}_{24}$$"),
        (r"$$\bar\Psi$$", r"$$\overline{\Psi}$$"),
        # an accent takes one token, so the subscript stays outside
        (r"$$\bar f_O(R)$$", r"$$\overline{f}_O(R)$$"),
        # square brackets survive only as \left[ ... \right]
        (r"$$G=\Big[x\Big]^{n}$$", r"$$G=\left[x\right]^{n}$$"),
        (r"$$\mathrm{Var}[\log R]$$", r"$$\mathrm{Var}\left[\log R\right]$$"),
        (r"$n_Q\in[1,4]$", r"$n_Q\in\left[1,4\right]$"),
        # already-correct maths is left alone
        (r"$$x=\left[y\right]$$", r"$$x=\left[y\right]$$"),
    ],
)
def test_constructs_pandoc_gets_wrong_are_rewritten(source: str, expected: str) -> None:
    assert B.fix_accents_and_brackets(source) == expected


def test_a_row_spacing_argument_is_not_a_bracket() -> None:
    r"""``\\[4pt]`` sets row spacing in an array; rewriting it breaks the array."""
    source = r"$$\begin{array}{l} a=1\\[4pt] b=2 \end{array}$$"
    assert B.fix_accents_and_brackets(source) == source


def test_no_bare_bracket_or_bar_survives_the_draft(draft: str) -> None:
    fixed = B.fix_accents_and_brackets(draft)
    for body in re.findall(r"\$\$(.+?)\$\$", fixed, re.S):
        stripped = re.sub(r"\\\\\[[^\]]*\]", "", body)      # row spacing
        stripped = stripped.replace(r"\left[", "").replace(r"\right]", "")
        assert "[" not in stripped and "]" not in stripped, body[:80]
        assert not re.search(r"\\bar\b", body), body[:80]


# -- the six hand-written rewrites ---------------------------------------


def test_each_word_safe_rewrite_still_matches_the_draft(draft: str) -> None:
    """If an equation is edited in the Markdown, its Word rewrite must be
    revisited -- so a missing tag is a build failure, not a silent stale copy."""
    for tag in B.WORD_SAFE_EQUATIONS:
        B._equation(draft, tag)  # raises SystemExit if the tag is gone


def test_the_rewrites_remove_what_pandoc_cannot_carry(draft: str) -> None:
    out = B.apply_word_safe_equations(draft)
    for tag, _ in B.WORD_SAFE_EQUATIONS.items():
        body = B._equation(out, tag).group(1)
        assert "&" not in body, f"({tag}) still has an alignment marker"
        assert r"\underbrace" not in body, f"({tag}) still has an underbrace"
        assert not re.search(r"\\text\{[^}]*[()][^}]*\}", body), \
            f"({tag}) still has parens inside \\text"


def test_overset_labels_sit_above_a_parenthesised_base() -> None:
    """With a bare fraction as the base the label lands between numerator and
    denominator instead of above the term."""
    for latex in B.WORD_SAFE_EQUATIONS.values():
        for base in re.findall(r"\\overset\{[^}]*\}\{(.)", latex):
            assert base == "\\", "an overset base must start with \\left("


# -- end to end ----------------------------------------------------------


@pytest.mark.skipif(
    not (shutil.which("pandoc") or Path(__import__("os").environ.get("PANDOC", "")).is_file()),
    reason="pandoc not installed",
)
def test_the_built_document_has_its_equations_tables_and_figures() -> None:
    import zipfile

    out = B.main()
    with zipfile.ZipFile(out) as doc:
        body = doc.read("word/document.xml").decode("utf-8")
        media = [n for n in doc.namelist() if n.startswith("word/media/")]
        settings = doc.read("word/settings.xml").decode("utf-8")

    figures = list((ROOT / "outputs" / "figures").glob("*.png"))
    assert body.count("<m:oMath") > 400, "equations should be native Word objects"
    source = (ROOT / "WIKI_DRAFT.md").read_text(encoding="utf-8")
    tables = len(re.findall(r"^\|---", source, re.M))
    assert body.count("<w:tbl>") == tables
    assert len(media) == len(figures)
    assert "<m:t>" not in body, "every equation run must preserve its spaces"
    assert "<m:t>&amp;</m:t>" not in body, "a literal & leaked into an equation"
    assert "updateFields" in settings, "Word must fill the contents page on open"
