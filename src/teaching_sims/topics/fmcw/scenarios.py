"""Scripted lecture scenarios for FMCW radar."""

from __future__ import annotations

from dataclasses import dataclass

from teaching_sims.topics.fmcw.physics import FMCWParams, FMCWTarget, FMCWWaveform


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: FMCWParams
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "stationary_tone": Scenario(
        id="stationary_tone",
        title="Stationary target beat tone",
        teaching_point="A fixed target makes one IF tone; range follows fb = 2 S R / c.",
        params=FMCWParams(
            waveform=FMCWWaveform.SAWTOOTH,
            targets=(FMCWTarget(50.0, 0.0, snr_db=28.0),),
        ),
        notes="Read the spectrum peak and convert fb -> R.",
    ),
    "two_range_cells": Scenario(
        id="two_range_cells",
        title="Range resolution (two targets)",
        teaching_point="Targets closer than c/(2B) merge in the range FFT.",
        params=FMCWParams(
            bandwidth_hz=100e6,  # ΔR ~ 1.5 m
            targets=(
                FMCWTarget(40.0, 0.0, snr_db=26.0),
                FMCWTarget(41.0, 0.0, snr_db=26.0),
            ),
        ),
        notes="Raise bandwidth until the two peaks split (~0.75 m needed).",
    ),
    "sawtooth_coupling": Scenario(
        id="sawtooth_coupling",
        title="Sawtooth range-Doppler coupling",
        teaching_point="On a sawtooth, Doppler shifts the beat so naive R = c fb/(2S) is biased.",
        params=FMCWParams(
            waveform=FMCWWaveform.SAWTOOTH,
            targets=(FMCWTarget(40.0, 30.0, snr_db=26.0),),
            n_chirps=64,
        ),
        notes="Compare true range vs range-from-beat in the status panel.",
    ),
    "triangle_decouple": Scenario(
        id="triangle_decouple",
        title="Triangle up/down decoupling",
        teaching_point="Up and down beats recover both R and v: fb+/- = 2SR/c +/- 2v/λ.",
        params=FMCWParams(
            waveform=FMCWWaveform.TRIANGLE,
            targets=(FMCWTarget(40.0, 30.0, snr_db=26.0),),
            n_chirps=64,
        ),
        notes="Status shows fb_up, fb_down and the solved (R, v).",
    ),
    "range_doppler_map": Scenario(
        id="range_doppler_map",
        title="FMCW range-Doppler map",
        teaching_point="A CPI of chirps + 2D FFT yields the automotive-style RD map.",
        params=FMCWParams(
            waveform=FMCWWaveform.SAWTOOTH,
            n_chirps=64,
            targets=(
                FMCWTarget(30.0, 12.0, snr_db=24.0),
                FMCWTarget(70.0, -8.0, snr_db=22.0),
            ),
        ),
        notes="Two cells at different range and velocity.",
    ),
    "max_range_nyquist": Scenario(
        id="max_range_nyquist",
        title="IF Nyquist / max range",
        teaching_point="If 2SR/c exceeds fs/2, the beat aliases and range folds.",
        params=FMCWParams(
            bandwidth_hz=200e6,
            chirp_time_s=50e-6,
            sample_rate_hz=2e6,  # low IF sampling -> small R_max
            targets=(FMCWTarget(120.0, 0.0, snr_db=28.0),),
            n_chirps=32,
        ),
        notes="Check R_unamb in status; peak appears folded if R > R_max.",
    ),
}


def list_scenarios() -> list[Scenario]:
    return list(SCENARIOS.values())


def get_scenario(scenario_id: str) -> Scenario:
    try:
        return SCENARIOS[scenario_id]
    except KeyError as exc:
        known = ", ".join(SCENARIOS)
        raise KeyError(f"unknown scenario {scenario_id!r}; choose from: {known}") from exc
