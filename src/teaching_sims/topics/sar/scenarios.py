"""Scripted lecture scenarios for stripmap SAR."""

from __future__ import annotations

from dataclasses import dataclass

from teaching_sims.topics.sar.physics import SARParams, SARPointTarget


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: SARParams
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "single_point": Scenario(
        id="single_point",
        title="Single point target",
        teaching_point="Range compression then azimuth focus collapses a hyperbola into a point.",
        params=SARParams(
            n_pulses=256,
            targets=(SARPointTarget(0.0, 8000.0, rcs_db=0.0),),
            noise_enabled=True,
            noise_snr_db=28.0,
        ),
        notes="Compare unfocused streak vs focused bright cell.",
    ),
    "two_azimuth": Scenario(
        id="two_azimuth",
        title="Two targets in azimuth",
        teaching_point="Synthetic aperture resolves along-track spacing finer than the real antenna.",
        params=SARParams(
            n_pulses=256,
            targets=(
                SARPointTarget(-30.0, 8000.0, rcs_db=0.0),
                SARPointTarget(30.0, 8000.0, rcs_db=0.0),
            ),
            noise_snr_db=26.0,
        ),
        notes="Targets share range; azimuth focus separates them.",
    ),
    "two_range": Scenario(
        id="two_range",
        title="Two targets in range",
        teaching_point="Bandwidth sets slant-range resolution ΔR = c/(2B).",
        params=SARParams(
            bandwidth_hz=30e6,  # ΔR ≈ 5 m
            targets=(
                SARPointTarget(0.0, 8000.0, rcs_db=0.0),
                SARPointTarget(0.0, 8008.0, rcs_db=0.0),
            ),
            noise_snr_db=26.0,
        ),
        notes="Raise B until the two range cells split.",
    ),
    "aperture_resolution": Scenario(
        id="aperture_resolution",
        title="Aperture length vs Δx",
        teaching_point="Longer synthetic aperture (more pulses / slower v) sharpens azimuth.",
        params=SARParams(
            n_pulses=64,
            velocity_mps=150.0,
            targets=(
                SARPointTarget(-20.0, 8000.0, 0.0),
                SARPointTarget(20.0, 8000.0, 0.0),
            ),
            noise_snr_db=26.0,
        ),
        notes="Increase N pulses until the pair resolves cleanly.",
    ),
    "unfocused_vs_focused": Scenario(
        id="unfocused_vs_focused",
        title="Unfocused vs focused",
        teaching_point="Without azimuth matched filtering you only see range-compressed streaks.",
        params=SARParams(
            n_pulses=192,
            targets=(
                SARPointTarget(-50.0, 7900.0, 0.0),
                SARPointTarget(40.0, 8100.0, -2.0),
            ),
            noise_snr_db=24.0,
        ),
        notes="Toggle the unfocused panel against the focused image.",
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
