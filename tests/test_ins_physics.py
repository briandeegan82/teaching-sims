"""Unit tests for strapdown INS."""

from __future__ import annotations

from teaching_sims.topics.ins.physics import INSParams, PathProfile, process


def test_perfect_circle_stays_close():
    out = process(
        INSParams(
            profile=PathProfile.CIRCLE,
            perfect_attitude=True,
            gyro_bias_dps=0.0,
            accel_bias_x_mps2=0.0,
            accel_bias_y_mps2=0.0,
            accel_noise_mps2=0.0,
            gyro_noise_dps=0.0,
            duration_s=40.0,
            fs_hz=50.0,
        )
    )
    assert out["final_pos_err_m"] < 3.0


def test_accel_bias_grows_error():
    clean = process(
        INSParams(
            profile=PathProfile.STRAIGHT,
            perfect_attitude=True,
            accel_bias_x_mps2=0.0,
            accel_noise_mps2=0.0,
            gyro_noise_dps=0.0,
            duration_s=20.0,
        )
    )
    biased = process(
        INSParams(
            profile=PathProfile.STRAIGHT,
            perfect_attitude=True,
            accel_bias_x_mps2=0.1,
            accel_noise_mps2=0.0,
            gyro_noise_dps=0.0,
            duration_s=20.0,
        )
    )
    assert biased["final_pos_err_m"] > clean["final_pos_err_m"] + 5.0


def test_gyro_bias_hurts_circle():
    out = process(
        INSParams(
            profile=PathProfile.CIRCLE,
            perfect_attitude=False,
            gyro_bias_dps=0.5,
            accel_bias_x_mps2=0.0,
            accel_bias_y_mps2=0.0,
            accel_noise_mps2=0.0,
            gyro_noise_dps=0.0,
            duration_s=40.0,
        )
    )
    assert out["final_pos_err_m"] > 5.0
