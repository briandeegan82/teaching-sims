"""Shared IMU / navigation constants and small helpers."""

from __future__ import annotations

import numpy as np

G0 = 9.80665  # standard gravity, m/s^2
DEG2RAD = np.pi / 180.0
RAD2DEG = 180.0 / np.pi


def wrap_pi(angle_rad: float | np.ndarray) -> float | np.ndarray:
    """Wrap angle(s) to (-π, π]."""
    return (angle_rad + np.pi) % (2.0 * np.pi) - np.pi


def wrap_180(angle_deg: float | np.ndarray) -> float | np.ndarray:
    """Wrap angle(s) to (-180, 180]."""
    return (angle_deg + 180.0) % 360.0 - 180.0


def gravity_ned(g: float = G0) -> np.ndarray:
    """Local-level gravity vector in NED (down positive for g magnitude)."""
    return np.array([0.0, 0.0, g], dtype=float)
