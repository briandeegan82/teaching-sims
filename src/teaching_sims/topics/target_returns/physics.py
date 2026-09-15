"""Target return physics: RCS by shape/size and A-scope echo."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from teaching_sims.core.units import C_LIGHT, wavelength


class TargetShape(str, Enum):
    SPHERE = "sphere"
    FLAT_PLATE = "flat_plate"
    CYLINDER = "cylinder"
    CORNER = "corner"  # trihedral corner reflector
    EXTENDED = "extended"  # long body with range depth (vehicle-like)


@dataclass(frozen=True)
class TargetReturnsParams:
    """Monostatic pulsed radar looking at one canonical target shape."""

    shape: TargetShape = TargetShape.SPHERE
    # Characteristic size (m): sphere radius; plate side; cylinder radius;
    # corner edge length; extended body length along LOS when aspect=90 deg.
    size_m: float = 1.0
    # Secondary size (m): plate width / cylinder length / extended width.
    size2_m: float = 1.0
    # Aspect from face-on / broadside (deg). 0 = max RCS for plate/cylinder.
    aspect_deg: float = 0.0
    range_m: float = 5000.0
    frequency_hz: float = 10e9  # X-band
    # Teaching radar equation anchor: SNR for a 1 m^2 RCS target at range_ref.
    snr_ref_db: float = 25.0
    range_ref_m: float = 5000.0
    rcs_ref_m2: float = 1.0
    # Waveform (simple rect pulse for A-scope shape teaching)
    pulse_width_s: float = 0.5e-6
    sample_rate_hz: float = 40e6
    pri_s: float = 100e-6
    noise_enabled: bool = True
    seed: int = 0

    def __post_init__(self) -> None:
        if self.size_m <= 0 or self.size2_m <= 0:
            raise ValueError("sizes must be positive")
        if self.range_m <= 0 or self.range_ref_m <= 0:
            raise ValueError("ranges must be positive")
        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be positive")
        if self.pulse_width_s <= 0 or self.sample_rate_hz <= 0 or self.pri_s <= 0:
            raise ValueError("waveform timing must be positive")
        if self.pri_s <= self.pulse_width_s:
            raise ValueError("pri_s must exceed pulse_width_s")
        if self.rcs_ref_m2 <= 0:
            raise ValueError("rcs_ref_m2 must be positive")


def lambda_m(params: TargetReturnsParams) -> float:
    return wavelength(params.frequency_hz)


def rcs_sphere_m2(radius_m: float) -> float:
    """Optical-regime conducting sphere: sigma = pi a^2 (ka >> 1)."""
    return float(np.pi * radius_m**2)


def rcs_flat_plate_m2(area_m2: float, wavelength_m: float, aspect_deg: float) -> float:
    """Broadside plate sigma = 4 pi A^2 / lambda^2, with cos^2 aspect falloff."""
    if wavelength_m <= 0:
        raise ValueError("wavelength must be positive")
    sigma0 = 4.0 * np.pi * (area_m2**2) / (wavelength_m**2)
    c = float(np.cos(np.deg2rad(aspect_deg)))
    # Soft floor so the echo does not vanish completely off-aspect in the demo
    return float(sigma0 * max(c * c, 1e-4))


def rcs_cylinder_m2(radius_m: float, length_m: float, wavelength_m: float, aspect_deg: float) -> float:
    """Finite conducting cylinder (broadside teaching approx): 2 pi a L^2 / lambda."""
    if wavelength_m <= 0:
        raise ValueError("wavelength must be positive")
    sigma0 = 2.0 * np.pi * radius_m * (length_m**2) / wavelength_m
    c = float(np.cos(np.deg2rad(aspect_deg)))
    return float(sigma0 * max(c * c, 1e-4))


def rcs_corner_m2(edge_m: float, wavelength_m: float) -> float:
    """Trihedral corner reflector: sigma ≈ 12 pi a^4 / lambda^2."""
    if wavelength_m <= 0:
        raise ValueError("wavelength must be positive")
    return float(12.0 * np.pi * (edge_m**4) / (wavelength_m**2))


def rcs_extended_m2(length_m: float, width_m: float, wavelength_m: float, aspect_deg: float) -> float:
    """Extended body: treat projected area like a plate with modest RCS."""
    # Effective area shrinks with aspect; keep a body RCS floor from the side face.
    area = length_m * width_m
    return rcs_flat_plate_m2(area * 0.15, wavelength_m, aspect_deg) + 0.5 * width_m * length_m * 0.05


def target_rcs_m2(params: TargetReturnsParams) -> float:
    """Monostatic RCS (m^2) for the selected shape."""
    lam = lambda_m(params)
    a = params.size_m
    b = params.size2_m
    asp = params.aspect_deg
    if params.shape == TargetShape.SPHERE:
        return rcs_sphere_m2(a)
    if params.shape == TargetShape.FLAT_PLATE:
        return rcs_flat_plate_m2(a * b, lam, asp)
    if params.shape == TargetShape.CYLINDER:
        return rcs_cylinder_m2(a, b, lam, asp)
    if params.shape == TargetShape.CORNER:
        return rcs_corner_m2(a, lam)
    if params.shape == TargetShape.EXTENDED:
        return rcs_extended_m2(a, b, lam, asp)
    raise ValueError(f"unknown shape: {params.shape}")


def range_extent_m(params: TargetReturnsParams) -> float:
    """Projected depth along the line of sight (smears the echo)."""
    if params.shape == TargetShape.SPHERE:
        return 2.0 * params.size_m
    if params.shape == TargetShape.CORNER:
        # Compact retroreflector — treat as near point-like
        return 0.5 * params.size_m
    if params.shape == TargetShape.FLAT_PLATE:
        # Face-on: thin; edge-on: plate length along LOS
        return abs(float(np.sin(np.deg2rad(params.aspect_deg)))) * params.size_m + 0.05
    if params.shape == TargetShape.CYLINDER:
        return abs(float(np.sin(np.deg2rad(params.aspect_deg)))) * params.size2_m + 2.0 * params.size_m
    if params.shape == TargetShape.EXTENDED:
        # Body length projected onto LOS
        return abs(float(np.sin(np.deg2rad(params.aspect_deg)))) * params.size_m + params.size2_m * 0.3
    return 0.1


def snr_from_rcs_db(params: TargetReturnsParams, rcs_m2: float | None = None) -> float:
    """Teaching radar equation: SNR ∝ σ / R^4."""
    sigma = target_rcs_m2(params) if rcs_m2 is None else float(rcs_m2)
    snr = (
        params.snr_ref_db
        + 10.0 * np.log10(max(sigma, 1e-30) / params.rcs_ref_m2)
        - 40.0 * np.log10(params.range_m / params.range_ref_m)
    )
    return float(snr)


def compare_shapes_rcs(
    params: TargetReturnsParams,
) -> dict[str, float]:
    """RCS for every shape at the current size / wavelength / aspect."""
    out: dict[str, float] = {}
    for shape in TargetShape:
        p = TargetReturnsParams(
            shape=shape,
            size_m=params.size_m,
            size2_m=params.size2_m,
            aspect_deg=params.aspect_deg if shape != TargetShape.SPHERE else 0.0,
            range_m=params.range_m,
            frequency_hz=params.frequency_hz,
            snr_ref_db=params.snr_ref_db,
            range_ref_m=params.range_ref_m,
            rcs_ref_m2=params.rcs_ref_m2,
            pulse_width_s=params.pulse_width_s,
            sample_rate_hz=params.sample_rate_hz,
            pri_s=params.pri_s,
            noise_enabled=False,
            seed=params.seed,
        )
        out[shape.value] = target_rcs_m2(p)
    return out


def _rect_pulse(n: int) -> np.ndarray:
    tx = np.ones(n, dtype=complex)
    return tx / np.sqrt(float(n))


def simulate_echo(params: TargetReturnsParams) -> dict[str, object]:
    """Build an A-scope envelope for the selected target."""
    fs = params.sample_rate_hz
    n_pri = max(int(round(params.pri_s * fs)), 8)
    t = np.arange(n_pri, dtype=float) / fs
    range_axis = C_LIGHT * t / 2.0

    n_pulse = max(int(round(params.pulse_width_s * fs)), 1)
    tx = _rect_pulse(n_pulse)

    sigma = target_rcs_m2(params)
    snr_db = snr_from_rcs_db(params, sigma)
    extent = range_extent_m(params)
    # Number of range bins spanned by the body (beyond the pulse itself)
    extent_bins = max(int(round(2.0 * extent / C_LIGHT * fs)), 1)

    # Noise floor from design SNR (peak amplitude for a point target)
    sigma_n = 10 ** (-snr_db / 20.0) if params.noise_enabled else 1e-6
    amp = 10 ** (snr_db / 20.0) * sigma_n

    rx = np.zeros(n_pri, dtype=complex)
    delay0 = int(round(2.0 * params.range_m / C_LIGHT * fs))
    # Spread energy across the projected depth so peak falls for extended targets
    weights = np.ones(extent_bins, dtype=float)
    weights /= float(np.sum(weights))
    for k, w in enumerate(weights):
        d = delay0 + k
        if d < 0:
            continue
        for i, v in enumerate(tx):
            idx = d + i
            if 0 <= idx < n_pri:
                rx[idx] += (amp * w) * v

    if params.noise_enabled:
        rng = np.random.default_rng(params.seed)
        noise = (rng.normal(size=n_pri) + 1j * rng.normal(size=n_pri)) * (sigma_n / np.sqrt(2.0))
        rx = rx + noise

    # Matched filter (correlate with rect pulse)
    mf = np.convolve(rx, np.conj(tx[::-1]), mode="full")
    start = len(tx) - 1
    video = mf[start : start + n_pri]
    envelope = np.abs(video)

    compare = compare_shapes_rcs(params)
    compare_db = {k: 10.0 * np.log10(max(v, 1e-30)) for k, v in compare.items()}

    return {
        "t_s": t,
        "range_m": range_axis,
        "envelope": envelope,
        "rx": rx,
        "rcs_m2": sigma,
        "rcs_dbsm": 10.0 * np.log10(max(sigma, 1e-30)),
        "snr_db": snr_db,
        "extent_m": extent,
        "lambda_m": lambda_m(params),
        "pulse_resolution_m": C_LIGHT * params.pulse_width_s / 2.0,
        "compare_rcs_m2": compare,
        "compare_rcs_dbsm": compare_db,
        "shape": params.shape.value,
    }


def process(params: TargetReturnsParams) -> dict[str, object]:
    return simulate_echo(params)
