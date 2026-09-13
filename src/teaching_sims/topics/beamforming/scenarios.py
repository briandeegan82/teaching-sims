"""Scripted lecture scenarios for digital beamforming."""

from __future__ import annotations

from dataclasses import dataclass

from teaching_sims.topics.beamforming.physics import BeamformerMethod, BeamformerParams


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: BeamformerParams
    compare_methods: bool = False
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "conventional_look": Scenario(
        id="conventional_look",
        title="Conventional delay-and-sum",
        teaching_point="Point the look direction; the pattern is the array factor for those weights.",
        params=BeamformerParams(
            method=BeamformerMethod.CONVENTIONAL,
            look_deg=0.0,
            signal_deg=0.0,
            interferer_enabled=False,
        ),
        notes="Relate this to the phased-array AF lecture.",
    ),
    "interferer_sidelobe": Scenario(
        id="interferer_sidelobe",
        title="Strong interferer in a sidelobe",
        teaching_point="Conventional BF still passes interferers that land in sidelobes.",
        params=BeamformerParams(
            method=BeamformerMethod.CONVENTIONAL,
            look_deg=0.0,
            signal_deg=0.0,
            interferer_deg=35.0,
            interferer_enabled=True,
            snr_db=10.0,
            inr_db=25.0,
        ),
        notes="Watch SINR drop even though the look direction is correct.",
    ),
    "mvdr_adaptive_null": Scenario(
        id="mvdr_adaptive_null",
        title="MVDR adaptive null",
        teaching_point="MVDR keeps unity gain on the look direction and nulls interferers in R.",
        params=BeamformerParams(
            method=BeamformerMethod.MVDR,
            look_deg=0.0,
            signal_deg=0.0,
            interferer_deg=35.0,
            interferer_enabled=True,
            snr_db=10.0,
            inr_db=25.0,
        ),
        compare_methods=True,
        notes="Enable compare to overlay conventional vs MVDR.",
    ),
    "null_steer_fixed": Scenario(
        id="null_steer_fixed",
        title="Deterministic null steering",
        teaching_point="A fixed projection null works when the interferer angle is known.",
        params=BeamformerParams(
            method=BeamformerMethod.NULL_STEER,
            look_deg=0.0,
            signal_deg=0.0,
            null_deg=35.0,
            interferer_deg=35.0,
            interferer_enabled=True,
            inr_db=25.0,
        ),
        notes="Compare with MVDR, which learns the null from data.",
    ),
    "two_source_resolution": Scenario(
        id="two_source_resolution",
        title="Resolving two close sources",
        teaching_point="Capon spectrum peaks sharper than the conventional beam pattern.",
        params=BeamformerParams(
            method=BeamformerMethod.MVDR,
            n_elements=12,
            look_deg=-8.0,
            signal_deg=-8.0,
            interferer_deg=8.0,
            interferer_enabled=True,
            snr_db=15.0,
            inr_db=15.0,
            n_snapshots=400,
        ),
        notes="Use the Capon spectrum panel; sweep separation with the interferer angle.",
    ),
    "diagonal_loading": Scenario(
        id="diagonal_loading",
        title="Diagonal loading",
        teaching_point="Loading stabilises MVDR when snapshots are few or R is ill-conditioned.",
        params=BeamformerParams(
            method=BeamformerMethod.MVDR,
            look_deg=0.0,
            signal_deg=0.0,
            interferer_deg=30.0,
            n_snapshots=20,
            snr_db=10.0,
            inr_db=20.0,
            diagonal_loading_db=-10.0,
        ),
        notes="Toggle loading from −∞ (off) toward 0 dB and watch the null soften.",
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
