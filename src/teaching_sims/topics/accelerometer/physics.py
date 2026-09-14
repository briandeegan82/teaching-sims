"""Accelerometer teaching physics: specific force, tilt, vibration contamination."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from teaching_sims.core.imu import DEG2RAD, G0, RAD2DEG
from teaching_sims.topics.attitude.physics import euler_zyx_to_dcm


@dataclass(frozen=True)
class AccelParams:
    """Static / quasi-static accelerometer experiment in body frame."""

    yaw_deg: float = 0.0
    roll_deg: float = 10.0
    pitch_deg: float = -5.0
    # Optional body linear acceleration (m/s^2) contaminating tilt
    ax_mps2: float = 0.0
    ay_mps2: float = 0.0
    az_mps2: float = 0.0
    bias_x_mps2: float = 0.0
    bias_y_mps2: float = 0.0
    bias_z_mps2: float = 0.0
    noise_mps2: float = 0.02
    duration_s: float = 4.0
    fs_hz: float = 100.0
    # Vibration (sinusoid on body X) to show averaging vs tilt
    vibe_amp_mps2: float = 0.0
    vibe_hz: float = 25.0
    seed: int = 0

    def __post_init__(self) -> None:
        if self.fs_hz <= 0 or self.duration_s <= 0:
            raise ValueError("fs_hz and duration_s must be positive")
        if abs(self.pitch_deg) >= 89.0:
            raise ValueError("pitch_deg must be in (-89, 89) for this demo")


def true_specific_force_body(params: AccelParams) -> np.ndarray:
    """Ideal body specific force for a static (or quasi-static) platform.

    Uses the common aerospace level convention: at rest and level, f ≈ [0, 0, -g].
    Optional ax/ay/az add true linear acceleration in body axes (contamination).
    """
    yaw = params.yaw_deg * DEG2RAD
    pitch = params.pitch_deg * DEG2RAD
    roll = params.roll_deg * DEG2RAD
    r_nb = euler_zyx_to_dcm(yaw, pitch, roll)
    # Level NED specific force (stationary, a=0): [0, 0, -g]
    f_ned = np.array([0.0, 0.0, -G0], dtype=float)
    f_body = r_nb.T @ f_ned
    f_body = f_body + np.array([params.ax_mps2, params.ay_mps2, params.az_mps2], dtype=float)
    return f_body


def tilt_from_accel(fx: float, fy: float, fz: float) -> tuple[float, float]:
    """Roll/pitch (deg) from specific force (ZYX body frame, Z down).

    Yaw is unobservable from gravity alone; these formulas recover roll/pitch only.
    """
    roll = np.arctan2(-fy, -fz)
    pitch = np.arctan2(fx, np.hypot(fy, fz))
    return float(roll * RAD2DEG), float(pitch * RAD2DEG)


def simulate_accel(params: AccelParams) -> dict[str, object]:
    """Time series of noisy accel + tilt estimates."""
    n = int(params.duration_s * params.fs_hz)
    t = np.arange(n, dtype=float) / params.fs_hz
    f0 = true_specific_force_body(params)
    vibe = params.vibe_amp_mps2 * np.sin(2.0 * np.pi * params.vibe_hz * t)
    rng = np.random.default_rng(params.seed)
    noise = rng.normal(0.0, params.noise_mps2, size=(n, 3))
    bias = np.array([params.bias_x_mps2, params.bias_y_mps2, params.bias_z_mps2])
    meas = np.tile(f0, (n, 1)) + noise + bias
    meas[:, 0] += vibe

    rolls = np.empty(n)
    pitches = np.empty(n)
    for i in range(n):
        rolls[i], pitches[i] = tilt_from_accel(meas[i, 0], meas[i, 1], meas[i, 2])

    # Mean estimate over window (teaching: averaging helps vibration, not bias/accel)
    mean_f = meas.mean(axis=0)
    roll_hat, pitch_hat = tilt_from_accel(mean_f[0], mean_f[1], mean_f[2])

    return {
        "t_s": t,
        "fx": meas[:, 0],
        "fy": meas[:, 1],
        "fz": meas[:, 2],
        "roll_est_deg": rolls,
        "pitch_est_deg": pitches,
        "true_f_body": f0,
        "roll_mean_deg": roll_hat,
        "pitch_mean_deg": pitch_hat,
        "roll_err_deg": roll_hat - params.roll_deg,
        "pitch_err_deg": pitch_hat - params.pitch_deg,
        "true_yaw_deg": params.yaw_deg,
        "true_roll_deg": params.roll_deg,
        "true_pitch_deg": params.pitch_deg,
    }


def process(params: AccelParams) -> dict[str, object]:
    return simulate_accel(params)
