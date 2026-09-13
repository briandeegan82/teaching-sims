"""Tests for FMCW physics."""

from __future__ import annotations

import numpy as np

from teaching_sims.core.units import C_LIGHT
from teaching_sims.topics.fmcw.physics import (
    FMCWParams,
    FMCWTarget,
    FMCWWaveform,
    beat_frequency_hz,
    process_fmcw,
    range_from_beat_hz,
    triangle_solve,
)


def test_stationary_range_from_beat():
    p = FMCWParams(targets=(FMCWTarget(50.0, 0.0, snr_db=40.0),), noise_enabled=False, n_chirps=8)
    fb = beat_frequency_hz(50.0, 0.0, p)
    assert abs(range_from_beat_hz(fb, p) - 50.0) < 1e-6


def test_range_resolution_formula():
    p = FMCWParams(bandwidth_hz=150e6)
    assert abs(p.range_resolution_m - C_LIGHT / (2 * 150e6)) < 1e-9


def test_spectrum_peak_near_stationary_target():
    p = FMCWParams(
        targets=(FMCWTarget(45.0, 0.0, snr_db=35.0),),
        noise_enabled=False,
        n_chirps=16,
        seed=1,
    )
    out = process_fmcw(p)
    i = int(np.argmax(out["range_profile_db"]))
    assert abs(float(out["range_m"][i]) - 45.0) < 2.0 * p.range_resolution_m


def test_sawtooth_range_bias_with_doppler():
    p = FMCWParams(
        waveform=FMCWWaveform.SAWTOOTH,
        targets=(FMCWTarget(40.0, 25.0, snr_db=35.0),),
        noise_enabled=False,
    )
    fb = beat_frequency_hz(40.0, 25.0, p, up=True)
    r_hat = range_from_beat_hz(fb, p)
    assert abs(r_hat - 40.0) > 0.5  # biased


def test_triangle_recovers_range_and_velocity():
    p = FMCWParams(
        waveform=FMCWWaveform.TRIANGLE,
        targets=(FMCWTarget(40.0, 25.0, snr_db=40.0),),
        noise_enabled=False,
        n_chirps=16,
    )
    fb_up = beat_frequency_hz(40.0, 25.0, p, up=True)
    fb_dn = beat_frequency_hz(40.0, 25.0, p, up=False)
    r, v = triangle_solve(fb_up, fb_dn, p)
    assert abs(r - 40.0) < 1e-6
    assert abs(v - 25.0) < 1e-6


def test_rd_map_peak_near_mover():
    p = FMCWParams(
        waveform=FMCWWaveform.SAWTOOTH,
        n_chirps=64,
        targets=(FMCWTarget(35.0, 15.0, snr_db=30.0),),
        noise_enabled=True,
        seed=2,
    )
    out = process_fmcw(p)
    rd = out["rd_db"]
    i, j = np.unravel_index(int(np.argmax(rd)), rd.shape)
    assert abs(float(out["range_m"][j]) - 35.0) < 3.0
    assert abs(float(out["velocity_mps"][i]) - 15.0) < 5.0
