"""Magnetometer / heading teaching topic."""

from teaching_sims.topics.magnetometer.physics import MagParams, process
from teaching_sims.topics.magnetometer.scenarios import SCENARIOS, get_scenario, list_scenarios

__all__ = [
    "MagParams",
    "process",
    "SCENARIOS",
    "get_scenario",
    "list_scenarios",
]
