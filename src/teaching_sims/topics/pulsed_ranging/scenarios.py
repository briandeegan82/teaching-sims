"""Scripted lecture scenarios for pulsed radar ranging."""

from __future__ import annotations

from dataclasses import dataclass

from teaching_sims.topics.pulsed_ranging.physics import (
    PulseRadarParams,
    Target,
    WaveformType,
)


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: PulseRadarParams
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "single_echo": Scenario(
        id="single_echo",
        title="Single echo delay",
        teaching_point="Echo delay τ = 2R/c maps directly to target range.",
        params=PulseRadarParams(
            waveform=WaveformType.RECT,
            pulse_width_s=1.0e-6,
            matched_filter=True,
            targets=(Target(2000.0, snr_db=30.0),),
        ),
        notes="Read the peak on the range axis; compare to the true 2 km marker.",
    ),
    "unresolved_pair": Scenario(
        id="unresolved_pair",
        title="Unresolved targets (coarse pulse)",
        teaching_point="If ΔR < c Tp / 2, two echoes merge into one blob.",
        params=PulseRadarParams(
            waveform=WaveformType.RECT,
            pulse_width_s=2.0e-6,
            matched_filter=True,
            targets=(
                Target(2000.0, snr_db=28.0),
                Target(2150.0, snr_db=28.0),
            ),
        ),
        notes="Resolution ≈ 300 m here — targets are only 150 m apart.",
    ),
    "resolved_pair": Scenario(
        id="resolved_pair",
        title="Resolved by shorter pulse",
        teaching_point="Shorter Tp improves range resolution for a simple pulse.",
        params=PulseRadarParams(
            waveform=WaveformType.RECT,
            pulse_width_s=0.4e-6,
            sample_rate_hz=50e6,
            matched_filter=True,
            targets=(
                Target(2000.0, snr_db=26.0),
                Target(2150.0, snr_db=26.0),
            ),
        ),
        notes="Same geometry as the unresolved case; now ΔR ≈ 60 m.",
    ),
    "lfm_compression": Scenario(
        id="lfm_compression",
        title="LFM pulse compression",
        teaching_point="A long LFM pulse can still resolve finely after matched filtering (≈ c/2B).",
        params=PulseRadarParams(
            waveform=WaveformType.LFM,
            pulse_width_s=20e-6,
            bandwidth_hz=10e6,
            sample_rate_hz=40e6,
            pri_s=200e-6,
            matched_filter=True,
            targets=(
                Target(5000.0, snr_db=25.0),
                Target(5120.0, snr_db=25.0),
            ),
        ),
        notes="Toggle matched filter off to see the long smear; on to see compression.",
    ),
    "range_ambiguity": Scenario(
        id="range_ambiguity",
        title="Range ambiguity (PRI fold)",
        teaching_point="Targets beyond R_unamb = c·PRI/2 appear folded into the PRI window.",
        params=PulseRadarParams(
            waveform=WaveformType.RECT,
            pulse_width_s=0.5e-6,
            pri_s=50e-6,  # R_unamb ≈ 7.5 km
            matched_filter=True,
            targets=(Target(10000.0, snr_db=28.0),),  # true 10 km → folds
        ),
        notes="True range 10 km; unambiguous window ≈ 7.5 km — peak is a PRI alias.",
    ),
    "matched_filter_gain": Scenario(
        id="matched_filter_gain",
        title="Matched-filter SNR gain",
        teaching_point="The matched filter maximises SNR; raw video looks noisier.",
        params=PulseRadarParams(
            waveform=WaveformType.LFM,
            pulse_width_s=10e-6,
            bandwidth_hz=8e6,
            matched_filter=True,
            targets=(Target(3000.0, snr_db=12.0),),
            noise_enabled=True,
        ),
        notes="Toggle MF off/on and watch the peak emerge from noise.",
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
