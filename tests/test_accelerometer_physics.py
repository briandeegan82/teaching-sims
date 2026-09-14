"""Unit tests for accelerometer physics."""

from __future__ import annotations

import numpy as np

from teaching_sims.core.imu import G0
from teaching_sims.topics.accelerometer.physics import AccelParams, process, tilt_from_accel, true_specific_force_body


def test_level_specific_force():
    f = true_specific_force_body(AccelParams(roll_deg=0.0, pitch_deg=0.0))
    assert abs(f[0]) < 1e-9
    assert abs(f[1]) < 1e-9
    assert abs(f[2] + G0) < 1e-9


def test_tilt_roundtrip_static():
    p = AccelParams(roll_deg=18.0, pitch_deg=-12.0, noise_mps2=0.0, vibe_amp_mps2=0.0)
    f = true_specific_force_body(p)
    roll, pitch = tilt_from_accel(f[0], f[1], f[2])
    assert abs(roll - 18.0) < 1e-6
    assert abs(pitch - (-12.0)) < 1e-6


def test_bias_looks_like_pitch():
    p = AccelParams(roll_deg=0.0, pitch_deg=0.0, bias_x_mps2=0.5, noise_mps2=0.0)
    out = process(p)
    assert abs(out["pitch_mean_deg"]) > 2.0


def test_surge_contaminates_pitch():
    p = AccelParams(roll_deg=0.0, pitch_deg=0.0, ax_mps2=2.0, noise_mps2=0.0)
    out = process(p)
    assert abs(out["pitch_mean_deg"]) > 5.0


def test_yaw_invisible_to_accel():
    """Gravity specific force depends on roll/pitch only, not yaw."""
    base = AccelParams(yaw_deg=0.0, roll_deg=15.0, pitch_deg=-8.0, noise_mps2=0.0)
    turned = AccelParams(yaw_deg=60.0, roll_deg=15.0, pitch_deg=-8.0, noise_mps2=0.0)
    f0 = true_specific_force_body(base)
    f1 = true_specific_force_body(turned)
    assert np.allclose(f0, f1)
    r0, p0 = tilt_from_accel(f0[0], f0[1], f0[2])
    r1, p1 = tilt_from_accel(f1[0], f1[1], f1[2])
    assert abs(r0 - 15.0) < 1e-6
    assert abs(p0 + 8.0) < 1e-6
    assert abs(r0 - r1) < 1e-6
    assert abs(p0 - p1) < 1e-6


def test_vibration_mean_recovers():
    p = AccelParams(
        roll_deg=10.0,
        pitch_deg=5.0,
        vibe_amp_mps2=3.0,
        vibe_hz=40.0,
        noise_mps2=0.0,
        duration_s=2.0,
        fs_hz=200.0,
    )
    out = process(p)
    assert abs(out["roll_mean_deg"] - 10.0) < 0.5
    assert abs(out["pitch_mean_deg"] - 5.0) < 0.5
