"""Module 6 results, pinned.

The model is scenario-only, so the assertions are about its *structure* -- the
limits it respects, the thresholds it predicts, the monotonicities -- not about
any efficacy number.
"""

from __future__ import annotations

import numpy as np
import pytest

from src import immune as I


@pytest.fixture(scope="module")
def cascade() -> I.ImmuneCascade:
    return I.ImmuneCascade(evasion_scale=0.2)


# -- the reduction behaves at its limits ---------------------------------


def test_no_immunity_leaves_the_lesion_at_carrying_capacity(cascade):
    assert cascade.escape_burden(0.0) == pytest.approx(1.0, rel=1e-12)
    assert cascade.burden_reduction(0.0) == pytest.approx(0.0, abs=1e-12)


def test_at_the_control_threshold_the_escape_state_is_one_minus_h(cascade):
    assert cascade.escape_burden(1.0) == pytest.approx(1.0 - cascade.evasion_scale, rel=1e-12)


def test_escape_burden_falls_monotonically_with_pressure(cascade):
    pressures = np.linspace(0.0, 1.8, 50)
    burdens = cascade.escape_burden(pressures)
    assert np.all(np.diff(burdens) <= 1e-12)


def test_equilibria_are_actually_equilibria(cascade):
    """Each reported escape burden must zero the growth rate."""
    for pressure in (0.3, 0.8, 1.2, 1.7):
        burden = cascade.escape_burden(pressure)
        assert burden > 0
        assert cascade.growth_rate(burden, pressure) == pytest.approx(0.0, abs=1e-12)


def test_max_treatable_burden_is_also_an_equilibrium(cascade):
    """The basin boundary is the unstable root, so it is also a fixed point."""
    for pressure in (1.1, 1.4, 1.7):
        boundary = cascade.max_treatable_burden(pressure)
        assert 0.0 < boundary < 1.0
        assert cascade.growth_rate(boundary, pressure) == pytest.approx(0.0, abs=1e-12)


def test_the_escape_state_is_stable_and_the_boundary_is_not(cascade):
    pressure = 1.5
    stable = cascade.escape_burden(pressure)
    boundary = cascade.max_treatable_burden(pressure)
    eps = 1e-4
    # just below the stable state the lesion grows back up to it
    assert cascade.growth_rate(stable - eps, pressure) > 0
    assert cascade.growth_rate(stable + eps, pressure) < 0
    # the boundary repels on both sides
    assert cascade.growth_rate(boundary - eps, pressure) < 0
    assert cascade.growth_rate(boundary + eps, pressure) > 0


# -- bistability, and the two thresholds ---------------------------------


def test_bistable_window_exists_between_the_two_thresholds(cascade):
    guaranteed = cascade.guaranteed_eradication_pressure()
    assert guaranteed == pytest.approx(1.8, abs=0.001)
    midway = (1.0 + guaranteed) / 2
    # small lesions cleared, large ones not
    assert 0.0 < cascade.max_treatable_burden(midway) < cascade.escape_burden(midway)


def test_above_guaranteed_threshold_nothing_escapes(cascade):
    for pressure in (1.81, 2.5, 10.0):
        assert cascade.escape_burden(pressure) == 0.0
        assert cascade.max_treatable_burden(pressure) == pytest.approx(1.0)


def test_early_saturating_killing_makes_eradication_harder():
    """Smaller h means a fixed CTL pool is evaded sooner by a big lesion."""
    thresholds = [
        I.ImmuneCascade(h).guaranteed_eradication_pressure() for h in (0.05, 0.1, 0.2, 0.3, 0.5)
    ]
    assert thresholds == sorted(thresholds, reverse=True)
    assert thresholds[0] == pytest.approx(5.51, abs=0.01)
    assert thresholds[-1] == pytest.approx(1.125, abs=0.01)


# -- the structural feasibility ceiling ----------------------------------


def test_immune_pressure_is_bounded_by_the_effective_gain():
    """Psi < epsilon G for every flux, because x/(1+x) < 1."""
    for flux in (0.01, 1.0, 100.0, 1e6):
        psi = I.ImmuneCascade.immune_pressure(flux, epsilon=0.2, gain=10.0)
        assert psi < 0.2 * 10.0


def test_effective_gain_below_one_is_infeasible_at_any_flux():
    """The hard ceiling: no amount of pyroptosis rescues epsilon G <= 1."""
    assert not I.ImmuneCascade.is_feasible(epsilon=0.1, gain=5.0)
    assert I.ImmuneCascade.required_flux(epsilon=0.1, gain=5.0) == float("inf")
    huge = I.ImmuneCascade.immune_pressure(1e9, epsilon=0.1, gain=5.0)
    assert huge < 1.0


def test_required_flux_closed_form_and_divergence():
    assert I.ImmuneCascade.required_flux(epsilon=0.2, gain=10.0) == pytest.approx(1.0)
    assert I.ImmuneCascade.required_flux(epsilon=1.0, gain=2.0) == pytest.approx(1.0)
    # diverges as the effective gain approaches 1 from above
    near = I.ImmuneCascade.required_flux(epsilon=1.0, gain=1.001)
    assert near > 500


def test_required_flux_is_exactly_the_pressure_one_point():
    """x_min must be the flux at which Psi = 1."""
    for epsilon, gain in ((0.2, 10.0), (0.5, 5.0), (1.0, 3.0)):
        x = I.ImmuneCascade.required_flux(epsilon=epsilon, gain=gain)
        assert I.ImmuneCascade.immune_pressure(x, epsilon=epsilon, gain=gain) == pytest.approx(
            1.0, rel=1e-12
        )


def test_cold_tumour_needs_a_much_larger_cascade_gain():
    table = I.cold_tumour_penalty().set_index(["cascade_gain", "epsilon"])
    # a permissive tumour is feasible even at modest gain
    assert table.loc[(2.0, 1.0), "feasible"]
    # a cold one is not, at the same gain
    assert not table.loc[(2.0, 0.1), "feasible"]
    # and at epsilon = 0.05 even a gain of 10 fails
    assert not table.loc[(10.0, 0.05), "feasible"]
    assert table.loc[(30.0, 0.05), "feasible"]


def test_feasibility_boundary_is_the_reciprocal():
    boundary = I.feasibility_boundary(np.array([1.0, 10.0, 100.0]))
    assert list(boundary["min_epsilon"]) == pytest.approx([1.0, 0.1, 0.01])


# -- the supervisor's question 6: local versus distant -------------------


def test_local_versus_distant_split_reports_both(cascade):
    split = I.local_vs_distant_split(0.158, cascade, epsilon=0.2, gain=10.0, normalised_flux=1.0)
    assert split["immune_pressure"] == pytest.approx(1.0, rel=1e-12)
    assert 0.0 < split["local_removed"] < 1.0
    assert 0.0 <= split["distant_removed"] < 1.0
    assert split["total_removed"] == pytest.approx(
        split["local_removed"] + split["distant_removed"], rel=1e-12
    )


def test_distant_contribution_vanishes_when_the_cascade_is_infeasible(cascade):
    split = I.local_vs_distant_split(0.158, cascade, epsilon=0.05, gain=5.0)
    assert not split["eradication_possible"]
    assert split["distant_contribution_share"] < 0.5
