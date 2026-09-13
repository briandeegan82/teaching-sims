"""Phased-array teaching topic."""

from teaching_sims.topics.phased_array.features import PatternFeatures, pattern_features
from teaching_sims.topics.phased_array.physics import ArrayParams, SteeringMode
from teaching_sims.topics.phased_array.scenarios import SCENARIOS, get_scenario, list_scenarios

__all__ = [
    "ArrayParams",
    "SteeringMode",
    "PatternFeatures",
    "pattern_features",
    "SCENARIOS",
    "get_scenario",
    "list_scenarios",
]
