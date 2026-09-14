"""Dear PyGui desktop app for accelerometer teaching."""

from __future__ import annotations

import dearpygui.dearpygui as dpg

from teaching_sims.topics.accelerometer.physics import AccelParams, process
from teaching_sims.topics.accelerometer.scenarios import SCENARIOS, get_scenario
from teaching_sims.ui.desktop.plot_utils import fit_axes, fxy as _fxy
from teaching_sims.ui.external.cube_view import CubeAttitudeView


class AccelApp:
    def __init__(self, initial: AccelParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or AccelParams()
        self.scenario_id = scenario_id
        self._presenter = False
        self._seed = self.params.seed
        self._cube_view = CubeAttitudeView()
        self._suppress_refresh = False
        if scenario_id:
            sc = get_scenario(scenario_id)
            self.params = sc.params
            self._title = sc.title
            self._note = f"{sc.teaching_point}\n{sc.notes}"
        else:
            self._title = "Accelerometer / specific force"
            self._note = "Gravity, tilt from accel, bias, and linear-acceleration contamination."

    def _read_controls(self) -> AccelParams:
        return AccelParams(
            yaw_deg=float(dpg.get_value("yaw")),
            roll_deg=float(dpg.get_value("roll")),
            pitch_deg=float(dpg.get_value("pitch")),
            ax_mps2=float(dpg.get_value("ax")),
            ay_mps2=float(dpg.get_value("ay")),
            az_mps2=float(dpg.get_value("az")),
            bias_x_mps2=float(dpg.get_value("bias_x")),
            bias_y_mps2=float(dpg.get_value("bias_y")),
            bias_z_mps2=float(dpg.get_value("bias_z")),
            noise_mps2=float(dpg.get_value("noise")),
            vibe_amp_mps2=float(dpg.get_value("vibe_amp")),
            vibe_hz=float(dpg.get_value("vibe_hz")),
            duration_s=float(dpg.get_value("duration")),
            fs_hz=100.0,
            seed=self._seed,
        )

    def _push_controls(self, p: AccelParams) -> None:
        self._suppress_refresh = True
        try:
            dpg.set_value("yaw", p.yaw_deg)
            dpg.set_value("roll", p.roll_deg)
            dpg.set_value("pitch", p.pitch_deg)
            dpg.set_value("ax", p.ax_mps2)
            dpg.set_value("ay", p.ay_mps2)
            dpg.set_value("az", p.az_mps2)
            dpg.set_value("bias_x", p.bias_x_mps2)
            dpg.set_value("bias_y", p.bias_y_mps2)
            dpg.set_value("bias_z", p.bias_z_mps2)
            dpg.set_value("noise", p.noise_mps2)
            dpg.set_value("vibe_amp", p.vibe_amp_mps2)
            dpg.set_value("vibe_hz", p.vibe_hz)
            dpg.set_value("duration", p.duration_s)
            self._seed = p.seed
        finally:
            self._suppress_refresh = False

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
        # refresh() already pushes cube pose; send once more after scenario load
        if self._cube_view.enabled:
            self._cube_view.update(sc.params.yaw_deg, sc.params.pitch_deg, sc.params.roll_deg)

    def _sync_cube_enabled(self) -> None:
        if not dpg.does_item_exist("show_3d"):
            return
        want = bool(dpg.get_value("show_3d"))
        if want != self._cube_view.enabled:
            self._cube_view.set_enabled(want)

    def _update_cube_attitude(self, params: AccelParams | None = None) -> None:
        self._sync_cube_enabled()
        if not self._cube_view.enabled:
            return
        p = params or self.params
        self._cube_view.update(p.yaw_deg, p.pitch_deg, p.roll_deg)

    def _set_presenter(self, _s=None, app_data=None, _u=None) -> None:
        self._presenter = bool(app_data if app_data is not None else dpg.get_value("presenter_mode"))
        dpg.configure_item("advanced_controls", show=not self._presenter)
        dpg.configure_item("banner_panel", height=110 if self._presenter else 72)

    def _toggle_3d(self, _s=None, app_data=None, _u=None) -> None:
        want = bool(app_data if app_data is not None else dpg.get_value("show_3d"))
        self._cube_view.set_enabled(want)
        self.refresh()

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
        t = out["t_s"]
        dpg.set_value("fx_series", _fxy(t, out["fx"]))
        dpg.set_value("fy_series", _fxy(t, out["fy"]))
        dpg.set_value("fz_series", _fxy(t, out["fz"]))
        dpg.set_value("roll_series", _fxy(t, out["roll_est_deg"]))
        dpg.set_value("pitch_series", _fxy(t, out["pitch_est_deg"]))
        dpg.set_value(
            "roll_true",
            [[0.0, float(t[-1])], [float(out["true_roll_deg"]), float(out["true_roll_deg"])]],
        )
        dpg.set_value(
            "pitch_true",
            [[0.0, float(t[-1])], [float(out["true_pitch_deg"]), float(out["true_pitch_deg"])]],
        )
        fit_axes("acc_t", "acc_y", "tilt_t", "tilt_y")
        self._update_cube_attitude()
        if self._cube_view.last_error and dpg.does_item_exist("show_3d"):
            dpg.set_value("show_3d", False)
            self._cube_view.set_enabled(False)
        cube_note = ""
        if self._cube_view.last_error:
            cube_note = f"\n3D window: {self._cube_view.last_error}"
        elif bool(dpg.get_value("show_3d")) if dpg.does_item_exist("show_3d") else False:
            cube_note = "\n3D window: open (matplotlib Qt)"
        dpg.set_value(
            "status_text",
            (
                f"True yaw/roll/pitch: {out['true_yaw_deg']:.1f}° / "
                f"{out['true_roll_deg']:.1f}° / {out['true_pitch_deg']:.1f}°\n"
                f"Mean estimate:       {out['roll_mean_deg']:.1f}° / {out['pitch_mean_deg']:.1f}° "
                f"(accel tilt has no yaw)\n"
                f"Error:               {out['roll_err_deg']:+.2f}° / {out['pitch_err_deg']:+.2f}°\n"
                f"Ideal f (m/s²):      [{out['true_f_body'][0]:.2f}, "
                f"{out['true_f_body'][1]:.2f}, {out['true_f_body'][2]:.2f}]"
                f"{cube_note}"
            ),
        )

    def _on_change(self, *_a, **_k) -> None:
        if self._suppress_refresh:
            return
        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims — Accelerometer", width=1480, height=920)
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        try:
            with dpg.window(tag="primary", label="Accelerometer"):
                with dpg.child_window(tag="banner_panel", height=72, border=True):
                    dpg.add_text(self._title, tag="banner_title")
                    dpg.add_text(self._note, tag="banner_body", wrap=1000)
                with dpg.group(horizontal=True):
                    with dpg.child_window(width=350, border=True):
                        dpg.add_checkbox(
                            tag="presenter_mode",
                            label="Presenter mode (hide advanced)",
                            default_value=False,
                            callback=self._set_presenter,
                        )
                        dpg.add_checkbox(
                            tag="show_3d",
                            label="Show 3D attitude window (matplotlib)",
                            default_value=False,
                            callback=self._toggle_3d,
                        )
                        dpg.add_button(label="Resample noise", width=-1, callback=lambda: self._resample())
                        dpg.add_separator()
                        dpg.add_text("Attitude (truth)")
                        dpg.add_slider_float(
                            tag="yaw",
                            label="Yaw (deg)",
                            default_value=self.params.yaw_deg,
                            min_value=-180.0,
                            max_value=180.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="roll",
                            label="Roll (deg)",
                            default_value=self.params.roll_deg,
                            min_value=-60.0,
                            max_value=60.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="pitch",
                            label="Pitch (deg)",
                            default_value=self.params.pitch_deg,
                            min_value=-80.0,
                            max_value=80.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="ax",
                            label="Body ax (m/s²)",
                            default_value=self.params.ax_mps2,
                            min_value=-5.0,
                            max_value=5.0,
                            callback=self._on_change,
                        )
                        with dpg.group(tag="advanced_controls"):
                            dpg.add_separator()
                            dpg.add_text("Advanced")
                            dpg.add_slider_float(
                                tag="ay",
                                label="Body ay (m/s²)",
                                default_value=self.params.ay_mps2,
                                min_value=-5.0,
                                max_value=5.0,
                                callback=self._on_change,
                            )
                            dpg.add_slider_float(
                                tag="az",
                                label="Body az (m/s²)",
                                default_value=self.params.az_mps2,
                                min_value=-5.0,
                                max_value=5.0,
                                callback=self._on_change,
                            )
                            dpg.add_slider_float(
                                tag="bias_x",
                                label="Bias X",
                                default_value=self.params.bias_x_mps2,
                                min_value=-1.0,
                                max_value=1.0,
                                callback=self._on_change,
                            )
                            dpg.add_slider_float(
                                tag="bias_y",
                                label="Bias Y",
                                default_value=self.params.bias_y_mps2,
                                min_value=-1.0,
                                max_value=1.0,
                                callback=self._on_change,
                            )
                            dpg.add_slider_float(
                                tag="bias_z",
                                label="Bias Z",
                                default_value=self.params.bias_z_mps2,
                                min_value=-1.0,
                                max_value=1.0,
                                callback=self._on_change,
                            )
                            dpg.add_slider_float(
                                tag="noise",
                                label="Noise σ (m/s²)",
                                default_value=self.params.noise_mps2,
                                min_value=0.0,
                                max_value=0.5,
                                callback=self._on_change,
                            )
                            dpg.add_slider_float(
                                tag="vibe_amp",
                                label="Vibration amp",
                                default_value=self.params.vibe_amp_mps2,
                                min_value=0.0,
                                max_value=5.0,
                                callback=self._on_change,
                            )
                            dpg.add_slider_float(
                                tag="vibe_hz",
                                label="Vibration Hz",
                                default_value=self.params.vibe_hz,
                                min_value=1.0,
                                max_value=80.0,
                                callback=self._on_change,
                            )
                            dpg.add_slider_float(
                                tag="duration",
                                label="Duration (s)",
                                default_value=self.params.duration_s,
                                min_value=1.0,
                                max_value=10.0,
                                callback=self._on_change,
                            )
                        dpg.add_separator()
                        dpg.add_text("Lecture scenarios")
                        for sid, sc in SCENARIOS.items():
                            dpg.add_button(
                                label=sc.title,
                                width=-1,
                                user_data=sid,
                                callback=lambda s, a, u: self._apply_scenario(u),
                            )
                        dpg.add_separator()
                        dpg.add_text(self._note, tag="scenario_text", wrap=310)
                        dpg.add_separator()
                        dpg.add_text("", tag="status_text", wrap=310)

                    with dpg.child_window(border=False):
                        with dpg.plot(label="Specific force (body)", height=400, width=-1):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label="t (s)", tag="acc_t")
                            with dpg.plot_axis(dpg.mvYAxis, label="m/s²", tag="acc_y"):
                                dpg.add_line_series([0.0], [0.0], label="fx", tag="fx_series")
                                dpg.add_line_series([0.0], [0.0], label="fy", tag="fy_series")
                                dpg.add_line_series([0.0], [0.0], label="fz", tag="fz_series")
                        with dpg.plot(label="Tilt from accelerometer", height=360, width=-1):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label="t (s)", tag="tilt_t")
                            with dpg.plot_axis(dpg.mvYAxis, label="deg", tag="tilt_y"):
                                dpg.add_line_series([0.0], [0.0], label="roll est", tag="roll_series")
                                dpg.add_line_series([0.0], [0.0], label="pitch est", tag="pitch_series")
                                dpg.add_line_series([0.0], [0.0], label="roll true", tag="roll_true")
                                dpg.add_line_series([0.0], [0.0], label="pitch true", tag="pitch_true")

            dpg.setup_dearpygui()
            dpg.show_viewport()
            dpg.set_primary_window("primary", True)
            self._push_controls(self.params)
            self.refresh()

            while dpg.is_dearpygui_running():
                dpg.render_dearpygui_frame()
        finally:
            self._cube_view.close()
            dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: AccelParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    AccelApp(initial=params, scenario_id=scenario_id).run()
