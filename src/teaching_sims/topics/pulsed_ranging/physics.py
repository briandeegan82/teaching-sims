"""Pulsed radar ranging physics for teaching."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from teaching_sims.core.units import C_LIGHT


class WaveformType(str, Enum):
    RECT = "rect"
    LFM = "lfm"


@dataclass(frozen=True)
class Target:
    range_m: float
    snr_db: float = 20.0  # peak SNR after matched filter (approx design)

    def __post_init__(self) -> None:
        if self.range_m < 0:
            raise ValueError("range_m must be >= 0")


@dataclass(frozen=True)
class PulseRadarParams:
    """Baseband pulsed-radar scene (complex envelope)."""

    waveform: WaveformType = WaveformType.RECT
    pulse_width_s: float = 1e-6
    bandwidth_hz: float = 5e6  # LFM sweep; also used for rect approx B≈1/Tp teaching note
    pri_s: float = 100e-6
    sample_rate_hz: float = 40e6
    targets: tuple[Target, ...] = field(
        default_factory=lambda: (Target(range_m=2000.0, snr_db=25.0),)
    )
    noise_enabled: bool = True
    matched_filter: bool = True
    window_hann: bool = False
    seed: int = 0
    # Display window: number of PRIs to show (usually 1)
    n_pri_display: int = 1

    def __post_init__(self) -> None:
        if self.pulse_width_s <= 0:
            raise ValueError("pulse_width_s must be positive")
        if self.bandwidth_hz <= 0:
            raise ValueError("bandwidth_hz must be positive")
        if self.pri_s <= self.pulse_width_s:
            raise ValueError("pri_s must exceed pulse_width_s")
        if self.sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")
        if self.n_pri_display < 1:
            raise ValueError("n_pri_display must be >= 1")


def range_resolution_m(params: PulseRadarParams) -> float:
    """Approximate range resolution.

    Rect: c * Tp / 2.  LFM (pulse compression): c / (2 B).
    """
    if params.waveform == WaveformType.LFM and params.matched_filter:
        return C_LIGHT / (2.0 * params.bandwidth_hz)
    return C_LIGHT * params.pulse_width_s / 2.0


def max_unambiguous_range_m(params: PulseRadarParams) -> float:
    return C_LIGHT * params.pri_s / 2.0


def time_to_range_m(t_s: np.ndarray | float) -> np.ndarray | float:
    return C_LIGHT * t_s / 2.0


def range_to_time_s(range_m: np.ndarray | float) -> np.ndarray | float:
    return 2.0 * range_m / C_LIGHT


def _pulse_samples(params: PulseRadarParams) -> int:
    return max(int(round(params.pulse_width_s * params.sample_rate_hz)), 1)


def transmit_waveform(params: PulseRadarParams) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(t_s, tx)`` complex baseband pulse starting at t=0."""
    n = _pulse_samples(params)
    t = np.arange(n, dtype=float) / params.sample_rate_hz
    if params.waveform == WaveformType.RECT:
        tx = np.ones(n, dtype=complex)
    elif params.waveform == WaveformType.LFM:
        # Sweep −B/2 .. +B/2 over the pulse
        b = params.bandwidth_hz
        tp = params.pulse_width_s
        # Instantaneous phase: π (B/Tp) t^2 - π B t  (starts at -B/2)
        tx = np.exp(1j * np.pi * (b / tp) * t**2 - 1j * np.pi * b * t)
    else:
        raise ValueError(f"unknown waveform: {params.waveform}")

    if params.window_hann and n > 1:
        tx = tx * np.hanning(n)

    # Unit energy pulse (before amplitude scaling per target)
    tx = tx / np.sqrt(np.vdot(tx, tx).real + 1e-30)
    return t, tx


def _delay_samples(range_m: float, fs: float) -> int:
    return int(round(range_to_time_s(range_m) * fs))


def simulate_pri(params: PulseRadarParams) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Simulate one (or more) PRI of received baseband video.

    Returns ``(t_s, rx, range_m_axis)``.
    Ambiguous ranges fold modulo PRI into the display window.
    """
    rng = np.random.default_rng(params.seed)
    fs = params.sample_rate_hz
    n_pri = max(int(round(params.pri_s * fs)), _pulse_samples(params) + 1)
    n = n_pri * params.n_pri_display
    t = np.arange(n, dtype=float) / fs
    _, tx = transmit_waveform(params)
    rx = np.zeros(n, dtype=complex)

    # Noise variance chosen so MF peak SNR ≈ requested for a unit-energy pulse.
    # For matched filter, peak SNR ≈ 2 E / N0 with complex baseband convention;
    # with unit-energy pulse and amplitude A, MF peak ≈ A and noise var σ²,
    # SNR_amp^2 ≈ |A|^2 / σ². We set σ² from the first target as reference floor.
    sigma = 1.0
    if params.noise_enabled and params.targets:
        # Use median requested SNR to set noise; amplitudes set per target below.
        ref = float(np.median([tr.snr_db for tr in params.targets]))
        sigma = 10 ** (-ref / 20.0)

    for tr in params.targets:
        amp = 10 ** (tr.snr_db / 20.0) * sigma
        # Fold range into unambiguous interval for placement, but keep true
        # delay modulo PRI (range ambiguity teaching).
        tau = range_to_time_s(tr.range_m)
        delay = int(round((tau % params.pri_s) * fs))
        if delay + len(tx) <= n:
            rx[delay : delay + len(tx)] += amp * tx
        else:
            # Wrap within buffer (rare for n_pri_display=1 if delay near end)
            for i, v in enumerate(tx):
                rx[(delay + i) % n] += amp * v

    if params.noise_enabled:
        noise = (rng.normal(size=n) + 1j * rng.normal(size=n)) * (sigma / np.sqrt(2.0))
        rx = rx + noise

    return t, rx, time_to_range_m(t)


def matched_filter_output(
    params: PulseRadarParams,
    rx: np.ndarray,
) -> np.ndarray:
    """Correlate ``rx`` with the TX waveform (matched filter)."""
    _, tx = transmit_waveform(params)
    # Full correlation, then align so peak delay matches echo delay
    # (same indexing as rx: lag 0 at sample 0).
    mf = np.convolve(rx, np.conj(tx[::-1]), mode="full")
    # Convolve full length is len(rx)+len(tx)-1; trim to rx length with
    # causal alignment (filter delay = len(tx)-1).
    start = len(tx) - 1
    return mf[start : start + len(rx)]


def process_video(params: PulseRadarParams) -> dict[str, np.ndarray | float]:
    """Run TX/RX/(optional MF) and return arrays for plotting."""
    t, rx, r_axis = simulate_pri(params)
    _, tx = transmit_waveform(params)
    t_tx = np.arange(len(tx), dtype=float) / params.sample_rate_hz

    if params.matched_filter:
        y = matched_filter_output(params, rx)
    else:
        y = rx

    env = np.abs(y)
    return {
        "t_s": t,
        "range_m": r_axis,
        "rx": rx,
        "video": y,
        "envelope": env,
        "t_tx_s": t_tx,
        "tx": tx,
        "range_resolution_m": range_resolution_m(params),
        "max_unambiguous_range_m": max_unambiguous_range_m(params),
    }


def detect_peaks(
    envelope: np.ndarray,
    range_m: np.ndarray,
    *,
    min_prominence_ratio: float = 0.25,
    max_peaks: int = 6,
) -> tuple[np.ndarray, np.ndarray]:
    """Simple peak picker for teaching overlays."""
    if len(envelope) < 3:
        return np.array([]), np.array([])
    thr = min_prominence_ratio * float(np.max(envelope) + 1e-30)
    idx = []
    for i in range(1, len(envelope) - 1):
        if envelope[i] >= envelope[i - 1] and envelope[i] > envelope[i + 1] and envelope[i] >= thr:
            idx.append(i)
    # Keep strongest
    idx = sorted(idx, key=lambda i: envelope[i], reverse=True)[:max_peaks]
    idx = sorted(idx)
    return range_m[idx], envelope[idx]
