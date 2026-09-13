"""Stripmap SAR physics for teaching (range compression + azimuth FFT)."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from teaching_sims.core.units import C_LIGHT, wavelength


@dataclass(frozen=True)
class SARPointTarget:
    """Ground-plane point scatterer.

    ``x_m`` is along-track (azimuth), ``y_m`` is cross-track ground range from
    the flight-track nadir line (broadside looks at +y).
    """

    x_m: float
    y_m: float
    rcs_db: float = 0.0

    def __post_init__(self) -> None:
        if self.y_m <= 0:
            raise ValueError("y_m (ground range) must be positive")


@dataclass(frozen=True)
class SARParams:
    """Side-looking stripmap SAR with stop-and-hop LFM pulses."""

    # Platform
    altitude_m: float = 5000.0
    velocity_mps: float = 150.0
    # RF / waveform
    center_freq_hz: float = 5.3e9  # C-band-ish
    bandwidth_hz: float = 50e6
    pulse_width_s: float = 5e-6
    # Sampling / aperture
    prf_hz: float = 800.0
    n_pulses: int = 256
    sample_rate_hz: float = 60e6
    # Scene
    targets: tuple[SARPointTarget, ...] = field(
        default_factory=lambda: (
            SARPointTarget(0.0, 8000.0, rcs_db=0.0),
            SARPointTarget(40.0, 8050.0, rcs_db=-3.0),
        )
    )
    squint_deg: float = 0.0  # reserved; processor assumes broadside
    noise_enabled: bool = True
    noise_snr_db: float = 25.0  # peak SNR after range compression (ref target)
    azimuth_window: bool = True
    seed: int = 0

    def __post_init__(self) -> None:
        if self.altitude_m <= 0 or self.velocity_mps <= 0:
            raise ValueError("altitude and velocity must be positive")
        if self.bandwidth_hz <= 0 or self.pulse_width_s <= 0:
            raise ValueError("bandwidth and pulse_width must be positive")
        if self.prf_hz <= 0 or self.n_pulses < 8:
            raise ValueError("invalid PRF / n_pulses")
        if self.sample_rate_hz <= 0 or self.center_freq_hz <= 0:
            raise ValueError("sample_rate and center_freq must be positive")

    @property
    def lambda_m(self) -> float:
        return wavelength(self.center_freq_hz)

    @property
    def range_resolution_m(self) -> float:
        return C_LIGHT / (2.0 * self.bandwidth_hz)

    @property
    def slant_range_m(self) -> float:
        """Reference slant range to scene centre (mean target y)."""
        if self.targets:
            y0 = float(np.mean([t.y_m for t in self.targets]))
        else:
            y0 = 8000.0
        return float(np.hypot(self.altitude_m, y0))

    @property
    def synthetic_aperture_m(self) -> float:
        return self.velocity_mps * (self.n_pulses - 1) / self.prf_hz

    @property
    def azimuth_resolution_m(self) -> float:
        """Approx broadside stripmap: Δx ≈ L_sa_eff related; use λ R /(2 L_sa)."""
        L = max(self.synthetic_aperture_m, 1e-6)
        return self.lambda_m * self.slant_range_m / (2.0 * L)

    @property
    def doppler_bandwidth_hz(self) -> float:
        # Rough: B_a ≈ 2 v / Δx
        return 2.0 * self.velocity_mps / max(self.azimuth_resolution_m, 1e-6)

    @property
    def n_fast(self) -> int:
        # Record window: cover scene ranges with margin
        return max(int(round(self.pulse_width_s * self.sample_rate_hz)) * 8, 256)


def platform_positions(params: SARParams) -> np.ndarray:
    """Along-track platform x positions at each pulse (metres)."""
    t = (np.arange(params.n_pulses, dtype=float) - 0.5 * (params.n_pulses - 1)) / params.prf_hz
    return params.velocity_mps * t


def slant_range_to_target(x_plat: float, tgt: SARPointTarget, altitude_m: float) -> float:
    return float(np.sqrt((x_plat - tgt.x_m) ** 2 + altitude_m**2 + tgt.y_m**2))


def _tx_lfm(params: SARParams) -> np.ndarray:
    n = max(int(round(params.pulse_width_s * params.sample_rate_hz)), 8)
    t = np.arange(n, dtype=float) / params.sample_rate_hz
    b, tp = params.bandwidth_hz, params.pulse_width_s
    tx = np.exp(1j * np.pi * (b / tp) * t**2 - 1j * np.pi * b * t)
    tx = tx / np.sqrt(np.vdot(tx, tx).real + 1e-30)
    return tx


def simulate_raw(params: SARParams) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(x_plat, fast_time_s, raw)`` with raw shape (n_pulses, n_fast)."""
    rng = np.random.default_rng(params.seed)
    x_plat = platform_positions(params)
    n_f = params.n_fast
    t_fast = np.arange(n_f, dtype=float) / params.sample_rate_hz
    # Start recording slightly before closest expected echo
    r_min = min(slant_range_to_target(float(x_plat[len(x_plat) // 2]), t, params.altitude_m) for t in params.targets) if params.targets else params.slant_range_m
    t0 = 2.0 * (r_min - 200.0) / C_LIGHT
    t0 = max(t0, 0.0)
    t_fast = t_fast + t0

    tx = _tx_lfm(params)
    raw = np.zeros((params.n_pulses, n_f), dtype=complex)
    sigma = 1.0
    if params.noise_enabled:
        raw += (rng.normal(size=raw.shape) + 1j * rng.normal(size=raw.shape)) * (sigma / np.sqrt(2.0))

    # Amplitude so first target ~ noise_snr_db after matched filter energy
    for tgt in params.targets:
        amp = 10 ** ((params.noise_snr_db + tgt.rcs_db) / 20.0) * sigma
        for i, xp in enumerate(x_plat):
            r = slant_range_to_target(float(xp), tgt, params.altitude_m)
            delay = 2.0 * r / C_LIGHT
            # Carrier phase for azimuth chirp
            phase = np.exp(-1j * 4.0 * np.pi * r / params.lambda_m)
            # Place LFM echo
            i0 = int(round((delay - t_fast[0]) * params.sample_rate_hz))
            if i0 >= n_f or i0 + len(tx) <= 0:
                continue
            a = max(i0, 0)
            b = min(i0 + len(tx), n_f)
            ta = a - i0
            tb = ta + (b - a)
            raw[i, a:b] += amp * phase * tx[ta:tb]

    return x_plat, t_fast, raw


def range_compress(params: SARParams, raw: np.ndarray) -> np.ndarray:
    """Matched filter along fast time (all pulses)."""
    tx = _tx_lfm(params)
    n_p, n_f = raw.shape
    n_fft = int(2 ** np.ceil(np.log2(n_f + len(tx) - 1)))
    H = np.fft.fft(np.conj(tx[::-1]), n=n_fft)
    out = np.zeros((n_p, n_f), dtype=complex)
    start = len(tx) - 1
    for i in range(n_p):
        y = np.fft.ifft(np.fft.fft(raw[i], n=n_fft) * H)
        out[i] = y[start : start + n_f]
    return out


def range_axis_m(t_fast: np.ndarray) -> np.ndarray:
    return C_LIGHT * t_fast / 2.0


def azimuth_compress(
    params: SARParams,
    x_plat: np.ndarray,
    range_m: np.ndarray,
    rc: np.ndarray,
) -> dict[str, np.ndarray | float]:
    """Approximate azimuth compression via deramp + FFT per range bin.

    Uses a single reference R0 (scene centre) for the azimuth matched phase —
    good enough for teaching stripmap focusing of compact scenes.

    After deramp, a target at along-track ``x0`` becomes a tone at
    ``f_d = K_a x0 / v``, so ``x0 = f_d v / K_a``.
    """
    R0 = params.slant_range_m
    ka = 2.0 * params.velocity_mps**2 / (params.lambda_m * R0)
    t_az = x_plat / params.velocity_mps
    href = np.exp(1j * np.pi * ka * t_az**2)
    if params.azimuth_window:
        w = np.hanning(len(t_az))
    else:
        w = np.ones(len(t_az))
    w = w / (np.linalg.norm(w) + 1e-15)

    deramped = rc * (href * w)[:, None]
    focused = np.fft.fftshift(np.fft.fft(deramped, axis=0), axes=0)
    power = np.abs(focused) ** 2
    peak = float(np.max(power)) + 1e-30
    img_db = 10.0 * np.log10(power / peak + 1e-30)

    n = len(x_plat)
    fd = np.fft.fftshift(np.fft.fftfreq(n, d=1.0 / params.prf_hz))
    x_axis = fd * params.velocity_mps / ka

    return {
        "x_m": x_axis.astype(float),
        "range_m": range_m,
        "image_db": img_db,
        "range_compressed": rc,
        "R0_m": float(R0),
        "ka": float(ka),
        "range_resolution_m": float(params.range_resolution_m),
        "azimuth_resolution_m": float(params.azimuth_resolution_m),
        "synthetic_aperture_m": float(params.synthetic_aperture_m),
    }


def process_sar(params: SARParams) -> dict[str, object]:
    x_plat, t_fast, raw = simulate_raw(params)
    rc = range_compress(params, raw)
    r_axis = range_axis_m(t_fast)
    focused = azimuth_compress(params, x_plat, r_axis, rc)

    # Unfocused: just |rc| mean / peak for comparison panel
    unf = np.abs(rc) ** 2
    unf = unf / (np.max(unf) + 1e-30)
    unf_db = 10.0 * np.log10(unf + 1e-30)

    return {
        "x_plat_m": x_plat,
        "t_fast_s": t_fast,
        "raw": raw,
        "unfocused_db": unf_db,
        **focused,
    }
