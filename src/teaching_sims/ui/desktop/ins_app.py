"""Dear PyGui desktop app for strapdown INS teaching."""

from __future__ import annotations

import dearpygui.dearpygui as dpg

from teaching_sims.topics.ins.physics import INSParams, PathProfile, process
from teaching_sims.topics.ins.scenarios import SCENARIOS, get_scenario
from teaching_sims.ui.desktop.plot_utils import fit_axes, fxy as _fxy


PROFILE_LABELS = {
    "Circle": PathProfile.CIRCLE,
    "Straight": PathProfile.STRAIGHT,
    "Stop-and-go": PathProfile.STOP_AND_GO,
}
LABEL_FOR_PROFILE = {v: k for k, v in PROFILE_LABELS.items()}


class INSApp:
    def __init__(self, initial: INSParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or INSParams()
        self.scenario_id = scenario_id
        self._presenter = False
        self._seed = self.params.seed
        if scenario_id:
            sc = get_scenario(scenario_id)
            self.params = sc.params
            self._title = sc.title
            self._note = f"{sc.teaching_point}\n{sc.notes}"
        else:
            self._title = "Strapdown INS / dead reckoning"
            self._note = "Unaided 2D navigation: attitude drift and accel bias grow position error."

    def _read_controls(self) -> INSParams:
        return INSParams(
            profile=PROFILE_LABELS[dpg.get_value("profile")],
            speed_mps=float(dpg.get_value("speed")),
            radius_m=float(dpg.get_value("radius")),
            duration_s=float(dpg.get_value("duration")),
            gyro_bias_dps=float(dpg.get_value("gyro_bias")),
            accel_bias_x_mps2=float(dpg.get_value("abx")),
            accel_bias_y_mps2=float(dpg.get_value("aby")),
            accel_noise_mps2=float(dpg.get_value("an")),
            gyro_noise_dps=float(dpg.get_value("gn")),
            perfect_attitude=bool(dpg.get_value("perfect_att")),
            fs_hz=50.0,
            seed=self._seed,
        )

    def _push_controls(self, p: INSParams) -> None:
        dpg.set_value("profile", LABEL_FOR_PROFILE[p.profile])
        dpg.set_value("speed", p.speed_mps)
        dpg.set_value("radius", p.radius_m)
        dpg.set_value("duration", p.duration_s)
        dpg.set_value("gyro_bias", p.gyro_bias_dps)
        dpg.set_value("abx", p.accel_bias_x_mps2)
        dpg.set_value("aby", p.accel_bias_y_mps2)
        dpg.set_value("an", p.accel_noise_mps2)
        dpg.set_value("gn", p.gyro_noise_dps)
        dpg.set_value("perfect_att", p.perfect_attitude)
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
        dpg.set_value("path_true", _fxy(out["east_true_m"], out["north_true_m"]))
        dpg.set_value("path_est", _fxy(out["east_est_m"], out["north_est_m"]))
        dpg.set_value("err_series", _fxy(out["t_s"], out["pos_err_m"]))
        dpg.set_value("hdg_true", _fxy(out["t_s"], out["hdg_true_deg"]))
        dpg.set_value("hdg_est", _fxy(out["t_s"], out["hdg_est_deg"]))
        fit_axes("east_ax", "north_ax", "err_t", "err_y", "hdg_t", "hdg_y")
        dpg.set_value(
            "status_text",
            (
                f"Final position error: {out['final_pos_err_m']:.2f} m\n"
                f"Perfect attitude: {'ON' if self.params.perfect_attitude else 'OFF'}\n"
                f"Gyro bias {self.params.gyro_bias_dps:.2f}  deg/s   "
                f"Accel bias x/y {self.params.accel_bias_x_mps2:.3f}/{self.params.accel_bias_y_mps2:.3f}"
            ),
        )

    def _on_change(self, *_a, **_k) -> None:
        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims - Strapdown INS", width=1480, height=920)
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.window(tag="primary", label="INS"):
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
                        tag="perfect_att", label="Perfect attitude (isolate accel)",
                        default_value=self.params.perfect_attitude, callback=self._on_change,
                    )
                    dpg.add_button(label="Resample noise", width=-1, callback=lambda: self._resample())
                    dpg.add_separator()
                    dpg.add_combo(
                        tag="profile", label="Path", items=list(PROFILE_LABELS.keys()),
                        default_value=LABEL_FOR_PROFILE[self.params.profile], callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="speed", label="Speed (m/s)", default_value=self.params.speed_mps,
                        min_value=1.0, max_value=15.0, callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="gyro_bias", label="Gyro bias (deg/s)", default_value=self.params.gyro_bias_dps,
                        min_value=-1.0, max_value=1.0, callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="abx", label="Accel bias X (m/s^2)", default_value=self.params.accel_bias_x_mps2,
                        min_value=-0.2, max_value=0.2, callback=self._on_change,
                    )
                    with dpg.group(tag="advanced_controls"):
                        dpg.add_separator()
                        dpg.add_text("Advanced")
                        dpg.add_slider_float(
                            tag="radius", label="Circle radius (m)", default_value=self.params.radius_m,
                            min_value=10.0, max_value=100.0, callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="duration", label="Duration (s)", default_value=self.params.duration_s,
                            min_value=10.0, max_value=90.0, callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="aby", label="Accel bias Y", default_value=self.params.accel_bias_y_mps2,
                            min_value=-0.2, max_value=0.2, callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="an", label="Accel noise", default_value=self.params.accel_noise_mps2,
                            min_value=0.0, max_value=0.2, callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="gn", label="Gyro noise", default_value=self.params.gyro_noise_dps,
                            min_value=0.0, max_value=0.5, callback=self._on_change,
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
                    with dpg.plot(label="Horizontal path (NED)", height=420, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="East (m)", tag="east_ax")
                        with dpg.plot_axis(dpg.mvYAxis, label="North (m)", tag="north_ax"):
                            dpg.add_line_series([0.0], [0.0], label="truth", tag="path_true")
                            dpg.add_line_series([0.0], [0.0], label="INS", tag="path_est")
                    with dpg.group(horizontal=True):
                        with dpg.plot(label="Position error", height=300, width=540):
                            dpg.add_plot_axis(dpg.mvXAxis, label="t (s)", tag="err_t")
                            with dpg.plot_axis(dpg.mvYAxis, label="m", tag="err_y"):
                                dpg.add_line_series([0.0], [0.0], label="|err|", tag="err_series")
                        with dpg.plot(label="Heading", height=300, width=540):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label="t (s)", tag="hdg_t")
                            with dpg.plot_axis(dpg.mvYAxis, label="deg", tag="hdg_y"):
                                dpg.add_line_series([0.0], [0.0], label="true", tag="hdg_true")
                                dpg.add_line_series([0.0], [0.0], label="est", tag="hdg_est")

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        self._push_controls(self.params)
        self.refresh()
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()
        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: INSParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    INSApp(initial=params, scenario_id=scenario_id).run()
