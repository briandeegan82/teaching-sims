"""Unit tests for MEMS accelerometer physics."""

from __future__ import annotations

import numpy as np

from teaching_sims.topics.mems_accel.physics import Excitation, MEMSAccelParams, process


def test_rest_centered():
    out = process(MEMSAccelParams(excitation=Excitation.REST, mech_offset_um=0.0, output_bias_mps2=0.0))
    assert abs(float(np.mean(out["x_um"]))) < 1e-6
    assert abs(float(np.mean(out["a_meas_mps2"]))) < 1e-6
    assert abs(float(np.mean(out["dc_fF"]))) < 1e-3


def test_constant_accel_settles():
    p = MEMSAccelParams(
        excitation=Excitation.CONSTANT,
        a_const_mps2=10.0,
        zeta=0.9,
        duration_s=0.3,
        output_bias_mps2=0.0,
        mech_offset_um=0.0,
    )
    out = process(p)
    # Late-time estimate near commanded accel
    assert abs(float(np.mean(out["a_meas_mps2"][-200:])) - 10.0) < 0.5
    assert float(np.mean(out["x_um"][-200:])) < 0.0  # mass lags opposite to +a_ext


def test_output_bias_at_rest():
    out = process(
        MEMSAccelParams(excitation=Excitation.REST, output_bias_mps2=3.0, mech_offset_um=0.0)
    )
    assert abs(float(np.mean(out["a_meas_mps2"])) - 3.0) < 1e-6
    assert abs(float(np.mean(out["x_um"]))) < 1e-6


def test_mech_offset_unbalances_caps():
    out = process(
        MEMSAccelParams(excitation=Excitation.REST, mech_offset_um=0.3, output_bias_mps2=0.0)
    )
    assert abs(float(np.mean(out["dc_fF"]))) > 0.1
    assert abs(float(np.mean(out["a_meas_mps2"]))) > 0.5


def test_impulse_rings_when_underdamped():
    under = process(
        MEMSAccelParams(
            excitation=Excitation.IMPULSE,
            zeta=0.1,
            impulse_amp_mps2=40.0,
            duration_s=0.4,
        )
    )
    over = process(
        MEMSAccelParams(
            excitation=Excitation.IMPULSE,
            zeta=1.4,
            impulse_amp_mps2=40.0,
            duration_s=0.4,
        )
    )
    # Count zero crossings of x after the impulse as a ringing proxy
    def crossings(x):
        s = np.sign(x)
        s[s == 0] = 1
        return int(np.sum(s[1:] * s[:-1] < 0))

    assert crossings(under["x_um"]) > crossings(over["x_um"])
