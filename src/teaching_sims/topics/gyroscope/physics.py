"""Gyroscope teaching physics: rate sensing, integration, bias, and random walk."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from teaching_sims.core.imu import DEG2RAD, RAD2DEG, wrap_180


class MotionProfile(str, Enum):
    CONSTANT = "constant"  # constant rate then stop
    SINE = "sine"
    STEP_TURN = "step_turn"


@dataclass(frozen=True)
class GyroParams:
    """Single-axis (Z) gyro experiment for attitude about one axis."""

    profile: MotionProfile = MotionProfile.STEP_TURN
    rate_dps: float = 30.0  # commanded rate magnitude
    sine_hz: float = 0.5
    duration_s: float = 8.0
    fs_hz: float = 100.0
    bias_dps: float = 0.5
    # Angle random walk (deg/√s) — white rate noise density
    arw_deg_per_sqrt_s: float = 0.05
    # Integrate with / without bias compensation (subtract known bias)
    compensate_bias: bool = False
    seed: int = 0

    def __post_init__(self) -> None:
        if self.fs_hz <= 0 or self.duration_s <= 0:
            raise ValueError("fs_hz and duration_s must be positive")
        if self.arw_deg_per_sqrt_s < 0:
            raise ValueError("arw must be >= 0")


def true_rate_dps(params: GyroParams, t: np.ndarray) -> np.ndarray:
    """Scripted true angular rate about Z (deg/s)."""
    if params.profile == MotionProfile.CONSTANT:
        return np.full_like(t, params.rate_dps, dtype=float)
    if params.profile == MotionProfile.SINE:
        return params.rate_dps * np.sin(2.0 * np.pi * params.sine_hz * t)
    # step turn: rotate for 3 s then stop
    w = np.zeros_like(t)
    w[(t >= 1.0) & (t < 4.0)] = params.rate_dps
    return w


def simulate_gyro(params: GyroParams) -> dict[str, object]:
    n = int(params.duration_s * params.fs_hz)
    dt = 1.0 / params.fs_hz
    t = np.arange(n, dtype=float) * dt
    w_true = true_rate_dps(params, t)
    theta_true = np.cumsum(w_true) * dt
    theta_true = wrap_180(theta_true)

    rng = np.random.default_rng(params.seed)
    # White rate noise: σ_rate = ARW * √fs  (deg/s)
    sigma = params.arw_deg_per_sqrt_s * np.sqrt(params.fs_hz)
    noise = rng.normal(0.0, sigma, size=n) if sigma > 0 else np.zeros(n)
    w_meas = w_true + params.bias_dps + noise
    w_int = w_meas - (params.bias_dps if params.compensate_bias else 0.0)
    theta_hat = wrap_180(np.cumsum(w_int) * dt)
    err = wrap_180(theta_hat - theta_true)

    return {
        "t_s": t,
        "rate_true_dps": w_true,
        "rate_meas_dps": w_meas,
        "angle_true_deg": theta_true,
        "angle_est_deg": theta_hat,
        "angle_err_deg": err,
        "final_err_deg": float(err[-1]),
        "bias_dps": params.bias_dps,
        "sigma_rate_dps": float(sigma),
    }


def process(params: GyroParams) -> dict[str, object]:
    return simulate_gyro(params)
