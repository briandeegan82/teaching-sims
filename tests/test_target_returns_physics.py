"""Unit tests for target-returns / RCS physics."""

from __future__ import annotations

import numpy as np

from teaching_sims.core.units import C_LIGHT, wavelength
from teaching_sims.topics.target_returns.physics import (
    TargetReturnsParams,
    TargetShape,
    process,
    rcs_corner_m2,
    rcs_flat_plate_m2,
    rcs_sphere_m2,
    snr_from_rcs_db,
    target_rcs_m2,
)


def test_sphere_optical_rcs():
    assert abs(rcs_sphere_m2(1.0) - np.pi) < 1e-12


def test_plate_much_larger_than_sphere_at_xband():
    lam = wavelength(10e9)
    plate = rcs_flat_plate_m2(1.0, lam, 0.0)
    sphere = rcs_sphere_m2(0.5)
    assert plate > 100.0 * sphere


def test_corner_formula():
    lam = 0.03
    a = 0.5
    expect = 12.0 * np.pi * a**4 / lam**2
    assert abs(rcs_corner_m2(a, lam) - expect) < 1e-9


def test_range_law_12db_when_double_range():
    near = TargetReturnsParams(shape=TargetShape.SPHERE, size_m=1.0, range_m=5000.0, noise_enabled=False)
    far = TargetReturnsParams(shape=TargetShape.SPHERE, size_m=1.0, range_m=10_000.0, noise_enabled=False)
    assert abs(snr_from_rcs_db(near) - snr_from_rcs_db(far) - 12.0412) < 0.05


def test_plate_aspect_reduces_rcs():
    broad = TargetReturnsParams(shape=TargetShape.FLAT_PLATE, size_m=1.0, size2_m=1.0, aspect_deg=0.0)
    edge = TargetReturnsParams(shape=TargetShape.FLAT_PLATE, size_m=1.0, size2_m=1.0, aspect_deg=80.0)
    assert target_rcs_m2(broad) > 10.0 * target_rcs_m2(edge)


def test_echo_peak_near_true_range():
    p = TargetReturnsParams(
        shape=TargetShape.SPHERE,
        size_m=1.0,
        range_m=4000.0,
        noise_enabled=False,
        pulse_width_s=0.4e-6,
        sample_rate_hz=50e6,
    )
    out = process(p)
    r = np.asarray(out["range_m"], dtype=float)
    env = np.asarray(out["envelope"], dtype=float)
    i = int(np.argmax(env))
    assert abs(float(r[i]) - 4000.0) < C_LIGHT * p.pulse_width_s  # within one pulse width in range


def test_extended_wider_than_sphere():
    sphere = process(
        TargetReturnsParams(
            shape=TargetShape.SPHERE,
            size_m=1.0,
            range_m=5000.0,
            noise_enabled=False,
            pulse_width_s=0.25e-6,
            sample_rate_hz=50e6,
        )
    )
    extended = process(
        TargetReturnsParams(
            shape=TargetShape.EXTENDED,
            size_m=50.0,
            size2_m=3.0,
            aspect_deg=90.0,
            range_m=5000.0,
            noise_enabled=False,
            pulse_width_s=0.25e-6,
            sample_rate_hz=50e6,
        )
    )
    assert float(extended["extent_m"]) > float(sphere["extent_m"])
    # Half-energy width proxy: count bins above 50% of peak
    def width(out):
        env = np.asarray(out["envelope"], dtype=float)
        thr = 0.5 * float(np.max(env))
        return int(np.sum(env >= thr))

    assert width(extended) > width(sphere)
