"""Unit tests for attitude / rotation helpers."""

from __future__ import annotations

import numpy as np

from teaching_sims.core.imu import DEG2RAD
from teaching_sims.topics.attitude.physics import (
    AttitudeParams,
    dcm_to_euler_zyx,
    euler_to_quat,
    euler_zyx_to_dcm,
    process,
    quat_to_dcm,
)


def test_dcm_orthogonal():
    r = euler_zyx_to_dcm(0.3, -0.2, 0.1)
    assert abs(np.linalg.det(r) - 1.0) < 1e-9
    assert np.allclose(r @ r.T, np.eye(3), atol=1e-9)


def test_euler_roundtrip():
    y, p, r = 0.4, -0.25, 0.15
    y2, p2, r2 = dcm_to_euler_zyx(euler_zyx_to_dcm(y, p, r))
    assert abs(y2 - y) < 1e-9
    assert abs(p2 - p) < 1e-9
    assert abs(r2 - r) < 1e-9


def test_quat_roundtrip():
    q = euler_to_quat(0.2, -0.1, 0.3)
    y, p, r = dcm_to_euler_zyx(quat_to_dcm(q))
    assert abs(y - 0.2) < 1e-9
    assert abs(p + 0.1) < 1e-9
    assert abs(r - 0.3) < 1e-9


def test_gimbal_lock_flagged():
    out = process(
        AttitudeParams(yaw_deg=20.0, roll_deg=10.0, animate_pitch=True, pitch_scan_deg=89.0, n_samples=179)
    )
    assert bool(np.any(out["near_singular"]))
