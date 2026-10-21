"""Module 3.5 results, pinned."""

from __future__ import annotations

import numpy as np
import pytest

from src import data as D
from src import gut_lumen as GL
from src import sensitivity as SA
from src import tissue as T


@pytest.fixture(scope="module")
def wb() -> D.Workbook:
    return D.load()


@pytest.fixture(scope="module")
def indices(wb):
    return SA.run(n_base=512, wb=wb)


# -- the fast evaluator must agree with the module it summarises ---------


def test_vectorised_evaluator_matches_the_tissue_module(wb):
    """Cross-check: same ratios, computed two different ways."""
    # The project defaults, so the cross-check exercises the shipped config:
    # EC50 1.6, n_L 1, b_L 1/7, K_O2 0.49, n_O2 2, b_O2 0.05, n_Q 1, d 1, rho 1.
    sample = np.array(
        [[1.6, 1.0, 1.0 / 7.0, 0.49, 2.0, 0.05, 1.0, 1.0, 1.0]]
    )
    fast = SA.evaluate(sample, wb)
    slow = T.TissueAxis().arms(wb).set_index("site")
    for site in slow.index:
        assert fast[site][0] == pytest.approx(
            np.log10(slow.loc[site, "total_ratio"]), rel=1e-9
        ), site


def test_bottleneck_is_the_minimum_over_sites(wb):
    rng = np.random.default_rng(0)
    bounds = np.array(SA.PROBLEM["bounds"])
    sample = bounds[:, 0] + rng.random((8, bounds.shape[0])) * (bounds[:, 1] - bounds[:, 0])
    outputs = SA.evaluate(sample, wb)
    stacked = np.vstack([outputs[s] for s in outputs if s != "bottleneck"])
    assert np.allclose(outputs["bottleneck"], stacked.min(axis=0))


# -- log scale linearises the product ------------------------------------


def test_single_site_outputs_are_nearly_additive_on_the_log_scale(indices):
    """A multiplicative model becomes a sum under log10, so S1 should sum near 1."""
    table = SA.additivity_check(indices).set_index("output")
    assert table.loc["colonic_mucosa", "sum_S1"] > 0.75
    assert table.loc["colon_lumen_dysbiotic", "sum_S1"] > 0.85


def test_the_bottleneck_keeps_real_interaction_because_min_is_nonlinear(indices):
    table = SA.additivity_check(indices).set_index("output")
    assert table.loc["bottleneck", "residual_interaction"] > 0.25
    assert table.loc["bottleneck", "residual_interaction"] > table.loc[
        "colon_lumen_dysbiotic", "residual_interaction"
    ]


def test_n_q_is_the_predicted_interaction_carrier(indices):
    """n_Q multiplies log(hypoxia/density), so ST should far exceed S1."""
    for output in ("colonic_mucosa", "bottleneck"):
        row = indices[(indices.output == output) & (indices.parameter == "n_Q")].iloc[0]
        assert row["ST"] > row["S1"]
        assert row["interaction_share"] > 0.4, output


def test_repression_is_a_pure_multiplier_in_the_lumen(indices):
    """It enters the log sum additively, so it should show almost no interaction."""
    row = indices[
        (indices.output == "colon_lumen_dysbiotic")
        & (indices.parameter == "repression_fold")
    ].iloc[0]
    assert row["interaction_share"] < 0.1
    assert row["S1"] == pytest.approx(row["ST"], rel=0.15)


# -- 9.23's mucosa finding is independently confirmed --------------------


def test_oxygen_affinity_dominates_the_mucosa_fold(indices):
    """9.23 reported K_O2 first for tumour-vs-mucosa; so does this."""
    top = SA.top_drivers(indices, "colonic_mucosa", 3)
    assert top.iloc[0]["parameter"] == "k_o2_percent"
    assert top.iloc[0]["ST"] > 0.6
    # its other two named drivers are both oxygen-sensor parameters too
    assert set(top["parameter"]) == {"k_o2_percent", "hill_o2", "basal_o2"}


# -- the bottleneck is driven by parameters 9.23 did not have ------------


def test_lumen_is_driven_by_density_and_repression(indices):
    top = SA.top_drivers(indices, "colon_lumen_dysbiotic", 2)
    assert set(top["parameter"]) == {"lumen_density_ratio", "repression_fold"}
    assert top["ST"].min() > 0.3


def test_the_two_lumen_drivers_are_absent_from_the_9_23_model(indices):
    """Neither parameter exists in 9.23's Sobol, because the lumen was not a site."""
    top = set(SA.top_drivers(indices, "bottleneck", 2)["parameter"])
    assert top == {"repression_fold", "lumen_density_ratio"}
    legacy_reported = {"K_O2_uM", "clearance_max_per_h", "n_Q", "pept_basal_fraction",
                       "oxygen_rim_uM", "delta_G_ssra"}
    assert not (top & legacy_reported)


def test_sensor_parameters_barely_matter_at_the_bottleneck(indices):
    """The lactate-prior disagreement from module 3.1 is not what decides safety."""
    frame = indices[indices.output == "colon_lumen_dysbiotic"].set_index("parameter")
    for parameter in ("ec50_lactate_mM", "hill_lactate", "basal_lactate"):
        assert frame.loc[parameter, "ST"] < 0.1


# -- coverage over the declared ranges -----------------------------------


def test_tissue_sites_are_protective_almost_everywhere(wb):
    table = SA.safety_probability(n_base=512, wb=wb).set_index("site")
    for site in ("tumour_rim", "well_perfused"):
        assert table.loc[site, "fraction_protective"] == pytest.approx(1.0, abs=0.01)
    assert table.loc["colonic_mucosa", "fraction_protective"] > 0.98


def test_every_failure_in_the_sampled_space_is_a_lumen_failure(wb):
    table = SA.safety_probability(n_base=512, wb=wb).set_index("site")
    non_lumen = ("tumour_rim", "colonic_mucosa", "well_perfused")
    assert min(table.loc[s, "fraction_protective"] for s in non_lumen) > 0.98
    assert max(table.loc[s, "fraction_protective"] for s in GL.LUMEN_SITES) < 0.95
    assert table.loc["bottleneck", "fraction_protective"] == pytest.approx(
        min(table.loc[s, "fraction_protective"] for s in GL.LUMEN_SITES), abs=0.03
    )


def test_coverage_is_substantial_but_not_complete(wb):
    table = SA.safety_probability(n_base=512, wb=wb).set_index("site")
    coverage = table.loc["bottleneck", "fraction_protective"]
    assert 0.6 < coverage < 0.85
