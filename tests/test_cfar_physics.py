"""Tests for CFAR physics."""

from __future__ import annotations

import numpy as np

from teaching_sims.topics.cfar.physics import (
    CFARMethod,
    CFARParams,
    CFARTarget,
    ca_cfar_alpha,
    process,
)


def test_ca_alpha_formula():
    n = 24
    pfa = 1e-3
    alpha = ca_cfar_alpha(n, pfa)
    assert abs((1.0 + alpha / n) ** (-n) - pfa) < 1e-12


def test_ca_detects_strong_target():
    p = CFARParams(
        method=CFARMethod.CA,
        pfa=1e-3,
        targets=(CFARTarget(100, snr_db=25.0),),
        seed=1,
    )
    out = process(p)
    report = out["report"]
    assert 100 in report["hits"]
    assert report["misses"] == []


def test_fixed_threshold_false_alarms_in_clutter():
    p = CFARParams(
        method=CFARMethod.CA,
        pfa=1e-3,
        clutter_edge_enabled=True,
        clutter_edge_cell=120,
        clutter_ratio_db=15.0,
        targets=(CFARTarget(60, snr_db=20.0),),
        seed=2,
    )
    out = process(p)
    power = out["power"]
    fixed = out["fixed_threshold"]
    fixed_det = power > fixed
    # Noise-only fixed threshold floods the clutter region.
    clutter_fas = int(np.sum(fixed_det[p.clutter_edge_cell :]))
    assert clutter_fas > 10

    # Deep inside clutter (away from the edge), CA-CFAR should track the
    # higher power and declare far fewer FAs than the fixed threshold.
    interior = p.clutter_edge_cell + 2 * (p.n_train + p.n_guard)
    fixed_interior = int(np.sum(fixed_det[interior:]))
    cfar_interior = [
        i for i in out["report"]["false_alarms"] if i >= interior
    ]
    assert fixed_interior > 5
    assert len(cfar_interior) < fixed_interior // 2


def test_go_fewer_edge_fas_than_so():
    shared = dict(
        clutter_edge_enabled=True,
        clutter_edge_cell=140,
        clutter_ratio_db=14.0,
        pfa=1e-3,
        targets=(CFARTarget(80, snr_db=18.0),),
        seed=5,
    )
    go = process(CFARParams(method=CFARMethod.GO, **shared))
    so = process(CFARParams(method=CFARMethod.SO, **shared))
    assert len(go["report"]["false_alarms"]) <= len(so["report"]["false_alarms"])


def test_os_helps_masked_neighbour():
    shared = dict(
        n_train=16,
        n_guard=1,
        pfa=1e-3,
        targets=(CFARTarget(120, 28.0), CFARTarget(128, 14.0)),
        seed=3,
    )
    ca = process(CFARParams(method=CFARMethod.CA, **shared))
    os_ = process(CFARParams(method=CFARMethod.OS, os_rank=3, **shared))
    # Weak neighbour at 128: OS should be at least as good as CA at finding it.
    ca_hit = 128 in ca["report"]["hits"]
    os_hit = 128 in os_["report"]["hits"]
    assert os_hit or not ca_hit
    assert os_hit


def test_lower_pfa_raises_threshold():
    base = dict(method=CFARMethod.CA, targets=(CFARTarget(100, 20.0),), seed=4)
    hi = process(CFARParams(pfa=1e-2, **base))
    lo = process(CFARParams(pfa=1e-4, **base))
    # Compare mean finite thresholds
    thr_hi = np.nanmean(hi["threshold"])
    thr_lo = np.nanmean(lo["threshold"])
    assert thr_lo > thr_hi
