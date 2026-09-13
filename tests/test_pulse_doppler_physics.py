"""Tests for pulse-Doppler physics."""

from __future__ import annotations

import numpy as np

from teaching_sims.topics.pulse_doppler.physics import (
    MovingTarget,
    PulseDopplerParams,
    apparent_velocity_mps,
    range_doppler_map,
    wrap_doppler_hz,
)


def test_wrap_doppler():
    assert abs(wrap_doppler_hz(0.0, 1000.0)) < 1e-9
    assert abs(wrap_doppler_hz(1200.0, 1000.0) - 200.0) < 1e-9
    # −600 Hz at PRF=1000 aliases to +400 Hz in (−500, 500]
    assert abs(wrap_doppler_hz(-600.0, 1000.0) - 400.0) < 1e-9


def test_single_mover_peak_near_truth():
    p = PulseDopplerParams(
        clutter_enabled=False,
        noise_enabled=True,
        n_pulses=64,
        targets=(MovingTarget(3000.0, 40.0, snr_db=30.0),),
        seed=1,
    )
    out = range_doppler_map(p)
    rd = out["rd_db"]
    i, j = np.unravel_index(int(np.argmax(rd)), rd.shape)
    r_hat = float(out["range_m"][j])
    v_hat = float(out["velocity_mps"][i])
    assert abs(r_hat - 3000.0) < 80.0
    assert abs(v_hat - 40.0) < 5.0


def test_mti_suppresses_zero_doppler():
    p_off = PulseDopplerParams(
        clutter_enabled=True,
        clutter_cnr_db=35.0,
        targets=(),
        mti_canceller=False,
        seed=2,
    )
    p_on = PulseDopplerParams(
        clutter_enabled=True,
        clutter_cnr_db=35.0,
        targets=(),
        mti_canceller=True,
        seed=2,
    )
    rd_off = range_doppler_map(p_off)["rd_db"]
    rd_on = range_doppler_map(p_on)["rd_db"]

    def center_fraction(rd_db: np.ndarray) -> float:
        power = 10.0 ** (rd_db / 10.0)
        mid = power.shape[0] // 2
        return float(power[mid - 1 : mid + 2].sum() / power.sum())

    # Without MTI, a large share of energy sits near zero Doppler.
    assert center_fraction(rd_off) > 0.15
    # Two-pulse canceller removes a large fraction of that DC ridge.
    assert center_fraction(rd_on) < 0.5 * center_fraction(rd_off)


def test_doppler_ambiguity_folds_velocity():
    p = PulseDopplerParams(
        frequency_hz=10e9,
        pri_s=200e-6,
        clutter_enabled=False,
        targets=(MovingTarget(2500.0, 120.0, snr_db=35.0),),
        seed=3,
    )
    v_app = apparent_velocity_mps(120.0, p)
    assert abs(v_app - 120.0) > 10.0  # truly ambiguous
    out = range_doppler_map(p)
    rd = out["rd_db"]
    i, j = np.unravel_index(int(np.argmax(rd)), rd.shape)
    v_hat = float(out["velocity_mps"][i])
    assert abs(v_hat - v_app) < 8.0


def test_longer_cpi_finer_velocity_resolution():
    short = PulseDopplerParams(n_pulses=16, clutter_enabled=False, targets=())
    long = PulseDopplerParams(n_pulses=64, clutter_enabled=False, targets=())
    assert long.velocity_resolution_mps < short.velocity_resolution_mps
