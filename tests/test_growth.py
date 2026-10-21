"""Module 2.3 results, pinned."""

from __future__ import annotations

import numpy as np
import pytest

from src import data as D
from src import growth as GR


@pytest.fixture(scope="module")
def wb() -> D.Workbook:
    return D.load()


@pytest.fixture(scope="module")
def fits(wb):
    return GR.fit_table(wb).set_index(["construct", "condition"])


# -- the misfit is the first hour, not the growth law --------------------


def test_dropping_t0_fixes_the_normoxic_corners(fits):
    """9.23's RMSE 0.166 problem, localised."""
    for construct in ("GSDMD-SsrA", "GSDMD"):
        row = fits.loc[(construct, "有氧无酸")]
        assert row["rmse_gompertz_all"] > 0.14
        assert row["rmse_gompertz_from_1h"] < 0.03
        assert row["improvement_from_dropping_t0"] > 5.0


def test_hypoxic_corners_were_never_misfitted(fits):
    """No burst there, so removing t = 0 changes essentially nothing."""
    for construct in ("GSDMD-SsrA", "GSDMD"):
        for condition in ("无氧无酸", "无氧有酸"):
            row = fits.loc[(construct, condition)]
            assert row["rmse_gompertz_all"] < 0.05
            assert 0.9 < row["improvement_from_dropping_t0"] < 1.6


def test_freeing_the_initial_condition_does_not_help(fits):
    """So the problem is the shape of the first hour, not the anchor value."""
    for construct in ("GSDMD-SsrA", "GSDMD"):
        row = fits.loc[(construct, "有氧无酸")]
        assert row["rmse_monomolecular_free_start"] > 0.8 * row["rmse_gompertz_all"]
        # and the fitted start barely moves off 1.0
        assert row["fitted_start"] < 1.25


# -- the burst is real growth, not a reading artefact --------------------


def test_the_burst_is_abolished_only_in_the_self_toxic_construct(wb):
    """A plate artefact cannot know which wells carry the untagged construct."""
    table = GR.burst_tracks_induction(wb).set_index(["construct", "condition"])
    for condition in ("有氧有酸", "无氧有酸"):
        tagged = table.loc[("GSDMD-SsrA", condition), "burst_retained"]
        untagged = table.loc[("GSDMD", condition), "burst_retained"]
        assert tagged > 0.75, condition
        assert untagged < 0.20, condition
        assert tagged / untagged > 4.0, condition


def test_the_tagged_construct_controls_for_the_medium(wb):
    """Same lactate, same oxygen; only the degron differs."""
    table = GR.burst_tracks_induction(wb).set_index(["construct", "condition"])
    # the tagged strain keeps nearly all of its burst under lactate
    assert table.loc[("GSDMD-SsrA", "无氧有酸"), "burst_retained"] > 0.9


def test_phase_rates_differ_by_more_than_an_order_of_magnitude(wb):
    rates = GR.phase_rates(wb)
    uninduced = rates[rates.condition.isin(["有氧无酸", "无氧无酸"])]
    assert uninduced["ratio"].min() > 10.0


# -- the plateau is what propagates, and it is tight ---------------------


def test_capacities_match_the_values_used_downstream(wb):
    """Module 3.1's densities must be these numbers."""
    from src import tissue as T

    table = GR.capacities(wb)
    tagged = table[table.construct == "GSDMD-SsrA"].set_index("condition")["capacity"]
    measured = T.measured_capacities(wb)
    for condition, value in measured.items():
        assert tagged[condition] == pytest.approx(value, rel=1e-12)


def test_capacities_are_determined_to_within_about_15_percent(wb):
    table = GR.capacities(wb)
    assert table["relative_precision"].max() < 0.16
    assert table["relative_precision"].min() < 0.02
    assert (table["n"] == 3).all()


def test_normoxic_capacities_are_tighter_than_hypoxic_ones(wb):
    table = GR.capacities(wb).set_index(["construct", "condition"])
    normoxic = table.loc[("GSDMD-SsrA", "有氧无酸"), "relative_precision"]
    hypoxic = table.loc[("GSDMD-SsrA", "无氧有酸"), "relative_precision"]
    assert normoxic < hypoxic


def test_the_misfit_does_not_propagate():
    """Executable record: nothing downstream reads a fitted trajectory."""
    assert GR.misfit_propagates() is False


# -- the growth models behave --------------------------------------------


def test_monomolecular_has_its_maximum_rate_at_the_origin():
    t = np.linspace(0, 10, 201)
    y = GR.monomolecular(t, cap=3.0, start=1.0, k=0.5)
    rates = np.diff(y)
    assert np.all(np.diff(rates) < 0)  # monotonically decelerating


def test_gompertz_has_an_interior_inflection():
    t = np.linspace(0, 20, 401)
    y = GR.gompertz(t, cap=3.0, b=3.0, c=0.4)
    rates = np.diff(y)
    peak = int(np.argmax(rates))
    assert 0 < peak < len(rates) - 1  # the lag is why it misfits a t=0 burst
