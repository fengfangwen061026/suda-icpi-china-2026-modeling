"""Module 3.2 results, pinned."""

from __future__ import annotations

import numpy as np
import pytest

from src import lesion_size as L
from src import multilesion as ML


@pytest.fixture(scope="module")
def model() -> L.LesionSize:
    return L.LesionSize()


# -- the parameter-free geometric floor ----------------------------------


def test_small_lesions_have_no_hypoxic_core_at_all(model):
    """The one result here that needs no calibration."""
    assert model.smallest_lesion_with_a_hypoxic_core_um == pytest.approx(178.0)
    for radius in (50.0, 100.0, 150.0, 177.9):
        assert model.hypoxic_core_radius(radius) == 0.0
        assert model.hypoxic_fraction(radius) == 0.0
    assert model.hypoxic_core_radius(200.0) == pytest.approx(22.0)


def test_below_the_floor_the_hypoxia_arm_is_flat(model):
    """No hypoxic volume means mean pPepT activity cannot vary with size."""
    values = model.mean_hypoxia_activity(np.array([50.0, 100.0, 150.0, 177.0]))
    assert np.allclose(values, values[0])


def test_hypoxic_fraction_rises_monotonically(model):
    radii = np.linspace(178.0, 2000.0, 60)
    fractions = model.hypoxic_fraction(radii)
    assert np.all(np.diff(fractions) >= -1e-12)
    assert model.hypoxic_fraction(1000.0) == pytest.approx(0.5554, abs=0.001)


# -- the two mechanisms ---------------------------------------------------


def test_mechanism_split(model):
    split = L.mechanism_split()
    assert split["hypoxic_volume_fold"] == pytest.approx(5.293, abs=0.001)
    assert split["ahl_integration_fold"] == pytest.approx(36.91, abs=0.05)
    assert split["quorum_signal_fold"] == pytest.approx(
        split["hypoxic_volume_fold"] * split["ahl_integration_fold"], rel=1e-12
    )


def test_the_ahl_term_is_module_4_4s_kernel_unchanged(model):
    """3.2 reuses 4.4's closed form rather than re-deriving it."""
    field = ML.AHLField()
    for radius in (150.0, 400.0, 1000.0):
        assert model.volume_kernel(radius) == pytest.approx(
            field.centre_of_isolated(radius), rel=1e-12
        )


def test_gate_output_rises_monotonically_with_size(model):
    radii = np.linspace(50.0, 1500.0, 80)
    output = model.gate_output(radii)
    assert np.all(np.diff(output) > 0)


# -- the published range is an n_Q span ----------------------------------


def test_published_range_is_reproduced_by_the_hill_exponent_alone():
    """Using 9.23's *own* signal fold, n_Q in [1, 2.978] brackets its folds."""
    result = L.published_range_is_a_hill_span()
    assert result["signal_fold"] == pytest.approx(22.0)
    assert result["predicted_low"] == pytest.approx(22.0, abs=0.1)
    assert result["predicted_high"] == pytest.approx(9948, rel=0.01)
    # brackets the published pair, within a factor of ~1.6 at each end
    assert result["predicted_low"] / result["published_low"] < 2.0
    assert result["predicted_high"] / result["published_high"] < 2.0


def test_low_hills_land_inside_the_published_range():
    span = L.quorum_hill_span().set_index("quorum_hill")
    assert span.loc[1.0, "brackets_published"]
    assert span.loc[2.0, "brackets_published"]
    assert not span.loc[4.0, "brackets_published"]


def test_turn_on_fold_is_a_power_of_the_signal_fold():
    span = L.quorum_hill_span(hills=(1.0, 2.0, 3.0))
    folds = span["gate_turn_on_fold"].to_numpy()
    assert folds[1] == pytest.approx(folds[0] ** 2, rel=1e-9)
    assert folds[2] == pytest.approx(folds[0] ** 3, rel=1e-9)


# -- honest about what this closed form omits ----------------------------


def test_the_free_field_is_an_upper_bound_and_says_by_how_much():
    """No boundary sink here; 9.23's PDE has a Robin washout at the rim."""
    overestimate = L.free_field_overestimates_by()
    assert overestimate == pytest.approx(8.88, abs=0.01)
    assert overestimate > 1.0


def test_free_field_signal_fold_exceeds_the_9_23_value():
    assert L.mechanism_split()["quorum_signal_fold"] > L.QUORUM_SIGNAL_FOLD_9_23


# -- the profile table ---------------------------------------------------


def test_profile_covers_the_floor_and_is_normalised_at_150um():
    profile = L.size_profile().set_index("radius_um")
    assert profile.loc[150.0, "fold_over_150um"] == pytest.approx(1.0)
    assert profile.loc[178.0, "hypoxic_fraction"] == 0.0
    assert profile.loc[200.0, "hypoxic_fraction"] > 0.0
    assert profile["gate_output"].is_monotonic_increasing


def test_the_geometric_floor_sits_inside_the_histological_bracket() -> None:
    """2.2's corroboration table, recomputed.

    `d_O2` = 178 um was derived from last cycle's 1 % O2 contour, with no
    histology in it. Thomlinson & Gray (1955) measured the same quantity
    directly: necrosis absent below 160 um radius, present above 200 um, viable
    rim never exceeding 180 um. The page claims our value lands inside that
    bracket and that the turn-on barely moves across it. Both are checkable.
    """
    from src import lesion_size as L

    assert 160.0 < L.OXYGEN_PENETRATION_UM < 200.0, "outside the measured bracket"

    printed = {160.0: (0.2160, 4.854e-3), 178.0: (0.1710, 5.119e-3), 200.0: (0.1250, 5.465e-3)}
    for penetration, (hypoxic_fraction, turn_on) in printed.items():
        model = L.LesionSize(penetration_um=penetration)
        # The floor is the penetration depth by construction; that is the point.
        assert model.smallest_lesion_with_a_hypoxic_core_um == pytest.approx(penetration)
        assert model.hypoxic_fraction(400.0) == pytest.approx(hypoxic_fraction, abs=1e-4)
        ratio = model.gate_output(150.0) / model.gate_output(1000.0)
        assert ratio == pytest.approx(turn_on, rel=0.01)

    across = [
        L.LesionSize(penetration_um=p).gate_output(150.0)
        / L.LesionSize(penetration_um=p).gate_output(1000.0)
        for p in (160.0, 200.0)
    ]
    assert max(across) / min(across) == pytest.approx(1.13, abs=0.01), "the quoted 13 %"
