"""Module 3.1 results, pinned."""

from __future__ import annotations

import pytest

from src import data as D
from src import gut_lumen as GL
from src import tissue as T


@pytest.fixture(scope="module")
def wb() -> D.Workbook:
    return D.load()


# -- densities are measured, not assumed ---------------------------------


def test_densities_come_from_the_growth_block(wb):
    capacities = T.measured_capacities(wb)
    assert capacities["有氧无酸"] == pytest.approx(2.613, abs=0.001)
    assert capacities["无氧有酸"] == pytest.approx(1.507, abs=0.001)
    # every site maps onto a condition that exists
    assert set(T.SITE_CONDITION.values()) <= set(D.GROWTH_CONDITIONS)
    assert set(T.SITE_CONDITION) == set(GL.load_sites().index)


# -- the published range is an n_Q span ----------------------------------


def test_the_two_9_23_calibrations_differ_in_the_quorum_hill():
    hills = {k: v["n_Q"] for k, v in T.CALIBRATION_9_23.items()}
    assert hills["dynamic_fit"] == pytest.approx(1.0)
    assert hills["endpoint_matched"] == pytest.approx(2.978, abs=0.001)


def test_tissue_folds_grow_with_the_quorum_hill(wb):
    sweep = T.quorum_hill_sweep(hills=(1.0, 2.0, 4.0), wb=wb)
    for site in ("colonic_mucosa", "well_perfused"):
        values = sweep[sweep.site == site].sort_values("quorum_hill")["total_ratio"]
        assert list(values) == sorted(values)


def test_reconstruction_lands_in_the_published_order_of_magnitude(wb):
    """A well-mixed point estimate against 9.23's spatially averaged PDE.

    Exact agreement is not expected and not claimed; the test is that the same
    driver moves it the same way over the same decades.
    """
    span = T.calibration_span(wb).set_index(["variant", "site"])
    mucosa_low = span.loc[("dynamic_fit", "colonic_mucosa"), "total_ratio"]
    mucosa_high = span.loc[("endpoint_matched", "colonic_mucosa"), "total_ratio"]
    assert mucosa_high > mucosa_low
    assert 10 < mucosa_low < 200
    assert 10 < mucosa_high < 2000


# -- 9.23's lactate priors are more generous than the real part ----------


def test_the_lactate_arm_is_inflated_by_the_legacy_priors(wb):
    table = T.prior_comparison(wb).set_index("label")
    assert table.loc["Colonic mucosa", "lactate_arm_pub"] == pytest.approx(1.54, abs=0.02)
    assert table.loc["Colonic mucosa", "lactate_arm_923"] == pytest.approx(8.04, abs=0.05)
    assert table.loc["Colonic mucosa", "lactate_arm_inflation"] == pytest.approx(5.2, abs=0.1)


def test_legacy_lactate_priors_differ_from_the_published_part_on_all_three():
    legacy, _ = T.sensors_9_23()
    published, _ = T.sensors_published()
    assert legacy.ec50_mM == 5.0 and published.ec50_mM == 1.6
    assert legacy.hill == 2.0 and published.hill == 1.0
    assert legacy.basal < 0.01 and published.basal > 0.1


def test_the_published_oxygen_prior_replaced_the_inherited_one():
    """9.23's two parameter sets agreed at 1 % O2; neither was a measurement.

    As of 2026-10-14 the project default is Hojberg's 0.49 %. The legacy
    sensor keeps 9.23's value so module 3.1 can still report both, and the
    gap between them is the thing 2.5 is about -- if they silently converge
    again, that section has lost its subject.
    """
    _, legacy = T.sensors_9_23()
    _, published = T.sensors_published()
    assert legacy.k_o2_percent == 1.0, "the inherited prior"
    assert published.k_o2_percent == 0.49, "Hojberg et al. 1999"
    assert legacy.hill == published.hill == 2.0


# -- the lumen verdict survives both parameter sets ----------------------


def test_dysbiotic_lumen_is_anti_selective_under_either_prior_set(wb):
    table = T.prior_comparison(wb).set_index("label")
    row = table.loc["Colon lumen (dysbiosis/UC)"]
    assert row["total_ratio_pub"] < 1.0
    assert row["total_ratio_923"] < 1.0
    # and the generous priors buy nothing there, because both sensors saturate
    assert row["lactate_arm_inflation"] < 1.0


def test_both_9_23_calibrations_also_fail_the_dysbiotic_lumen(wb):
    span = T.calibration_span(wb)
    values = span[span.site == "colon_lumen_dysbiotic"]["total_ratio"]
    assert (values < 1.0).all()


# -- native repression, and what it does to the bottleneck ---------------


def test_repression_raises_the_tumour_over_site_ratio(wb):
    """Direction check: repressing the site makes the gate *more* selective."""
    without = T.TissueAxis(quorum_hill=2.0).arms(wb).set_index("site")
    with_rep = (
        T.TissueAxis(quorum_hill=2.0, anoxic_repression=10.0, glucose_repression=10.0)
        .arms(wb)
        .set_index("site")
    )
    for site in GL.LUMEN_SITES:
        assert with_rep.loc[site, "total_ratio"] == pytest.approx(
            without.loc[site, "total_ratio"] * 100.0, rel=1e-9
        )
    # non-lumen sites are untouched
    assert with_rep.loc["colonic_mucosa", "total_ratio"] == pytest.approx(
        without.loc["colonic_mucosa", "total_ratio"], rel=1e-12
    )


def test_repression_turns_every_luminal_site_protective(wb):
    frame = T.TissueAxis(anoxic_repression=10.0, glucose_repression=10.0).arms(wb)
    assert frame["protective"].all()
    # Lower K_O2 halves the luminal margins; every one still clears 10x.
    assert frame[frame.is_lumen]["total_ratio"].min() == pytest.approx(23.08, abs=0.01)

    # And at the inherited priors too, at a smaller margin.
    legacy = T.TissueAxis(
        quorum_hill=2.0, anoxic_repression=10.0, glucose_repression=10.0
    ).arms(wb)
    assert legacy["protective"].all()
    assert legacy[legacy.is_lumen]["total_ratio"].min() > 10.0


def test_the_bottleneck_moves_from_the_lumen_to_the_mucosa(wb):
    """The headline of the migration."""
    bare = T.weakest_link(wb)
    assert bare["site"] == "colon_lumen_dysbiotic"
    assert bare["total_ratio"] == pytest.approx(0.2308, abs=0.0001)

    repressed = T.weakest_link(
        wb, anoxic_repression=10.0, glucose_repression=10.0
    )
    assert repressed["site"] == "colonic_mucosa"
    assert repressed["total_ratio"] == pytest.approx(21.8523, abs=0.0001)
    assert repressed["total_ratio"] > 10.0

    # It also held at the inherited priors, at a smaller margin. Both readings
    # put the weakest link at the mucosa once the native repression is on.
    legacy = T.weakest_link(
        wb, quorum_hill=2.0, anoxic_repression=10.0, glucose_repression=10.0
    )
    assert legacy["total_ratio"] > 10.0


# -- the one unmeasured lumen parameter ----------------------------------


def test_denser_luminal_colonisation_lowers_the_margin(wb):
    sweep = T.lumen_density_sweep(wb=wb, with_repression=True)
    dysbiotic = sweep[sweep.site == "colon_lumen_dysbiotic"].sort_values(
        "lumen_density_ratio"
    )
    assert list(dysbiotic["total_ratio"]) == sorted(dysbiotic["total_ratio"], reverse=True)


def test_there_is_a_critical_luminal_density(wb):
    """The quorum arm protects a sparsely colonised lumen and fails a dense one."""
    bare = T.critical_lumen_density(repression_fold=1.0, wb=wb)
    repressed = T.critical_lumen_density(repression_fold=10.0, wb=wb)
    assert bare == pytest.approx(0.231, abs=0.001)
    assert repressed == pytest.approx(23.08, abs=0.01)
    # At n_Q = 1 the critical density scales linearly in the repression fold
    # rather than as its square root, which is why the headroom jumps.
    assert repressed / bare == pytest.approx(100.0, rel=0.01)


def test_repression_buys_margin_as_its_fold_to_the_one_over_n_q(wb):
    """R**(1/n_Q): a steep quorum arm devalues a strong repression."""
    for hill in (1.0, 2.0, 4.0):
        bare = T.critical_lumen_density(quorum_hill=hill, repression_fold=1.0, wb=wb)
        repressed = T.critical_lumen_density(quorum_hill=hill, repression_fold=10.0, wb=wb)
        assert repressed / bare == pytest.approx(100.0 ** (1.0 / hill), rel=1e-9)


def test_the_sweep_agrees_with_the_closed_form(wb):
    """Everything below d_crit is protective, everything above is not."""
    critical = T.critical_lumen_density(repression_fold=10.0, wb=wb)
    sweep = T.lumen_density_sweep(wb=wb, with_repression=True)
    dysbiotic = sweep[sweep.site == "colon_lumen_dysbiotic"]
    for _, row in dysbiotic.iterrows():
        assert row["protective"] == (row["lumen_density_ratio"] < critical)


def test_the_mixed_and_published_corners_of_the_box() -> None:
    """The 3x3 table of 2.5, recomputed from the code it describes.

    Both parameters were adopted from the literature on 2026-10-14, so these
    cells are now a record of what the inherited priors gave rather than a
    live configuration. 2.5 prints them; prose drifts where code does not.

    * 19.64x is what the inherited priors gave -- the old headline;
    * 21.85x is what the published values give -- the current one;
    * K_O2 = 2 % breaks the requirement at every n_Q, which is the direction
      to watch.
    """
    from src import data as D, sensors as S, tissue

    workbook = D.load()

    def bottleneck(quorum_hill: float, k_o2_percent: float):
        original = tissue.sensors_published
        tissue.sensors_published = lambda: (
            S.LactateSensor(),
            S.HypoxiaSensor(k_o2_percent=k_o2_percent),
        )
        try:
            arms = tissue.TissueAxis(
                quorum_hill=quorum_hill,
                anoxic_repression=10.0,
                glucose_repression=10.0,
            ).arms(workbook)
        finally:
            tissue.sensors_published = original
        row = arms.loc[arms["total_ratio"].idxmin()]
        return float(row["total_ratio"]), str(row["label"])

    printed = {
        (1.0, 0.5): 21.79, (1.0, 1.0): 10.09, (1.0, 2.0): 2.87,
        (1.5, 0.5): 17.35, (1.5, 1.0): 14.08, (1.5, 2.0): 2.92,
        (2.0, 0.5): 12.57, (2.0, 1.0): 19.64, (2.0, 2.0): 2.97,
    }
    for (quorum_hill, k_o2), expected in printed.items():
        margin, _ = bottleneck(quorum_hill, k_o2)
        assert margin == pytest.approx(expected, abs=0.01), (quorum_hill, k_o2)

    published_box = [
        bottleneck(n, k)[0] for n in (1.0, 1.5) for k in (0.5, 1.0)
    ]
    assert min(published_box) == pytest.approx(10.09, abs=0.01)
    assert min(published_box) > 10.0, "the requirement is met across the box"

    both_central, site = bottleneck(1.0, 0.49)
    assert both_central == pytest.approx(21.85, abs=0.01)
    assert both_central > 19.64, "the published prior is not the flattering one"
    assert site == "Colonic mucosa"

    for quorum_hill in (1.0, 1.5, 2.0):
        failing, failing_site = bottleneck(quorum_hill, 2.0)
        assert failing < 10.0, "K_O2 = 2 % must break it at every n_Q"
        assert failing_site == "Colonic mucosa"


def test_the_quorum_exponent_moves_the_weakest_link_not_the_verdict() -> None:
    """n_Q decides *which* site is the bottleneck; the verdict does not move.

    Swept from the published centre up through the inherited prior and beyond,
    the bottleneck stays above the 10x requirement everywhere, but the site it
    sits at changes. That distinction is 2.5's point: the exponent is the
    dominant unknown of the axis and it still does not decide whether the
    design passes.
    """
    from src import data as D, tissue

    workbook = D.load()
    margins = {}
    for quorum_hill in (1.0, 1.5, 2.0, 3.0, 4.0):
        arms = tissue.TissueAxis(
            quorum_hill=quorum_hill, anoxic_repression=10.0, glucose_repression=10.0
        ).arms(workbook)
        row = arms.loc[arms["total_ratio"].idxmin()]
        margins[quorum_hill] = (float(row["total_ratio"]), str(row["label"]))

    printed = {1.0: 21.85, 1.5: 16.57, 2.0: 11.90, 3.0: 6.13, 4.0: 3.16}
    for quorum_hill, expected in printed.items():
        assert margins[quorum_hill][0] == pytest.approx(expected, abs=0.01)

    # The published span (0.95-1.5) and the inherited prior (2.0) all clear it.
    assert all(margins[n][0] > 10.0 for n in (1.0, 1.5, 2.0))
    # Well above the published range it does not, which is worth knowing and is
    # why 2.5 reports the span rather than a point.
    assert margins[3.0][0] < 10.0

    # Low n_Q puts the mucosa last; raising it hands the bottleneck to the lumen.
    assert margins[1.0][1] == "Colonic mucosa"
    assert "dysbiosis" in margins[4.0][1]
