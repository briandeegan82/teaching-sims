"""Scripted lecture scenarios for the accelerometer demo."""

from __future__ import annotations

from dataclasses import dataclass

from teaching_sims.topics.accelerometer.physics import AccelParams


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: AccelParams
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "level_plate": Scenario(
        id="level_plate",
        title="Level plate",
        teaching_point="At rest and level, specific force is ≈ −g along body Z.",
        params=AccelParams(roll_deg=0.0, pitch_deg=0.0, noise_mps2=0.01),
        notes="Read fx≈0, fy≈0, fz≈−9.81 m/s².",
    ),
    "static_tilt": Scenario(
        id="static_tilt",
        title="Static tilt",
        teaching_point="Tilt maps gravity into fx/fy; arctan recovers roll/pitch when static.",
        params=AccelParams(yaw_deg=25.0, roll_deg=20.0, pitch_deg=-12.0, noise_mps2=0.02),
        notes="Enable the 3D window — yaw rotates the cube but not the accel tilt estimate.",
    ),
    "bias_tilts_estimate": Scenario(
        id="bias_tilts_estimate",
        title="Bias looks like tilt",
        teaching_point="A constant accel bias is indistinguishable from a static attitude error.",
        params=AccelParams(roll_deg=0.0, pitch_deg=0.0, bias_x_mps2=0.5, noise_mps2=0.01),
        notes="Level truth, but pitch estimate is wrong.",
    ),
    "surge_contaminates": Scenario(
        id="surge_contaminates",
        title="Linear accel contamination",
        teaching_point="Accelerometers sense specific force: real linear accel spoofs tilt.",
        params=AccelParams(roll_deg=0.0, pitch_deg=0.0, ax_mps2=1.5, noise_mps2=0.02),
    ),
    "vibration_average": Scenario(
        id="vibration_average",
        title="Vibration vs averaging",
        teaching_point="High-frequency vibration jitters instantaneous tilt; a mean recovers the static pose.",
        params=AccelParams(
            roll_deg=8.0,
            pitch_deg=5.0,
            vibe_amp_mps2=2.0,
            vibe_hz=30.0,
            noise_mps2=0.05,
        ),
    ),
    "large_pitch": Scenario(
        id="large_pitch",
        title="Large pitch",
        teaching_point="Near vertical pitch, horizontal axes swap roles — tilt formulas get fragile.",
        params=AccelParams(roll_deg=5.0, pitch_deg=60.0, noise_mps2=0.02),
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
