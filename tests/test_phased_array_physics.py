"""Physics tests for ULA array factor."""

from __future__ import annotations

import numpy as np
import pytest

from teaching_sims.topics.phased_array.physics import (
    ArrayParams,
    SteeringMode,
    array_factor,
    half_power_beamwidth_deg,
    pattern_db,
    peak_angle_deg,
    steering_phases,
)


def test_broadside_peak_at_zero():
    p = ArrayParams(n_elements=8, d_over_lambda=0.5, steer_deg=0.0)
    assert abs(peak_angle_deg(p)) < 1.0


def test_steered_peak_tracks_command():
    p = ArrayParams(n_elements=16, d_over_lambda=0.5, steer_deg=30.0)
    assert abs(peak_angle_deg(p) - 30.0) < 1.5


def test_progressive_phase_is_linear():
    p = ArrayParams(n_elements=5, d_over_lambda=0.5, steer_deg=20.0)
    ph = np.unwrap(steering_phases(p))
    diffs = np.diff(ph)
    assert np.allclose(diffs, diffs[0], rtol=1e-6, atol=1e-9)


def test_grating_lobe_when_spacing_large():
    p = ArrayParams(n_elements=8, d_over_lambda=1.0, steer_deg=0.0)
    theta = np.linspace(-90, 90, 1801)
    pdb = pattern_db(theta, p)
    # At d=λ there should be strong responses near ±90° as well as 0°.
    near_edge = np.max(pdb[np.abs(np.abs(theta) - 90) < 2])
    assert near_edge > -3.0


def test_hpbw_narrows_with_n():
    narrow = half_power_beamwidth_deg(ArrayParams(n_elements=16, d_over_lambda=0.5))
    wide = half_power_beamwidth_deg(ArrayParams(n_elements=4, d_over_lambda=0.5))
    assert narrow < wide


def test_phase_squint_vs_ttd():
    base = dict(
        n_elements=12,
        d_over_lambda=0.5,
        steer_deg=40.0,
        frequency_hz=12e9,
        design_frequency_hz=10e9,
    )
    phase = ArrayParams(**base, steering_mode=SteeringMode.PHASE_SHIFT)
    ttd = ArrayParams(**base, steering_mode=SteeringMode.TRUE_TIME_DELAY)
    # Phase steering designed at 10 GHz should squint when run at 12 GHz.
    assert abs(peak_angle_deg(phase) - 40.0) > 2.0
    assert abs(peak_angle_deg(ttd) - 40.0) < 2.0


def test_array_factor_normalization():
    p = ArrayParams(n_elements=8, steer_deg=0.0)
    af = array_factor(np.array([0.0]), p, normalize=True)
    assert abs(abs(af[0]) - 1.0) < 1e-6


def test_quantized_phase_changes_weights():
    cont = ArrayParams(n_elements=8, steer_deg=25.0, phase_bits=None)
    quant = ArrayParams(n_elements=8, steer_deg=25.0, phase_bits=2)
    assert not np.allclose(steering_phases(cont), steering_phases(quant))
