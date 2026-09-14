"""Strapdown INS teaching: 2D dead reckoning with attitude and accel errors."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from teaching_sims.core.imu import DEG2RAD, RAD2DEG, wrap_180


class PathProfile(str, Enum):
    STRAIGHT = "straight"
    CIRCLE = "circle"
    STOP_AND_GO = "stop_and_go"


@dataclass(frozen=True)
class INSParams:
    """Planar (North-East) INS; heading from yaw-rate gyro, accel in body x/y."""

    profile: PathProfile = PathProfile.CIRCLE
    speed_mps: float = 5.0
    radius_m: float = 40.0
    duration_s: float = 40.0
    fs_hz: float = 50.0
    gyro_bias_dps: float = 0.2
    accel_bias_x_mps2: float = 0.05  # body forward
    accel_bias_y_mps2: float = 0.0  # body right
    accel_noise_mps2: float = 0.02
    gyro_noise_dps: float = 0.05
    perfect_attitude: bool = False
    seed: int = 0

    def __post_init__(self) -> None:
        if self.fs_hz <= 0 or self.duration_s <= 0:
            raise ValueError("fs_hz and duration_s must be positive")
        if self.speed_mps < 0:
            raise ValueError("speed_mps must be >= 0")


def _truth(params: INSParams, t: np.ndarray) -> dict[str, np.ndarray]:
    n = len(t)
    dt = t[1] - t[0] if n > 1 else 1.0
    north = np.zeros(n)
    east = np.zeros(n)
    hdg = np.zeros(n)
    ax = np.zeros(n)  # body forward
    ay = np.zeros(n)  # body right

    if params.profile == PathProfile.STRAIGHT:
        north = params.speed_mps * t
        return {"north": north, "east": east, "hdg": hdg, "ax": ax, "ay": ay}

    if params.profile == PathProfile.STOP_AND_GO:
        v = np.zeros(n)
        for i, ti in enumerate(t):
            if ti < 5.0:
                ax[i] = params.speed_mps / 5.0
                v[i] = ax[i] * ti
            elif ti < 25.0:
                v[i] = params.speed_mps
            elif ti < 30.0:
                ax[i] = -params.speed_mps / 5.0
                v[i] = params.speed_mps + ax[i] * (ti - 25.0)
            else:
                v[i] = max(0.0, v[i - 1] + ax[i] * dt) if i else 0.0
        north = np.cumsum(v) * dt
        return {"north": north, "east": east, "hdg": hdg, "ax": ax, "ay": ay}

    r = max(params.radius_m, 1e-9)
    omega = params.speed_mps / r  # rad/s
    north = r * np.sin(omega * t)
    east = r * (1.0 - np.cos(omega * t))
    hdg = wrap_180(omega * t * RAD2DEG)
    ay[:] = params.speed_mps**2 / r  # centripetal to the right for CCW
    return {"north": north, "east": east, "hdg": hdg, "ax": ax, "ay": ay}


def simulate_ins(params: INSParams) -> dict[str, object]:
    n = int(params.duration_s * params.fs_hz)
    dt = 1.0 / params.fs_hz
    t = np.arange(n, dtype=float) * dt
    truth = _truth(params, t)
    n_true, e_true, hdg_true = truth["north"], truth["east"], truth["hdg"]
    ax_true, ay_true = truth["ax"], truth["ay"]
    yaw_rate_true = np.gradient(hdg_true, dt)

    rng = np.random.default_rng(params.seed)
    gyro = yaw_rate_true + params.gyro_bias_dps + rng.normal(0.0, params.gyro_noise_dps, n)
    ax_m = ax_true + params.accel_bias_x_mps2 + rng.normal(0.0, params.accel_noise_mps2, n)
    ay_m = ay_true + params.accel_bias_y_mps2 + rng.normal(0.0, params.accel_noise_mps2, n)

    hdg_est = hdg_true.copy() if params.perfect_attitude else wrap_180(np.cumsum(gyro) * dt)

    vn = np.zeros(n)
    ve = np.zeros(n)
    n_est = np.zeros(n)
    e_est = np.zeros(n)
    for i in range(1, n):
        psi = hdg_est[i] * DEG2RAD
        c, s = np.cos(psi), np.sin(psi)
        # body x forward, y right → NED
        an = ax_m[i] * c - ay_m[i] * s
        ae = ax_m[i] * s + ay_m[i] * c
        vn[i] = vn[i - 1] + an * dt
        ve[i] = ve[i - 1] + ae * dt
        n_est[i] = n_est[i - 1] + vn[i] * dt
        e_est[i] = e_est[i - 1] + ve[i] * dt

    # Seed initial velocity from truth so constant-speed cases start fair
    if params.profile in (PathProfile.STRAIGHT, PathProfile.CIRCLE):
        vn0 = params.speed_mps
        ve0 = 0.0
        vn[0], ve[0] = vn0, ve0
        for i in range(1, n):
            psi = hdg_est[i] * DEG2RAD
            c, s = np.cos(psi), np.sin(psi)
            an = ax_m[i] * c - ay_m[i] * s
            ae = ax_m[i] * s + ay_m[i] * c
            vn[i] = vn[i - 1] + an * dt
            ve[i] = ve[i - 1] + ae * dt
            n_est[i] = n_est[i - 1] + vn[i] * dt
            e_est[i] = e_est[i - 1] + ve[i] * dt

    pos_err = np.hypot(n_est - n_true, e_est - e_true)
    return {
        "t_s": t,
        "north_true_m": n_true,
        "east_true_m": e_true,
        "north_est_m": n_est,
        "east_est_m": e_est,
        "hdg_true_deg": hdg_true,
        "hdg_est_deg": hdg_est,
        "pos_err_m": pos_err,
        "final_pos_err_m": float(pos_err[-1]),
        "ax_meas": ax_m,
        "ay_meas": ay_m,
        "gyro_meas_dps": gyro,
    }


def process(params: INSParams) -> dict[str, object]:
    return simulate_ins(params)
