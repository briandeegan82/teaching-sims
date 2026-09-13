"""CFAR detection physics for teaching (1D range profiles)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class CFARMethod(str, Enum):
    CA = "ca"  # cell averaging
    OS = "os"  # ordered statistic
    GO = "go"  # greatest of (left/right CA)
    SO = "so"  # smallest of (left/right CA)


@dataclass(frozen=True)
class CFARTarget:
    cell: int  # index in the range profile
    snr_db: float = 15.0

    def __post_init__(self) -> None:
        if self.cell < 0:
            raise ValueError("cell must be >= 0")


@dataclass(frozen=True)
class CFARParams:
    """Synthetic square-law range profile + CFAR detector settings."""

    n_cells: int = 256
    n_train: int = 12  # training cells each side
    n_guard: int = 2  # guard cells each side
    pfa: float = 1e-3
    method: CFARMethod = CFARMethod.CA
    os_rank: int = 3  # k-th largest in the 2*n_train window (1 = max)
    noise_power: float = 1.0
    targets: tuple[CFARTarget, ...] = field(
        default_factory=lambda: (CFARTarget(100, snr_db=18.0), CFARTarget(160, snr_db=14.0))
    )
    # Optional clutter edge: cells >= edge_cell have power * clutter_ratio
    clutter_edge_enabled: bool = False
    clutter_edge_cell: int = 128
    clutter_ratio_db: float = 15.0
    seed: int = 0

    def __post_init__(self) -> None:
        if self.n_cells < 32:
            raise ValueError("n_cells must be >= 32")
        if self.n_train < 1:
            raise ValueError("n_train must be >= 1")
        if self.n_guard < 0:
            raise ValueError("n_guard must be >= 0")
        if not (0.0 < self.pfa < 1.0):
            raise ValueError("pfa must be in (0,1)")
        if self.os_rank < 1:
            raise ValueError("os_rank must be >= 1")
        need = 2 * (self.n_train + self.n_guard) + 1
        if need >= self.n_cells:
            raise ValueError("n_train/n_guard too large for n_cells")


def ca_cfar_alpha(n_train_total: int, pfa: float) -> float:
    """Scale factor for square-law CA-CFAR when ``Z`` is the *mean* of N cells.

    With ``T = alpha * mean(train)``,
    ``P_fa = (1 + alpha/N)^(-N)``, so ``alpha = N * (P_fa^(-1/N) - 1)``.
    """
    n = float(n_train_total)
    return float(n * (pfa ** (-1.0 / n) - 1.0))


def generate_profile(params: CFARParams) -> np.ndarray:
    """Complex matched-filter samples → square-law power profile."""
    rng = np.random.default_rng(params.seed)
    n = params.n_cells
    # Rayleigh amplitude / exponential power noise
    noise = (rng.normal(size=n) + 1j * rng.normal(size=n)) * np.sqrt(params.noise_power / 2.0)
    x = noise

    clutter_scale = np.ones(n, dtype=float)
    if params.clutter_edge_enabled:
        clutter_scale[params.clutter_edge_cell :] = 10 ** (params.clutter_ratio_db / 20.0)
        x = x * clutter_scale

    for tgt in params.targets:
        if 0 <= tgt.cell < n:
            amp = 10 ** (tgt.snr_db / 20.0) * np.sqrt(params.noise_power) * clutter_scale[tgt.cell]
            # deterministic complex tone in that cell (post-MF peak model)
            x[tgt.cell] += amp

    return np.abs(x) ** 2  # square-law detector


def _training_indices(cut: int, params: CFARParams) -> tuple[np.ndarray, np.ndarray]:
    n = params.n_cells
    g = params.n_guard
    t = params.n_train
    left = np.arange(cut - g - t, cut - g, dtype=int)
    right = np.arange(cut + g + 1, cut + g + 1 + t, dtype=int)
    left = left[(left >= 0) & (left < n)]
    right = right[(right >= 0) & (right < n)]
    return left, right


def cfar_threshold_and_detections(
    power: np.ndarray,
    params: CFARParams,
) -> dict[str, np.ndarray | float]:
    """Run CFAR over interior cells; edges without full windows are skipped."""
    n = len(power)
    threshold = np.full(n, np.nan, dtype=float)
    detected = np.zeros(n, dtype=bool)
    noise_est = np.full(n, np.nan, dtype=float)

    n_train_nominal = 2 * params.n_train
    alpha_ca = ca_cfar_alpha(n_train_nominal, params.pfa)

    first = params.n_train + params.n_guard
    last = n - params.n_train - params.n_guard

    for cut in range(first, last):
        left, right = _training_indices(cut, params)
        if len(left) == 0 or len(right) == 0:
            continue
        train = np.concatenate([power[left], power[right]])

        if params.method == CFARMethod.CA:
            z = float(np.mean(train))
            alpha = ca_cfar_alpha(len(train), params.pfa)
            thr = alpha * z
        elif params.method == CFARMethod.GO:
            z_l, z_r = float(np.mean(power[left])), float(np.mean(power[right]))
            z = max(z_l, z_r)
            # Use half-window N for alpha as a teaching approximation
            alpha = ca_cfar_alpha(max(len(left), len(right)), params.pfa)
            thr = alpha * z
        elif params.method == CFARMethod.SO:
            z_l, z_r = float(np.mean(power[left])), float(np.mean(power[right]))
            z = min(z_l, z_r)
            alpha = ca_cfar_alpha(max(len(left), len(right)), params.pfa)
            thr = alpha * z
        elif params.method == CFARMethod.OS:
            # k-th largest: sort descending
            ranked = np.sort(train)[::-1]
            k = min(params.os_rank, len(ranked)) - 1
            z = float(ranked[k])
            # OS scaling: use same alpha form with N as a simple teaching stand-in
            alpha = ca_cfar_alpha(len(train), params.pfa)
            thr = alpha * z
        else:
            raise ValueError(f"unknown method: {params.method}")

        noise_est[cut] = z
        threshold[cut] = thr
        detected[cut] = power[cut] > thr

    return {
        "power": power,
        "threshold": threshold,
        "noise_est": noise_est,
        "detected": detected,
        "alpha_ca": alpha_ca,
        "n_train_total": float(n_train_nominal),
    }


def fixed_threshold(power: np.ndarray, pfa: float, noise_power: float) -> np.ndarray:
    """Ideal exponential-noise fixed threshold: P(x>T)=exp(-T/σ²) for power x."""
    # For complex AWGN → exponential power with mean σ²: P_fa = exp(-T/σ²)
    # T = -σ² ln(P_fa)
    t = -noise_power * np.log(pfa)
    return np.full_like(power, t, dtype=float)


def detection_report(
    params: CFARParams,
    detected: np.ndarray,
    *,
    match_radius: int = 1,
) -> dict[str, object]:
    """Compare detections to known target cells."""
    det_idx = np.flatnonzero(detected)
    hits = []
    misses = []
    for tgt in params.targets:
        ok = np.any(np.abs(det_idx - tgt.cell) <= match_radius)
        (hits if ok else misses).append(tgt.cell)
    # False alarms: detections not near any target
    fas = []
    for i in det_idx:
        if not any(abs(int(i) - t.cell) <= match_radius for t in params.targets):
            fas.append(int(i))
    return {
        "hits": hits,
        "misses": misses,
        "false_alarms": fas,
        "n_detections": int(det_idx.size),
    }


def process(params: CFARParams) -> dict[str, object]:
    power = generate_profile(params)
    out = cfar_threshold_and_detections(power, params)
    report = detection_report(params, out["detected"])  # type: ignore[arg-type]
    out["fixed_threshold"] = fixed_threshold(power, params.pfa, params.noise_power)
    out["report"] = report
    out["power_db"] = 10.0 * np.log10(np.asarray(out["power"]) + 1e-30)
    thr = np.asarray(out["threshold"], dtype=float)
    out["threshold_db"] = 10.0 * np.log10(np.where(np.isfinite(thr), thr, np.nan) + 1e-30)
    out["fixed_threshold_db"] = 10.0 * np.log10(np.asarray(out["fixed_threshold"]) + 1e-30)
    return out
