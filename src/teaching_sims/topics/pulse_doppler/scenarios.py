"""Scripted lecture scenarios for pulse-Doppler / MTI."""

from __future__ import annotations

from dataclasses import dataclass

from teaching_sims.topics.pulse_doppler.physics import MovingTarget, PulseDopplerParams


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: PulseDopplerParams
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "single_mover": Scenario(
        id="single_mover",
        title="Single moving target",
        teaching_point="A closing target appears as a bright cell at its range and Doppler.",
        params=PulseDopplerParams(
            clutter_enabled=False,
            targets=(MovingTarget(3500.0, 35.0, snr_db=28.0),),
            mti_canceller=False,
        ),
        notes="You should see one bright blob - not a noisy field. Read R and v from it.",
    ),
    "clutter_masks_target": Scenario(
        id="clutter_masks_target",
        title="Clutter masks a slow target",
        teaching_point="A bright zero-Doppler clutter ridge can hide slow movers.",
        params=PulseDopplerParams(
            clutter_enabled=True,
            clutter_cnr_db=28.0,
            clutter_width_mps=0.6,
            targets=(MovingTarget(4000.0, 4.0, snr_db=16.0),),
            mti_canceller=False,
        ),
        notes="Look for the horizontal clutter ridge near v=0; the slow target sits in it.",
    ),
    "mti_reveals_target": Scenario(
        id="mti_reveals_target",
        title="MTI reveals the mover",
        teaching_point="A two-pulse canceller notches zero Doppler and unmasks movers.",
        params=PulseDopplerParams(
            clutter_enabled=True,
            clutter_cnr_db=28.0,
            clutter_width_mps=0.6,
            targets=(MovingTarget(4000.0, 28.0, snr_db=18.0),),
            mti_canceller=True,
        ),
        notes="Toggle MTI off to bring the clutter ridge back.",
    ),
    "two_velocities": Scenario(
        id="two_velocities",
        title="Two velocities at one range",
        teaching_point="Doppler FFT separates targets that share a range cell.",
        params=PulseDopplerParams(
            clutter_enabled=False,
            bandwidth_hz=2e6,
            targets=(
                MovingTarget(3000.0, -20.0, snr_db=26.0),
                MovingTarget(3000.0, 45.0, snr_db=26.0),
            ),
        ),
        notes="Same range; two Doppler peaks on the cut plot.",
    ),
    "doppler_ambiguity": Scenario(
        id="doppler_ambiguity",
        title="Doppler ambiguity (PRF fold)",
        teaching_point="Velocities outside +/-v_unamb wrap into the PRF window.",
        params=PulseDopplerParams(
            frequency_hz=10e9,
            pri_s=200e-6,
            n_pulses=64,
            clutter_enabled=False,
            targets=(MovingTarget(2500.0, 120.0, snr_db=28.0),),
        ),
        notes="True 120 m/s appears near a folded velocity - check the annotation.",
    ),
    "cpi_resolution": Scenario(
        id="cpi_resolution",
        title="CPI length vs Doppler resolution",
        teaching_point="More pulses (longer CPI) narrows Doppler / velocity bins.",
        params=PulseDopplerParams(
            n_pulses=16,
            clutter_enabled=False,
            targets=(
                MovingTarget(3200.0, 20.0, snr_db=26.0),
                MovingTarget(3200.0, 30.0, snr_db=26.0),
            ),
        ),
        notes="Raise N pulses until the two Doppler peaks split cleanly.",
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
