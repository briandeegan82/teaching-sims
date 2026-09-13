"""Pulsed radar ranging teaching topic."""

from teaching_sims.topics.pulsed_ranging.physics import PulseRadarParams, Target, WaveformType
from teaching_sims.topics.pulsed_ranging.scenarios import SCENARIOS, get_scenario, list_scenarios

__all__ = [
    "PulseRadarParams",
    "Target",
    "WaveformType",
    "SCENARIOS",
    "get_scenario",
    "list_scenarios",
]
