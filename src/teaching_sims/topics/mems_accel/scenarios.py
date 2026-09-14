"""Lecture scenarios for the MEMS comb-drive accelerometer demo."""

from __future__ import annotations

from dataclasses import dataclass

from teaching_sims.topics.mems_accel.physics import Excitation, MEMSAccelParams


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: MEMSAccelParams
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "at_rest": Scenario(
        id="at_rest",
        title="At rest (ideal)",
        teaching_point="With no acceleration and no offsets, proof mass stays centered; C1=C2.",
        params=MEMSAccelParams(excitation=Excitation.REST, output_bias_mps2=0.0, mech_offset_um=0.0),
        notes="Watch equal finger gaps on both sides of the comb.",
    ),
    "constant_accel": Scenario(
        id="constant_accel",
        title="Constant acceleration",
        teaching_point="Steady accel shifts the mass until k x balances m a; output settles to a constant.",
        params=MEMSAccelParams(
            excitation=Excitation.CONSTANT,
            a_const_mps2=8.0,
            zeta=0.7,
            duration_s=0.2,
        ),
        notes="Mass displaces and stays; differential capacitance becomes nonzero.",
    ),
    "output_bias": Scenario(
        id="output_bias",
        title="Output bias at rest",
        teaching_point="Electronics bias reports nonzero accel even when the mass is centered.",
        params=MEMSAccelParams(
            excitation=Excitation.REST,
            output_bias_mps2=2.5,
            mech_offset_um=0.0,
        ),
        notes="Schematic gaps look symmetric, but a_meas is offset - classic IMU bias.",
    ),
    "mech_offset_bias": Scenario(
        id="mech_offset_bias",
        title="Mechanical offset looks like bias",
        teaching_point="A rest-position offset unbalances C1/C2; high omega0^2 turns a tiny x into a large a_meas bias.",
        params=MEMSAccelParams(
            excitation=Excitation.REST,
            mech_offset_um=0.25,
            output_bias_mps2=0.0,
        ),
        notes="Fingers off-center with a_ext=0. Compare to output bias: same symptom, mechanical cause.",
    ),
    "impulse_ring": Scenario(
        id="impulse_ring",
        title="Impulse then ring-down",
        teaching_point="A short accel impulse displaces the mass; underdamped suspension rings before settling.",
        params=MEMSAccelParams(
            excitation=Excitation.IMPULSE,
            impulse_amp_mps2=50.0,
            impulse_width_s=0.0015,
            impulse_time_s=0.04,
            zeta=0.12,
            duration_s=0.35,
        ),
        notes="Compare the impulse on a_ext to the decaying oscillation in x and a_meas.",
    ),
    "overdamped_impulse": Scenario(
        id="overdamped_impulse",
        title="Overdamped impulse",
        teaching_point="Higher damping removes ringing: the mass slides back without oscillating.",
        params=MEMSAccelParams(
            excitation=Excitation.IMPULSE,
            impulse_amp_mps2=50.0,
            impulse_width_s=0.0015,
            impulse_time_s=0.04,
            zeta=1.2,
            duration_s=0.35,
        ),
        notes="Same impulse energy as the ringing case; only zeta changed.",
    ),
}


def list_scenarios() -> list[Scenario]:
    return list(SCENARIOS.values())


def get_scenario(scenario_id: str) -> Scenario:
    try:
        return SCENARIOS[scenario_id]
    except KeyError as exc:
        known = ", ".join(SCENARIOS)
        raise KeyError(f"unknown scenario {scenario_id!r}; choose from: {known}") from exc
