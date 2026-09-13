"""Pulse-Doppler / MTI teaching topic."""

from teaching_sims.topics.pulse_doppler.physics import MovingTarget, PulseDopplerParams
from teaching_sims.topics.pulse_doppler.scenarios import SCENARIOS, get_scenario, list_scenarios

__all__ = [
    "MovingTarget",
    "PulseDopplerParams",
    "SCENARIOS",
    "get_scenario",
    "list_scenarios",
]
