"""The validation layer: held-out prediction, four tests.

These pin both the passes and the one deliberate failure. The 9 h corner
holdout must fail -- if every test passed, the protocol would have no power and
the passes would mean nothing.
"""

from __future__ import annotations

import numpy as np
import pytest

from src import data as D
from src import dose as X
from src import gate as G
from src import validation as V


@pytest.fixture(scope="module")
def wb():
    return D.load()


# -- the protocol itself ---------------------------------------------------


def test_tolerances_are_declared_not_chosen_afterwards():
    """Both tolerances are module constants, so they are visible in review."""
    assert V.RATIO_TOLERANCE == 0.25
    assert V.SE_TOLERANCE == 2.0


def test_heldout_verdict_uses_both_criteria():
    close = V.HeldOut("t", "h", predicted=1.0, observed=1.0, standard_errors=0.1)
    assert close.passed
    # inside the ratio band but far out in standard errors
    assert not V.HeldOut("t", "h", predicted=1.05, observed=1.0, standard_errors=9.0).passed
    # inside standard errors but far out in ratio
    assert not V.HeldOut("t", "h", predicted=2.0, observed=1.0, standard_errors=0.1).passed


def test_the_layer_reports_what_it_cannot_do(wb):
    record = V.validation_layer_is_no_longer_empty(wb)
    assert record["is_empty"] is False
    assert record["held_out_predictions"] >= 24
    assert record["external_dataset"] is False
    assert "one workbook" in record["kind"]
    assert "shared by the whole workbook" in record["cannot_detect"]


# -- 1. the dose-kill curve ------------------------------------------------


def test_every_held_out_dose_is_predicted(wb):
    frame = V.dose_curve_leave_one_out(wb)
    assert len(frame) == 6
    assert frame["passed"].all()


def test_held_out_dose_predictions_are_close(wb):
    frame = V.dose_curve_leave_one_out(wb)
    assert frame["ratio"].between(0.8, 1.2).all()
    assert frame["standard_errors"].abs().max() < V.SE_TOLERANCE


def test_the_dose_holdout_is_a_real_holdout(wb):
    """Each fit sees two points, so it cannot be interpolating the third."""
    frame = V.dose_curve_leave_one_out(wb)
    held = set(frame[frame.test.str.endswith("gfp")]["held"])
    assert held == {"6 OD", "8 OD", "10 OD"}


# -- 2. the gate corners ---------------------------------------------------


def test_endpoint_corners_predict_each_other(wb):
    frame = V.gate_corner_holdout(wb, time_h=V.ENDPOINT_H)
    assert len(frame) == 4
    assert frame["passed"].all()
    assert frame["ratio"].sub(1.0).abs().max() < 0.03


def test_the_full_on_corner_is_predicted_to_a_twentieth_of_a_percent(wb):
    """Corner D, predicted from three corners the fit was given instead."""
    frame = V.gate_corner_holdout(wb, time_h=V.ENDPOINT_H).set_index("held")
    row = frame.loc["D (1% - 20mM)"]
    assert row["predicted"] == pytest.approx(98.13, abs=0.05)
    assert row["observed"] == pytest.approx(98.08, abs=0.05)


def test_midcourse_corners_do_not(wb):
    """The 9 h interaction is real, so the holdout must reject it."""
    frame = V.gate_corner_holdout(wb, time_h=V.MIDCOURSE_H)
    assert not frame["passed"].any()
    assert frame["standard_errors"].abs().min() > V.SE_TOLERANCE


def test_the_holdout_has_power(wb):
    """A protocol that passed everywhere would prove nothing."""
    verdict = V.and_logic_holds_at_the_endpoint_only(wb)
    assert verdict["endpoint_predicts_held_out_corners"]
    assert verdict["midcourse_does_not"]
    assert verdict["holdout_has_power"]


def test_corner_rules_are_the_four_rearrangements(wb):
    """Each rule must name the three corners other than the held-out one."""
    for held, rule in V._CORNER_RULES.items():
        assert held not in rule
        assert set(rule) == set("ABCD") - {held}


def test_every_invertible_timepoint_is_covered(wb):
    frame = V.gate_corner_holdout_table(wb)
    assert len(frame) == 4 * len(G.invertible_timepoints(wb))


# -- 3. the carrying capacity ---------------------------------------------


def test_capacity_is_forecastable_from_the_first_twelve_hours(wb):
    frame = V.capacity_forecast(wb)
    assert len(frame) == 8
    assert frame["passed"].all()
    assert frame["ratio"].between(1.0, 1.09).all()


def test_the_forecast_overshoots_consistently(wb):
    """A consistent bias is a finding, not a failure: the Gompertz misses the
    creep phase module 2.3 characterised, so it reads the plateau high."""
    bias = V.capacity_forecast_bias(wb)
    assert 1.02 < bias < 1.08


def test_the_bias_cancels_in_the_quantity_the_ssra_decision_uses(wb):
    """Module 3.4 rests on a ratio of two plateaus, not on either plateau."""
    frame = V.biomass_ratio_survives_the_forecast(wb)
    aerobic = frame[frame.condition == "有氧有酸"].iloc[0]
    assert aerobic["error_percent"] < 1.0
    assert aerobic["observed_ratio"] == pytest.approx(0.5847, abs=1e-3)
    # the ratio is reproduced better than either plateau it is built from
    assert aerobic["error_percent"] < 100.0 * (V.capacity_forecast_bias(wb) - 1.0)


def test_forecast_cutoff_excludes_the_target(wb):
    assert V.FORECAST_CUTOFF_H < 24.0


# -- 4. the exponent across constructs ------------------------------------


def test_every_construct_is_supra_linear_in_dose(wb):
    frame = V.cross_construct_exponents(wb)
    assert len(frame) >= 5
    assert frame["supra_linear"].all()
    assert frame["exponent"].min() > 2.0


def test_most_of_the_constructs_are_out_of_sample(wb):
    frame = V.cross_construct_exponents(wb)
    assert frame["used_in_headline_fit"].sum() == 1
    assert (~frame["used_in_headline_fit"]).sum() >= 4


def test_the_headline_exponent_sits_inside_the_construct_spread(wb):
    frame = V.cross_construct_exponents(wb)
    low, high = X.exponent_interval(wb)
    assert frame["exponent"].min() < low
    assert frame["exponent"].max() > high


def test_constructs_without_an_effector_also_curve_up(wb):
    """So the curvature is not an effector property -- it is how dose enters."""
    frame = V.cross_construct_exponents(wb)
    bare = frame[~frame.carries_effector]
    assert len(bare) >= 2
    assert bare["supra_linear"].all()


# -- the summary -----------------------------------------------------------


def test_summary_counts_the_deliberate_failure_as_zero(wb):
    frame = V.validation_summary(wb).set_index("test")
    row = frame.loc[f"gate corners at {V.MIDCOURSE_H:.0f} h (expected to fail)"]
    assert row["passed"] == 0
    assert "power check" in row["would_have_falsified"]


def test_every_other_test_passes_in_full(wb):
    frame = V.validation_summary(wb)
    real = frame[~frame.test.str.contains("expected to fail")]
    assert (real["passed"] == real["n"]).all()


def test_each_test_names_what_it_would_have_falsified(wb):
    frame = V.validation_summary(wb)
    assert frame["would_have_falsified"].str.len().min() > 10
    assert frame["n"].sum() >= 24


def test_the_holdout_reports_its_mid_course_rows_as_the_power_check() -> None:
    """4.1 must keep the 6 h and 9 h rows, which are what give the test teeth.

    They are not failures of the claim -- 1.1 excluded the mid-course in
    advance -- but without them a reader cannot tell whether the holdout is
    capable of rejecting anything. Dropping them to tidy the section would
    make the 24 h agreement unfalsifiable, which is the edit this guard
    exists to catch.
    """
    from pathlib import Path

    from src import validation as V

    root = Path(__file__).resolve().parent.parent
    page = (root / "WIKI_DRAFT.md").read_text(encoding="utf-8")
    section = page.split("## 4.1 ", 1)[1].split("## 4.2 ", 1)[0]

    table = V.gate_corner_holdout_table()
    failures = table[~table["passed"]]
    assert len(failures) == 8, "6 h and 9 h should fail, all four corners each"
    assert int(table["passed"].sum()) == 4, "24 h should pass, all four corners"

    assert "6 h" in section and "9 h" in section, "the mid-course timepoints"
    worst = float(failures["ratio"].max())
    assert worst == pytest.approx(4.447, abs=0.001)
    assert "4.45" in section, "the worst miss is the power check; print it"

    legs = V.and_logic_holds_at_the_endpoint_only()
    assert legs == {
        "endpoint_predicts_held_out_corners": True,
        "midcourse_does_not": True,
        "holdout_has_power": True,
    }
