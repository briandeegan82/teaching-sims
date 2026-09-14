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


def test_gyro_compare_draws_without_gui():
    """Smoke-test the teaching compare drawer with a non-interactive backend."""
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    from teaching_sims.ui.external.cube_geometry import draw_gyro_heading_compare

    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    draw_gyro_heading_compare(ax, 10.0, 35.0, t_s=4.0, err_deg=25.0)
    plt.close(fig)


def test_view_disabled_does_not_require_matplotlib():
    view = CubeAttitudeView()
    view.set_enabled(False)
    view.update(10.0, 5.0, -3.0)
    assert view.enabled is False
