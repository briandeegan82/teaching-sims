"""Detect peaks, nulls, and grating-lobe angles on a ULA pattern."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from teaching_sims.topics.phased_array.physics import ArrayParams, pattern_db


@dataclass(frozen=True)
class PatternFeatures:
    """Callout locations for teaching overlays."""

    main_peak_deg: float
    main_peak_db: float
    grating_peaks_deg: tuple[float, ...]
    other_peaks_deg: tuple[float, ...]
    nulls_deg: tuple[float, ...]
    theoretical_grating_deg: tuple[float, ...]


def theoretical_grating_angles_deg(params: ArrayParams, *, max_order: int = 4) -> tuple[float, ...]:
    """Ideal grating directions: sinθ = sinθ₀ + m λ/d, m ≠ 0, |sinθ|≤1."""
    d_lam = params.d_over_lambda * (params.design_lambda_m / params.lambda_m)
    if d_lam <= 0:
        return ()
    s0 = np.sin(np.deg2rad(params.steer_deg))
    out: list[float] = []
    for m in range(-max_order, max_order + 1):
        if m == 0:
            continue
        s = s0 + m / d_lam
        if abs(s) <= 1.0 + 1e-9:
            out.append(float(np.rad2deg(np.arcsin(np.clip(s, -1.0, 1.0)))))
    return tuple(sorted(out))


def _local_maxima(y: np.ndarray) -> np.ndarray:
    """Indices i where y[i] is strictly greater than both neighbours."""
    if len(y) < 3:
        return np.array([], dtype=int)
    return np.where((y[1:-1] > y[:-2]) & (y[1:-1] > y[2:]))[0] + 1


def _local_minima(y: np.ndarray) -> np.ndarray:
    if len(y) < 3:
        return np.array([], dtype=int)
    return np.where((y[1:-1] < y[:-2]) & (y[1:-1] < y[2:]))[0] + 1


def pattern_features(
    params: ArrayParams,
    theta_deg: np.ndarray | None = None,
    *,
    peak_floor_db: float = -18.0,
    null_ceiling_db: float = -12.0,
    grating_match_deg: float = 4.0,
    max_nulls: int = 6,
) -> PatternFeatures:
    """Find main beam, grating / other peaks, and deep nulls for overlays."""
    theta = np.linspace(-90.0, 90.0, 1801) if theta_deg is None else np.asarray(theta_deg, dtype=float)
    pdb = pattern_db(theta, params)

    imax = int(np.argmax(pdb))
    main_deg = float(theta[imax])
    main_db = float(pdb[imax])

    theo = theoretical_grating_angles_deg(params)
    max_idx = _local_maxima(pdb)
    # Keep maxima that are visible enough for callouts.
    vis = [i for i in max_idx if pdb[i] >= peak_floor_db]

    grating: list[float] = []
    other: list[float] = []
    for i in vis:
        ang = float(theta[i])
        if abs(ang - main_deg) < 1.0:
            continue
        if any(abs(ang - g) <= grating_match_deg for g in theo):
            grating.append(ang)
        elif pdb[i] >= -6.0:
            # Strong non-main peak — treat as grating-like for teaching even if
            # theoretical list missed it (scan + quantization cases).
            grating.append(ang)
        else:
            other.append(ang)

    min_idx = _local_minima(pdb)
    # Prefer nulls near the main beam (first few on each side).
    null_cands = [i for i in min_idx if pdb[i] <= null_ceiling_db]
    null_cands.sort(key=lambda i: abs(float(theta[i]) - main_deg))
    nulls = [float(theta[i]) for i in null_cands[:max_nulls]]

    return PatternFeatures(
        main_peak_deg=main_deg,
        main_peak_db=main_db,
        grating_peaks_deg=tuple(sorted(grating)),
        other_peaks_deg=tuple(sorted(other)),
        nulls_deg=tuple(nulls),
        theoretical_grating_deg=theo,
    )
