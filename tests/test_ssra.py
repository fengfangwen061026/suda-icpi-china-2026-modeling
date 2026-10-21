"""Module 3.4 results, pinned."""

from __future__ import annotations

import numpy as np
import pytest

from src import ssra as A


@pytest.fixture(scope="module")
def anchors():
    return A.measured_anchors()


# -- convention 2 settles what 9.23 left open ----------------------------


def test_the_block6_potency_ratio_is_rejected_for_the_same_reason_as_11x(anchors):
    assert anchors.potency_ratio_source.startswith("block 5")
    assert anchors.potency_ratio == pytest.approx(1.414, abs=0.001)
    assert anchors.rejected_potency_ratio == pytest.approx(4.699, abs=0.001)
    assert "cross-block" in anchors.rejection_reason


def test_the_rejected_ratio_would_have_flipped_the_decision(anchors):
    """Why the convention matters: it is the difference between keep and drop."""
    crossover = A.crossover_potency_ratio(anchors.biomass_ratio)
    assert anchors.potency_ratio < crossover          # keep
    assert anchors.rejected_potency_ratio > crossover  # would have said drop


# -- the closed-form decision --------------------------------------------


def test_crossover_is_the_reciprocal_of_the_biomass_ratio(anchors):
    """Keep the tag iff the potency it costs is less than the biomass it buys."""
    assert A.crossover_potency_ratio(anchors.biomass_ratio) == pytest.approx(
        1.0 / anchors.biomass_ratio, rel=1e-12
    )
    assert A.crossover_potency_ratio(anchors.biomass_ratio) == pytest.approx(1.710, abs=0.001)


def test_every_dose_says_keep_the_tag():
    """Robustness: the conclusion does not rest on a single anchor."""
    table = A.potency_ratio_by_dose()
    assert table["keep_tag"].all()
    assert table["margin"].min() > 1.2
    # 10 OD is the most pessimistic of the three
    assert table.loc[table.dose_od == 10.0, "potency_ratio"].iloc[0] == table["potency_ratio"].max()
    # and at the lowest dose the tagged construct actually kills slightly more
    assert table.loc[table.dose_od == 6.0, "potency_ratio"].iloc[0] < 1.0


def test_the_eight_od_row_still_carries_its_missing_replicate():
    table = A.potency_ratio_by_dose().set_index("dose_od")
    assert table.loc[8.0, "n_untagged"] == 2
    assert table.loc[6.0, "n_untagged"] == 3
    assert table.loc[10.0, "n_untagged"] == 3


def test_decision_scan_crosses_exactly_at_the_crossover(anchors):
    scan = A.decision_scan(anchors, np.array([1.5, 1.70, 1.72, 2.0]))
    assert list(scan["keep_tag"]) == [True, True, False, False]
    at_crossover = A.crossover_potency_ratio(anchors.biomass_ratio)
    assert A.decision_scan(anchors, np.array([at_crossover]))["delivery_tagged_over_untagged"].iloc[
        0
    ] == pytest.approx(1.0, rel=1e-12)


# -- the continuous tag-strength model -----------------------------------


def test_model_identifies_from_the_conservative_anchor(anchors):
    model = A.TradeoffModel.from_anchors(anchors)
    assert model.pool(0.0) == pytest.approx(5.375, abs=0.001)
    assert model.lam == pytest.approx(0.1226, abs=0.0005)
    assert model.k_export == pytest.approx(0.561, abs=0.002)


def test_built_tag_is_slightly_stronger_than_optimal_but_cheaply_so(anchors):
    model = A.TradeoffModel.from_anchors(anchors)
    optimum = model.optimum_delta()
    assert optimum == pytest.approx(0.149, abs=0.005)
    assert optimum < A.DELTA_BUILT  # built tag is on the strong side
    penalty = 1.0 - model.delivery(A.DELTA_BUILT) / model.delivery(optimum)
    assert penalty == pytest.approx(0.073, abs=0.005)


def test_built_tag_beats_no_tag_by_the_closed_form_margin(anchors):
    model = A.TradeoffModel.from_anchors(anchors)
    ratio = model.delivery(A.DELTA_BUILT) / model.delivery(0.0)
    assert ratio == pytest.approx(A.keep_tag_margin(anchors), rel=1e-6)


def test_model_refuses_to_fit_when_the_tag_costs_no_potency(anchors):
    """At 6 OD the ratio is below 1 and the export form has nothing to identify."""
    cheap = A.Anchors(anchors.biomass_ratio, 0.888, "block 5 @ 6 OD", None, None)
    with pytest.raises(ValueError, match="closed-form decision"):
        A.TradeoffModel.from_anchors(cheap)


# -- the supervisor's half-life question ---------------------------------


def test_half_lives():
    table = A.half_life_table().set_index("variant")
    assert table.loc["untagged", "half_life_h"] == pytest.approx(8.66, abs=0.01)
    assert table.loc["SsrA as built", "half_life_h"] == pytest.approx(1.61, abs=0.01)
    assert table.loc["double SsrA (2x tag)", "half_life_h"] == pytest.approx(0.89, abs=0.01)


# -- ClpXP saturation as a selectivity amplifier -------------------------


def test_saturable_degradation_amplifies_rather_than_merely_damping():
    scan = A.amplification_scan(leak_production=1.0, induced_production=100.0)
    assert scan["amplification"].max() > 10.0


def test_amplification_peaks_inside_the_capacity_window():
    """The peak sits strictly inside the window; the edges are soft, not cliffs."""
    leak, induced = 1.0, 100.0
    scan = A.amplification_scan(leak_production=leak, induced_production=induced)
    best = scan.loc[scan["amplification"].idxmax()]
    assert leak < best["vmax"] < induced
    assert bool(best["in_window"])
    # far outside on either side the degron stops amplifying at all
    assert scan["amplification"].iloc[0] < 1.2    # vmax well below the leak rate
    assert scan["amplification"].iloc[-1] < 1.2   # vmax well above the induced rate
    # the mean inside the window beats the mean outside it by a wide margin
    inside = scan[scan["in_window"]]["amplification"]
    outside = scan[~scan["in_window"]]["amplification"]
    assert inside.mean() > 5 * outside.mean()


def test_capacity_window_is_the_leak_to_induced_interval():
    assert A.capacity_window(2.0, 50.0) == (2.0, 50.0)


def test_half_life_asymmetry_is_the_mechanism():
    """Short in normal tissue, long in tumour -- the same tag, different load."""
    cap = A.ClpXPCapacity(vmax=20.0, km=1.0, gamma=0.35)
    normal = cap.effective_rate(cap.steady_state(1.0))
    tumour = cap.effective_rate(cap.steady_state(100.0))
    assert normal > tumour * 10


def test_steady_state_solves_its_own_balance():
    cap = A.ClpXPCapacity(vmax=20.0, km=1.0, gamma=0.35)
    for production in (0.5, 5.0, 50.0, 500.0):
        pool = cap.steady_state(production)
        balance = cap.vmax * pool / (cap.km + pool) + cap.gamma * pool
        assert balance == pytest.approx(production, rel=1e-9)
