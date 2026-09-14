"""Scripted lecture scenarios for strapdown INS."""

from __future__ import annotations

from dataclasses import dataclass

from teaching_sims.topics.ins.physics import INSParams, PathProfile


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: INSParams
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "perfect_circle": Scenario(
        id="perfect_circle",
        title="Perfect sensors (circle)",
        teaching_point="With tiny errors and perfect attitude, the dead-reckoned path hugs truth.",
        params=INSParams(
            profile=PathProfile.CIRCLE,
            gyro_bias_dps=0.0,
            accel_bias_x_mps2=0.0,
            accel_bias_y_mps2=0.0,
            accel_noise_mps2=0.001,
            gyro_noise_dps=0.001,
            perfect_attitude=True,
            duration_s=50.0,
        ),
    ),
    "accel_bias_straight": Scenario(
        id="accel_bias_straight",
        title="Accel bias on straight path",
        teaching_point="Constant accel bias → velocity ramp → quadratic position growth.",
        params=INSParams(
            profile=PathProfile.STRAIGHT,
            perfect_attitude=True,
            gyro_bias_dps=0.0,
            accel_bias_x_mps2=0.08,
            accel_noise_mps2=0.0,
            gyro_noise_dps=0.0,
            duration_s=30.0,
        ),
    ),
    "gyro_bias_circle": Scenario(
        id="gyro_bias_circle",
        title="Gyro bias on a circle",
        teaching_point="Heading drift points the velocity vector wrong — path spirals away.",
        params=INSParams(
            profile=PathProfile.CIRCLE,
            perfect_attitude=False,
            gyro_bias_dps=0.4,
            accel_bias_x_mps2=0.0,
            accel_bias_y_mps2=0.0,
            duration_s=50.0,
        ),
    ),
    "both_errors": Scenario(
        id="both_errors",
        title="Gyro + accel errors",
        teaching_point="Real IMUs combine attitude drift and specific-force bias — errors compound.",
        params=INSParams(
            profile=PathProfile.CIRCLE,
            gyro_bias_dps=0.25,
            accel_bias_x_mps2=0.04,
            duration_s=45.0,
        ),
    ),
    "stop_and_go": Scenario(
        id="stop_and_go",
        title="Stop-and-go",
        teaching_point="During stops, accel bias still integrates — parked vehicles still 'drift' in unaided INS.",
        params=INSParams(
            profile=PathProfile.STOP_AND_GO,
            perfect_attitude=True,
            accel_bias_x_mps2=0.06,
            gyro_bias_dps=0.0,
            duration_s=40.0,
        ),
    ),
    "quiet_ins": Scenario(
        id="quiet_ins",
        title="Quiet tactical IMU",
        teaching_point="Lower biases shrink short-term error — but unaided INS still diverges eventually.",
        params=INSParams(
            profile=PathProfile.CIRCLE,
            gyro_bias_dps=0.05,
            accel_bias_x_mps2=0.01,
            accel_noise_mps2=0.01,
            gyro_noise_dps=0.02,
            duration_s=60.0,
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
