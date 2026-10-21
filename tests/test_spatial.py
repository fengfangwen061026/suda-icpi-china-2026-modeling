"""Modules 4.3 and 4.5 results, pinned."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.integrate import quad

from src import multilesion as ML
from src import spatial as SP


# -- the escape closed form is right -------------------------------------


@pytest.mark.parametrize("diffusion_length_um", [300.0, 670.8, 3000.0])
def test_escape_closed_form_matches_direct_integration(diffusion_length_um):
    """Steady state: decay outside the nodule, over total decay."""
    radius = SP.NODULE_RADIUS_UM
    field = ML.AHLField(diffusion_length_um=diffusion_length_um)
    outside = quad(
        lambda r: float(field.outside(r, radius)) * 4 * np.pi * r**2,
        radius,
        radius + 60 * diffusion_length_um,
        limit=400,
    )[0]
    inside = quad(
        lambda r: float(field.inside(r, radius)) * 4 * np.pi * r**2, 0, radius, limit=400
    )[0]
    numerical = outside / (outside + inside)
    assert SP.escape_fraction(radius, diffusion_length_um) == pytest.approx(
        numerical, rel=1e-4
    )


def test_escape_falls_as_the_range_shortens():
    lengths = sorted(SP.DIFFUSION_LENGTHS_UM.values())
    escapes = [SP.escape_fraction(SP.NODULE_RADIUS_UM, length) for length in lengths]
    assert escapes == sorted(escapes)


def test_everything_leaks_heavily_including_the_tagged_effector():
    """Both constructs lose most of what they make to the surroundings."""
    table = SP.length_scale_table().set_index("species")
    assert table.loc["GSDMD-N (no SsrA)", "escape_fraction"] == pytest.approx(0.911, abs=0.002)
    assert table.loc["GSDMD-N (+SsrA)", "escape_fraction"] == pytest.approx(0.732, abs=0.002)
    assert table["escape_fraction"].min() > 0.7


def test_only_the_tagged_effector_is_shorter_ranged_than_the_nodule():
    table = SP.length_scale_table().set_index("species")
    assert table.loc["GSDMD-N (+SsrA)", "shorter_than_nodule"]
    assert not table.loc["GSDMD-N (no SsrA)", "shorter_than_nodule"]
    assert int(table["shorter_than_nodule"].sum()) == 1


# -- correction 1: where SsrA's spatial benefit comes from ---------------


def test_confinement_is_the_small_part_of_the_ssra_benefit():
    benefit = SP.ssra_spatial_benefit()
    assert benefit.confinement_gain == pytest.approx(1.25, abs=0.02)
    assert benefit.production_gain == pytest.approx(5.375, abs=0.001)
    assert benefit.total_offtarget_reduction == pytest.approx(6.7, abs=0.1)
    assert benefit.confinement_share == pytest.approx(0.12, abs=0.02)


def test_retention_improves_threefold_even_though_confinement_barely_moves():
    """Both statements are true; 9.23 quoted the flattering one."""
    benefit = SP.ssra_spatial_benefit()
    assert benefit.retention_gain == pytest.approx(3.02, abs=0.05)
    assert benefit.confinement_gain < 1.3


# -- correction 2: flatness is a boundary condition ----------------------


def test_free_diffusion_gives_a_graded_field_not_a_flat_one():
    """9.23 reports 1.01-1.02 under its washout boundary; free field disagrees."""
    table = SP.length_scale_table().set_index("species")
    for species in ("AHL", "GSDMD-N (+SsrA)"):
        assert table.loc[species, "core_rim_free_field"] > 1.5
    assert table.loc["GSDMD-N (+SsrA)", "core_rim_free_field"] == pytest.approx(
        2.07, abs=0.02
    )
    # and 9.23's own numbers are far below every free-field value
    assert max(SP.CORE_RIM_9_23.values()) < table["core_rim_free_field"].min()


def test_long_range_does_not_by_itself_flatten_the_field():
    """Lactate has the longest range of all and is still graded in free field."""
    ratio = SP.core_rim_ratio_free_field(
        SP.NODULE_RADIUS_UM, SP.DIFFUSION_LENGTHS_UM["lactate"]
    )
    assert ratio > 1.5


def test_core_rim_rises_as_the_range_shortens():
    ratios = [
        SP.core_rim_ratio_free_field(SP.NODULE_RADIUS_UM, length)
        for length in sorted(SP.DIFFUSION_LENGTHS_UM.values(), reverse=True)
    ]
    assert ratios == sorted(ratios)


# -- 4.5 dosing ----------------------------------------------------------


def test_schedule_invariance_reproduces_the_9_23_finding():
    """A 32x range of inoculum moves week-long exposure by well under 1 %."""
    table = SP.schedule_invariance()
    spread = table["exposure_vs_lowest"].max() - table["exposure_vs_lowest"].min()
    assert spread < 0.01
    assert table["inoculum"].max() / table["inoculum"].min() == pytest.approx(32.0)


def test_what_the_dose_does_change_is_onset():
    table = SP.schedule_invariance().sort_values("inoculum")
    assert table["time_to_half_max_h"].is_monotonic_decreasing


def test_persistence_is_the_lever():
    table = SP.persistence_lever().set_index("clearance_per_h")
    assert table.loc[0.55, "exposure_vs_no_clearance"] < 0.1
    assert table.loc[1.0, "eliminated"]
    assert not table.loc[0.2, "eliminated"]


def test_exposure_falls_monotonically_with_clearance():
    table = SP.persistence_lever()
    assert list(table["exposure"]) == sorted(table["exposure"], reverse=True)


def test_the_redosing_conclusion_is_flagged_as_circular():
    """9.23's own caveat, as an executable record."""
    flags = SP.redosing_conclusion_is_circular()
    assert flags["conclusion_follows_from_construction"]
    assert not flags["model_permits_extinction"]
    assert not flags["supported_by_data"]
