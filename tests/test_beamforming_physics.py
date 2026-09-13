"""Tests for beamforming physics."""

from __future__ import annotations

import numpy as np

from teaching_sims.topics.beamforming.physics import (
    BeamformerMethod,
    BeamformerParams,
    beampattern_db,
    beamformer_weights,
    conventional_weights,
    output_sinr_db,
    sample_covariance,
    steering_vector,
)


def test_steering_vector_unit_magnitude():
    a = steering_vector(20.0, 8, 0.5)
    assert np.allclose(np.abs(a), 1.0)


def test_conventional_peak_at_look():
    w = conventional_weights(25.0, 16, 0.5)
    theta = np.linspace(-90, 90, 1801)
    pdb = beampattern_db(w, theta, 0.5)
    assert abs(theta[int(np.argmax(pdb))] - 25.0) < 1.0


def test_mvdr_improves_sinr_with_interferer():
    base = dict(
        n_elements=8,
        look_deg=0.0,
        signal_deg=0.0,
        interferer_deg=35.0,
        interferer_enabled=True,
        snr_db=10.0,
        inr_db=25.0,
        n_snapshots=400,
        seed=1,
    )
    p_c = BeamformerParams(**base, method=BeamformerMethod.CONVENTIONAL)
    p_m = BeamformerParams(**base, method=BeamformerMethod.MVDR)
    R, _ = sample_covariance(p_m)
    w_c = beamformer_weights(p_c, R)
    w_m = beamformer_weights(p_m, R)
    assert output_sinr_db(p_m, w_m) > output_sinr_db(p_c, w_c) + 5.0


def test_mvdr_has_deeper_null_near_interferer():
    p = BeamformerParams(
        method=BeamformerMethod.MVDR,
        look_deg=0.0,
        signal_deg=0.0,
        interferer_deg=40.0,
        inr_db=30.0,
        n_snapshots=500,
        seed=2,
    )
    R, _ = sample_covariance(p)
    w = beamformer_weights(p, R)
    theta = np.linspace(-90, 90, 1801)
    pdb = beampattern_db(w, theta, p.d_over_lambda)
    # Pattern near interferer should be low relative to main beam (0 dB).
    i = int(np.argmin(np.abs(theta - 40.0)))
    assert pdb[i] < -15.0


def test_null_steer_places_null():
    p = BeamformerParams(
        method=BeamformerMethod.NULL_STEER,
        look_deg=0.0,
        null_deg=30.0,
        interferer_enabled=False,
    )
    w = beamformer_weights(p)
    theta = np.linspace(-90, 90, 1801)
    pdb = beampattern_db(w, theta, p.d_over_lambda)
    i = int(np.argmin(np.abs(theta - 30.0)))
    assert pdb[i] < -25.0
