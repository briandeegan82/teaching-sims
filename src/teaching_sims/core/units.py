"""Physical constants and unit helpers."""

from __future__ import annotations

C_LIGHT = 299_792_458.0  # m/s


def wavelength(frequency_hz: float) -> float:
    """Return free-space wavelength in metres."""
    if frequency_hz <= 0:
        raise ValueError("frequency_hz must be positive")
    return C_LIGHT / frequency_hz
