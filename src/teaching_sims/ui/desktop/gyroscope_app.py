"""Dear PyGui desktop app for gyroscope teaching."""

from __future__ import annotations

import dearpygui.dearpygui as dpg

from teaching_sims.topics.gyroscope.physics import GyroParams, MotionProfile, process
from teaching_sims.topics.gyroscope.scenarios import SCENARIOS, get_scenario
from teaching_sims.ui.desktop.plot_utils import fit_axes, fxy as _fxy


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
        if scenario_id:
            sc = get_scenario(scenario_id)
            self.params = sc.params
            self._title = sc.title
            self._note = f"{sc.teaching_point}\n{sc.notes}"
        else:
            self._title = "Gyroscope / rate integration"
            self._note = "Integrate ω → θ; watch bias ramps and angle random walk."

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
        dpg.set_value("profile", LABEL_FOR_PROFILE[p.profile])
        dpg.set_value("rate", p.rate_dps)
        dpg.set_value("sine_hz", p.sine_hz)
        dpg.set_value("duration", p.duration_s)
        dpg.set_value("bias", p.bias_dps)
        dpg.set_value("arw", p.arw_deg_per_sqrt_s)
        dpg.set_value("comp_bias", p.compensate_bias)
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
        t = out["t_s"]
        dpg.set_value("rate_true", _fxy(t, out["rate_true_dps"]))
        dpg.set_value("rate_meas", _fxy(t, out["rate_meas_dps"]))
        dpg.set_value("ang_true", _fxy(t, out["angle_true_deg"]))
        dpg.set_value("ang_est", _fxy(t, out["angle_est_deg"]))
        dpg.set_value("ang_err", _fxy(t, out["angle_err_deg"]))
        fit_axes("rate_t", "rate_y", "ang_t", "ang_y", "err_t", "err_y")
        dpg.set_value(
            "status_text",
            (
                f"Bias: {out['bias_dps']:.2f} °/s   σ_rate: {out['sigma_rate_dps']:.3f} °/s\n"
                f"Final angle error: {out['final_err_deg']:+.2f}°\n"
                f"Compensation: {'ON' if self.params.compensate_bias else 'OFF'}"
            ),
        )

    def _on_change(self, *_a, **_k) -> None:
        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims — Gyroscope", width=1480, height=920)
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.window(tag="primary", label="Gyroscope"):
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
                        tag="comp_bias", label="Compensate known bias",
                        default_value=self.params.compensate_bias, callback=self._on_change,
                    )
                    dpg.add_button(label="Resample noise", width=-1, callback=lambda: self._resample())
                    dpg.add_separator()
                    dpg.add_combo(
                        tag="profile", label="Motion", items=list(PROFILE_LABELS.keys()),
                        default_value=LABEL_FOR_PROFILE[self.params.profile], callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="rate", label="Rate amp (°/s)", default_value=self.params.rate_dps,
                        min_value=-90.0, max_value=90.0, callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="bias", label="Bias (°/s)", default_value=self.params.bias_dps,
                        min_value=-3.0, max_value=3.0, callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="arw", label="ARW (°/√s)", default_value=self.params.arw_deg_per_sqrt_s,
                        min_value=0.0, max_value=1.0, callback=self._on_change,
                    )
                    with dpg.group(tag="advanced_controls"):
                        dpg.add_separator()
                        dpg.add_text("Advanced")
                        dpg.add_slider_float(
                            tag="sine_hz", label="Sine Hz", default_value=self.params.sine_hz,
                            min_value=0.1, max_value=2.0, callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="duration", label="Duration (s)", default_value=self.params.duration_s,
                            min_value=2.0, max_value=30.0, callback=self._on_change,
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
            dpg.render_dearpygui_frame()
        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: GyroParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    GyroApp(initial=params, scenario_id=scenario_id).run()
