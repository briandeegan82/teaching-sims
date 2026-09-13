"""Tests for SAR stripmap physics."""

from __future__ import annotations

import numpy as np

from teaching_sims.core.units import C_LIGHT
from teaching_sims.topics.sar.physics import SARParams, SARPointTarget, process_sar


def test_range_resolution_formula():
    p = SARParams(bandwidth_hz=50e6)
    assert abs(p.range_resolution_m - C_LIGHT / (2 * 50e6)) < 1e-9


def test_longer_aperture_finer_azimuth():
    short = SARParams(n_pulses=64, targets=(SARPointTarget(0.0, 8000.0),))
    long = SARParams(n_pulses=256, targets=(SARPointTarget(0.0, 8000.0),))
    assert long.azimuth_resolution_m < short.azimuth_resolution_m


def test_focused_peak_near_single_target():
    p = SARParams(
        n_pulses=128,
        targets=(SARPointTarget(0.0, 8000.0, rcs_db=0.0),),
        noise_enabled=False,
        noise_snr_db=40.0,
        seed=1,
    )
    out = process_sar(p)
    img = out["image_db"]
    i, j = np.unravel_index(int(np.argmax(img)), img.shape)
    assert abs(float(out["x_m"][i])) < 25.0
    r_true = float(np.hypot(p.altitude_m, 8000.0))
    assert abs(float(out["range_m"][j]) - r_true) < 30.0


def test_two_azimuth_targets_two_peaks():
    p = SARParams(
        n_pulses=256,
        targets=(
            SARPointTarget(-40.0, 8000.0, 0.0),
            SARPointTarget(40.0, 8000.0, 0.0),
        ),
        noise_enabled=False,
        noise_snr_db=35.0,
        seed=2,
    )
    out = process_sar(p)
    img = out["image_db"]
    mid = img.shape[0] // 2
    il, _ = np.unravel_index(int(np.argmax(img[:mid, :])), img[:mid, :].shape)
    ir, _ = np.unravel_index(int(np.argmax(img[mid:, :])), img[mid:, :].shape)
    ir = ir + mid
    assert float(out["x_m"][il]) < -10.0
    assert float(out["x_m"][ir]) > 10.0


def test_focused_sharper_than_unfocused_in_azimuth():
    p = SARParams(
        n_pulses=128,
        targets=(SARPointTarget(0.0, 8000.0, 0.0),),
        noise_enabled=False,
        noise_snr_db=40.0,
        seed=3,
    )
    out = process_sar(p)
    # At the peak range bin, focused azimuth mainlobe should be narrower
    # than the unfocused |rc| streak width (rough energy concentration).
    j = int(np.argmax(np.max(out["image_db"], axis=0)))
    focused_cut = 10 ** (out["image_db"][:, j] / 10.0)
    unf_cut = 10 ** (out["unfocused_db"][:, j] / 10.0)
    focused_cut = focused_cut / focused_cut.max()
    unf_cut = unf_cut / unf_cut.max()
    assert np.sum(focused_cut > 0.5) < np.sum(unf_cut > 0.5)
