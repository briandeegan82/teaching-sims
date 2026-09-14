"""Complementary-filter teaching topic."""

from teaching_sims.topics.complementary.physics import ComplementaryParams, PitchMotion, process
from teaching_sims.topics.complementary.scenarios import SCENARIOS, get_scenario, list_scenarios

__all__ = [
    "ComplementaryParams",
    "PitchMotion",
    "process",
    "SCENARIOS",
    "get_scenario",
    "list_scenarios",
]
