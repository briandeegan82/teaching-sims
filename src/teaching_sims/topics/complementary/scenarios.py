"""Scripted lecture scenarios for complementary-filter fusion."""

from __future__ import annotations

from dataclasses import dataclass

from teaching_sims.topics.complementary.physics import ComplementaryParams, PitchMotion


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: ComplementaryParams
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "balanced_sine": Scenario(
        id="balanced_sine",
        title="Balanced sine pitch",
        teaching_point="α≈0.98: gyro tracks fast motion; accel quietly removes bias drift.",
        params=ComplementaryParams(alpha=0.98, gyro_bias_dps=0.8, surge_mps2=0.0),
    ),
    "trust_gyro": Scenario(
        id="trust_gyro",
        title="Trust the gyro",
        teaching_point="α→1 ignores accel: fast and smooth, but bias makes angle walk away.",
        params=ComplementaryParams(alpha=0.999, gyro_bias_dps=1.2),
    ),
    "trust_accel": Scenario(
        id="trust_accel",
        title="Trust the accelerometer",
        teaching_point="α→0 follows accel tilt: no gyro drift, but noisy and laggy on fast motion.",
        params=ComplementaryParams(alpha=0.5, gyro_bias_dps=1.0, accel_noise_mps2=0.4),
    ),
    "surge_spoofs_accel": Scenario(
        id="surge_spoofs_accel",
        title="Surge spoofs accel",
        teaching_point="Forward acceleration looks like pitch to the accelerometer path.",
        params=ComplementaryParams(
            motion=PitchMotion.SINE,
            amp_deg=10.0,
            alpha=0.9,
            surge_mps2=2.0,
            gyro_bias_dps=0.2,
        ),
        notes="Raise α to trust gyro more during the surge.",
    ),
    "step_pitch": Scenario(
        id="step_pitch",
        title="Step pitch",
        teaching_point="A step stresses the filter: watch overshoot vs lag as you change α.",
        params=ComplementaryParams(motion=PitchMotion.STEP, amp_deg=30.0, alpha=0.97),
    ),
    "quiet_sensors": Scenario(
        id="quiet_sensors",
        title="Quiet sensors",
        teaching_point="With tiny noise/bias, all three estimators look similar — then turn errors back on.",
        params=ComplementaryParams(
            gyro_bias_dps=0.0,
            gyro_noise_dps=0.02,
            accel_noise_mps2=0.02,
            alpha=0.98,
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
