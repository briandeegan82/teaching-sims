"""Uniform linear array (ULA) physics for teaching demos."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from teaching_sims.core.units import C_LIGHT, wavelength


class SteeringMode(str, Enum):
    PHASE_SHIFT = "phase_shift"
    TRUE_TIME_DELAY = "true_time_delay"


@dataclass(frozen=True)
class ArrayParams:
    """Parameters for a narrowband / wideband ULA demo.

    Angles are in degrees, measured from broadside (0° = array normal).
    Positive θ is toward +x when the array lies along x.
    """

    n_elements: int = 8
    d_over_lambda: float = 0.5
    frequency_hz: float = 10e9
    steer_deg: float = 0.0
    design_frequency_hz: float | None = None
    steering_mode: SteeringMode = SteeringMode.PHASE_SHIFT
    element_pattern: bool = False
    phase_bits: int | None = None  # None = continuous phase
    amplitude_taper: str = "uniform"  # uniform | hann

    def __post_init__(self) -> None:
        if self.n_elements < 1:
            raise ValueError("n_elements must be >= 1")
        if self.d_over_lambda <= 0:
            raise ValueError("d_over_lambda must be positive")
        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be positive")
        if self.phase_bits is not None and self.phase_bits < 1:
            raise ValueError("phase_bits must be >= 1 when set")

    @property
    def lambda_m(self) -> float:
        return wavelength(self.frequency_hz)

    @property
    def design_lambda_m(self) -> float:
        f0 = self.design_frequency_hz or self.frequency_hz
        return wavelength(f0)

    @property
    def spacing_m(self) -> float:
        # Spacing is defined relative to the *design* wavelength so that
        # changing RF frequency demonstrates beam squint / grating motion.
        return self.d_over_lambda * self.design_lambda_m

    @property
    def k(self) -> float:
        return 2.0 * np.pi / self.lambda_m


def element_positions(params: ArrayParams) -> np.ndarray:
    """Return x-coordinates of elements centred on the origin (metres)."""
    n = params.n_elements
    idx = np.arange(n, dtype=float) - (n - 1) / 2.0
    return idx * params.spacing_m


def amplitude_weights(params: ArrayParams) -> np.ndarray:
    n = params.n_elements
    if params.amplitude_taper == "uniform":
        w = np.ones(n, dtype=float)
    elif params.amplitude_taper == "hann":
        if n == 1:
            w = np.ones(1, dtype=float)
        else:
            w = np.hanning(n)
    else:
        raise ValueError(f"unknown amplitude_taper: {params.amplitude_taper}")
    return w / np.max(w)


def _quantize_phase(phase_rad: np.ndarray, bits: int) -> np.ndarray:
    levels = 2**bits
    step = 2.0 * np.pi / levels
    # Wrap to [0, 2π), quantize, re-centre.
    wrapped = np.mod(phase_rad, 2.0 * np.pi)
    q = np.round(wrapped / step) * step
    return q


def steering_phases(params: ArrayParams) -> np.ndarray:
    """Progressive excitation phase (radians) applied to each element."""
    x = element_positions(params)
    theta0 = np.deg2rad(params.steer_deg)
    f = params.frequency_hz
    f0 = params.design_frequency_hz or params.frequency_hz

    if params.steering_mode == SteeringMode.PHASE_SHIFT:
        # Phase weights designed at f0; evaluated at operating frequency f
        # only through the free-space path term in the array factor.
        k0 = 2.0 * np.pi / wavelength(f0)
        phase = -k0 * x * np.sin(theta0)
    elif params.steering_mode == SteeringMode.TRUE_TIME_DELAY:
        delay_s = -(x * np.sin(theta0)) / C_LIGHT
        phase = 2.0 * np.pi * f * delay_s
    else:
        raise ValueError(f"unknown steering_mode: {params.steering_mode}")

    if params.phase_bits is not None:
        phase = _quantize_phase(phase, params.phase_bits)
    return phase


def element_factor(theta_deg: np.ndarray, enabled: bool) -> np.ndarray:
    """Simple embedded element pattern: isotropic or cos(θ) for |θ|<90°."""
    theta = np.deg2rad(theta_deg)
    if not enabled:
        return np.ones_like(theta, dtype=float)
    ef = np.cos(theta)
    ef = np.clip(ef, 0.0, None)
    return ef


def array_factor(
    theta_deg: np.ndarray,
    params: ArrayParams,
    *,
    normalize: bool = True,
) -> np.ndarray:
    """Complex array factor (optionally times element factor).

    Returns complex AF with shape matching ``theta_deg``.
    """
    theta = np.asarray(theta_deg, dtype=float)
    x = element_positions(params)
    w = amplitude_weights(params)
    phase = steering_phases(params)
    k = params.k
    sin_th = np.sin(np.deg2rad(theta))

    # AF(θ) = Σ w_n exp(j (k x_n sinθ + φ_n))
    # Broadcast: (N,1) vs (1,M)
    path = k * np.outer(x, sin_th)
    excitation = w[:, None] * np.exp(1j * (path + phase[:, None]))
    af = np.sum(excitation, axis=0)

    af = af * element_factor(theta, params.element_pattern)
    if normalize and params.n_elements > 0:
        af = af / params.n_elements
    return af


def pattern_db(theta_deg: np.ndarray, params: ArrayParams) -> np.ndarray:
    """Power pattern in dB, peak-normalized."""
    af = array_factor(theta_deg, params, normalize=True)
    power = np.abs(af) ** 2
    peak = np.max(power)
    if peak <= 0:
        return np.full_like(power, -200.0, dtype=float)
    return 10.0 * np.log10(power / peak + 1e-30)


def half_power_beamwidth_deg(params: ArrayParams, *, n_samples: int = 4001) -> float:
    """Estimate HPBW near the steered main beam (degrees)."""
    theta = np.linspace(-90.0, 90.0, n_samples)
    pdb = pattern_db(theta, params)
    # Search around steer angle for contiguous region above -3 dB.
    centre = float(np.clip(params.steer_deg, -89.0, 89.0))
    i0 = int(np.argmin(np.abs(theta - centre)))
    if pdb[i0] < -3.0:
        i0 = int(np.argmax(pdb))
    left = i0
    while left > 0 and pdb[left] >= -3.0:
        left -= 1
    right = i0
    while right < len(pdb) - 1 and pdb[right] >= -3.0:
        right += 1
    return float(theta[right] - theta[left])


def grating_lobe_hint(params: ArrayParams) -> str:
    """Short teaching note about grating-lobe risk."""
    d_lam = params.d_over_lambda * (params.design_lambda_m / params.lambda_m)
    # Visible grating lobe condition for scan to θ0: d/λ > 1/(1+|sinθ0|)
    sin0 = abs(np.sin(np.deg2rad(params.steer_deg)))
    limit = 1.0 / (1.0 + sin0) if (1.0 + sin0) > 0 else 1.0
    if d_lam > limit + 1e-9:
        return (
            f"Grating lobes likely: operating d/λ≈{d_lam:.2f} "
            f"exceeds ~{limit:.2f} at steer {params.steer_deg:.0f}°."
        )
    if d_lam > 0.5 + 1e-9:
        return (
            f"d/λ≈{d_lam:.2f} > 0.5: grating lobes appear as you scan away "
            "from broadside."
        )
    return f"Operating d/λ≈{d_lam:.2f} ≤ 0.5: no visible grating lobes for |θ|≤90°."


def wavefront_field(
    params: ArrayParams,
    *,
    x_span_m: float | None = None,
    z_max_m: float | None = None,
    nx: int = 220,
    nz: int = 160,
    t: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Snapshot of Re{Σ sources} in the x–z plane (z = range).

    Returns ``(x_grid, z_grid, field)`` suitable for a heatmap.
    """
    lam = params.lambda_m
    if x_span_m is None:
        x_span_m = max(8.0 * params.spacing_m * params.n_elements, 6.0 * lam)
    if z_max_m is None:
        z_max_m = 12.0 * lam

    x = np.linspace(-0.5 * x_span_m, 0.5 * x_span_m, nx)
    z = np.linspace(0.5 * lam, z_max_m, nz)
    xx, zz = np.meshgrid(x, z)

    xs = element_positions(params)
    w = amplitude_weights(params)
    phase = steering_phases(params)
    k = params.k
    omega = 2.0 * np.pi * params.frequency_hz

    field = np.zeros_like(xx, dtype=complex)
    for n, (xn, wn, ph) in enumerate(zip(xs, w, phase)):
        r = np.hypot(xx - xn, zz)
        # 2D cylindrical-ish amplitude falloff for nicer visuals
        field += wn * np.exp(1j * (k * r + ph - omega * t)) / np.sqrt(r + 1e-9)

    return x, z, np.real(field)


def peak_angle_deg(params: ArrayParams, *, n_samples: int = 4001) -> float:
    theta = np.linspace(-90.0, 90.0, n_samples)
    pdb = pattern_db(theta, params)
    return float(theta[int(np.argmax(pdb))])
