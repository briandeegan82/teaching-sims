"""FMCW radar physics for teaching (sawtooth / triangle, range–Doppler)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from teaching_sims.core.units import C_LIGHT, wavelength


class FMCWWaveform(str, Enum):
    SAWTOOTH = "sawtooth"
    TRIANGLE = "triangle"


@dataclass(frozen=True)
class FMCWTarget:
    """Point target. Positive velocity = closing (approaching)."""

    range_m: float
    velocity_mps: float = 0.0
    snr_db: float = 20.0

    def __post_init__(self) -> None:
        if self.range_m < 0:
            raise ValueError("range_m must be >= 0")


@dataclass(frozen=True)
class FMCWParams:
    """Dechirped FMCW IF model (complex baseband after mixing)."""

    bandwidth_hz: float = 150e6
    chirp_time_s: float = 40e-6
    n_chirps: int = 64
    sample_rate_hz: float = 5e6
    center_freq_hz: float = 77e9
    waveform: FMCWWaveform = FMCWWaveform.SAWTOOTH
    targets: tuple[FMCWTarget, ...] = field(
        default_factory=lambda: (FMCWTarget(60.0, 0.0, snr_db=25.0),)
    )
    noise_enabled: bool = True
    range_window: bool = True
    doppler_window: bool = True
    seed: int = 0

    def __post_init__(self) -> None:
        if self.bandwidth_hz <= 0 or self.chirp_time_s <= 0:
            raise ValueError("bandwidth and chirp_time must be positive")
        if self.n_chirps < 2:
            raise ValueError("n_chirps must be >= 2")
        if self.sample_rate_hz <= 0 or self.center_freq_hz <= 0:
            raise ValueError("sample_rate and center_freq must be positive")

    @property
    def lambda_m(self) -> float:
        return wavelength(self.center_freq_hz)

    @property
    def slope_hz_per_s(self) -> float:
        return self.bandwidth_hz / self.chirp_time_s

    @property
    def range_resolution_m(self) -> float:
        return C_LIGHT / (2.0 * self.bandwidth_hz)

    @property
    def max_beat_hz(self) -> float:
        return 0.5 * self.sample_rate_hz

    @property
    def max_unambiguous_range_m(self) -> float:
        # Highest IF tone at Nyquist: fb = 2 S R / c  => R = fb * c / (2 S)
        return self.max_beat_hz * C_LIGHT / (2.0 * self.slope_hz_per_s)

    @property
    def chirp_prf_hz(self) -> float:
        # For sawtooth CPI; triangle uses 2 sweeps per period conceptually
        return 1.0 / self.chirp_time_s

    @property
    def unambiguous_velocity_mps(self) -> float:
        # Slow-time sampling at chirp rate (sawtooth)
        return self.lambda_m * self.chirp_prf_hz / 4.0

    @property
    def velocity_resolution_mps(self) -> float:
        return self.lambda_m * self.chirp_prf_hz / (2.0 * self.n_chirps)

    @property
    def n_fast(self) -> int:
        return max(int(round(self.chirp_time_s * self.sample_rate_hz)), 8)


def beat_frequency_hz(range_m: float, velocity_mps: float, params: FMCWParams, *, up: bool = True) -> float:
    """Ideal IF beat frequency for one sweep.

    Sawtooth / up-sweep: fb = 2 S R / c + 2 v / λ
    Down-sweep:         fb = 2 S R / c - 2 v / λ
    """
    fb_r = 2.0 * params.slope_hz_per_s * range_m / C_LIGHT
    fd = 2.0 * velocity_mps / params.lambda_m
    return fb_r + fd if up else fb_r - fd


def range_from_beat_hz(fb_hz: float, params: FMCWParams) -> float:
    """Stationary-target range estimate ignoring Doppler (sawtooth coupling bias)."""
    return fb_hz * C_LIGHT / (2.0 * params.slope_hz_per_s)


def triangle_solve(fb_up: float, fb_down: float, params: FMCWParams) -> tuple[float, float]:
    """Estimate (R, v) from up/down beat frequencies."""
    fb_r = 0.5 * (fb_up + fb_down)
    fd = 0.5 * (fb_up - fb_down)
    r = fb_r * C_LIGHT / (2.0 * params.slope_hz_per_s)
    v = fd * params.lambda_m / 2.0
    return float(r), float(v)


def _fast_time(params: FMCWParams) -> np.ndarray:
    n = params.n_fast
    return np.arange(n, dtype=float) / params.sample_rate_hz


def simulate_if_cube(params: FMCWParams) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(t_fast, chirp_index_meta, if_cube)``.

    ``if_cube`` shape (n_chirps, n_fast). For triangle, even chirps are up,
    odd chirps are down.
    """
    rng = np.random.default_rng(params.seed)
    t = _fast_time(params)
    n_c = params.n_chirps
    n_f = len(t)
    cube = np.zeros((n_c, n_f), dtype=complex)
    sigma = 1.0

    if params.noise_enabled:
        cube += (rng.normal(size=(n_c, n_f)) + 1j * rng.normal(size=(n_c, n_f))) * (
            sigma / np.sqrt(2.0)
        )

    for tgt in params.targets:
        amp = 10 ** (tgt.snr_db / 20.0) * sigma
        for n in range(n_c):
            if params.waveform == FMCWWaveform.TRIANGLE:
                up = (n % 2 == 0)
            else:
                up = True
            fb = beat_frequency_hz(tgt.range_m, tgt.velocity_mps, params, up=up)
            # Slow-time Doppler phase across chirps (approx at chirp starts)
            fd = 2.0 * tgt.velocity_mps / params.lambda_m
            slow_phase = np.exp(1j * 2.0 * np.pi * fd * n * params.chirp_time_s)
            cube[n] += amp * slow_phase * np.exp(1j * 2.0 * np.pi * fb * t)

    return t, np.arange(n_c, dtype=float), cube


def range_axis_m(params: FMCWParams, n_fft: int | None = None) -> np.ndarray:
    n = n_fft or params.n_fast
    # FFT bins 0..Nyquist map to beat freq 0..fs/2 → range
    fb = np.fft.rfftfreq(n, d=1.0 / params.sample_rate_hz)
    return range_from_beat_hz(fb, params)


def velocity_axis_mps(params: FMCWParams) -> np.ndarray:
    # Use only up-chirps for Doppler when triangle
    if params.waveform == FMCWWaveform.TRIANGLE:
        n = max(params.n_chirps // 2, 2)
        pri = 2.0 * params.chirp_time_s
    else:
        n = params.n_chirps
        pri = params.chirp_time_s
    fd = np.fft.fftshift(np.fft.fftfreq(n, d=pri))
    return fd * params.lambda_m / 2.0


def process_fmcw(params: FMCWParams) -> dict[str, object]:
    """Range FFT per chirp + Doppler FFT → RD map; also one-chirp spectrum."""
    t, _, cube = simulate_if_cube(params)
    n_c, n_f = cube.shape

    # Select sweeps for RD (sawtooth: all; triangle: up-sweeps only)
    if params.waveform == FMCWWaveform.TRIANGLE:
        sweeps = cube[0::2]
    else:
        sweeps = cube

    n_slow = sweeps.shape[0]
    # Range window
    w_r = np.hanning(n_f) if params.range_window else np.ones(n_f)
    w_r = w_r / (np.linalg.norm(w_r) + 1e-15)
    gated = sweeps * w_r[None, :]

    # Complex IF → FFT; keep non-negative beat frequencies
    range_spec_full = np.fft.fft(gated, axis=1)
    fb_full = np.fft.fftfreq(n_f, d=1.0 / params.sample_rate_hz)
    pos = fb_full >= 0.0
    range_spec = range_spec_full[:, pos]
    range_power = np.abs(range_spec) ** 2
    fb_axis = fb_full[pos]
    r_axis = range_from_beat_hz(fb_axis, params)

    # Doppler FFT
    w_d = np.hanning(n_slow) if params.doppler_window else np.ones(n_slow)
    w_d = w_d / (np.linalg.norm(w_d) + 1e-15)
    rd = np.fft.fftshift(np.fft.fft(range_spec * w_d[:, None], axis=0), axes=0)
    rd_power = np.abs(rd) ** 2
    peak = float(np.max(rd_power)) + 1e-30
    rd_db = 10.0 * np.log10(rd_power / peak + 1e-30)
    v_axis = velocity_axis_mps(params)

    # Single-chirp IF spectrum (first up-chirp)
    if0 = cube[0] * w_r
    spec0_full = np.fft.fft(if0)
    spec0 = spec0_full[pos]
    spec0_db = 10.0 * np.log10(np.abs(spec0) ** 2 / (np.max(np.abs(spec0) ** 2) + 1e-30) + 1e-30)

    # Mean range profile
    rp = np.mean(range_power, axis=0)
    rp_db = 10.0 * np.log10(rp / (np.max(rp) + 1e-30) + 1e-30)

    # Triangle up/down peak estimates for first target (teaching panel)
    tri = None
    if params.waveform == FMCWWaveform.TRIANGLE and params.targets:
        def peak_fb(x: np.ndarray) -> float:
            s_full = np.abs(np.fft.fft(x * w_r)) ** 2
            s = s_full[pos]
            return float(fb_axis[int(np.argmax(s))])

        fb_up = peak_fb(cube[0])
        fb_dn = peak_fb(cube[1]) if n_c > 1 else fb_up
        r_hat, v_hat = triangle_solve(fb_up, fb_dn, params)
        tri = {
            "fb_up_hz": fb_up,
            "fb_down_hz": fb_dn,
            "range_m": r_hat,
            "velocity_mps": v_hat,
        }

    # Sawtooth biased range for first moving target
    saw_bias = None
    if params.targets:
        tgt = params.targets[0]
        fb = beat_frequency_hz(tgt.range_m, tgt.velocity_mps, params, up=True)
        saw_bias = {
            "true_range_m": tgt.range_m,
            "true_velocity_mps": tgt.velocity_mps,
            "beat_hz": fb,
            "range_from_beat_m": range_from_beat_hz(fb, params),
        }

    return {
        "t_fast_s": t,
        "if_cube": cube,
        "fb_axis_hz": fb_axis,
        "spectrum0_db": spec0_db,
        "range_m": r_axis,
        "range_profile_db": rp_db,
        "velocity_mps": v_axis,
        "rd_db": rd_db,
        "triangle": tri,
        "sawtooth_bias": saw_bias,
        "range_resolution_m": params.range_resolution_m,
        "max_unambiguous_range_m": params.max_unambiguous_range_m,
        "unambiguous_velocity_mps": params.unambiguous_velocity_mps,
        "velocity_resolution_mps": params.velocity_resolution_mps,
        "slope_hz_per_s": params.slope_hz_per_s,
    }
