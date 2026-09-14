"""Attitude / rotations teaching topic."""

from teaching_sims.topics.attitude.physics import AttitudeParams, process
from teaching_sims.topics.attitude.scenarios import SCENARIOS, get_scenario, list_scenarios

__all__ = [
    "AttitudeParams",
    "process",
    "SCENARIOS",
    "get_scenario",
    "list_scenarios",
]
