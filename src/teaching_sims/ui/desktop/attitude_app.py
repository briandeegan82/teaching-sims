"""Dear PyGui desktop app for attitude / rotations teaching."""

from __future__ import annotations

import dearpygui.dearpygui as dpg
import numpy as np

from teaching_sims.topics.attitude.physics import AttitudeParams, process
from teaching_sims.topics.attitude.scenarios import SCENARIOS, get_scenario
from teaching_sims.ui.desktop.plot_utils import fit_axes, fxy as _fxy


def _axis_line(origin, vec, scale=1.0):
    v = np.asarray(vec, dtype=float) * scale
    return [[float(origin[0]), float(origin[0] + v[0])], [float(origin[1]), float(origin[1] + v[1])]]


class AttitudeApp:
    def __init__(self, initial: AttitudeParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or AttitudeParams()
        self.scenario_id = scenario_id
        self._presenter = False
        if scenario_id:
            sc = get_scenario(scenario_id)
            self.params = sc.params
            self._title = sc.title
            self._note = f"{sc.teaching_point}\n{sc.notes}"
        else:
            self._title = "Attitude: Euler, DCM, quaternion"
            self._note = "Body axes in NED, Euler extraction, and gimbal lock."

    def _read_controls(self) -> AttitudeParams:
        return AttitudeParams(
            yaw_deg=float(dpg.get_value("yaw")),
            pitch_deg=float(dpg.get_value("pitch")),
            roll_deg=float(dpg.get_value("roll")),
            animate_pitch=bool(dpg.get_value("scan_pitch")),
            pitch_scan_deg=float(dpg.get_value("scan_amp")),
            n_samples=181,
        )

    def _push_controls(self, p: AttitudeParams) -> None:
        dpg.set_value("yaw", p.yaw_deg)
        dpg.set_value("pitch", p.pitch_deg)
        dpg.set_value("roll", p.roll_deg)
        dpg.set_value("scan_pitch", p.animate_pitch)
        dpg.set_value("scan_amp", p.pitch_scan_deg)

    def _apply_scenario(self, scenario_id: str) -> None:
        sc = get_scenario(scenario_id)
        self.scenario_id = scenario_id
        self.params = sc.params
        self._title = sc.title
        self._note = f"{sc.teaching_point}\n{sc.notes}"
        self._push_controls(self.params)
        dpg.set_value("banner_title", self._title)
        dpg.set_value("banner_body", self._note)
        dpg.set_value("scenario_text", self._note)
        self.refresh()

    def _set_presenter(self, _s=None, app_data=None, _u=None) -> None:
        self._presenter = bool(app_data if app_data is not None else dpg.get_value("presenter_mode"))
        dpg.configure_item("advanced_controls", show=not self._presenter)
        dpg.configure_item("banner_panel", height=110 if self._presenter else 72)

    def refresh(self) -> None:
        try:
            self.params = self._read_controls()
        except ValueError as exc:
            dpg.set_value("status_text", f"Invalid settings: {exc}")
            return
        out = process(self.params)
        # Top-down NE projection of body X/Y
        o = np.array([0.0, 0.0])
        bx, by, bz = out["body_x_ned"], out["body_y_ned"], out["body_z_ned"]
        dpg.set_value("axis_x", _axis_line(o, [bx[0], bx[1]]))
        dpg.set_value("axis_y", _axis_line(o, [by[0], by[1]]))
        dpg.set_value("axis_z", _axis_line(o, [bz[0], bz[1]], scale=0.6))
        pscan = out["pitch_scan_deg"]
        dpg.set_value("yaw_ext", _fxy(pscan, out["yaw_extracted_deg"]))
        dpg.set_value("roll_ext", _fxy(pscan, out["roll_extracted_deg"]))
        dpg.set_value("pitch_ext", _fxy(pscan, out["pitch_extracted_deg"]))
        fit_axes("ne_x", "ne_y", "scan_x", "scan_y")
        q = out["quat"]
        e = out["euler_from_quat_deg"]
        dpg.set_value(
            "status_text",
            (
                f"quat [w,x,y,z]: [{q[0]:+.3f}, {q[1]:+.3f}, {q[2]:+.3f}, {q[3]:+.3f}]\n"
                f"Euler<-quat ( deg): yaw {e[0]:.1f}, pitch {e[1]:.1f}, roll {e[2]:.1f}\n"
                f"det(DCM)={out['det_dcm']:.6f}   "
                f"near singular samples: {int(np.count_nonzero(out['near_singular']))}"
            ),
        )

    def _on_change(self, *_a, **_k) -> None:
        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims - Attitude", width=1480, height=920)
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.window(tag="primary", label="Attitude"):
            with dpg.child_window(tag="banner_panel", height=72, border=True):
                dpg.add_text(self._title, tag="banner_title")
                dpg.add_text(self._note, tag="banner_body", wrap=1000)
            with dpg.group(horizontal=True):
                with dpg.child_window(width=350, border=True):
                    dpg.add_checkbox(
                        tag="presenter_mode", label="Presenter mode (hide advanced)",
                        default_value=False, callback=self._set_presenter,
                    )
                    dpg.add_checkbox(
                        tag="scan_pitch", label="Pitch scan (gimbal lock)",
                        default_value=self.params.animate_pitch, callback=self._on_change,
                    )
                    dpg.add_separator()
                    dpg.add_slider_float(
                        tag="yaw", label="Yaw (deg)", default_value=self.params.yaw_deg,
                        min_value=-180.0, max_value=180.0, callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="pitch", label="Pitch (deg)", default_value=self.params.pitch_deg,
                        min_value=-89.0, max_value=89.0, callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="roll", label="Roll (deg)", default_value=self.params.roll_deg,
                        min_value=-90.0, max_value=90.0, callback=self._on_change,
                    )
                    with dpg.group(tag="advanced_controls"):
                        dpg.add_separator()
                        dpg.add_text("Advanced")
                        dpg.add_slider_float(
                            tag="scan_amp", label="Scan +/-pitch (deg)", default_value=self.params.pitch_scan_deg,
                            min_value=30.0, max_value=89.0, callback=self._on_change,
                        )
                    dpg.add_separator()
                    dpg.add_text("Lecture scenarios")
                    for sid, sc in SCENARIOS.items():
                        dpg.add_button(
                            label=sc.title, width=-1, user_data=sid,
                            callback=lambda s, a, u: self._apply_scenario(u),
                        )
                    dpg.add_separator()
                    dpg.add_text(self._note, tag="scenario_text", wrap=310)
                    dpg.add_separator()
                    dpg.add_text("", tag="status_text", wrap=310)

                with dpg.child_window(border=False):
                    with dpg.plot(label="Body axes in NE (top view)", height=380, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="East", tag="ne_x")
                        with dpg.plot_axis(dpg.mvYAxis, label="North", tag="ne_y"):
                            dpg.add_line_series([0.0, 1.0], [0.0, 0.0], label="X body", tag="axis_x")
                            dpg.add_line_series([0.0, 0.0], [0.0, 1.0], label="Y body", tag="axis_y")
                            dpg.add_line_series([0.0, 0.0], [0.0, 0.5], label="Z body (NE proj)", tag="axis_z")
                    with dpg.plot(label="Euler extraction vs pitch", height=360, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="pitch (deg)", tag="scan_x")
                        with dpg.plot_axis(dpg.mvYAxis, label="extracted (deg)", tag="scan_y"):
                            dpg.add_line_series([0.0], [0.0], label="yaw", tag="yaw_ext")
                            dpg.add_line_series([0.0], [0.0], label="pitch", tag="pitch_ext")
                            dpg.add_line_series([0.0], [0.0], label="roll", tag="roll_ext")

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        self._push_controls(self.params)
        self.refresh()
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()
        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: AttitudeParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    AttitudeApp(initial=params, scenario_id=scenario_id).run()
