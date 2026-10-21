"""Module 2.2 results, pinned."""

from __future__ import annotations

import numpy as np
import pytest

from src import data as D
from src import gate as G


@pytest.fixture(scope="module")
def wb() -> D.Workbook:
    return D.load()


# -- which timepoints can carry the test ---------------------------------


def test_three_hour_block_cannot_be_inverted(wb):
    """Corner A is 0 % positive at 3 h, which has no finite probit."""
    assert G.invertible_timepoints(wb) == [6.0, 9.0, 24.0]
    with pytest.raises(ValueError, match="no finite probit"):
        G.gate_test(wb, 3.0)


# -- the headline: multiplicative at the endpoint ------------------------


def test_endpoint_interaction_is_indistinguishable_from_zero(wb):
    test = G.gate_test(wb, 24.0)
    assert test.interaction == pytest.approx(-0.011, abs=0.01)
    assert test.interaction_se == pytest.approx(0.157, abs=0.01)
    assert test.multiplicative


def test_each_input_gives_the_same_effect_at_both_levels_of_the_other(wb):
    """The substance of multiplicativity, stated as two agreements."""
    test = G.gate_test(wb, 24.0)
    assert test.oxygen_effect_no_lactate == pytest.approx(
        test.oxygen_effect_with_lactate, rel=0.02
    )
    assert test.lactate_effect_normoxic == pytest.approx(
        test.lactate_effect_hypoxic, rel=0.02
    )


def test_the_conclusion_does_not_depend_on_sigma(wb):
    """sigma scales the contrast and its error equally, so the t ratio is fixed."""
    test = G.gate_test(wb, 24.0)
    baseline = test.interaction_t
    for sigma in (0.5, 1.0, 2.53, 10.0):
        scaled = G.GateTest(
            test.time_h,
            test.oxygen_effect_no_lactate * sigma,
            test.oxygen_effect_with_lactate * sigma,
            test.lactate_effect_normoxic * sigma,
            test.lactate_effect_hypoxic * sigma,
            test.interaction * sigma,
            test.interaction_se * sigma,
        )
        assert scaled.interaction_t == pytest.approx(baseline, rel=1e-12)
        assert scaled.multiplicative == test.multiplicative


# -- the paradox it resolves ---------------------------------------------


def test_raw_intensity_looks_strongly_sub_multiplicative(wb):
    paradox = G.raw_intensity_paradox(wb, 24.0)
    assert paradox["oxygen_fold"] == pytest.approx(16.2, abs=0.1)
    assert paradox["lactate_fold"] == pytest.approx(170.3, abs=0.5)
    assert paradox["dual_fold"] == pytest.approx(226.6, abs=0.5)
    assert paradox["multiplicative_prediction"] == pytest.approx(2768, abs=5)
    assert paradox["shortfall"] == pytest.approx(12.2, abs=0.1)


# -- 9.23's published folds are sigma-conditional ------------------------


def test_sigma_2_53_reproduces_the_9_23_numbers(wb):
    """Confirms the reconstruction of what 9.23's 'ceiling inversion' was."""
    test = G.gate_test(wb, 24.0)
    assert test.fold(test.oxygen_effect_no_lactate) == pytest.approx(17.4, abs=0.3)
    assert test.fold(test.oxygen_effect_with_lactate) == pytest.approx(16.9, abs=0.5)
    assert test.fold(test.lactate_effect_normoxic) == pytest.approx(645, abs=15)
    assert test.fold(test.lactate_effect_hypoxic) == pytest.approx(627, abs=15)


def test_the_folds_swing_by_orders_of_magnitude_across_plausible_sigma(wb):
    """Why they must never be quoted as measurements."""
    table = G.sigma_sensitivity(G.gate_test(wb, 24.0)).set_index("sigma")
    assert table.loc[1.0, "lactate_fold_C_over_A"] < 20
    assert table.loc[4.0, "lactate_fold_C_over_A"] > 20_000
    ratio = table.loc[4.0, "lactate_fold_C_over_A"] / table.loc[1.0, "lactate_fold_C_over_A"]
    assert ratio > 1_000


def test_exactly_one_sigma_row_is_flagged_as_matching(wb):
    table = G.sigma_sensitivity(G.gate_test(wb, 24.0))
    assert int(table["matches_9_23"].sum()) == 1


# -- the new finding 9.23 did not report ---------------------------------


def test_multiplicativity_fails_mid_transition_at_nine_hours(wb):
    """A significant positive interaction at 9 h, absent at the endpoint.

    Consistent with the settled finding that hypoxia acts on the *rate* rather
    than the level: a rate effect shows up as apparent synergy during the
    transient and vanishes once both corners have saturated.
    """
    nine = G.gate_test(wb, 9.0)
    assert nine.interaction == pytest.approx(1.135, abs=0.02)
    assert not nine.multiplicative
    assert nine.interaction_t > 3.0


def test_six_hour_interaction_is_marginal_but_passes(wb):
    six = G.gate_test(wb, 6.0)
    assert six.interaction == pytest.approx(0.284, abs=0.02)
    assert six.multiplicative
    assert six.interaction_t < 2.0


def test_table_covers_every_invertible_timepoint(wb):
    table = G.gate_test_table(wb)
    assert list(table["time_h"]) == [6.0, 9.0, 24.0]
    assert list(table["multiplicative"]) == [True, False, True]


def test_the_sigma_table_translates_to_a_checkable_cv() -> None:
    """1.1's sigma sweep prints the implied CV, which is the checkable column.

    sigma is not identifiable from this dataset, so the folds that depend on it
    are reported as a sweep. The CV column exists so a reader (or our own wet
    lab) can judge whether the sigma that reproduces last cycle's published
    folds is a physically plausible population spread -- it implies ~2,450 %.
    """
    from pathlib import Path

    import numpy as np

    from src import data as D, gate as G

    sweep = G.sigma_sensitivity(G.gate_test(D.load(), time_h=24.0)).set_index("sigma")
    assert float(sweep.loc[1.0, "lactate_fold_C_over_A"]) == pytest.approx(12.90, abs=0.01)
    assert float(sweep.loc[4.0, "lactate_fold_C_over_A"]) == pytest.approx(27659.8, rel=1e-4)
    assert bool(sweep.loc[G.SIGMA_MATCHING_9_23, "matches_9_23"])

    def cv_percent(sigma: float) -> float:
        return float(np.sqrt(np.exp(sigma**2) - 1.0) * 100.0)

    assert cv_percent(1.0) == pytest.approx(131, abs=1)
    assert cv_percent(G.SIGMA_MATCHING_9_23) == pytest.approx(2452, abs=1)

    page = (Path(__file__).resolve().parent.parent / "WIKI_DRAFT.md").read_text(
        encoding="utf-8"
    )
    for printed in ("131 %", "2,452 %", "298,000 %"):
        assert printed in page, printed
