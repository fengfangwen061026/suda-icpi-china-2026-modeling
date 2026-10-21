"""Module 4.4 -- do clustered micro-lesions share AHL and switch each other on?

9.23's finding 4 said an isolated 150 µm lesion stays OFF and a 1000 µm nodule
turns ON, by 14-6891x. Its finding 2 said the AHL diffusion length is ~3000 µm,
i.e. 7.5x a 400 µm nodule. Those two facts together raise a question its 1-D
spherically symmetric solver could not express:

    a cluster of micro-lesions 1-2 mm apart shares one AHL pool.
    Does it cross the threshold that none of its members reaches alone?

Both answers are useful. Cooperating means the circuit can clear
micrometastases that the single-lesion model predicts it would miss. Not
cooperating hardens the micro-lesion safety argument.

Why this is analytic, not numerical
-----------------------------------
In this circuit ``LuxI`` sits under ``pPepT``, **not** under ``pLux`` (team
design note, 2026-07-15: "pPepT 低氧输入驱动 LuxI 产生 AHL"). So AHL production
does not depend on AHL concentration: there is no autoinduction loop, unlike
canonical quorum sensing. The steady-state AHL equation

    D grad^2 C - delta C + q(x) = 0

is therefore **linear**, superposition is exact, and an arbitrary 3-D
arrangement of spherical sources is solved by summing closed-form single-sphere
fields. No 2-D axisymmetric grid is needed, and the result is exact rather than
discretised.

This also means the quorum module is a *colonised-volume integrator*, not a
bistable switch: no hysteresis, no sharp threshold crossing, a graded response.
That is a property of what was built, and it is what makes clusters add up.

Scale-free reporting
--------------------
Absolute AHL depends on ``beta_Q / K_Q``, which the two 9.23 calibrations
disagree on by 27x. So nothing here reports an absolute concentration or an
ON/OFF verdict. Everything is expressed as an **equivalent isolated radius**:
the radius of a single isolated lesion that would produce the same AHL at its
own centre. That maps onto 9.23's own 150 µm (OFF) to 1000 µm (ON) band without
needing the threshold itself.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import brentq

#: AHL diffusion length sqrt(D/delta), µm. From 9.23 `run_manifest.json`.
AHL_DIFFUSION_LENGTH_UM: float = 3000.0
#: The band 9.23 established for an isolated lesion: OFF at 150, ON at 1000.
LESION_OFF_UM: float = 150.0
LESION_ON_UM: float = 1000.0

#: Switchover to series expansions. Both closed forms below cancel to leading
#: order, but they still carry ~12 significant digits at alpha = 0.05 (a 150 µm
#: lesion) and only degrade below ~0.01. Switching earlier makes things *worse*:
#: a 4-term series at alpha = 0.05 is accurate to 1e-5, the closed form to 1e-13.
_SMALL = 0.01


def _centre_shape(alpha: np.ndarray | float) -> np.ndarray | float:
    """``1 - (1 + a)exp(-a)``, the normalised centre concentration of one sphere.

    Series ``a^2/2 - a^3/3 + a^4/8 - a^5/30 + a^6/144`` below ``_SMALL``.
    """
    a = np.asarray(alpha, dtype=float)
    series = (
        a**2 / 2.0 - a**3 / 3.0 + a**4 / 8.0 - a**5 / 30.0 + a**6 / 144.0
    )
    exact = 1.0 - (1.0 + a) * np.exp(-a)
    return np.where(a < _SMALL, series, exact)


def _outside_amplitude(alpha: np.ndarray | float) -> np.ndarray | float:
    """``a*exp(a) - (1 + a)sinh(a)``, the exterior field amplitude.

    Series ``a^3/3 + a^5/30 + a^7/840`` below ``_SMALL``; the two terms cancel
    to third order, so the closed form is unusable for very small spheres.
    """
    a = np.asarray(alpha, dtype=float)
    series = a**3 / 3.0 + a**5 / 30.0 + a**7 / 840.0
    exact = a * np.exp(a) - (1.0 + a) * np.sinh(a)
    return np.where(a < _SMALL, series, exact)


@dataclass(frozen=True)
class AHLField:
    """Steady-state AHL from uniformly producing spherical lesions.

    All concentrations are normalised by ``q / delta``, the level a lesion of
    infinite radius would reach, so they are dimensionless and independent of
    the unidentified ``beta_Q / K_Q`` scale.
    """

    diffusion_length_um: float = AHL_DIFFUSION_LENGTH_UM

    def centre_of_isolated(self, radius_um: float | np.ndarray) -> float | np.ndarray:
        """Normalised AHL at the centre of a single isolated lesion."""
        alpha = np.asarray(radius_um, dtype=float) / self.diffusion_length_um
        out = _centre_shape(alpha)
        return float(out) if out.ndim == 0 else out

    def inside(self, distance_um: float | np.ndarray, radius_um: float) -> float | np.ndarray:
        """Normalised AHL at ``distance_um <= radius_um`` inside one lesion.

        ``1 - (1 + a)exp(-a) sinh(s)/s`` with ``s = r/lambda``. Written as

            centre_shape(a) - (1 + a)exp(-a) * (sinh(s)/s - 1)

        so that the ``1 - (1+a)exp(-a)`` cancellation is taken from the same
        stable series :func:`_centre_shape` uses, and ``sinh(s)/s - 1`` from its
        own series. Evaluating the raw expression instead loses ~5 significant
        digits for a 150 µm lesion, which is enough to break the boundary match
        against :meth:`outside`.
        """
        lam = self.diffusion_length_um
        alpha = radius_um / lam
        s = np.asarray(distance_um, dtype=float) / lam
        series = s**2 / 6.0 + s**4 / 120.0 + s**6 / 5040.0
        with np.errstate(divide="ignore", invalid="ignore"):
            exact = np.where(s > 0, np.sinh(np.where(s > 0, s, 1.0)) / np.where(s > 0, s, 1.0) - 1.0, 0.0)
        sinhc_minus_one = np.where(np.abs(s) < _SMALL, series, exact)
        out = _centre_shape(alpha) - (1.0 + alpha) * np.exp(-alpha) * sinhc_minus_one
        return float(out) if out.ndim == 0 else out

    def outside(self, distance_um: float | np.ndarray, radius_um: float) -> float | np.ndarray:
        """Normalised AHL at ``distance_um`` from the centre of one lesion.

        Valid for ``distance_um >= radius_um``. This is the screened (Yukawa)
        kernel ``exp(-r/lambda)/r``, scaled by the source's amplitude.
        """
        lam = self.diffusion_length_um
        alpha = radius_um / lam
        r = np.asarray(distance_um, dtype=float)
        amp = lam * _outside_amplitude(alpha)
        out = amp * np.exp(-r / lam) / r
        return float(out) if out.ndim == 0 else out

    def centre_in_cluster(
        self, positions_um: np.ndarray, radius_um: float, index: int = 0
    ) -> float:
        """Normalised AHL at the centre of lesion ``index`` within a cluster.

        Its own contribution is the finite-sphere centre value; every other
        lesion contributes its exterior field at the separation. Exact, because
        the equation is linear.
        """
        positions = np.atleast_2d(np.asarray(positions_um, dtype=float))
        target = positions[index]
        total = self.centre_of_isolated(radius_um)
        for j, other in enumerate(positions):
            if j == index:
                continue
            distance = float(np.linalg.norm(other - target))
            if distance < 2.0 * radius_um - 1e-9:
                raise ValueError(
                    f"lesions {index} and {j} overlap: separation {distance:.1f} µm "
                    f"is below 2 x radius {2 * radius_um:.1f} µm"
                )
            total += self.outside(distance, radius_um)
        return float(total)

    def equivalent_isolated_radius(self, concentration: float) -> float:
        """Radius of the isolated lesion that reaches this centre concentration.

        Inverts :meth:`centre_of_isolated`. This is the scale-free way to say
        how much a cluster is worth: "this cluster looks, to its own quorum
        sensor, like one isolated nodule of radius R".
        """
        lam = self.diffusion_length_um
        ceiling = self.centre_of_isolated(50.0 * lam)
        if concentration >= ceiling:
            return float("inf")
        return float(
            brentq(
                lambda r: self.centre_of_isolated(r) - concentration,
                1e-6,
                50.0 * lam,
                xtol=1e-9,
                rtol=1e-12,
            )
        )


# -- arrangements ---------------------------------------------------------


def linear_chain(n: int, spacing_um: float) -> np.ndarray:
    """``n`` lesions in a line; the queried one is the middle of the chain."""
    offsets = (np.arange(n) - (n - 1) / 2.0) * spacing_um
    positions = np.zeros((n, 3))
    positions[:, 0] = offsets
    return np.roll(positions, -(n // 2), axis=0)


def cubic_lattice(n_per_side: int, spacing_um: float) -> np.ndarray:
    """``n**3`` lesions on a cubic lattice, the queried one nearest the centre."""
    grid = (np.arange(n_per_side) - (n_per_side - 1) / 2.0) * spacing_um
    positions = np.array([[x, y, z] for x in grid for y in grid for z in grid])
    centre_index = int(np.argmin(np.linalg.norm(positions, axis=1)))
    order = np.r_[centre_index, np.delete(np.arange(len(positions)), centre_index)]
    return positions[order]


def fcc_first_shell(spacing_um: float) -> np.ndarray:
    """One lesion plus its 12 close-packed neighbours, all at ``spacing_um``."""
    directions = []
    for i in range(3):
        for s1 in (+1, -1):
            for s2 in (+1, -1):
                vector = np.zeros(3)
                vector[i] = s1
                vector[(i + 1) % 3] = s2
                directions.append(vector / np.sqrt(2.0))
    return np.vstack([np.zeros(3), np.array(directions) * spacing_um])


def random_cluster(
    n: int, cluster_radius_um: float, radius_um: float, seed: int = 20261008
) -> np.ndarray:
    """``n`` non-overlapping lesions in a sphere, the first nearest the centre."""
    rng = np.random.default_rng(seed)
    placed: list[np.ndarray] = []
    attempts = 0
    while len(placed) < n and attempts < 200_000:
        attempts += 1
        point = rng.normal(size=3)
        point = point / np.linalg.norm(point) * cluster_radius_um * rng.random() ** (1 / 3)
        if all(np.linalg.norm(point - other) >= 2 * radius_um for other in placed):
            placed.append(point)
    if len(placed) < n:
        raise ValueError(f"could not place {n} lesions of radius {radius_um} µm")
    positions = np.array(placed)
    centre_index = int(np.argmin(np.linalg.norm(positions, axis=1)))
    order = np.r_[centre_index, np.delete(np.arange(len(positions)), centre_index)]
    return positions[order]


# -- analyses -------------------------------------------------------------


def cooperation_factor(
    positions_um: np.ndarray, radius_um: float, field: AHLField | None = None
) -> float:
    """Cluster AHL at a lesion centre, over the same lesion's isolated value."""
    field = field or AHLField()
    return field.centre_in_cluster(positions_um, radius_um) / field.centre_of_isolated(
        radius_um
    )


def cluster_scan(
    radius_um: float = LESION_OFF_UM,
    spacings_um=(300.0, 500.0, 1000.0, 2000.0),
    counts=(1, 2, 7, 13, 27, 125),
    field: AHLField | None = None,
) -> pd.DataFrame:
    """Equivalent isolated radius for cubic-lattice clusters of micro-lesions."""
    field = field or AHLField()
    rows = []
    for spacing in spacings_um:
        if spacing < 2 * radius_um:
            continue
        for count in counts:
            if count == 1:
                positions = np.zeros((1, 3))
            elif count == 13:
                positions = fcc_first_shell(spacing)
            else:
                side = int(round(count ** (1 / 3)))
                if side**3 != count:
                    positions = linear_chain(count, spacing)
                else:
                    positions = cubic_lattice(side, spacing)
            concentration = field.centre_in_cluster(positions, radius_um)
            rows.append(
                {
                    "radius_um": radius_um,
                    "spacing_um": spacing,
                    "n_lesions": len(positions),
                    "centre_ahl": concentration,
                    "cooperation_factor": concentration
                    / field.centre_of_isolated(radius_um),
                    "equivalent_isolated_radius_um": field.equivalent_isolated_radius(
                        concentration
                    ),
                    "total_volume_ratio": len(positions) * radius_um**3,
                }
            )
    frame = pd.DataFrame(rows)
    frame["reaches_on_band"] = frame["equivalent_isolated_radius_um"] >= LESION_ON_UM
    frame["leaves_off_band"] = frame["equivalent_isolated_radius_um"] > LESION_OFF_UM * 1.5
    return frame


def volume_equivalence(
    radius_um: float = LESION_OFF_UM,
    spacing_um: float = 300.0,
    counts=(1, 2, 4, 8, 13, 27, 64, 125),
    field: AHLField | None = None,
) -> pd.DataFrame:
    """Test whether a cluster behaves like one nodule of the same total volume.

    Because the diffusion length dwarfs every lesion and spacing, the field is
    close to a volume integral -- but not exactly, since a lesion's *own*
    centre contribution scales as ``a**2`` while a neighbour's scales as
    ``a**3 / d``. This quantifies the departure.
    """
    field = field or AHLField()
    rows = []
    for count in counts:
        if count == 13:
            positions = fcc_first_shell(spacing_um)
        else:
            side = round(count ** (1 / 3))
            positions = (
                cubic_lattice(int(side), spacing_um)
                if int(side) ** 3 == count
                else linear_chain(count, spacing_um)
            )
        n = len(positions)
        concentration = field.centre_in_cluster(positions, radius_um)
        equivalent = field.equivalent_isolated_radius(concentration)
        volume_matched = radius_um * n ** (1 / 3)
        rows.append(
            {
                "n_lesions": n,
                "equivalent_isolated_radius_um": equivalent,
                "volume_matched_radius_um": volume_matched,
                "equivalent_over_volume_matched": equivalent / volume_matched,
            }
        )
    return pd.DataFrame(rows)
