"""Unit tests for gyroscope physics."""

from __future__ import annotations

import numpy as np

from teaching_sims.topics.gyroscope.physics import GyroParams, MotionProfile, process


def test_clean_integration_step():
    p = GyroParams(
        profile=MotionProfile.STEP_TURN,
        bias_dps=0.0,
        arw_deg_per_sqrt_s=0.0,
        rate_dps=30.0,
        duration_s=8.0,
    )
    out = process(p)
    # 3 s * 30 deg/s = 90 deg
    assert abs(out["angle_true_deg"][-1] - 90.0) < 0.5
    assert abs(out["final_err_deg"]) < 0.5


def test_bias_causes_ramp():
    p = GyroParams(
        profile=MotionProfile.CONSTANT,
        rate_dps=0.0,
        bias_dps=1.0,
        arw_deg_per_sqrt_s=0.0,
        duration_s=10.0,
    )
    out = process(p)
    assert abs(out["final_err_deg"] - 10.0) < 0.2


def test_bias_compensation():
    p = GyroParams(
        profile=MotionProfile.STEP_TURN,
        bias_dps=2.0,
        arw_deg_per_sqrt_s=0.0,
        compensate_bias=True,
    )
    out = process(p)
    assert abs(out["final_err_deg"]) < 0.5
