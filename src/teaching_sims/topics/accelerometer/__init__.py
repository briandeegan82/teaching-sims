"""Accelerometer teaching topic."""

from teaching_sims.topics.accelerometer.physics import AccelParams, process, tilt_from_accel
from teaching_sims.topics.accelerometer.scenarios import SCENARIOS, get_scenario, list_scenarios

__all__ = [
    "AccelParams",
    "process",
    "tilt_from_accel",
    "SCENARIOS",
    "get_scenario",
    "list_scenarios",
]
