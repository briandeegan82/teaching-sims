"""Pulse-Doppler / MTI physics for teaching (range–Doppler maps)."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from teaching_sims.core.units import C_LIGHT, wavelength


@dataclass(frozen=True)
class MovingTarget:
    """Point target with range and radial velocity.

    Positive ``velocity_mps`` means closing (approaching) the radar, so Doppler
    is positive: f_d = +2 v / λ.
    """

    range_m: float
    velocity_mps: float
    snr_db: float = 20.0

    def __post_init__(self) -> None:
        if self.range_m < 0:
            raise ValueError("range_m must be >= 0")


@dataclass(frozen=True)
class PulseDopplerParams:
    """One CPI of baseband pulse-Doppler video after range matched filtering."""

    n_pulses: int = 64
    pri_s: float = 100e-6
    frequency_hz: float = 10e9
    # Range-impulse response width (post-MF), set by effective bandwidth
    bandwidth_hz: float = 5e6
    sample_rate_hz: float = 5e6  # keep range bins manageable for teaching displays
    range_max_m: float | None = 10_000.0
    targets: tuple[MovingTarget, ...] = field(
        default_factory=lambda: (MovingTarget(3500.0, 40.0, snr_db=25.0),)
    )
    clutter_cnr_db: float = 20.0  # clutter-to-noise near zero Doppler
    clutter_enabled: bool = False
    clutter_width_mps: float = 0.8  # Gaussian spectrum σ_v (narrow ridge)
    noise_enabled: bool = True
    mti_canceller: bool = False  # two-pulse canceller before Doppler FFT
    doppler_window: bool = True  # Hann on slow time
    seed: int = 0

    def __post_init__(self) -> None:
        if self.n_pulses < 4:
            raise ValueError("n_pulses must be >= 4")
        if self.pri_s <= 0 or self.bandwidth_hz <= 0 or self.sample_rate_hz <= 0:
            raise ValueError("PRI, bandwidth, and sample rate must be positive")
        if self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be positive")

    @property
    def lambda_m(self) -> float:
        return wavelength(self.frequency_hz)

    @property
    def prf_hz(self) -> float:
        return 1.0 / self.pri_s

    @property
    def unambiguous_range_m(self) -> float:
        return C_LIGHT * self.pri_s / 2.0

    @property
    def unambiguous_velocity_mps(self) -> float:
        # |f_d| < PRF/2 → |v| < λ·PRF/4
        return self.lambda_m * self.prf_hz / 4.0

    @property
    def range_resolution_m(self) -> float:
        return C_LIGHT / (2.0 * self.bandwidth_hz)

    @property
    def velocity_resolution_mps(self) -> float:
        # Doppler bin ≈ PRF / N → Δv = λ Δf / 2
        return self.lambda_m * self.prf_hz / (2.0 * self.n_pulses)


def doppler_hz(velocity_mps: float, lambda_m: float) -> float:
    return 2.0 * velocity_mps / lambda_m


def wrap_doppler_hz(fd_hz: float, prf_hz: float) -> float:
    """Wrap Doppler into (−PRF/2, PRF/2]."""
    return ((fd_hz + 0.5 * prf_hz) % prf_hz) - 0.5 * prf_hz


def apparent_velocity_mps(velocity_mps: float, params: PulseDopplerParams) -> float:
    fd = wrap_doppler_hz(doppler_hz(velocity_mps, params.lambda_m), params.prf_hz)
    return fd * params.lambda_m / 2.0


def _range_axis(params: PulseDopplerParams) -> np.ndarray:
    r_max = params.range_max_m if params.range_max_m is not None else params.unambiguous_range_m
    dr = C_LIGHT / (2.0 * params.sample_rate_hz)
    n = max(int(np.floor(r_max / dr)), 8)
    return np.arange(n, dtype=float) * dr


def _range_impulse(range_axis: np.ndarray, range_m: float, resolution_m: float) -> np.ndarray:
    """Simple Gaussian range IRF (post matched filter)."""
    sigma = max(resolution_m / 2.355, range_axis[1] - range_axis[0])
    return np.exp(-0.5 * ((range_axis - range_m) / sigma) ** 2)


def _smooth_range_texture(rng: np.random.Generator, n_r: int, corr_bins: int = 25) -> np.ndarray:
    """Positive, slowly varying range texture (not white speckles)."""
    raw = rng.lognormal(mean=0.0, sigma=0.35, size=n_r)
    corr_bins = max(int(corr_bins), 1)
    if corr_bins > 1:
        kernel = np.hanning(corr_bins * 2 + 1)
        kernel = kernel / kernel.sum()
        raw = np.convolve(raw, kernel, mode="same")
    return raw / (np.median(raw) + 1e-15)


def simulate_cpi(params: PulseDopplerParams) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(range_m, slow_time_s, video)`` with video shape (N_pulses, N_range)."""
    rng = np.random.default_rng(params.seed)
    r_axis = _range_axis(params)
    n_r = len(r_axis)
    n_p = params.n_pulses
    t_slow = np.arange(n_p, dtype=float) * params.pri_s
    video = np.zeros((n_p, n_r), dtype=complex)

    # Thermal noise (unit variance complex); target amplitudes set relative to it.
    sigma_n = 1.0
    if params.noise_enabled:
        video += (rng.normal(size=(n_p, n_r)) + 1j * rng.normal(size=(n_p, n_r))) * (
            sigma_n / np.sqrt(2.0)
        )

    # Clutter: smooth range ridge + narrow Doppler spectrum around 0 Hz.
    if params.clutter_enabled and params.clutter_cnr_db > -50:
        amp = 10 ** (params.clutter_cnr_db / 20.0) * sigma_n
        texture = _smooth_range_texture(rng, n_r)
        sigma_fd = max(2.0 * params.clutter_width_mps / params.lambda_m, 1e-3)
        white = (rng.normal(size=(n_p, n_r)) + 1j * rng.normal(size=(n_p, n_r))) / np.sqrt(2.0)
        spec = np.fft.fft(white, axis=0)
        fd = np.fft.fftfreq(n_p, d=params.pri_s)
        # Strong DC emphasis so the ridge reads as a line, not speckled noise.
        shape = np.exp(-0.5 * (fd / sigma_fd) ** 2).astype(float)
        shape[0] = max(shape[0], 1.0)  # ensure DC bin dominates
        shape = shape / (np.linalg.norm(shape) + 1e-15) * np.sqrt(n_p)
        coloured = np.fft.ifft(spec * shape[:, None], axis=0)
        video += amp * coloured * texture[None, :]

    for tgt in params.targets:
        # Fold range into unambiguous / display window for placement
        r_app = tgt.range_m % params.unambiguous_range_m
        r_lim = params.range_max_m if params.range_max_m is not None else params.unambiguous_range_m
        r_app = r_app % r_lim
        irf = _range_impulse(r_axis, r_app, params.range_resolution_m)
        amp = 10 ** (tgt.snr_db / 20.0) * sigma_n
        fd = doppler_hz(tgt.velocity_mps, params.lambda_m)
        phase = np.exp(1j * 2.0 * np.pi * fd * t_slow)
        video += amp * phase[:, None] * irf[None, :]

    return r_axis, t_slow, video


def two_pulse_mti(video: np.ndarray) -> np.ndarray:
    """Two-pulse canceller along slow time: y[n]=x[n]-x[n-1] (zero-pad first)."""
    out = np.zeros_like(video)
    out[1:] = video[1:] - video[:-1]
    return out


def range_doppler_map(
    params: PulseDopplerParams,
    *,
    video: np.ndarray | None = None,
    range_m: np.ndarray | None = None,
) -> dict[str, np.ndarray | float]:
    """Compute range–Doppler power map (dB, peak-normalised)."""
    if video is None:
        range_m, t_slow, video = simulate_cpi(params)
    else:
        if range_m is None:
            range_m = _range_axis(params)
        t_slow = np.arange(video.shape[0], dtype=float) * params.pri_s

    proc = two_pulse_mti(video) if params.mti_canceller else video
    n_p = proc.shape[0]

    win = np.hanning(n_p) if params.doppler_window else np.ones(n_p)
    win = win / (np.linalg.norm(win) + 1e-15)
    gated = proc * win[:, None]

    spec = np.fft.fftshift(np.fft.fft(gated, axis=0), axes=0)
    power = np.abs(spec) ** 2
    peak = float(np.max(power)) + 1e-30
    pdb = 10.0 * np.log10(power / peak)

    fd = np.fft.fftshift(np.fft.fftfreq(n_p, d=params.pri_s))
    vel = fd * params.lambda_m / 2.0

    return {
        "range_m": range_m,
        "slow_time_s": t_slow,
        "video": video,
        "processed": proc,
        "doppler_hz": fd,
        "velocity_mps": vel,
        "rd_db": pdb,
        "prf_hz": float(params.prf_hz),
        "unambiguous_range_m": float(params.unambiguous_range_m),
        "unambiguous_velocity_mps": float(params.unambiguous_velocity_mps),
        "range_resolution_m": float(params.range_resolution_m),
        "velocity_resolution_mps": float(params.velocity_resolution_mps),
    }


def doppler_cut_db(rd_db: np.ndarray, range_m: np.ndarray, range_query_m: float) -> np.ndarray:
    i = int(np.argmin(np.abs(range_m - range_query_m)))
    return rd_db[:, i]


def range_cut_db(rd_db: np.ndarray, velocity_mps: np.ndarray, vel_query_mps: float) -> np.ndarray:
    i = int(np.argmin(np.abs(velocity_mps - vel_query_mps)))
    return rd_db[i, :]
