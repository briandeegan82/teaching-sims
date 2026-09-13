"""Tests for pulsed ranging physics."""

from __future__ import annotations

import numpy as np

from teaching_sims.core.units import C_LIGHT
from teaching_sims.topics.pulsed_ranging.physics import (
    PulseRadarParams,
    Target,
    WaveformType,
    detect_peaks,
    max_unambiguous_range_m,
    process_video,
    range_resolution_m,
)


def test_rect_resolution_formula():
    p = PulseRadarParams(waveform=WaveformType.RECT, pulse_width_s=1e-6, matched_filter=True)
    assert abs(range_resolution_m(p) - C_LIGHT * 1e-6 / 2) < 1e-6


def test_lfm_resolution_uses_bandwidth():
    p = PulseRadarParams(
        waveform=WaveformType.LFM,
        pulse_width_s=20e-6,
        bandwidth_hz=10e6,
        matched_filter=True,
    )
    assert abs(range_resolution_m(p) - C_LIGHT / (2 * 10e6)) < 1e-6


def test_single_echo_peak_near_truth():
    p = PulseRadarParams(
        waveform=WaveformType.RECT,
        pulse_width_s=0.5e-6,
        sample_rate_hz=40e6,
        matched_filter=True,
        noise_enabled=False,
        targets=(Target(2500.0, snr_db=40.0),),
    )
    out = process_video(p)
    peaks_r, _ = detect_peaks(out["envelope"], out["range_m"], min_prominence_ratio=0.5)
    assert len(peaks_r) >= 1
    assert abs(float(peaks_r[0]) - 2500.0) < 40.0


def test_lfm_resolves_close_targets():
    p = PulseRadarParams(
        waveform=WaveformType.LFM,
        pulse_width_s=20e-6,
        bandwidth_hz=15e6,
        sample_rate_hz=50e6,
        pri_s=200e-6,
        matched_filter=True,
        noise_enabled=False,
        targets=(Target(4000.0, snr_db=35.0), Target(4120.0, snr_db=35.0)),
    )
    out = process_video(p)
    peaks_r, _ = detect_peaks(out["envelope"], out["range_m"], min_prominence_ratio=0.3, max_peaks=4)
    assert len(peaks_r) >= 2
    assert min(abs(float(r) - 4000.0) for r in peaks_r) < 40.0
    assert min(abs(float(r) - 4120.0) for r in peaks_r) < 40.0


def test_range_ambiguity_folds():
    p = PulseRadarParams(
        waveform=WaveformType.RECT,
        pulse_width_s=0.4e-6,
        pri_s=50e-6,
        matched_filter=True,
        noise_enabled=False,
        targets=(Target(10000.0, snr_db=40.0),),
    )
    r_unamb = max_unambiguous_range_m(p)
    apparent = 10000.0 % r_unamb
    out = process_video(p)
    peaks_r, _ = detect_peaks(out["envelope"], out["range_m"], min_prominence_ratio=0.5)
    assert abs(float(peaks_r[0]) - apparent) < 50.0
