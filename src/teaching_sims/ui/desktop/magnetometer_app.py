"""Dear PyGui desktop app for magnetometer / heading teaching."""

from __future__ import annotations

import dearpygui.dearpygui as dpg

from teaching_sims.topics.magnetometer.physics import MagParams, process
from teaching_sims.topics.magnetometer.scenarios import SCENARIOS, get_scenario
from teaching_sims.ui.desktop.plot_utils import fit_axes, fxy as _fxy


class MagApp:
    def __init__(self, initial: MagParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or MagParams()
        self.scenario_id = scenario_id
        self._presenter = False
        self._seed = self.params.seed
        if scenario_id:
            sc = get_scenario(scenario_id)
            self.params = sc.params
            self._title = sc.title
            self._note = f"{sc.teaching_point}\n{sc.notes}"
        else:
            self._title = "Magnetometer / tilt-compensated heading"
            self._note = "Earth field in body frame, hard/soft iron, and tilt compensation."

    def _read_controls(self) -> MagParams:
        return MagParams(
            yaw_deg=float(dpg.get_value("yaw")),
            pitch_deg=float(dpg.get_value("pitch")),
            roll_deg=float(dpg.get_value("roll")),
            hard_x_ut=float(dpg.get_value("hard_x")),
            hard_y_ut=float(dpg.get_value("hard_y")),
            hard_z_ut=float(dpg.get_value("hard_z")),
            soft_xx=float(dpg.get_value("soft_xx")),
            soft_yy=float(dpg.get_value("soft_yy")),
            soft_xy=float(dpg.get_value("soft_xy")),
            noise_ut=float(dpg.get_value("noise")),
            tilt_compensate=bool(dpg.get_value("tilt_comp")),
            sweep_yaw=True,
            n_sweep=72,
            seed=self._seed,
        )

    def _push_controls(self, p: MagParams) -> None:
        dpg.set_value("yaw", p.yaw_deg)
        dpg.set_value("pitch", p.pitch_deg)
        dpg.set_value("roll", p.roll_deg)
        dpg.set_value("hard_x", p.hard_x_ut)
        dpg.set_value("hard_y", p.hard_y_ut)
        dpg.set_value("hard_z", p.hard_z_ut)
        dpg.set_value("soft_xx", p.soft_xx)
        dpg.set_value("soft_yy", p.soft_yy)
        dpg.set_value("soft_xy", p.soft_xy)
        dpg.set_value("noise", p.noise_ut)
        dpg.set_value("tilt_comp", p.tilt_compensate)
        self._seed = p.seed

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

    def _resample(self) -> None:
        self._seed += 1
        self.refresh()

    def refresh(self) -> None:
        try:
            self.params = self._read_controls()
        except ValueError as exc:
            dpg.set_value("status_text", f"Invalid settings: {exc}")
            return
        out = process(self.params)
        dpg.set_value("polar", _fxy(out["bx"], out["by"]))
        dpg.set_value("hdg_err", _fxy(out["yaw_sweep_deg"], out["heading_err_deg"]))
        dpg.set_value("hdg_raw", _fxy(out["yaw_sweep_deg"], out["heading_raw_deg"]))
        dpg.set_value("hdg_tc", _fxy(out["yaw_sweep_deg"], out["heading_tc_deg"]))
        dpg.set_value("yaw_line", _fxy(out["yaw_sweep_deg"], out["yaw_sweep_deg"]))
        fit_axes("bx_ax", "by_ax", "yaw_ax", "hdg_y", "err_yaw", "err_y")
        b = out["snapshot_b_ut"]
        dpg.set_value(
            "status_text",
            (
                f"At yaw={self.params.yaw_deg:.0f}°: B=[{b[0]:.1f}, {b[1]:.1f}, {b[2]:.1f}] µT\n"
                f"Heading estimate: {out['snapshot_heading_deg']:.1f}°  "
                f"err {out['snapshot_err_deg']:+.1f}°\n"
                f"Sweep RMS heading error: {out['rms_err_deg']:.2f}°"
            ),
        )

    def _on_change(self, *_a, **_k) -> None:
        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims — Magnetometer", width=1480, height=920)
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.window(tag="primary", label="Magnetometer"):
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
                        tag="tilt_comp", label="Tilt-compensated heading",
                        default_value=self.params.tilt_compensate, callback=self._on_change,
                    )
                    dpg.add_button(label="Resample noise", width=-1, callback=lambda: self._resample())
                    dpg.add_separator()
                    dpg.add_slider_float(
                        tag="yaw", label="Yaw (deg)", default_value=self.params.yaw_deg,
                        min_value=-180.0, max_value=180.0, callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="pitch", label="Pitch (deg)", default_value=self.params.pitch_deg,
                        min_value=-60.0, max_value=60.0, callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="roll", label="Roll (deg)", default_value=self.params.roll_deg,
                        min_value=-60.0, max_value=60.0, callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="hard_x", label="Hard-iron X (µT)", default_value=self.params.hard_x_ut,
                        min_value=-20.0, max_value=20.0, callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="hard_y", label="Hard-iron Y (µT)", default_value=self.params.hard_y_ut,
                        min_value=-20.0, max_value=20.0, callback=self._on_change,
                    )
                    with dpg.group(tag="advanced_controls"):
                        dpg.add_separator()
                        dpg.add_text("Advanced")
                        dpg.add_slider_float(
                            tag="hard_z", label="Hard-iron Z", default_value=self.params.hard_z_ut,
                            min_value=-20.0, max_value=20.0, callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="soft_xx", label="Soft-iron xx", default_value=self.params.soft_xx,
                            min_value=0.5, max_value=1.5, callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="soft_yy", label="Soft-iron yy", default_value=self.params.soft_yy,
                            min_value=0.5, max_value=1.5, callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="soft_xy", label="Soft-iron xy", default_value=self.params.soft_xy,
                            min_value=-0.4, max_value=0.4, callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="noise", label="Noise σ (µT)", default_value=self.params.noise_ut,
                            min_value=0.0, max_value=2.0, callback=self._on_change,
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
                    with dpg.plot(label="Horizontal field locus (bx, by)", height=360, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="bx (µT)", tag="bx_ax")
                        with dpg.plot_axis(dpg.mvYAxis, label="by (µT)", tag="by_ax"):
                            dpg.add_scatter_series([0.0], [0.0], label="yaw sweep", tag="polar")
                    with dpg.plot(label="Heading vs true yaw", height=200, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="true yaw (deg)", tag="yaw_ax")
                        with dpg.plot_axis(dpg.mvYAxis, label="heading (deg)", tag="hdg_y"):
                            dpg.add_line_series([0.0], [0.0], label="truth", tag="yaw_line")
                            dpg.add_line_series([0.0], [0.0], label="raw", tag="hdg_raw")
                            dpg.add_line_series([0.0], [0.0], label="tilt-comp", tag="hdg_tc")
                    with dpg.plot(label="Heading error (selected estimator)", height=200, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="true yaw (deg)", tag="err_yaw")
                        with dpg.plot_axis(dpg.mvYAxis, label="error (deg)", tag="err_y"):
                            dpg.add_line_series([0.0], [0.0], label="error", tag="hdg_err")

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        self._push_controls(self.params)
        self.refresh()
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()
        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: MagParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    MagApp(initial=params, scenario_id=scenario_id).run()
