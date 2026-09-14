"""Unit tests for complementary filter."""

from __future__ import annotations

from teaching_sims.topics.complementary.physics import ComplementaryParams, process


def test_comp_beats_gyro_with_bias():
    p = ComplementaryParams(
        alpha=0.98,
        gyro_bias_dps=1.5,
        gyro_noise_dps=0.05,
        accel_noise_mps2=0.05,
        surge_mps2=0.0,
        duration_s=12.0,
    )
    out = process(p)
    assert out["rms_comp_deg"] < out["rms_gyro_deg"]


def test_surge_hurts_accel():
    quiet = process(
        ComplementaryParams(alpha=0.0, surge_mps2=0.0, gyro_bias_dps=0.0, amp_deg=5.0, duration_s=6.0)
    )
    surge = process(
        ComplementaryParams(alpha=0.0, surge_mps2=3.0, gyro_bias_dps=0.0, amp_deg=5.0, duration_s=6.0)
    )
    assert surge["rms_accel_deg"] > quiet["rms_accel_deg"]
