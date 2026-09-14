"""Dear PyGui desktop app for gyroscope teaching."""

from __future__ import annotations

import time

import dearpygui.dearpygui as dpg
import numpy as np

from teaching_sims.topics.gyroscope.physics import GyroParams, MotionProfile, process
from teaching_sims.topics.gyroscope.scenarios import SCENARIOS, get_scenario
from teaching_sims.ui.desktop.plot_utils import fit_axes, fxy as _fxy
from teaching_sims.ui.external.cube_view import CubeAttitudeView


PROFILE_LABELS = {
    "Step turn": MotionProfile.STEP_TURN,
    "Constant rate": MotionProfile.CONSTANT,
    "Sine": MotionProfile.SINE,
}
LABEL_FOR_PROFILE = {v: k for k, v in PROFILE_LABELS.items()}


class GyroApp:
    def __init__(self, initial: GyroParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or GyroParams()
        self.scenario_id = scenario_id
        self._presenter = False
        self._seed = self.params.seed
        self._cube_view = CubeAttitudeView()
        self._suppress_refresh = False
        self._out: dict[str, object] | None = None
        self._playing = False
        self._play_t0: float | None = None
        self._play_speed = 1.0
        if scenario_id:
            sc = get_scenario(scenario_id)
            self.params = sc.params
            self._title = sc.title
            self._note = f"{sc.teaching_point}\n{sc.notes}"
        else:
            self._title = "Gyroscope / rate integration"
            self._note = (
                "Integrate ω → θ about Down. Bias ramps heading; ARW wanders. "
                "Use the 3D window to see truth vs gyro cubes diverge."
            )

    def _read_controls(self) -> GyroParams:
        return GyroParams(
            profile=PROFILE_LABELS[dpg.get_value("profile")],
            rate_dps=float(dpg.get_value("rate")),
            sine_hz=float(dpg.get_value("sine_hz")),
            duration_s=float(dpg.get_value("duration")),
            bias_dps=float(dpg.get_value("bias")),
            arw_deg_per_sqrt_s=float(dpg.get_value("arw")),
            compensate_bias=bool(dpg.get_value("comp_bias")),
            fs_hz=100.0,
            seed=self._seed,
        )

    def _push_controls(self, p: GyroParams) -> None:
        self._suppress_refresh = True
        try:
            dpg.set_value("profile", LABEL_FOR_PROFILE[p.profile])
            dpg.set_value("rate", p.rate_dps)
            dpg.set_value("sine_hz", p.sine_hz)
            dpg.set_value("duration", p.duration_s)
            dpg.set_value("bias", p.bias_dps)
            dpg.set_value("arw", p.arw_deg_per_sqrt_s)
            dpg.set_value("comp_bias", p.compensate_bias)
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
        self._playing = False
        self.refresh()
        if self._cube_view.enabled and self._out is not None:
            # Jump 3D to end of scenario so bias drift is immediately visible.
            t = np.asarray(self._out["t_s"], dtype=float)
            self._set_view_time(float(t[-1]), scrub=True)

    def _set_presenter(self, _s=None, app_data=None, _u=None) -> None:
        self._presenter = bool(app_data if app_data is not None else dpg.get_value("presenter_mode"))
        dpg.configure_item("advanced_controls", show=not self._presenter)
        dpg.configure_item("banner_panel", height=110 if self._presenter else 72)

    def _toggle_3d(self, _s=None, app_data=None, _u=None) -> None:
        want = bool(app_data if app_data is not None else dpg.get_value("show_3d"))
        self._cube_view.set_enabled(want)
        if want:
            self._playing = True
            self._play_t0 = time.monotonic()
            if dpg.does_item_exist("view_t"):
                dpg.set_value("view_t", 0.0)
        else:
            self._playing = False
        self.refresh()

    def _play(self) -> None:
        if not self._cube_view.enabled:
            return
        self._playing = True
        self._play_t0 = time.monotonic()
        if dpg.does_item_exist("view_t"):
            dpg.set_value("view_t", 0.0)

    def _stop_play(self) -> None:
        self._playing = False

    def _on_scrub(self, *_a, **_k) -> None:
        if self._suppress_refresh:
            return
        self._playing = False
        if self._out is None:
            return
        self._set_view_time(float(dpg.get_value("view_t")), scrub=False)

    def _resample(self) -> None:
        self._seed += 1
        self.refresh()

    def _sync_cube_enabled(self) -> None:
        if not dpg.does_item_exist("show_3d"):
            return
        want = bool(dpg.get_value("show_3d"))
        if want != self._cube_view.enabled:
            self._cube_view.set_enabled(want)

    def _set_view_time(self, t_query: float, *, scrub: bool) -> None:
        if self._out is None or not self._cube_view.enabled:
            return
        t = np.asarray(self._out["t_s"], dtype=float)
        th_true = np.asarray(self._out["angle_true_deg"], dtype=float)
        th_est = np.asarray(self._out["angle_est_deg"], dtype=float)
        err = np.asarray(self._out["angle_err_deg"], dtype=float)
        t_query = float(np.clip(t_query, float(t[0]), float(t[-1])))
        i = int(np.searchsorted(t, t_query, side="right") - 1)
        i = int(np.clip(i, 0, len(t) - 1))
        if scrub and dpg.does_item_exist("view_t"):
            self._suppress_refresh = True
            try:
                dpg.set_value("view_t", float(t[i]))
            finally:
                self._suppress_refresh = False
        self._cube_view.update_gyro_compare(
            float(th_true[i]),
            float(th_est[i]),
            t_s=float(t[i]),
            err_deg=float(err[i]),
        )

    def _tick_animation(self) -> None:
        if not self._playing or self._out is None or not self._cube_view.enabled:
            return
        t = np.asarray(self._out["t_s"], dtype=float)
        if self._play_t0 is None:
            self._play_t0 = time.monotonic()
        elapsed = (time.monotonic() - self._play_t0) * self._play_speed
        if elapsed >= float(t[-1]):
            self._set_view_time(float(t[-1]), scrub=True)
            self._playing = False
            return
        self._set_view_time(elapsed, scrub=True)

    def refresh(self) -> None:
        try:
            self.params = self._read_controls()
        except ValueError as exc:
            dpg.set_value("status_text", f"Invalid settings: {exc}")
            return
        out = process(self.params)
        self._out = out
        t = out["t_s"]
        dpg.set_value("rate_true", _fxy(t, out["rate_true_dps"]))
        dpg.set_value("rate_meas", _fxy(t, out["rate_meas_dps"]))
        dpg.set_value("ang_true", _fxy(t, out["angle_true_deg"]))
        dpg.set_value("ang_est", _fxy(t, out["angle_est_deg"]))
        dpg.set_value("ang_err", _fxy(t, out["angle_err_deg"]))
        fit_axes("rate_t", "rate_y", "ang_t", "ang_y", "err_t", "err_y")

        if dpg.does_item_exist("view_t"):
            self._suppress_refresh = True
            try:
                dpg.configure_item("view_t", max_value=float(t[-1]))
                if not self._playing:
                    dpg.set_value("view_t", float(t[-1]))
            finally:
                self._suppress_refresh = False

        self._sync_cube_enabled()
        if self._cube_view.enabled:
            if self._playing:
                self._play_t0 = time.monotonic()
            else:
                self._set_view_time(float(dpg.get_value("view_t")) if dpg.does_item_exist("view_t") else float(t[-1]), scrub=False)

        if self._cube_view.last_error and dpg.does_item_exist("show_3d"):
            dpg.set_value("show_3d", False)
            self._cube_view.set_enabled(False)

        cube_note = ""
        if self._cube_view.last_error:
            cube_note = f"\n3D window: {self._cube_view.last_error}"
        elif bool(dpg.get_value("show_3d")) if dpg.does_item_exist("show_3d") else False:
            cube_note = "\n3D: dark=truth, orange=gyro ∫ω (scrub / Play)"

        dpg.set_value(
            "status_text",
            (
                f"Bias: {out['bias_dps']:.2f} °/s   σ_rate: {out['sigma_rate_dps']:.3f} °/s\n"
                f"Final angle error: {out['final_err_deg']:+.2f}°\n"
                f"Compensation: {'ON' if self.params.compensate_bias else 'OFF'}"
                f"{cube_note}"
            ),
        )

    def _on_change(self, *_a, **_k) -> None:
        if self._suppress_refresh:
            return
        self._playing = False
        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims — Gyroscope", width=1480, height=920)
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        try:
            with dpg.window(tag="primary", label="Gyroscope"):
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
                            label="Show 3D heading window (matplotlib)",
                            default_value=False,
                            callback=self._toggle_3d,
                        )
                        dpg.add_checkbox(
                            tag="comp_bias",
                            label="Compensate known bias",
                            default_value=self.params.compensate_bias,
                            callback=self._on_change,
                        )
                        dpg.add_button(label="Resample noise", width=-1, callback=lambda: self._resample())
                        dpg.add_separator()
                        dpg.add_text("3D playback (about Down)")
                        dpg.add_slider_float(
                            tag="view_t",
                            label="View time (s)",
                            default_value=self.params.duration_s,
                            min_value=0.0,
                            max_value=self.params.duration_s,
                            callback=self._on_scrub,
                        )
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="Play", width=100, callback=lambda: self._play())
                            dpg.add_button(label="Pause", width=100, callback=lambda: self._stop_play())
                        dpg.add_separator()
                        dpg.add_combo(
                            tag="profile",
                            label="Motion",
                            items=list(PROFILE_LABELS.keys()),
                            default_value=LABEL_FOR_PROFILE[self.params.profile],
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="rate",
                            label="Rate amp (°/s)",
                            default_value=self.params.rate_dps,
                            min_value=-90.0,
                            max_value=90.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="bias",
                            label="Bias (°/s)",
                            default_value=self.params.bias_dps,
                            min_value=-3.0,
                            max_value=3.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="arw",
                            label="ARW (°/√s)",
                            default_value=self.params.arw_deg_per_sqrt_s,
                            min_value=0.0,
                            max_value=1.0,
                            callback=self._on_change,
                        )
                        with dpg.group(tag="advanced_controls"):
                            dpg.add_separator()
                            dpg.add_text("Advanced")
                            dpg.add_slider_float(
                                tag="sine_hz",
                                label="Sine Hz",
                                default_value=self.params.sine_hz,
                                min_value=0.1,
                                max_value=2.0,
                                callback=self._on_change,
                            )
                            dpg.add_slider_float(
                                tag="duration",
                                label="Duration (s)",
                                default_value=self.params.duration_s,
                                min_value=2.0,
                                max_value=30.0,
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
                        with dpg.plot(label="Angular rate", height=260, width=-1):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label="t (s)", tag="rate_t")
                            with dpg.plot_axis(dpg.mvYAxis, label="°/s", tag="rate_y"):
                                dpg.add_line_series([0.0], [0.0], label="true", tag="rate_true")
                                dpg.add_line_series([0.0], [0.0], label="measured", tag="rate_meas")
                        with dpg.plot(label="Integrated angle", height=260, width=-1):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label="t (s)", tag="ang_t")
                            with dpg.plot_axis(dpg.mvYAxis, label="deg", tag="ang_y"):
                                dpg.add_line_series([0.0], [0.0], label="true", tag="ang_true")
                                dpg.add_line_series([0.0], [0.0], label="estimate", tag="ang_est")
                        with dpg.plot(label="Angle error", height=220, width=-1):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label="t (s)", tag="err_t")
                            with dpg.plot_axis(dpg.mvYAxis, label="deg", tag="err_y"):
                                dpg.add_line_series([0.0], [0.0], label="error", tag="ang_err")

            dpg.setup_dearpygui()
            dpg.show_viewport()
            dpg.set_primary_window("primary", True)
            self._push_controls(self.params)
            self.refresh()
            while dpg.is_dearpygui_running():
                self._tick_animation()
                dpg.render_dearpygui_frame()
        finally:
            self._cube_view.close()
            dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: GyroParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    GyroApp(initial=params, scenario_id=scenario_id).run()
