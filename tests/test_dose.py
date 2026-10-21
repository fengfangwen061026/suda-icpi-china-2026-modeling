"""Module 4.6 -- the effective-dose back-calculation.

These pin the numbers the wiki quotes, and the guard rails that stop the
inversion from being read further than three points of data can carry it.
"""

from __future__ import annotations

import numpy as np
import pytest

from src import data as D
from src import dose as X


@pytest.fixture(scope="module")
def wb():
    return D.load()


# -- the net dose-kill curve ----------------------------------------------


def test_block_5_has_a_plasmid_bearing_control(wb):
    """`gfp` is a plasmid-bearing non-effector strain at all three doses.

    Convention 4 records that the *growth* blocks have no empty-vector control.
    The killing block does have one, which is what makes a net curve possible.
    """
    block = wb.killing_block(5)
    for control in X.CONTROLS:
        doses = set(block[block.construct == control].dose_od)
        assert doses == set(X.MEASURED_DOSES)


def test_net_killing_subtracts_within_dose(wb):
    frame = X.net_killing(wb, control="gfp")
    assert list(frame.dose_od) == list(X.MEASURED_DOSES)
    np.testing.assert_allclose(
        frame.net_percent, frame.raw_percent - frame.control_percent, rtol=0, atol=1e-12
    )
    assert (frame.net_percent > 0).all()


def test_net_killing_values(wb):
    frame = X.net_killing(wb, control="gfp")
    np.testing.assert_allclose(frame.net_percent, [2.9667, 5.9000, 11.5667], atol=1e-3)


def test_chassis_alone_kills_and_rises_with_dose(wb):
    """The subtraction is not cosmetic: the control itself is dose-dependent."""
    frame = X.net_killing(wb, control="gfp")
    assert frame.control_percent.iloc[-1] > frame.control_percent.iloc[0]
    # at the top dose the chassis accounts for a quarter of the raw readout
    assert 0.2 < frame.control_percent.iloc[-1] / frame.raw_percent.iloc[-1] < 0.3


# -- the power law --------------------------------------------------------


def test_power_law_is_supra_linear_and_fits(wb):
    for control in X.CONTROLS:
        law = X.fit_power_law(wb, control=control)
        assert law.exponent > 2.0
        assert law.r_squared > 0.995


def test_exponent_interval_brackets_a_cube_law(wb):
    low, high = X.exponent_interval(wb)
    np.testing.assert_allclose([low, high], [2.651, 3.376], atol=1e-3)
    assert low < 3.0 < high


def test_power_law_round_trips(wb):
    law = X.fit_power_law(wb)
    for dose in X.MEASURED_DOSES:
        kill = float(law.kill_percent(dose))
        assert law.dose_for(kill) == pytest.approx(dose, rel=1e-9)


# -- the efficacy criterion -----------------------------------------------


def test_required_kill_fraction_is_the_closed_form():
    # one doubling per exposure window means half must go
    assert X.required_kill_fraction(24.0, exposure_h=24.0) == pytest.approx(50.0)
    # a slow lesion needs almost nothing
    assert X.required_kill_fraction(600 * 24.0) < 0.2
    with pytest.raises(ValueError):
        X.required_kill_fraction(0.0)


def test_requirement_is_monotone_in_doubling_time():
    fractions = [X.required_kill_fraction(t) for t in (24.0, 48.0, 240.0, 2400.0)]
    assert fractions == sorted(fractions, reverse=True)


# -- the inversion --------------------------------------------------------


def test_human_requirement_sits_below_every_dose_tested(wb):
    """The clinical indication needs less than the team already achieved.

    This is the interpolation-free half of the answer: it does not rest on the
    fitted curve at all, only on the measured kill at the lowest dose.
    """
    verdicts = X.met_at_every_tested_dose(wb)
    assert verdicts["Human CRC, 100 d doubling"]
    assert verdicts["Human CRC, 600 d doubling"]
    assert not verdicts["CT26, 24 h doubling"]
    assert not verdicts["CT26, 48 h doubling"]


def test_ct26_needs_a_modest_escalation(wb):
    table = X.dose_requirement_table(wb)
    ct26 = table[table.target.str.startswith("CT26")]
    assert ct26.fold_of_highest_tested.min() > 1.0
    assert ct26.fold_of_highest_tested.max() < 2.0


def test_the_answer_is_robust_to_the_control_choice(wb):
    """Which control is subtracted moves the exponent but not the verdict."""
    table = X.dose_requirement_table(wb)
    for target in X.TARGETS:
        doses = table[table.target == target].required_dose_od
        assert doses.max() / doses.min() < 1.5


def test_cube_law_compresses_the_requirement_spread(wb):
    out = X.cube_law_compression(wb)
    assert out["kill_fraction_span"] > 400.0
    assert out["dose_span"] < 11.0
    # the compression is exactly the fitted exponent, by construction
    law = X.fit_power_law(wb)
    assert out["implied_exponent"] == pytest.approx(law.exponent, rel=1e-9)


def test_delivery_loss_costs_a_cube_root(wb):
    law = X.fit_power_law(wb)
    penalty = X.delivery_penalty(X.NODULE_RETENTION, exponent=law.exponent)
    # a 3.7x loss of delivered effector costs under 1.7x in dose
    assert 1.0 < penalty < 1.7
    assert X.delivery_penalty(1.0, exponent=law.exponent) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        X.delivery_penalty(0.0)


# -- guard rails ----------------------------------------------------------


def test_inversion_refuses_a_far_extrapolation(wb):
    law = X.fit_power_law(wb)
    with pytest.raises(X.DoseExtrapolationError):
        law.dose_for(1e-6)
    with pytest.raises(X.DoseExtrapolationError):
        law.dose_for(1e6)
    with pytest.raises(X.DoseExtrapolationError):
        law.dose_for(0.0)


def test_every_reported_requirement_carries_its_extrapolation(wb):
    table = X.dose_requirement_table(wb)
    assert (table.extrapolation_fold >= 1.0).all()
    # nothing in the table is inside the measured range, so the flag must say so
    assert not table.inside_measured_range.any()
    assert table.extrapolation_fold.max() < 4.0


def test_fit_refuses_a_non_positive_net_curve(wb):
    """Guard rail, not decoration: `EcN` against itself has zero net killing."""
    with pytest.raises(D.DataConventionError):
        X.fit_power_law(wb, control="GSDMD-SsrA")


def test_missing_construct_is_refused(wb):
    with pytest.raises(D.DataConventionError):
        X.net_killing(wb, construct="not-a-construct")


# -- lesion radius and the joint constraint -------------------------------


def test_dose_multiplier_falls_with_lesion_radius(wb):
    frame = X.dose_vs_lesion_radius()
    assert list(frame.dose_multiplier) == sorted(frame.dose_multiplier, reverse=True)
    assert frame.dose_multiplier.iloc[-1] < 1.0 < frame.dose_multiplier.iloc[0]


def test_micro_lesion_needs_a_large_but_finite_escalation(wb):
    """Basal expression, not zero, so the multiplier does not diverge."""
    frame = X.dose_vs_lesion_radius(np.array([150.0]))
    multiplier = float(frame.dose_multiplier.iloc[0])
    assert multiplier == pytest.approx(2.82, abs=0.01)
    assert 1.0 < multiplier < 12.0
    assert not bool(frame.has_hypoxic_core.iloc[0])

    # The inherited n_Q of 2 made this nearly three times as expensive; the
    # published exponent is what brings a micro-lesion back within reach (2.5).
    legacy = float(
        X.dose_vs_lesion_radius(np.array([150.0]), quorum_hill=2.0).dose_multiplier.iloc[0]
    )
    assert legacy == pytest.approx(7.96, abs=0.01)
    assert legacy / multiplier == pytest.approx(2.82, abs=0.01)


def test_reaching_a_micro_lesion_spends_the_safety_margin(wb):
    """Chapters 3 and 4 meet here: the escalation that reaches a 150 um lesion
    spends most of the colonic-mucosa margin.

    At the published sensor values it leaves 4.41x rather than the 1.36x the
    inherited priors gave -- better, but still under the 10x requirement, so
    the trade-off this section exists to report is unchanged.
    """
    frame = X.escalation_erodes_margin(wb)
    at_400 = frame[frame.radius_um == 400.0].iloc[0]
    at_150 = frame[frame.radius_um == 150.0].iloc[0]
    assert at_400.mucosa_margin_left == pytest.approx(12.44, abs=0.01)
    assert at_150.mucosa_margin_left == pytest.approx(4.41, abs=0.01)
    assert at_150.mucosa_margin_left < 10.0, "the trade-off is still real"
    assert at_150.total_escalation > at_400.total_escalation

    legacy = X.escalation_erodes_margin(wb, quorum_hill=2.0)
    assert float(
        legacy[legacy.radius_um == 150.0].iloc[0].mucosa_margin_left
    ) == pytest.approx(1.56, abs=0.02)


# -- scope ----------------------------------------------------------------


def test_the_module_does_not_claim_an_oral_dose(wb):
    record = X.effective_dose_conclusion(wb)
    assert record["derived_from_team_data"] is True
    assert record["reports_oral_cfu"] is False
    assert record["human_requirement_inside_measured_range"] is True
    assert "plate count" in record["missing_bridge_1"]
    assert "CFU/g tumour" in record["missing_bridge_2"]


# -- what counts as enough margin -----------------------------------------


def test_renewal_rate_is_a_cycle_not_a_doubling():
    """Epithelium is replaced, not doubled, so the rate is 1/T and not ln2/T."""
    four_days = X.tolerable_offtarget_loss(4 * 24.0)
    assert four_days == pytest.approx(100.0 * (1.0 - np.exp(-0.25)), rel=1e-9)
    # and it is therefore larger than the doubling form would give
    assert four_days > X.required_kill_fraction(4 * 24.0)
    with pytest.raises(ValueError):
        X.tolerable_offtarget_loss(0.0)


def test_margin_converts_to_a_rate(wb):
    """A fold is not a safety claim until it is a rate compared with something."""
    frame = X.margin_table(wb)
    mucosa = frame[frame.site == "colonic_mucosa"].iloc[0]
    assert mucosa["margin_fold"] == pytest.approx(21.85, abs=0.05)
    assert mucosa["implied_loss_percent_24h"] < 1e-3
    assert mucosa["renewal_headroom"] > 1e4
    assert not frame["above_renewal"].any()


def test_the_claim_survives_the_conservative_exponent(wb):
    """Linear credits the margin with no amplification at all."""
    frame = X.margin_table(wb, exponent=X.CONSERVATIVE_EXPONENT)
    mucosa = frame[frame.site == "colonic_mucosa"].iloc[0]
    assert mucosa["renewal_headroom"] > 500.0
    assert not frame["above_renewal"].any()
    # every site is worse off under the conservative reading, as it should be
    fitted = X.margin_table(wb).set_index("site")
    for site, row in frame.set_index("site").iterrows():
        assert row["renewal_headroom"] < fitted.loc[site, "renewal_headroom"]


def test_the_loss_criterion_demands_little(wb):
    """So 19.6x is not marginal against it -- which is the honest finding."""
    frame = X.margin_requirement_is_modest(wb)
    assert frame["required_margin_fold"].max() < 3.0
    human = frame[frame.target.str.startswith("Human")]
    assert human["required_margin_fold"].max() < 1.0


def test_required_margin_inverts_implied_loss(wb):
    law = X.fit_power_law(wb)
    margin = X.required_margin(
        target_kill_percent=50.0, tolerable_kill_percent=22.0, exponent=law.exponent
    )
    back = X.implied_offtarget_loss(
        margin, target_kill_percent=50.0, exponent=law.exponent
    )
    assert back == pytest.approx(22.0, rel=1e-9)
    with pytest.raises(ValueError):
        X.required_margin(target_kill_percent=1.0, tolerable_kill_percent=0.0)
    with pytest.raises(ValueError):
        X.implied_offtarget_loss(0.0, target_kill_percent=1.0)


def test_the_criterion_states_what_it_does_not_cover():
    record = X.margin_criterion_covers_cell_loss_only()
    assert record["settles_the_question"] is False
    assert record["is_a_lower_bound_on_the_requirement"] is True
    assert "inflammation" in record["does_not_cover"]
    assert "pyroptosis" in record["why_that_matters"]


def test_the_renewal_placeholder_is_not_load_bearing() -> None:
    """3.5's renewal table, recomputed.

    `T_renew` is a declared 96 h, the midpoint of the 3-5 day range human crypt
    kinetics support (Potten et al. 1992). The page claims the choice does not
    matter: across 3-5 days the margin the constraint demands stays below 1.0,
    i.e. crypt renewal alone would absorb the off-target dose with no gate
    selectivity at all. If that ever stops being true the claim has to change.
    """
    from src import dose

    printed = {72.0: (28.347, 0.2463), 96.0: (22.120, 0.2704), 120.0: (18.127, 0.2915)}
    for renewal_h, (tolerable, required) in printed.items():
        actual = dose.tolerable_offtarget_loss(renewal_h)
        assert actual == pytest.approx(tolerable, abs=0.001), renewal_h
        margin = dose.required_margin(
            target_kill_percent=0.6908, tolerable_kill_percent=actual
        )
        assert margin == pytest.approx(required, abs=0.0001), renewal_h
        assert margin < 1.0, "renewal alone must absorb it, or 3.5 is wrong"

    spread = printed[120.0][1] / printed[72.0][1] - 1.0
    assert spread == pytest.approx(0.18, abs=0.01), "the quoted 18 % swing"


def test_the_renewal_fraction_column_uses_the_renewal_as_its_denominator() -> None:
    """"Fraction of renewal" means against 22.12 %/24 h, not against 100 %.

    Both WIKI_DRAFT 3.5 and MODULE_4_6 print this column. They disagreed once,
    on 2026-10-14, because the page was updated on the wrong basis while the
    module doc kept the right one. Pin the basis so they cannot drift apart.
    """
    from src import data as D, dose

    renewal = dose.tolerable_offtarget_loss(96.0)
    assert renewal == pytest.approx(22.12, abs=0.01)

    table = dose.margin_table(D.load()).set_index("label")
    loss = float(table.loc["Colonic mucosa", "implied_loss_percent_24h"])
    assert renewal / loss == pytest.approx(113_800, rel=0.001)
    # The wrong basis would give ~514,000; keep them far apart on purpose.
    assert 100.0 / loss == pytest.approx(514_500, rel=0.001)
