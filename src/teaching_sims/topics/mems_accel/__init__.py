"""MEMS comb-drive accelerometer teaching topic."""

from teaching_sims.topics.mems_accel.physics import Excitation, MEMSAccelParams, process
from teaching_sims.topics.mems_accel.scenarios import SCENARIOS, get_scenario, list_scenarios

__all__ = [
    "Excitation",
    "MEMSAccelParams",
    "process",
    "SCENARIOS",
    "get_scenario",
    "list_scenarios",
]
