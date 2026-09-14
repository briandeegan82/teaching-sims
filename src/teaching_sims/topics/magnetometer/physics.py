"""Magnetometer / tilt-compensated heading teaching physics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from teaching_sims.core.imu import DEG2RAD, RAD2DEG, wrap_180
from teaching_sims.topics.attitude.physics import euler_zyx_to_dcm


@dataclass(frozen=True)
class MagParams:
    """Body magnetometer with optional hard/soft-iron and tilt."""

    yaw_deg: float = 35.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    # Local Earth field in NED (µT) — mild Northern-hemisphere-like
    b_north_ut: float = 20.0
    b_east_ut: float = 0.0
    b_down_ut: float = 45.0
    # Hard-iron bias (body µT)
    hard_x_ut: float = 0.0
    hard_y_ut: float = 0.0
    hard_z_ut: float = 0.0
    # Soft-iron scale (diagonal) and cross-coupling xy
    soft_xx: float = 1.0
    soft_yy: float = 1.0
    soft_zz: float = 1.0
    soft_xy: float = 0.0
    noise_ut: float = 0.3
    # Sweep yaw for polar plot if enabled
    sweep_yaw: bool = True
    n_sweep: int = 72
    tilt_compensate: bool = True
    seed: int = 0

    def __post_init__(self) -> None:
        if self.n_sweep < 8:
            raise ValueError("n_sweep must be >= 8")


def earth_field_ned(params: MagParams) -> np.ndarray:
    return np.array([params.b_north_ut, params.b_east_ut, params.b_down_ut], dtype=float)


def soft_iron_matrix(params: MagParams) -> np.ndarray:
    s = np.eye(3)
    s[0, 0] = params.soft_xx
    s[1, 1] = params.soft_yy
    s[2, 2] = params.soft_zz
    s[0, 1] = s[1, 0] = params.soft_xy
    return s


def measure_mag_body(params: MagParams, yaw_deg: float, pitch_deg: float, roll_deg: float, rng) -> np.ndarray:
    r_bn = euler_zyx_to_dcm(yaw_deg * DEG2RAD, pitch_deg * DEG2RAD, roll_deg * DEG2RAD).T
    b_body = r_bn @ earth_field_ned(params)
    hard = np.array([params.hard_x_ut, params.hard_y_ut, params.hard_z_ut])
    b = soft_iron_matrix(params) @ b_body + hard
    if params.noise_ut > 0:
        b = b + rng.normal(0.0, params.noise_ut, size=3)
    return b


def heading_from_mag(bx: float, by: float, bz: float, pitch_deg: float, roll_deg: float, compensate: bool) -> float:
    """Magnetic heading (deg). With compensate=True use tilt-compensated horizontal field."""
    if compensate:
        p = pitch_deg * DEG2RAD
        r = roll_deg * DEG2RAD
        # Tilt compensation (common aerospace form)
        xh = bx * np.cos(p) + by * np.sin(r) * np.sin(p) + bz * np.cos(r) * np.sin(p)
        yh = by * np.cos(r) - bz * np.sin(r)
        return float(wrap_180(np.arctan2(-yh, xh) * RAD2DEG))
    return float(wrap_180(np.arctan2(-by, bx) * RAD2DEG))


def process(params: MagParams) -> dict[str, object]:
    rng = np.random.default_rng(params.seed)
    if params.sweep_yaw:
        yaws = np.linspace(-180.0, 180.0, params.n_sweep, endpoint=False)
    else:
        yaws = np.array([params.yaw_deg], dtype=float)

    bx_s, by_s, bz_s = [], [], []
    hdg_raw, hdg_tc, hdg_err = [], [], []
    for yaw in yaws:
        b = measure_mag_body(params, float(yaw), params.pitch_deg, params.roll_deg, rng)
        bx_s.append(b[0])
        by_s.append(b[1])
        bz_s.append(b[2])
        raw = heading_from_mag(b[0], b[1], b[2], params.pitch_deg, params.roll_deg, False)
        tc = heading_from_mag(b[0], b[1], b[2], params.pitch_deg, params.roll_deg, True)
        use = tc if params.tilt_compensate else raw
        hdg_raw.append(raw)
        hdg_tc.append(tc)
        hdg_err.append(wrap_180(use - yaw))

    # Single pose snapshot at selected yaw
    b0 = measure_mag_body(params, params.yaw_deg, params.pitch_deg, params.roll_deg, rng)
    h0 = heading_from_mag(
        b0[0], b0[1], b0[2], params.pitch_deg, params.roll_deg, params.tilt_compensate
    )

    return {
        "yaw_sweep_deg": yaws,
        "bx": np.asarray(bx_s),
        "by": np.asarray(by_s),
        "bz": np.asarray(bz_s),
        "heading_raw_deg": np.asarray(hdg_raw),
        "heading_tc_deg": np.asarray(hdg_tc),
        "heading_err_deg": np.asarray(hdg_err),
        "snapshot_b_ut": b0,
        "snapshot_heading_deg": h0,
        "snapshot_err_deg": wrap_180(h0 - params.yaw_deg),
        "rms_err_deg": float(np.sqrt(np.mean(np.asarray(hdg_err) ** 2))),
    }
