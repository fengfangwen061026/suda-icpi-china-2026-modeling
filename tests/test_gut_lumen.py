"""Module 3.3 results, pinned.

The load-bearing assertions are the parameter-free ones: they hold for every
EC50, Hill coefficient and basal level, so they cannot be invalidated by the
lactate-gradient experiment that will not be run.
"""

from __future__ import annotations

import math

import pytest

from src import gut_lumen as G
from src import sensors as S


@pytest.fixture(scope="module")
def sites():
    return G.load_sites()


# -- parameter-free: direction of each designed arm -----------------------


def test_hypoxia_arm_is_anti_selective_at_every_luminal_site():
    """The lumen is anoxic; the tumour core is only hypoxic.

    pPepT is hypoxia-activated and monotone, so a strictly anoxic site always
    drives it at least as hard as the tumour core does. No parameter choice
    reverses this.
    """
    verdicts = {(v.site, v.arm): v for v in G.arm_verdicts()}
    for site in G.LUMEN_SITES:
        assert verdicts[(site, "hypoxia")].anti_selective, site


def test_both_arms_fail_in_the_dysbiotic_lumen():
    """The headline. Neither designed input can hold the gate OFF there."""
    verdicts = {(v.site, v.arm): v for v in G.arm_verdicts()}
    assert verdicts[("colon_lumen_dysbiotic", "lactate")].anti_selective
    assert verdicts[("colon_lumen_dysbiotic", "hypoxia")].anti_selective


def test_the_tumour_arms_still_work_against_perfused_tissue():
    """Sanity: the 9.23 tissue axis is not being contradicted, only extended."""
    verdicts = {(v.site, v.arm): v for v in G.arm_verdicts()}
    for site in ("colonic_mucosa", "well_perfused"):
        assert not verdicts[(site, "lactate")].anti_selective, site
        assert not verdicts[(site, "hypoxia")].anti_selective, site


# -- the analytic bound ---------------------------------------------------


def test_discrimination_bound_is_the_concentration_ratio_to_the_hill_power():
    """sup ratio = (L_t / L_off) ** hill, at zero basal."""
    for hill in (1.0, 2.0, 4.0):
        bound = G.max_achievable_discrimination(0.6, target_lactate_mM=8.0, hill=hill)
        assert bound == pytest.approx((8.0 / 0.6) ** hill, rel=1e-12)


def test_grid_search_never_beats_the_analytic_bound():
    """Cross-check: the bound really is a bound."""
    for offsite in (0.6, 1.5, 5.0):
        for hill in (1.0, 2.0, 4.0):
            grid = G.lactate_specification(
                offsite, hill_grid=[hill], basal=0.0, required_fold=1.0
            )
            bound = G.max_achievable_discrimination(
                offsite, target_lactate_mM=8.0, hill=hill
            )
            assert grid["ratio"].max() <= bound * (1 + 1e-9)


def test_basal_caps_discrimination_independently_of_shape():
    """A wild-type basal of ~1/7 caps the arm at 7x whatever EC50 and Hill do."""
    assert G.basal_ceiling(S.BASAL_LACTATE_WT) == pytest.approx(7.0, rel=1e-9)
    capped = G.max_achievable_discrimination(
        0.6, hill=4.0, basal=S.BASAL_LACTATE_WT
    )
    assert capped == pytest.approx(7.0, rel=1e-9)


def test_required_hill_coefficients():
    # 8 vs 5 mM is only a 1.6x concentration ratio, so 10x needs ln10/ln1.6
    assert G.required_hill_for_fold(5.0, required_fold=10.0) == pytest.approx(4.9, abs=0.05)
    # 8 vs 0.6 mM is a 13.3x ratio, so a single-site sensor is enough in principle
    assert G.required_hill_for_fold(0.6, required_fold=10.0) == pytest.approx(0.9, abs=0.05)
    # and when the off-target site is richer, there is no such coefficient
    assert G.required_hill_for_fold(100.0, required_fold=10.0) is None


def test_faecal_lactate_is_unreachable_at_any_plausible_hill():
    """LldR has no reported cooperativity, so Hill ~ 1; 4.9 is out of reach."""
    for hill in (1.0, 2.0, 3.0, 4.0):
        assert G.minimum_ec50_for_fold(5.0, required_fold=10.0, hill=hill) is None


# -- wild-type numbers ----------------------------------------------------


@pytest.mark.parametrize(
    "offsite_mM, expected",
    [(0.6, 2.28), (5.0, 1.08), (100.0, 0.87), (1.5, 1.54)],
)
def test_wild_type_lactate_discrimination(offsite_mM, expected):
    assert S.lactate_discrimination(8.0, offsite_mM) == pytest.approx(expected, abs=0.01)


def test_published_wild_type_parameters_are_the_ones_cited():
    assert S.EC50_LACTATE_WT == 1.6
    assert S.HILL_LACTATE_WT == 1.0
    assert S.BASAL_LACTATE_WT == pytest.approx(1 / 7)


# -- the two candidate rescues -------------------------------------------


def test_washout_only_helps_when_transit_is_fast_relative_to_ahl_decay():
    table = G.quorum_requirement().set_index("transit_time_h")
    # 1 h transit against an 8 h AHL half-life suppresses ~12x
    assert table.loc[1.0, "suppression_fold"] == pytest.approx(12.5, abs=0.2)
    # a day-long residence suppresses almost nothing
    assert table.loc[24.0, "suppression_fold"] == pytest.approx(1.48, abs=0.02)
    assert table["suppression_fold"].is_monotonic_decreasing


def test_native_repression_would_rescue_every_luminal_site():
    """If the built part kept the native anoxic + glucose repression."""
    table = G.native_repression_rescue().set_index(["site", "variant"])
    for site in G.LUMEN_SITES:
        native = table.loc[(site, "native (repressed)"), "discrimination"]
        engineered = table.loc[(site, "engineered (de-repressed)"), "discrimination"]
        assert native > 80.0, site
        assert engineered < 2.3, site
        assert native / engineered > 35.0, site


def test_required_repression_is_modest_and_within_a_native_promoter_range():
    """The specification the native promoter has to meet.

    Resolved 2026-10-08: the part is BBa_M36021, the native E. coli lldPRD
    operon promoter, so both the anoxic and the glucose repression are retained.
    The worst luminal site needs only ~12x combined repression, and each of the
    two native repressions is reported as strong on its own.
    """
    table = G.required_repression_for_fold(required_fold=10.0).set_index("site")
    assert table.loc["colon_lumen_healthy", "required_repression_fold"] == pytest.approx(4.4, abs=0.1)
    assert table.loc["colon_lumen_faecal", "required_repression_fold"] == pytest.approx(9.2, abs=0.1)
    assert table.loc["colon_lumen_dysbiotic", "required_repression_fold"] == pytest.approx(11.5, abs=0.1)
    # the binding case is dysbiosis, and it is still a single-promoter-sized ask
    assert table["required_repression_fold"].max() < 15.0


def test_requirement_scales_linearly_with_the_target_margin():
    ten = G.required_repression_for_fold(required_fold=10.0)
    hundred = G.required_repression_for_fold(required_fold=100.0)
    ratio = hundred["required_repression_fold"] / ten["required_repression_fold"]
    assert ratio.min() == pytest.approx(10.0, rel=1e-9)
    assert ratio.max() == pytest.approx(10.0, rel=1e-9)


def test_de_repressed_variant_is_anti_selective_in_dysbiosis():
    table = G.native_repression_rescue().set_index(["site", "variant"])
    value = table.loc[
        ("colon_lumen_dysbiotic", "engineered (de-repressed)"), "discrimination"
    ]
    assert value < 1.0


# -- config integrity -----------------------------------------------------


def test_every_site_carries_an_evidence_class_and_a_source(sites):
    assert set(sites["evidence_class"]) <= {"literature_prior", "scenario_only"}
    assert sites["source"].str.len().min() > 20
    assert sites.loc["colon_lumen_dysbiotic", "evidence_class"] == "scenario_only"


def test_lumen_sites_are_anoxic_and_the_tumour_is_not(sites):
    for site in G.LUMEN_SITES:
        assert sites.loc[site, "anoxic"]
        assert sites.loc[site, "o2_percent"] == 0.0
    assert not sites.loc[G.TARGET, "anoxic"]
    assert sites.loc[G.TARGET, "o2_percent"] > 0.0


# -- the single point of failure ------------------------------------------


def test_the_structural_assumption_is_recorded():
    record = G.single_structural_assumption()
    assert record["is_the_only_single_point_of_failure"] is True
    assert record["form"] == "binary flag, not a fitted parameter"
    assert "sign change" in record["failure_mode"]
    assert record["luminal_sites"] == 3


def test_the_assumption_flips_a_sign_rather_than_widening_an_interval():
    record = G.single_structural_assumption()
    low_with, high_with = record["lactate_arm_with_repression"]
    low_without, high_without = record["lactate_arm_without"]
    # with the repressions every luminal site is protective
    assert low_with > 1.0
    # without them the worst site inverts
    assert low_without < 1.0
    assert low_with / low_without == pytest.approx(100.0, rel=1e-6)


def test_only_half_the_assumption_is_measured():
    record = G.single_structural_assumption()
    assert "1 % O2" in record["measured_half"]
    assert "0 % O2" in record["assumed_half"]
    assert "0 % O2" in record["experiment"]


def test_the_repression_needed_is_modest():
    """Modest and reported is the reason to think it holds; it is not a measurement."""
    record = G.single_structural_assumption()
    assert record["worst_case_repression_needed"] < 15.0
    assert record["worst_case_repression_needed"] > 10.0
