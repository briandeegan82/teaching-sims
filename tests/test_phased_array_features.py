"""Tests for pattern feature callouts."""

from __future__ import annotations

from teaching_sims.topics.phased_array.features import (
    pattern_features,
    theoretical_grating_angles_deg,
)
from teaching_sims.topics.phased_array.physics import ArrayParams


def test_theoretical_grating_at_d_equals_lambda():
    p = ArrayParams(n_elements=8, d_over_lambda=1.0, steer_deg=0.0)
    g = theoretical_grating_angles_deg(p)
    assert any(abs(a - 90.0) < 1.0 or abs(a + 90.0) < 1.0 for a in g)


def test_features_find_main_and_grating():
    p = ArrayParams(n_elements=8, d_over_lambda=0.9, steer_deg=25.0)
    feat = pattern_features(p)
    assert abs(feat.main_peak_deg - 25.0) < 3.0
    assert len(feat.grating_peaks_deg) + len(feat.theoretical_grating_deg) > 0


def test_features_find_nulls_near_main():
    p = ArrayParams(n_elements=8, d_over_lambda=0.5, steer_deg=0.0)
    feat = pattern_features(p)
    assert len(feat.nulls_deg) >= 2
