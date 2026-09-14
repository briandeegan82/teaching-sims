"""Complementary-filter attitude fusion (1-DOF pitch teaching model)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from teaching_sims.core.imu import DEG2RAD, G0, RAD2DEG, wrap_180


class PitchMotion(str, Enum):
    SINE = "sine"
    RAMP = "ramp"
    STEP = "step"


@dataclass(frozen=True)
class ComplementaryParams:
    """Fuse gyro rate with accelerometer tilt on a single pitch axis."""

    motion: PitchMotion = PitchMotion.SINE
    amp_deg: float = 25.0
    sine_hz: float = 0.25
    duration_s: float = 12.0
    fs_hz: float = 100.0
    # Complementary weight on gyro path (0→trust accel only, 1→gyro only)
    alpha: float = 0.98
    gyro_bias_dps: float = 0.8
    gyro_noise_dps: float = 0.3
    accel_noise_mps2: float = 0.15
    # Horizontal linear accel (m/s^2) that contaminates accel tilt
    surge_mps2: float = 0.0
    seed: int = 0

    def __post_init__(self) -> None:
        if not (0.0 <= self.alpha <= 1.0):
            raise ValueError("alpha must be in [0, 1]")
        if self.fs_hz <= 0 or self.duration_s <= 0:
            raise ValueError("fs_hz and duration_s must be positive")


def true_pitch_deg(params: ComplementaryParams, t: np.ndarray) -> np.ndarray:
    if params.motion == PitchMotion.SINE:
        return params.amp_deg * np.sin(2.0 * np.pi * params.sine_hz * t)
    if params.motion == PitchMotion.RAMP:
        return np.clip(params.amp_deg * (t / max(params.duration_s, 1e-9)), -90, 90)
    # step at mid-time
    out = np.zeros_like(t)
    out[t >= 0.5 * params.duration_s] = params.amp_deg
    return out


def simulate_complementary(params: ComplementaryParams) -> dict[str, object]:
    n = int(params.duration_s * params.fs_hz)
    dt = 1.0 / params.fs_hz
    t = np.arange(n, dtype=float) * dt
    pitch = true_pitch_deg(params, t)
    # Central-difference rate (deg/s)
    rate = np.gradient(pitch, dt)

    rng = np.random.default_rng(params.seed)
    gyro = rate + params.gyro_bias_dps + rng.normal(0.0, params.gyro_noise_dps, n)

    # Specific force for pitch-only: f_x = -g sin(θ) + surge, f_z = -g cos(θ)
    th = pitch * DEG2RAD
    fx = -G0 * np.sin(th) + params.surge_mps2 + rng.normal(0.0, params.accel_noise_mps2, n)
    fz = -G0 * np.cos(th) + rng.normal(0.0, params.accel_noise_mps2, n)
    accel_tilt = wrap_180(np.arctan2(-fx, -fz) * RAD2DEG)

    # Pure integrations / filters
    gyro_only = wrap_180(np.cumsum(gyro) * dt)
    # complementary: high-pass gyro + low-pass accel
    a = params.alpha
    comp = np.zeros(n)
    comp[0] = accel_tilt[0]
    for i in range(1, n):
        comp[i] = a * (comp[i - 1] + gyro[i] * dt) + (1.0 - a) * accel_tilt[i]
    comp = wrap_180(comp)

    return {
        "t_s": t,
        "pitch_true_deg": pitch,
        "gyro_rate_dps": gyro,
        "accel_tilt_deg": accel_tilt,
        "gyro_only_deg": gyro_only,
        "comp_deg": comp,
        "err_gyro_deg": wrap_180(gyro_only - pitch),
        "err_accel_deg": wrap_180(accel_tilt - pitch),
        "err_comp_deg": wrap_180(comp - pitch),
        "rms_comp_deg": float(np.sqrt(np.mean(wrap_180(comp - pitch) ** 2))),
        "rms_gyro_deg": float(np.sqrt(np.mean(wrap_180(gyro_only - pitch) ** 2))),
        "rms_accel_deg": float(np.sqrt(np.mean(wrap_180(accel_tilt - pitch) ** 2))),
    }


def process(params: ComplementaryParams) -> dict[str, object]:
    return simulate_complementary(params)
