"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys

TOPIC_ALIASES = {
    "phased-array": "phased_array",
    "phased_array": "phased_array",
    "beamforming": "beamforming",
    "beamformer": "beamforming",
    "pulsed-ranging": "pulsed_ranging",
    "pulsed_ranging": "pulsed_ranging",
    "ranging": "pulsed_ranging",
    "radar-ranging": "pulsed_ranging",
    "pulse-doppler": "pulse_doppler",
    "pulse_doppler": "pulse_doppler",
    "doppler": "pulse_doppler",
    "mti": "pulse_doppler",
    "cfar": "cfar",
    "detection": "cfar",
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="teaching-sims",
        description="Interactive teaching simulations (Dear PyGui).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Launch an interactive demo")
    demo.add_argument(
        "topic",
        choices=sorted(set(TOPIC_ALIASES)),
        help="Topic to launch",
    )
    demo.add_argument(
        "--scenario",
        default=None,
        help="Optional scripted scenario id",
    )
    demo.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List scenarios for the topic and exit",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command != "demo":
        print(f"unknown command: {args.command}", file=sys.stderr)
        return 1

    topic = TOPIC_ALIASES[args.topic]

    if topic == "phased_array":
        from teaching_sims.topics.phased_array.scenarios import list_scenarios
        from teaching_sims.ui.desktop.phased_array_app import run_app
    elif topic == "beamforming":
        from teaching_sims.topics.beamforming.scenarios import list_scenarios
        from teaching_sims.ui.desktop.beamforming_app import run_app
    elif topic == "pulsed_ranging":
        from teaching_sims.topics.pulsed_ranging.scenarios import list_scenarios
        from teaching_sims.ui.desktop.pulsed_ranging_app import run_app
    elif topic == "pulse_doppler":
        from teaching_sims.topics.pulse_doppler.scenarios import list_scenarios
        from teaching_sims.ui.desktop.pulse_doppler_app import run_app
    elif topic == "cfar":
        from teaching_sims.topics.cfar.scenarios import list_scenarios
        from teaching_sims.ui.desktop.cfar_app import run_app
    else:
        print(f"unsupported topic: {args.topic}", file=sys.stderr)
        return 1

    if args.list_scenarios:
        for sc in list_scenarios():
            print(f"{sc.id:24s}  {sc.title}")
            print(f"  {sc.teaching_point}")
        return 0

    run_app(scenario_id=args.scenario)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
