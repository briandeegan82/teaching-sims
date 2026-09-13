"""FMCW teaching topic."""

from teaching_sims.topics.fmcw.physics import FMCWParams, FMCWTarget, FMCWWaveform
from teaching_sims.topics.fmcw.scenarios import SCENARIOS, get_scenario, list_scenarios

__all__ = [
    "FMCWParams",
    "FMCWTarget",
    "FMCWWaveform",
    "SCENARIOS",
    "get_scenario",
    "list_scenarios",
]
