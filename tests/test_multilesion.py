"""Module 4.4 results, pinned.

The first group validates the closed-form field against the PDE it is supposed
to solve, so the rest of the module does not rest on my algebra.
"""

from __future__ import annotations

import numpy as np
import pytest

from src import multilesion as M


@pytest.fixture(scope="module")
def field() -> M.AHLField:
    return M.AHLField()


# -- the closed form really solves the equation ---------------------------


def _radial_laplacian(f, r: float, h: float = 10.0) -> float:
    """``C'' + 2 C' / r`` by central differences.

    ``h`` must be large enough that the second difference, which is of order
    ``C'' h^2 ~ h^2 / lambda^2``, stays well above double-precision noise on
    values of order 1e-3. At h = 1e-3 µm with lambda = 3000 µm the noise
    exceeds the signal; 10 µm is still 1/300 of the length scale.
    """
    second = (f(r + h) - 2 * f(r) + f(r - h)) / h**2
    first = (f(r + h) - f(r - h)) / (2 * h)
    return second + 2 * first / r


@pytest.mark.parametrize("radius_um", [150.0, 400.0, 1000.0])
def test_interior_field_satisfies_the_pde(field, radius_um):
    """``lambda^2 grad^2 C - C + 1 = 0`` inside a producing lesion."""
    lam = field.diffusion_length_um
    for r in (0.3 * radius_um, 0.6 * radius_um, 0.9 * radius_um):
        residual = lam**2 * _radial_laplacian(
            lambda x: field.inside(x, radius_um), r
        ) - field.inside(r, radius_um) + 1.0
        assert abs(residual) < 1e-5, (radius_um, r, residual)


@pytest.mark.parametrize("radius_um", [150.0, 400.0, 1000.0])
def test_exterior_field_satisfies_the_homogeneous_pde(field, radius_um):
    """``lambda^2 grad^2 C - C = 0`` outside, where there is no production."""
    lam = field.diffusion_length_um
    for r in (1.5 * radius_um, 3.0 * radius_um, 1000.0 + radius_um):
        residual = lam**2 * _radial_laplacian(
            lambda x: field.outside(x, radius_um), r
        ) - field.outside(r, radius_um)
        assert abs(residual) < 1e-5, (radius_um, r, residual)


@pytest.mark.parametrize("radius_um", [150.0, 400.0, 1000.0, 3000.0])
def test_interior_and_exterior_match_at_the_boundary(field, radius_um):
    assert field.inside(radius_um, radius_um) == pytest.approx(
        field.outside(radius_um, radius_um), rel=1e-10
    )


def test_interior_tends_to_the_centre_value(field):
    for radius_um in (150.0, 1000.0):
        assert field.inside(1e-9, radius_um) == pytest.approx(
            field.centre_of_isolated(radius_um), rel=1e-12
        )


def test_far_field_reduces_to_the_point_source_kernel(field):
    """``Q / (4 pi D r) exp(-r/lambda)`` in normalised units, for a small source."""
    lam = field.diffusion_length_um
    radius_um = 50.0
    r = 20_000.0
    expected = radius_um**3 / (3 * lam**2 * r) * np.exp(-r / lam)
    assert field.outside(r, radius_um) == pytest.approx(expected, rel=1e-6)


def test_series_and_closed_form_agree_across_the_switchover(field):
    """The series must not introduce a step at the switchover."""
    lam = field.diffusion_length_um
    for fn in (field.centre_of_isolated, lambda r: field.outside(10 * lam, r)):
        below = fn(0.999 * M._SMALL * lam)
        above = fn(1.001 * M._SMALL * lam)
        assert above / below == pytest.approx(1.0, rel=1e-2)


def test_series_beats_the_closed_form_where_it_is_used(field):
    """Justifies the threshold: below it, cancellation dominates."""
    lam = field.diffusion_length_um
    tiny = 1e-6
    series = tiny**2 / 2 - tiny**3 / 3 + tiny**4 / 8 - tiny**5 / 30 + tiny**6 / 144
    naive = 1.0 - (1.0 + tiny) * np.exp(-tiny)
    assert field.centre_of_isolated(tiny * lam) == pytest.approx(series, rel=1e-15)
    assert abs(naive / series - 1.0) > 1e-5  # the closed form has lost precision


def test_equivalent_radius_round_trips(field):
    for radius_um in (150.0, 400.0, 1000.0, 3000.0):
        concentration = field.centre_of_isolated(radius_um)
        assert field.equivalent_isolated_radius(concentration) == pytest.approx(
            radius_um, rel=1e-6
        )


# -- superposition is exact because there is no autoinduction ------------


def test_superposition_is_additive(field):
    """LuxI sits under pPepT, not pLux, so the equation is linear."""
    radius_um = 150.0
    pair = np.array([[0.0, 0.0, 0.0], [600.0, 0.0, 0.0]])
    both = field.centre_in_cluster(pair, radius_um)
    alone = field.centre_of_isolated(radius_um)
    neighbour = field.outside(600.0, radius_um)
    assert both == pytest.approx(alone + neighbour, rel=1e-12)


def test_overlapping_lesions_are_refused(field):
    touching_too_close = np.array([[0.0, 0.0, 0.0], [299.0, 0.0, 0.0]])
    with pytest.raises(ValueError, match="overlap"):
        field.centre_in_cluster(touching_too_close, 150.0)


def test_fcc_shell_has_twelve_equidistant_neighbours():
    positions = M.fcc_first_shell(300.0)
    assert len(positions) == 13
    distances = np.linalg.norm(positions[1:] - positions[0], axis=1)
    assert distances == pytest.approx(np.full(12, 300.0), rel=1e-9)


# -- the headline: clusters do not reach the ON band ---------------------


def test_cooperation_is_real_but_weak_at_realistic_spacing(field):
    scan = M.cluster_scan(radius_um=150.0).set_index(["spacing_um", "n_lesions"])
    # touching lesions do shift a micro-lesion out of the OFF band
    assert scan.loc[(300.0, 13), "equivalent_isolated_radius_um"] == pytest.approx(333.0, abs=1.0)
    # but at millimetre spacing the shift is small
    assert scan.loc[(1000.0, 13), "equivalent_isolated_radius_um"] == pytest.approx(207.0, abs=1.0)
    assert scan.loc[(2000.0, 125), "equivalent_isolated_radius_um"] == pytest.approx(201.0, abs=1.0)


def test_no_cluster_in_the_scan_reaches_the_on_band():
    """The safety-positive result: 9.23's finding 4 survives the extension."""
    scan = M.cluster_scan(radius_um=150.0)
    assert not scan["reaches_on_band"].any()
    assert scan["equivalent_isolated_radius_um"].max() < M.LESION_ON_UM


def test_reaching_the_on_band_needs_a_contiguous_mass(field):
    """512 touching 150 µm lesions is a 2.4 mm block, not micrometastases."""
    for side, expected_on in ((7, False), (8, True)):
        positions = M.cubic_lattice(side, 300.0)
        equivalent = field.equivalent_isolated_radius(
            field.centre_in_cluster(positions, 150.0)
        )
        assert (equivalent >= M.LESION_ON_UM) is expected_on, (side, equivalent)


def test_dispersion_is_always_worse_than_compaction():
    """A cluster is worth less than one nodule of the same total volume."""
    table = M.volume_equivalence()
    multi = table[table.n_lesions > 1]["equivalent_over_volume_matched"]
    assert (multi < 1.0).all()
    assert multi.min() > 0.8  # the penalty is real but bounded


def test_cooperation_factor_grows_with_count_and_falls_with_spacing(field):
    radius_um = 150.0
    tight = M.cooperation_factor(M.cubic_lattice(3, 300.0), radius_um, field)
    loose = M.cooperation_factor(M.cubic_lattice(3, 2000.0), radius_um, field)
    bigger = M.cooperation_factor(M.cubic_lattice(5, 300.0), radius_um, field)
    assert tight > loose > 1.0
    assert bigger > tight


def test_random_clusters_sit_between_the_lattice_bounds(field):
    positions = M.random_cluster(13, 900.0, 150.0)
    equivalent = field.equivalent_isolated_radius(
        field.centre_in_cluster(positions, 150.0)
    )
    assert M.LESION_OFF_UM < equivalent < M.LESION_ON_UM


def test_the_cluster_conclusion_survives_a_tenfold_screening_length() -> None:
    """3.2's lambda table, recomputed.

    `lambda` = 3000 um is inherited from last cycle's run manifest and is the
    least defensible number in the section. The page's defence is not that the
    value is right but that the conclusion -- no cluster reaches the ON band
    below 512 lesions -- holds across a ten-fold span, and that a *shorter*
    screening length makes it harder rather than easier.
    """
    from src import multilesion as M

    counts = (1, 2, 4, 8, 13, 27, 64, 125, 216, 343, 512, 729, 1000)
    printed = {1000.0: (608.4, 888.7, 1000), 3000.0: (651.7, 1009.8, 512),
               10000.0: (665.9, 1049.4, 512)}

    for diffusion_length, (at_125, at_512, first_on) in printed.items():
        frame = M.volume_equivalence(
            counts=counts, field=M.AHLField(diffusion_length_um=diffusion_length)
        ).set_index("n_lesions")
        assert frame.loc[125, "equivalent_isolated_radius_um"] == pytest.approx(at_125, abs=0.1)
        assert frame.loc[512, "equivalent_isolated_radius_um"] == pytest.approx(at_512, abs=0.1)

        reaching = frame[frame["equivalent_isolated_radius_um"] >= M.LESION_ON_UM]
        assert int(reaching.index[0]) == first_on, diffusion_length
        assert int(reaching.index[0]) >= 512, "a cluster must never turn on sooner"
