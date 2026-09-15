"""Lecture scenarios for target returns / RCS demo."""

from __future__ import annotations

from dataclasses import dataclass

from teaching_sims.topics.target_returns.physics import TargetReturnsParams, TargetShape


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: TargetReturnsParams
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "sphere_size_scaling": Scenario(
        id="sphere_size_scaling",
        title="Sphere size scaling",
        teaching_point="In the optical regime, sphere RCS grows as pi a^2 — larger balls return more.",
        params=TargetReturnsParams(
            shape=TargetShape.SPHERE,
            size_m=1.5,
            range_m=5000.0,
            noise_enabled=True,
        ),
        notes="Compare the RCS bar for sphere vs other shapes at the same characteristic size.",
    ),
    "plate_vs_sphere": Scenario(
        id="plate_vs_sphere",
        title="Plate vs sphere (broadside)",
        teaching_point="A flat plate broadside has huge RCS (~A^2/lambda^2) vs a same-size sphere (~a^2).",
        params=TargetReturnsParams(
            shape=TargetShape.FLAT_PLATE,
            size_m=1.0,
            size2_m=1.0,
            aspect_deg=0.0,
            range_m=5000.0,
            frequency_hz=10e9,
        ),
        notes="Watch peak amplitude jump relative to the sphere bar on the comparison plot.",
    ),
    "corner_boost": Scenario(
        id="corner_boost",
        title="Corner reflector boost",
        teaching_point="A trihedral corner returns strongly over a wide aspect — classic calibration / buoy target.",
        params=TargetReturnsParams(
            shape=TargetShape.CORNER,
            size_m=0.5,
            range_m=8000.0,
            frequency_hz=10e9,
        ),
        notes="Small edge length still outshines a much larger sphere at the same range.",
    ),
    "aspect_null_plate": Scenario(
        id="aspect_null_plate",
        title="Plate aspect collapse",
        teaching_point="Rotate a plate off broadside and RCS collapses — shape + aspect matter as much as size.",
        params=TargetReturnsParams(
            shape=TargetShape.FLAT_PLATE,
            size_m=1.0,
            size2_m=1.0,
            aspect_deg=70.0,
            range_m=5000.0,
        ),
        notes="Same plate as the broadside case; only aspect changed.",
    ),
    "range_law_r4": Scenario(
        id="range_law_r4",
        title="Range law (1/R^4)",
        teaching_point="Same target twice as far loses ~12 dB (power ~ 1/R^4).",
        params=TargetReturnsParams(
            shape=TargetShape.SPHERE,
            size_m=1.0,
            range_m=10_000.0,
            range_ref_m=5000.0,
            snr_ref_db=25.0,
        ),
        notes="Anchor is 1 m^2 at 5 km; this sphere at 10 km should sit ~12 dB lower.",
    ),
    "extended_smear": Scenario(
        id="extended_smear",
        title="Extended target smear",
        teaching_point="A long body along the line of sight stretches the echo; peak falls as energy spreads in range.",
        params=TargetReturnsParams(
            shape=TargetShape.EXTENDED,
            size_m=40.0,
            size2_m=3.0,
            aspect_deg=90.0,
            range_m=6000.0,
            pulse_width_s=0.25e-6,
            sample_rate_hz=50e6,
        ),
        notes="Compare to a corner or sphere of similar RCS — the blob is wider and the peak lower.",
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
