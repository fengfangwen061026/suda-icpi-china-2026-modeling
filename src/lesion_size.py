"""Module 3.2 -- the lesion-size turn-on (migrated from 9.23).

9.23's finding 4: whole-lesion gate output rises monotonically with radius, by
"14x (dynamic fit) to 6,891x (endpoint-matched)" between r = 150 µm and
r = 1000 µm, with two compounding causes -- a small lesion has no hypoxic volume
so pPepT stays basal, and the AHL pool scales with colonised volume.

Both causes are computable here without a PDE solve:

* the **AHL volume integration** is exactly module 4.4's closed-form field,
  ``centre_of_isolated(R)``, which already encodes how a sphere of radius ``R``
  builds its own signal against a 3000 µm screening length;
* the **hypoxic volume fraction** follows from an oxygen penetration depth,
  calibrated to 9.23's own statement that the 1 % O2 contour sits at 222 µm in a
  400 µm nodule -- i.e. oxygen reaches 178 µm in from the surface.

As in module 3.1, the reported *range* turns out to be the ``n_Q`` span rather
than a measurement uncertainty: the underlying quorum signal ratio across this
size range is about two orders of magnitude, and raising it to a Hill
coefficient somewhere between 1 and 3 is what produces "14x to 6891x".

The safety statement that needs no calibration at all is the geometric one: a
lesion smaller than the penetration depth has **no hypoxic volume whatsoever**,
so the hypoxia arm cannot leave basal however the rest is parameterised.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import multilesion as ML
from .sensors import QUORUM_HILL_PLUX
from . import sensors as S

#: Oxygen penetration depth from the perfused surface, µm.
#: 9.23 `MODEL_SPEC_4_3.md` §2: with its calibrated uptake the 1 % O2 contour
#: falls at 222 µm in a 400 µm nodule, so oxygen reaches 400 - 222 = 178 µm in.
OXYGEN_PENETRATION_UM: float = 178.0

#: Oxygen at the perfused rim and in the hypoxic core, % O2.
RIM_O2_PERCENT: float = 5.0
CORE_O2_PERCENT: float = 0.5

#: The size range 9.23 quoted its turn-on over.
SIZE_REFERENCE_UM: tuple[float, float] = (150.0, 1000.0)
#: Its two published folds, which this module reinterprets.
PUBLISHED_TURN_ON: tuple[float, float] = (14.1, 6891.1)


@dataclass(frozen=True)
class LesionSize:
    """Gate output as a function of isolated lesion radius."""

    penetration_um: float = OXYGEN_PENETRATION_UM
    rim_o2_percent: float = RIM_O2_PERCENT
    core_o2_percent: float = CORE_O2_PERCENT
    quorum_hill: float = QUORUM_HILL_PLUX

    # -- geometry --------------------------------------------------------

    def hypoxic_core_radius(self, radius_um: float | np.ndarray) -> np.ndarray:
        """Radius of the hypoxic core; zero for lesions thinner than the depth."""
        radius = np.asarray(radius_um, dtype=float)
        return np.maximum(radius - self.penetration_um, 0.0)

    def hypoxic_fraction(self, radius_um: float | np.ndarray) -> np.ndarray:
        """Volume fraction of the lesion that is hypoxic."""
        radius = np.asarray(radius_um, dtype=float)
        core = self.hypoxic_core_radius(radius)
        with np.errstate(divide="ignore", invalid="ignore"):
            fraction = np.where(radius > 0, (core / radius) ** 3, 0.0)
        return fraction

    @property
    def smallest_lesion_with_a_hypoxic_core_um(self) -> float:
        """Below this radius the hypoxia arm cannot leave basal. Pure geometry."""
        return self.penetration_um

    # -- the two mechanisms ----------------------------------------------

    def mean_hypoxia_activity(self, radius_um: float | np.ndarray) -> np.ndarray:
        """Volume-averaged pPepT activity, which sets AHL production per volume."""
        sensor = S.HypoxiaSensor()
        core = float(sensor(self.core_o2_percent))
        rim = float(sensor(self.rim_o2_percent))
        fraction = self.hypoxic_fraction(radius_um)
        return fraction * core + (1.0 - fraction) * rim

    def volume_kernel(self, radius_um: float | np.ndarray) -> np.ndarray:
        """Module 4.4's closed-form centre field for a unit-strength source."""
        field = ML.AHLField()
        return np.asarray(field.centre_of_isolated(radius_um), dtype=float)

    def quorum_signal(self, radius_um: float | np.ndarray) -> np.ndarray:
        """Relative AHL at the lesion centre: production per volume x integration."""
        return self.mean_hypoxia_activity(radius_um) * self.volume_kernel(radius_um)

    def gate_output(self, radius_um: float | np.ndarray) -> np.ndarray:
        """Quorum arm in its sub-threshold power-law regime (see module 3.1)."""
        return self.quorum_signal(radius_um) ** self.quorum_hill

    # -- what the turn-on is worth ---------------------------------------

    def turn_on_fold(
        self, small_um: float = SIZE_REFERENCE_UM[0], large_um: float = SIZE_REFERENCE_UM[1]
    ) -> float:
        return float(self.gate_output(large_um) / self.gate_output(small_um))

    def turn_on_radius(self, fraction_of: float = 1000.0, level: float = 0.5) -> float:
        """Radius at which the gate reaches ``level`` of its value at ``fraction_of``."""
        from scipy.optimize import brentq

        target = level * float(self.gate_output(fraction_of))
        return float(
            brentq(lambda r: float(self.gate_output(r)) - target, 1.0, fraction_of, xtol=1e-6)
        )


def size_profile(
    radii_um: np.ndarray | None = None, quorum_hill: float = QUORUM_HILL_PLUX
) -> pd.DataFrame:
    """Every component of the turn-on, across lesion radius."""
    if radii_um is None:
        radii_um = np.array([50, 100, 150, 178, 200, 300, 400, 600, 800, 1000], dtype=float)
    model = LesionSize(quorum_hill=quorum_hill)
    reference = float(model.gate_output(SIZE_REFERENCE_UM[0]))
    return pd.DataFrame(
        {
            "radius_um": radii_um,
            "hypoxic_core_um": model.hypoxic_core_radius(radii_um),
            "hypoxic_fraction": model.hypoxic_fraction(radii_um),
            "mean_hypoxia_activity": model.mean_hypoxia_activity(radii_um),
            "volume_kernel": model.volume_kernel(radii_um),
            "quorum_signal": model.quorum_signal(radii_um),
            "gate_output": model.gate_output(radii_um),
            "fold_over_150um": model.gate_output(radii_um) / reference,
        }
    )


def mechanism_split(
    small_um: float = SIZE_REFERENCE_UM[0], large_um: float = SIZE_REFERENCE_UM[1]
) -> dict[str, float]:
    """How much of the turn-on each cause contributes, before the Hill exponent."""
    model = LesionSize()
    hypoxia = float(
        model.mean_hypoxia_activity(large_um) / model.mean_hypoxia_activity(small_um)
    )
    volume = float(model.volume_kernel(large_um) / model.volume_kernel(small_um))
    return {
        "hypoxic_volume_fold": hypoxia,
        "ahl_integration_fold": volume,
        "quorum_signal_fold": hypoxia * volume,
    }


#: 9.23's own stated quorum signal across the size range: "Q rises from 0.3 to
#: 6.6 relative units" (MODEL_SPEC_4_3.md finding 4).
QUORUM_SIGNAL_FOLD_9_23: float = 6.6 / 0.3

#: The two quorum Hill coefficients 9.23's two calibrations settled on.
QUORUM_HILLS_9_23: tuple[float, float] = (1.0, 2.978)


def free_field_overestimates_by() -> float:
    """How much the infinite-medium kernel exceeds 9.23's signal fold.

    This module's closed form has no boundary sink: it solves an isolated sphere
    in an unbounded medium screened at 3000 µm. 9.23's PDE instead imposes a
    **Robin washout at the nodule surface**, which drains the large nodule's
    advantage. So the free-field calculation is an *upper bound* on the turn-on,
    and the gap is the price of not modelling that boundary.
    """
    return mechanism_split()["quorum_signal_fold"] / QUORUM_SIGNAL_FOLD_9_23


def quorum_hill_span(
    hills=(1.0, 1.5, 2.0, 2.978, 4.0),
    signal_fold: float | None = None,
) -> pd.DataFrame:
    """The published 14x-6891x range, reinterpreted as an n_Q span.

    Uses 9.23's **own** signal fold by default, so the comparison tests the
    interpretation rather than this module's boundary treatment.
    """
    signal_fold = QUORUM_SIGNAL_FOLD_9_23 if signal_fold is None else signal_fold
    rows = []
    for hill in hills:
        fold = signal_fold**hill
        rows.append(
            {
                "quorum_hill": hill,
                "quorum_signal_fold": signal_fold,
                "gate_turn_on_fold": fold,
                "brackets_published": PUBLISHED_TURN_ON[0] <= fold <= PUBLISHED_TURN_ON[1],
            }
        )
    return pd.DataFrame(rows)


def published_range_is_a_hill_span() -> dict[str, float]:
    """Does n_Q alone, applied to 9.23's own signal fold, give its published range?"""
    low_hill, high_hill = QUORUM_HILLS_9_23
    return {
        "signal_fold": QUORUM_SIGNAL_FOLD_9_23,
        "predicted_low": QUORUM_SIGNAL_FOLD_9_23**low_hill,
        "predicted_high": QUORUM_SIGNAL_FOLD_9_23**high_hill,
        "published_low": PUBLISHED_TURN_ON[0],
        "published_high": PUBLISHED_TURN_ON[1],
    }
