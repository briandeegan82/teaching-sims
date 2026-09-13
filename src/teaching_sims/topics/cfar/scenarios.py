"""Scripted lecture scenarios for CFAR detection."""

from __future__ import annotations

from dataclasses import dataclass

from teaching_sims.topics.cfar.physics import CFARMethod, CFARParams, CFARTarget


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    teaching_point: str
    params: CFARParams
    notes: str = ""


SCENARIOS: dict[str, Scenario] = {
    "ca_two_targets": Scenario(
        id="ca_two_targets",
        title="CA-CFAR two targets",
        teaching_point="CA-CFAR adapts the threshold to local noise and catches both peaks.",
        params=CFARParams(
            method=CFARMethod.CA,
            pfa=1e-3,
            targets=(CFARTarget(90, 18.0), CFARTarget(170, 15.0)),
        ),
        notes="Compare the adaptive threshold curve to the flat fixed threshold.",
    ),
    "fixed_vs_cfar_clutter": Scenario(
        id="fixed_vs_cfar_clutter",
        title="Clutter edge: fixed vs CFAR",
        teaching_point="A fixed noise threshold floods with false alarms in stronger clutter.",
        params=CFARParams(
            method=CFARMethod.CA,
            pfa=1e-3,
            clutter_edge_enabled=True,
            clutter_edge_cell=130,
            clutter_ratio_db=12.0,
            targets=(CFARTarget(80, 16.0), CFARTarget(190, 16.0)),
        ),
        notes="Target in clear + target in clutter; overlay fixed threshold false alarms.",
    ),
    "ca_masks_near_target": Scenario(
        id="ca_masks_near_target",
        title="CA masking of a weak neighbour",
        teaching_point="A strong target in the training window raises the threshold and can hide a neighbour.",
        params=CFARParams(
            method=CFARMethod.CA,
            n_train=16,
            n_guard=1,
            pfa=1e-3,
            targets=(CFARTarget(120, 25.0), CFARTarget(128, 12.0)),
        ),
        notes="Switch to OS-CFAR and watch the weak target reappear.",
    ),
    "os_recovers_neighbour": Scenario(
        id="os_recovers_neighbour",
        title="OS-CFAR recovers neighbour",
        teaching_point="Ordered-statistic CFAR is more robust when training cells contain targets.",
        params=CFARParams(
            method=CFARMethod.OS,
            os_rank=3,
            n_train=16,
            n_guard=1,
            pfa=1e-3,
            targets=(CFARTarget(120, 25.0), CFARTarget(128, 12.0)),
        ),
        notes="Same geometry as the CA-masking scenario.",
    ),
    "go_at_clutter_edge": Scenario(
        id="go_at_clutter_edge",
        title="GO-CFAR at a clutter edge",
        teaching_point="Greatest-of CFAR reduces false alarms when one side is in clutter.",
        params=CFARParams(
            method=CFARMethod.GO,
            clutter_edge_enabled=True,
            clutter_edge_cell=140,
            clutter_ratio_db=14.0,
            pfa=1e-3,
            targets=(CFARTarget(100, 17.0),),
        ),
        notes="Compare with SO-CFAR (more detections, more FAs near the edge).",
    ),
    "pfa_tradeoff": Scenario(
        id="pfa_tradeoff",
        title="P_fa vs detections",
        teaching_point="Lower design P_fa raises the threshold: fewer FAs, more misses.",
        params=CFARParams(
            method=CFARMethod.CA,
            pfa=1e-4,
            targets=(CFARTarget(110, 13.0), CFARTarget(180, 20.0)),
        ),
        notes="Raise P_fa toward 1e-2 and watch weak-target detections return.",
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
