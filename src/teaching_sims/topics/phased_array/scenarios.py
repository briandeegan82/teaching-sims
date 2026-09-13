"""Scripted lecture scenarios for the phased-array demo."""

from __future__ import annotations

from dataclasses import dataclass, replace

from teaching_sims.topics.phased_array.physics import ArrayParams, SteeringMode


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: ArrayParams
    animate_steer: bool = False
    animate_n: bool = False
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "interference_basics": Scenario(
        id="interference_basics",
        title="Two-element interference",
        teaching_point="Two sources make fringes; an array is controlled interference.",
        params=ArrayParams(n_elements=2, d_over_lambda=0.5, steer_deg=0.0),
        notes="Watch the pattern nulls. Increase N next to form a main beam.",
    ),
    "steer_main_beam": Scenario(
        id="steer_main_beam",
        title="Electronic beam steering",
        teaching_point="A progressive phase shift steers the main lobe without moving the array.",
        params=ArrayParams(n_elements=8, d_over_lambda=0.5, steer_deg=-20.0),
        animate_steer=True,
        notes="Slider / auto-sweep the steer angle; peak tracks φ = −kd sinθ₀.",
    ),
    "grating_lobes": Scenario(
        id="grating_lobes",
        title="Grating lobes (d > λ/2)",
        teaching_point="Spacing above λ/2 aliases the spatial frequency → extra main beams.",
        params=ArrayParams(n_elements=8, d_over_lambda=0.9, steer_deg=25.0),
        notes="Compare with d/λ=0.5 at the same steer angle.",
    ),
    "beamwidth_vs_n": Scenario(
        id="beamwidth_vs_n",
        title="Beamwidth vs aperture",
        teaching_point="Larger N (larger aperture) narrows the main beam ≈ 0.886 λ/(N d).",
        params=ArrayParams(n_elements=4, d_over_lambda=0.5, steer_deg=0.0),
        animate_n=True,
        notes="Auto-grows N so students see HPBW shrink.",
    ),
    "phase_vs_ttd": Scenario(
        id="phase_vs_ttd",
        title="Phase shift vs true time delay",
        teaching_point="Phase steering is designed at one f₀; off that frequency the beam squints. TTD does not.",
        params=ArrayParams(
            n_elements=12,
            d_over_lambda=0.5,
            steer_deg=40.0,
            frequency_hz=12e9,
            design_frequency_hz=10e9,
            steering_mode=SteeringMode.PHASE_SHIFT,
        ),
        notes="Toggle steering mode or sweep frequency to show squint vs TTD lock.",
    ),
    "quantized_phase": Scenario(
        id="quantized_phase",
        title="Phase quantization",
        teaching_point="Finite phase bits raise quantization lobes / pointing error.",
        params=ArrayParams(
            n_elements=16,
            d_over_lambda=0.5,
            steer_deg=30.0,
            phase_bits=2,
        ),
        notes="Raise bits from 2→3→4 and watch spurious lobes drop.",
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


def with_overrides(scenario: Scenario, **kwargs) -> ArrayParams:
    return replace(scenario.params, **kwargs)
