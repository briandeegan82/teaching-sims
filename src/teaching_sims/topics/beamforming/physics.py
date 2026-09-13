"""Digital beamforming physics for teaching (ULA, conventional + MVDR)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np


class BeamformerMethod(str, Enum):
    CONVENTIONAL = "conventional"
    MVDR = "mvdr"
    NULL_STEER = "null_steer"


@dataclass(frozen=True)
class BeamformerParams:
    """Narrowband ULA beamforming scene.

    Angles in degrees from broadside (same convention as the phased-array topic).
    """

    n_elements: int = 8
    d_over_lambda: float = 0.5
    look_deg: float = 0.0
    signal_deg: float = 0.0
    interferer_deg: float = 35.0
    interferer_enabled: bool = True
    snr_db: float = 10.0
    inr_db: float = 20.0
    n_snapshots: int = 256
    method: BeamformerMethod = BeamformerMethod.CONVENTIONAL
    null_deg: float = 35.0
    diagonal_loading_db: float = -np.inf  # relative to trace(R)/N; -inf = off
    seed: int = 0

    def __post_init__(self) -> None:
        if self.n_elements < 2:
            raise ValueError("n_elements must be >= 2")
        if self.d_over_lambda <= 0:
            raise ValueError("d_over_lambda must be positive")
        if self.n_snapshots < 1:
            raise ValueError("n_snapshots must be >= 1")


def element_indices(n: int) -> np.ndarray:
    return np.arange(n, dtype=float) - (n - 1) / 2.0


def steering_vector(theta_deg: float, n: int, d_over_lambda: float) -> np.ndarray:
    """Unit-norm? No — classic a(θ) with |a_n|=1 (not normalised by √N)."""
    idx = element_indices(n)
    phase = 2.0 * np.pi * d_over_lambda * idx * np.sin(np.deg2rad(theta_deg))
    return np.exp(1j * phase)


def steering_matrix(theta_deg: np.ndarray, n: int, d_over_lambda: float) -> np.ndarray:
    """Return A with shape (N, M) for M angles."""
    theta = np.asarray(theta_deg, dtype=float)
    idx = element_indices(n)[:, None]
    phase = 2.0 * np.pi * d_over_lambda * idx * np.sin(np.deg2rad(theta))[None, :]
    return np.exp(1j * phase)


def conventional_weights(look_deg: float, n: int, d_over_lambda: float) -> np.ndarray:
    """Delay-and-sum / Bartlett weights looking at ``look_deg``."""
    a = steering_vector(look_deg, n, d_over_lambda)
    return a / n


def null_steer_weights(
    look_deg: float,
    null_deg: float,
    n: int,
    d_over_lambda: float,
) -> np.ndarray:
    """Simple projection null: (I − a_n a_n^H/‖a_n‖²) a_look, then normalise."""
    a_l = steering_vector(look_deg, n, d_over_lambda)
    a_n = steering_vector(null_deg, n, d_over_lambda)
    p = np.outer(a_n, a_n.conj()) / (np.vdot(a_n, a_n).real + 1e-15)
    w = a_l - p @ a_l
    denom = np.vdot(a_l, w)
    if abs(denom) < 1e-15:
        return conventional_weights(look_deg, n, d_over_lambda)
    return w / denom


def sample_covariance(params: BeamformerParams) -> tuple[np.ndarray, np.ndarray]:
    """Generate snapshots and sample covariance R = XX^H / L.

    Returns ``(R, X)`` with X shape (N, L).
    """
    rng = np.random.default_rng(params.seed)
    n = params.n_elements
    l = params.n_snapshots
    noise = (rng.normal(size=(n, l)) + 1j * rng.normal(size=(n, l))) / np.sqrt(2.0)

    sigma_s = 10 ** (params.snr_db / 20.0)
    a_s = steering_vector(params.signal_deg, n, params.d_over_lambda)
    s = sigma_s * (rng.normal(size=l) + 1j * rng.normal(size=l)) / np.sqrt(2.0)
    X = a_s[:, None] * s[None, :] + noise

    if params.interferer_enabled:
        sigma_i = 10 ** (params.inr_db / 20.0)
        a_i = steering_vector(params.interferer_deg, n, params.d_over_lambda)
        i = sigma_i * (rng.normal(size=l) + 1j * rng.normal(size=l)) / np.sqrt(2.0)
        X = X + a_i[:, None] * i[None, :]

    R = (X @ X.conj().T) / l
    return R, X


def apply_diagonal_loading(R: np.ndarray, loading_db: float) -> np.ndarray:
    if not np.isfinite(loading_db):
        return R
    n = R.shape[0]
    level = (np.trace(R).real / n) * (10 ** (loading_db / 10.0))
    return R + level * np.eye(n, dtype=complex)


def mvdr_weights(R: np.ndarray, look_deg: float, n: int, d_over_lambda: float) -> np.ndarray:
    """Capon / MVDR beamformer for look direction."""
    a = steering_vector(look_deg, n, d_over_lambda)
    # Hermitian solve
    try:
        inv_a = np.linalg.solve(R, a)
    except np.linalg.LinAlgError:
        inv_a = np.linalg.lstsq(R, a, rcond=None)[0]
    denom = np.vdot(a, inv_a)
    return inv_a / denom


def beamformer_weights(params: BeamformerParams, R: np.ndarray | None = None) -> np.ndarray:
    n = params.n_elements
    d = params.d_over_lambda
    if params.method == BeamformerMethod.CONVENTIONAL:
        return conventional_weights(params.look_deg, n, d)
    if params.method == BeamformerMethod.NULL_STEER:
        return null_steer_weights(params.look_deg, params.null_deg, n, d)
    if params.method == BeamformerMethod.MVDR:
        if R is None:
            R, _ = sample_covariance(params)
        R = apply_diagonal_loading(R, params.diagonal_loading_db)
        return mvdr_weights(R, params.look_deg, n, d)
    raise ValueError(f"unknown method: {params.method}")


def beampattern_db(
    weights: np.ndarray,
    theta_deg: np.ndarray,
    d_over_lambda: float,
    *,
    normalize_peak: bool = True,
) -> np.ndarray:
    """Power pattern |w^H a(θ)|² in dB."""
    n = len(weights)
    A = steering_matrix(theta_deg, n, d_over_lambda)
    resp = weights.conj() @ A
    power = np.abs(resp) ** 2
    if normalize_peak:
        peak = np.max(power)
        if peak > 0:
            power = power / peak
    return 10.0 * np.log10(power + 1e-30)


def capon_spectrum_db(
    R: np.ndarray,
    theta_deg: np.ndarray,
    d_over_lambda: float,
    *,
    normalize_peak: bool = True,
) -> np.ndarray:
    """MVDR spatial spectrum P(θ) = 1 / (a^H R^{-1} a)."""
    n = R.shape[0]
    A = steering_matrix(theta_deg, n, d_over_lambda)
    try:
        inv_A = np.linalg.solve(R, A)
    except np.linalg.LinAlgError:
        inv_A = np.linalg.lstsq(R, A, rcond=None)[0]
    denom = np.sum(np.conj(A) * inv_A, axis=0).real
    power = 1.0 / np.maximum(denom, 1e-30)
    if normalize_peak:
        power = power / np.max(power)
    return 10.0 * np.log10(power + 1e-30)


def output_sinr_db(params: BeamformerParams, weights: np.ndarray) -> float:
    """Analytical SINR for the single-interferer + white-noise model."""
    n = params.n_elements
    d = params.d_over_lambda
    a_s = steering_vector(params.signal_deg, n, d)
    ps = 10 ** (params.snr_db / 10.0)
    pn = 1.0
    R_n = pn * np.eye(n, dtype=complex)
    if params.interferer_enabled:
        pi = 10 ** (params.inr_db / 10.0)
        a_i = steering_vector(params.interferer_deg, n, d)
        R_n = R_n + pi * np.outer(a_i, a_i.conj())
    num = ps * abs(np.vdot(weights, a_s)) ** 2
    den = np.real(np.vdot(weights, R_n @ weights))
    return float(10.0 * np.log10(num / max(den, 1e-30)))


def eigenvalues_db(R: np.ndarray) -> np.ndarray:
    ev = np.sort(np.linalg.eigvalsh(R).real)[::-1]
    return 10.0 * np.log10(np.maximum(ev, 1e-30))
