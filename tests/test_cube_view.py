"""Tests for matplotlib cube attitude helper (no GUI)."""

from __future__ import annotations

import numpy as np

from teaching_sims.ui.external.cube_geometry import cube_vertices_body, rotate_body_to_plot
from teaching_sims.ui.external.cube_view import CubeAttitudeView


def test_cube_has_eight_vertices():
    v = cube_vertices_body(0.5)
    assert v.shape == (8, 3)


def test_yaw_rotates_cube_in_plot():
    v0 = rotate_body_to_plot(0.0, 0.0, 0.0, cube_vertices_body())
    v1 = rotate_body_to_plot(90.0, 0.0, 0.0, cube_vertices_body())
    assert not np.allclose(v0, v1)


def test_roll_tilts_cube():
    v0 = rotate_body_to_plot(0.0, 0.0, 0.0, cube_vertices_body())
    v1 = rotate_body_to_plot(0.0, 0.0, 30.0, cube_vertices_body())
    assert not np.allclose(v0, v1)


def test_view_disabled_does_not_require_matplotlib():
    view = CubeAttitudeView()
    view.set_enabled(False)
    view.update(10.0, 5.0, -3.0)
    assert view.enabled is False
