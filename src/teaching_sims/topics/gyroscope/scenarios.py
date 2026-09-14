"""Scripted lecture scenarios for the gyroscope demo."""

from __future__ import annotations

from dataclasses import dataclass

from teaching_sims.topics.gyroscope.physics import GyroParams, MotionProfile


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: GyroParams
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "clean_step_turn": Scenario(
        id="clean_step_turn",
        title="Clean step turn",
        teaching_point="Integrating rate recovers angle when bias and noise are tiny.",
        params=GyroParams(
            profile=MotionProfile.STEP_TURN,
            bias_dps=0.0,
            arw_deg_per_sqrt_s=0.0,
            rate_dps=40.0,
        ),
    ),
    "bias_ramp": Scenario(
        id="bias_ramp",
        title="Bias -> angle ramp",
        teaching_point="A constant rate bias integrates to a linear angle error (unbounded drift).",
        params=GyroParams(
            profile=MotionProfile.STEP_TURN,
            bias_dps=1.5,
            arw_deg_per_sqrt_s=0.0,
            compensate_bias=False,
        ),
        notes="Enable bias compensation to reset the ramp. In 3D, truth stops; the gyro cube keeps turning.",
    ),
    "bias_compensated": Scenario(
        id="bias_compensated",
        title="Bias compensated",
        teaching_point="Subtracting a calibrated bias restores the turn - until the bias changes.",
        params=GyroParams(
            profile=MotionProfile.STEP_TURN,
            bias_dps=1.5,
            arw_deg_per_sqrt_s=0.0,
            compensate_bias=True,
        ),
    ),
    "angle_random_walk": Scenario(
        id="angle_random_walk",
        title="Angle random walk",
        teaching_point="White rate noise integrates to a random-walk angle error (grows like sqrt(t)).",
        params=GyroParams(
            profile=MotionProfile.CONSTANT,
            rate_dps=0.0,
            bias_dps=0.0,
            arw_deg_per_sqrt_s=0.4,
            duration_s=20.0,
        ),
    ),
    "sine_tracking": Scenario(
        id="sine_tracking",
        title="Sine rate tracking",
        teaching_point="Gyro follows oscillatory motion; bias still adds a slow ramp underneath.",
        params=GyroParams(
            profile=MotionProfile.SINE,
            rate_dps=45.0,
            sine_hz=0.4,
            bias_dps=0.6,
            arw_deg_per_sqrt_s=0.05,
        ),
    ),
    "noisy_turn": Scenario(
        id="noisy_turn",
        title="Noisy turn",
        teaching_point="Bias and ARW together: ramp plus wandering residual after the motion stops.",
        params=GyroParams(
            profile=MotionProfile.STEP_TURN,
            bias_dps=0.8,
            arw_deg_per_sqrt_s=0.15,
        ),
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
