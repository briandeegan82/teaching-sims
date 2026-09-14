"""Body-cube geometry for the external 3D attitude viewer."""

from __future__ import annotations

import numpy as np

from teaching_sims.core.imu import DEG2RAD
from teaching_sims.topics.attitude.physics import euler_zyx_to_dcm

CUBE_EDGES = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 0),
    (4, 5),
    (5, 6),
    (6, 7),
    (7, 4),
    (0, 4),
    (1, 5),
    (2, 6),
    (3, 7),
)


def cube_vertices_body(half_size: float = 0.5) -> np.ndarray:
    """Unit cube corners in body frame (X forward, Y right, Z down)."""
    s = half_size
    return np.array(
        [
            [s, -s, -s],
            [s, s, -s],
            [-s, s, -s],
            [-s, -s, -s],
            [s, -s, s],
            [s, s, s],
            [-s, s, s],
            [-s, -s, s],
        ],
        dtype=float,
    )


def rotate_body_to_plot(
    yaw_deg: float,
    pitch_deg: float,
    roll_deg: float,
    points_body: np.ndarray,
) -> np.ndarray:
    """Map body-frame points to matplotlib XYZ (East, North, Up)."""
    r_nb = euler_zyx_to_dcm(yaw_deg * DEG2RAD, pitch_deg * DEG2RAD, roll_deg * DEG2RAD)
    ned = (r_nb @ points_body.T).T
    return np.column_stack([ned[:, 1], ned[:, 0], -ned[:, 2]])


def _draw_wire_cube(ax, yaw_deg: float, pitch_deg: float, roll_deg: float, *, color: str, half: float, lw: float, label: str | None) -> None:
    verts_plot = rotate_body_to_plot(yaw_deg, pitch_deg, roll_deg, cube_vertices_body(half))
    for k, (i, j) in enumerate(CUBE_EDGES):
        xs = [verts_plot[i, 0], verts_plot[j, 0]]
        ys = [verts_plot[i, 1], verts_plot[j, 1]]
        zs = [verts_plot[i, 2], verts_plot[j, 2]]
        ax.plot(xs, ys, zs, color=color, linewidth=lw, label=label if k == 0 else None)


def _draw_body_x(ax, yaw_deg: float, pitch_deg: float, roll_deg: float, *, color: str, lim: float, label: str) -> None:
    r_nb = euler_zyx_to_dcm(yaw_deg * DEG2RAD, pitch_deg * DEG2RAD, roll_deg * DEG2RAD)
    axis_ned = r_nb[:, 0]
    tip = np.array([axis_ned[1], axis_ned[0], -axis_ned[2]]) * lim
    ax.plot([0, tip[0]], [0, tip[1]], [0, tip[2]], color=color, linewidth=2.8, label=label)


def draw_cube_attitude(ax, yaw_deg: float, pitch_deg: float, roll_deg: float, *, half: float = 0.5) -> None:
    """Draw cube + body/NED axes on a matplotlib 3D axis."""
    ax.cla()
    ax.set_xlabel("East")
    ax.set_ylabel("North")
    ax.set_zlabel("Up")
    ax.set_title(f"Yaw {yaw_deg:.0f} deg  Pitch {pitch_deg:.0f} deg  Roll {roll_deg:.0f} deg")

    lim = 1.1
    ax.plot([0, 0], [0, lim], [0, 0], color="0.55", linewidth=1.0, label="N")
    ax.plot([0, lim], [0, 0], [0, 0], color="0.55", linewidth=1.0, label="E")
    ax.plot([0, 0], [0, 0], [0, lim], color="0.55", linewidth=1.0, label="Up")

    _draw_wire_cube(ax, yaw_deg, pitch_deg, roll_deg, color="0.25", half=half, lw=1.5, label="body")
    r_nb = euler_zyx_to_dcm(yaw_deg * DEG2RAD, pitch_deg * DEG2RAD, roll_deg * DEG2RAD)
    for idx, (color, label) in enumerate((("C0", "X body"), ("C1", "Y body"), ("C2", "Z body"))):
        axis_ned = r_nb[:, idx]
        tip = np.array([axis_ned[1], axis_ned[0], -axis_ned[2]]) * lim
        ax.plot([0, tip[0]], [0, tip[1]], [0, tip[2]], color=color, linewidth=2.5, label=label)

    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-lim, lim)
    ax.set_box_aspect((1, 1, 1))
    ax.legend(loc="upper left", fontsize=8)


def draw_gyro_heading_compare(
    ax,
    yaw_true_deg: float,
    yaw_est_deg: float,
    *,
    t_s: float | None = None,
    err_deg: float | None = None,
) -> None:
    """Compare true vs gyro-integrated heading about Down (Z).

    Truth cube is dark; estimate is orange - the angular mismatch is the
    teaching signal for bias/ARW drift.
    """
    ax.cla()
    ax.set_xlabel("East")
    ax.set_ylabel("North")
    ax.set_zlabel("Up")
    title = f"True yaw {yaw_true_deg:.1f} deg   Gyro yaw {yaw_est_deg:.1f} deg"
    if t_s is not None:
        title = f"t = {t_s:.2f} s\n" + title
    if err_deg is not None:
        title += f"   err {err_deg:+.1f} deg"
    ax.set_title(title)

    lim = 1.1
    ax.plot([0, 0], [0, lim], [0, 0], color="0.55", linewidth=1.0, label="N")
    ax.plot([0, lim], [0, 0], [0, 0], color="0.55", linewidth=1.0, label="E")
    ax.plot([0, 0], [0, 0], [0, lim], color="0.55", linewidth=1.0, label="Up")

    _draw_wire_cube(ax, yaw_true_deg, 0.0, 0.0, color="0.2", half=0.55, lw=2.0, label="truth")
    _draw_wire_cube(ax, yaw_est_deg, 0.0, 0.0, color="C1", half=0.42, lw=1.8, label="gyro int omega")
    _draw_body_x(ax, yaw_true_deg, 0.0, 0.0, color="C0", lim=lim, label="X truth")
    _draw_body_x(ax, yaw_est_deg, 0.0, 0.0, color="C3", lim=0.85 * lim, label="X gyro")

    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-lim, lim)
    ax.set_box_aspect((1, 1, 1))
    ax.legend(loc="upper left", fontsize=8)
