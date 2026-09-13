"""CLI smoke tests (no GUI launch)."""

from __future__ import annotations

from teaching_sims.ui.cli import main


def test_list_topics(capsys):
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert "phased-array" in out
    assert "sar" in out


def test_list_scenarios_cfar(capsys):
    assert main(["demo", "cfar", "--list-scenarios"]) == 0
    out = capsys.readouterr().out
    assert "ca_two_targets" in out
