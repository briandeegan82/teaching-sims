"""Scripted lecture scenarios for attitude / rotations."""

from __future__ import annotations

from dataclasses import dataclass

from teaching_sims.topics.attitude.physics import AttitudeParams


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: AttitudeParams
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "level_heading": Scenario(
        id="level_heading",
        title="Level heading",
        teaching_point="Yaw rotates body X/Y in the horizontal plane; Z stays down.",
        params=AttitudeParams(yaw_deg=45.0, pitch_deg=0.0, roll_deg=0.0),
    ),
    "pitch_nose_up": Scenario(
        id="pitch_nose_up",
        title="Nose-up pitch",
        teaching_point="Pitch tips body X out of the horizontal; DCM columns are body axes in NED.",
        params=AttitudeParams(yaw_deg=0.0, pitch_deg=30.0, roll_deg=0.0),
    ),
    "banked_turn_pose": Scenario(
        id="banked_turn_pose",
        title="Banked pose",
        teaching_point="Combined roll and yaw — typical aircraft attitude; quaternion stays well-behaved.",
        params=AttitudeParams(yaw_deg=25.0, pitch_deg=5.0, roll_deg=35.0),
    ),
    "gimbal_lock_scan": Scenario(
        id="gimbal_lock_scan",
        title="Gimbal-lock scan",
        teaching_point="Near pitch ±90°, Euler yaw/roll become coupled — extraction is singular.",
        params=AttitudeParams(
            yaw_deg=30.0,
            pitch_deg=0.0,
            roll_deg=20.0,
            animate_pitch=True,
            pitch_scan_deg=89.0,
        ),
        notes="Watch extracted yaw/roll jump as pitch crosses ±90°.",
    ),
    "quat_roundtrip": Scenario(
        id="quat_roundtrip",
        title="Quaternion round-trip",
        teaching_point="Euler → quaternion → DCM → Euler recovers the same attitude away from singularities.",
        params=AttitudeParams(yaw_deg=-40.0, pitch_deg=18.0, roll_deg=-12.0),
    ),
    "steep_pitch": Scenario(
        id="steep_pitch",
        title="Steep pitch",
        teaching_point="Large but non-singular pitch: still OK for Euler, but getting close to trouble.",
        params=AttitudeParams(yaw_deg=10.0, pitch_deg=70.0, roll_deg=5.0),
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
