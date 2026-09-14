"""Attitude / rotation teaching: Euler ZYX, DCM, quaternion, gimbal lock."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from teaching_sims.core.imu import DEG2RAD, RAD2DEG, wrap_180, wrap_pi


@dataclass(frozen=True)
class AttitudeParams:
    """Visualize body axes and Euler ↔ quaternion conversions."""

    yaw_deg: float = 20.0
    pitch_deg: float = 15.0
    roll_deg: float = -10.0
    # Animated tip toward gimbal lock
    animate_pitch: bool = False
    pitch_scan_deg: float = 85.0
    n_samples: int = 181
    seed: int = 0

    def __post_init__(self) -> None:
        if self.n_samples < 3:
            raise ValueError("n_samples must be >= 3")


def euler_zyx_to_dcm(yaw: float, pitch: float, roll: float) -> np.ndarray:
    """Body-to-NED DCM for ZYX (yaw-pitch-roll) aerospace sequence."""
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cr, sr = np.cos(roll), np.sin(roll)
    return np.array(
        [
            [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
            [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
            [-sp, cp * sr, cp * cr],
        ],
        dtype=float,
    )


def dcm_to_euler_zyx(r: np.ndarray) -> tuple[float, float, float]:
    """Extract yaw, pitch, roll (rad). Pitch near ±90 is singular."""
    sp = float(np.clip(-r[2, 0], -1.0, 1.0))
    pitch = np.arcsin(sp)
    if abs(sp) < 0.999999:
        roll = np.arctan2(r[2, 1], r[2, 2])
        yaw = np.arctan2(r[1, 0], r[0, 0])
    else:
        # Gimbal lock: yaw and roll coupled
        roll = 0.0
        yaw = np.arctan2(-r[0, 1], r[1, 1])
    return float(yaw), float(pitch), float(roll)


def euler_to_quat(yaw: float, pitch: float, roll: float) -> np.ndarray:
    """Quaternion [w, x, y, z] for ZYX Euler."""
    cy, sy = np.cos(yaw * 0.5), np.sin(yaw * 0.5)
    cp, sp = np.cos(pitch * 0.5), np.sin(pitch * 0.5)
    cr, sr = np.cos(roll * 0.5), np.sin(roll * 0.5)
    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    q = np.array([w, x, y, z], dtype=float)
    return q / np.linalg.norm(q)


def quat_to_dcm(q: np.ndarray) -> np.ndarray:
    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=float,
    )


def body_axes_ned(yaw_deg: float, pitch_deg: float, roll_deg: float) -> dict[str, np.ndarray]:
    """Unit body axes expressed in NED."""
    r = euler_zyx_to_dcm(yaw_deg * DEG2RAD, pitch_deg * DEG2RAD, roll_deg * DEG2RAD)
    return {"x": r[:, 0], "y": r[:, 1], "z": r[:, 2], "dcm": r}


def process(params: AttitudeParams) -> dict[str, object]:
    yaw0 = params.yaw_deg * DEG2RAD
    roll0 = params.roll_deg * DEG2RAD

    if params.animate_pitch:
        pitches = np.linspace(-params.pitch_scan_deg, params.pitch_scan_deg, params.n_samples)
    else:
        pitches = np.array([params.pitch_deg], dtype=float)

    yaw_ext = []
    pitch_ext = []
    roll_ext = []
    singular = []
    for p_deg in pitches:
        r = euler_zyx_to_dcm(yaw0, p_deg * DEG2RAD, roll0)
        y, p, rr = dcm_to_euler_zyx(r)
        yaw_ext.append(wrap_180(y * RAD2DEG))
        pitch_ext.append(p * RAD2DEG)
        roll_ext.append(wrap_180(rr * RAD2DEG))
        singular.append(abs(np.cos(p)) < 0.05)

    # Snapshot at current / mid pitch
    p_use = params.pitch_deg if not params.animate_pitch else 0.0
    axes = body_axes_ned(params.yaw_deg, p_use, params.roll_deg)
    q = euler_to_quat(params.yaw_deg * DEG2RAD, p_use * DEG2RAD, params.roll_deg * DEG2RAD)
    r_q = quat_to_dcm(q)
    y2, p2, r2 = dcm_to_euler_zyx(r_q)

    return {
        "pitch_scan_deg": pitches,
        "yaw_extracted_deg": np.asarray(yaw_ext),
        "pitch_extracted_deg": np.asarray(pitch_ext),
        "roll_extracted_deg": np.asarray(roll_ext),
        "near_singular": np.asarray(singular, dtype=bool),
        "body_x_ned": axes["x"],
        "body_y_ned": axes["y"],
        "body_z_ned": axes["z"],
        "quat": q,
        "euler_from_quat_deg": np.array([y2, p2, r2]) * RAD2DEG,
        "det_dcm": float(np.linalg.det(axes["dcm"])),
    }
