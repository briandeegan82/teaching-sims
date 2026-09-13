"""CFAR teaching topic."""

from teaching_sims.topics.cfar.physics import CFARMethod, CFARParams, CFARTarget
from teaching_sims.topics.cfar.scenarios import SCENARIOS, get_scenario, list_scenarios

__all__ = [
    "CFARMethod",
    "CFARParams",
    "CFARTarget",
    "SCENARIOS",
    "get_scenario",
    "list_scenarios",
]
