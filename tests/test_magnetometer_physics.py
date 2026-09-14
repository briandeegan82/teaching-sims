"""Unit tests for magnetometer / heading."""

from __future__ import annotations

from teaching_sims.topics.magnetometer.physics import MagParams, process


def test_level_heading_ok():
    out = process(MagParams(pitch_deg=0.0, roll_deg=0.0, noise_ut=0.0, tilt_compensate=True))
    assert out["rms_err_deg"] < 1.0


def test_pitch_without_tc_errs():
    raw = process(
        MagParams(pitch_deg=30.0, roll_deg=0.0, noise_ut=0.0, tilt_compensate=False, soft_xx=1.0, soft_yy=1.0)
    )
    tc = process(
        MagParams(pitch_deg=30.0, roll_deg=0.0, noise_ut=0.0, tilt_compensate=True, soft_xx=1.0, soft_yy=1.0)
    )
    assert tc["rms_err_deg"] < raw["rms_err_deg"]


def test_hard_iron_raises_error():
    clean = process(MagParams(noise_ut=0.0, hard_x_ut=0.0, hard_y_ut=0.0))
    dirty = process(MagParams(noise_ut=0.0, hard_x_ut=10.0, hard_y_ut=-8.0))
    assert dirty["rms_err_deg"] > clean["rms_err_deg"]
