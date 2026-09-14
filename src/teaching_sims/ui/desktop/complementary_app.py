"""Dear PyGui desktop app for complementary-filter teaching."""

from __future__ import annotations

import dearpygui.dearpygui as dpg

from teaching_sims.topics.complementary.physics import ComplementaryParams, PitchMotion, process
from teaching_sims.topics.complementary.scenarios import SCENARIOS, get_scenario
from teaching_sims.ui.desktop.plot_utils import fit_axes, fxy as _fxy


MOTION_LABELS = {
    "Sine": PitchMotion.SINE,
    "Ramp": PitchMotion.RAMP,
    "Step": PitchMotion.STEP,
}
LABEL_FOR_MOTION = {v: k for k, v in MOTION_LABELS.items()}


class ComplementaryApp:
    def __init__(self, initial: ComplementaryParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or ComplementaryParams()
        self.scenario_id = scenario_id
        self._presenter = False
        self._seed = self.params.seed
        if scenario_id:
            sc = get_scenario(scenario_id)
            self.params = sc.params
            self._title = sc.title
            self._note = f"{sc.teaching_point}\n{sc.notes}"
        else:
            self._title = "Complementary filter (pitch)"
            self._note = "Fuse gyro (short-term) with accelerometer tilt (long-term)."

    def _read_controls(self) -> ComplementaryParams:
        return ComplementaryParams(
            motion=MOTION_LABELS[dpg.get_value("motion")],
            amp_deg=float(dpg.get_value("amp")),
            sine_hz=float(dpg.get_value("sine_hz")),
            duration_s=float(dpg.get_value("duration")),
            alpha=float(dpg.get_value("alpha")),
            gyro_bias_dps=float(dpg.get_value("gyro_bias")),
            gyro_noise_dps=float(dpg.get_value("gyro_noise")),
            accel_noise_mps2=float(dpg.get_value("accel_noise")),
            surge_mps2=float(dpg.get_value("surge")),
            seed=self._seed,
        )

    def _push_controls(self, p: ComplementaryParams) -> None:
        dpg.set_value("motion", LABEL_FOR_MOTION[p.motion])
        dpg.set_value("amp", p.amp_deg)
        dpg.set_value("sine_hz", p.sine_hz)
        dpg.set_value("duration", p.duration_s)
        dpg.set_value("alpha", p.alpha)
        dpg.set_value("gyro_bias", p.gyro_bias_dps)
        dpg.set_value("gyro_noise", p.gyro_noise_dps)
        dpg.set_value("accel_noise", p.accel_noise_mps2)
        dpg.set_value("surge", p.surge_mps2)
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
        dpg.set_value("true_series", _fxy(t, out["pitch_true_deg"]))
        dpg.set_value("gyro_series", _fxy(t, out["gyro_only_deg"]))
        dpg.set_value("accel_series", _fxy(t, out["accel_tilt_deg"]))
        dpg.set_value("comp_series", _fxy(t, out["comp_deg"]))
        dpg.set_value("err_gyro", _fxy(t, out["err_gyro_deg"]))
        dpg.set_value("err_accel", _fxy(t, out["err_accel_deg"]))
        dpg.set_value("err_comp", _fxy(t, out["err_comp_deg"]))
        fit_axes("pitch_t", "pitch_y", "err_t", "err_y")
        dpg.set_value(
            "status_text",
            (
                f"α={self.params.alpha:.3f}\n"
                f"RMS error (°): gyro {out['rms_gyro_deg']:.2f}  "
                f"accel {out['rms_accel_deg']:.2f}  comp {out['rms_comp_deg']:.2f}"
            ),
        )

    def _on_change(self, *_a, **_k) -> None:
        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims — Complementary Filter", width=1480, height=920)
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.window(tag="primary", label="Complementary"):
            with dpg.child_window(tag="banner_panel", height=72, border=True):
                dpg.add_text(self._title, tag="banner_title")
                dpg.add_text(self._note, tag="banner_body", wrap=1000)
            with dpg.group(horizontal=True):
                with dpg.child_window(width=350, border=True):
                    dpg.add_checkbox(
                        tag="presenter_mode", label="Presenter mode (hide advanced)",
                        default_value=False, callback=self._set_presenter,
                    )
                    dpg.add_button(label="Resample noise", width=-1, callback=lambda: self._resample())
                    dpg.add_separator()
                    dpg.add_combo(
                        tag="motion", label="Motion", items=list(MOTION_LABELS.keys()),
                        default_value=LABEL_FOR_MOTION[self.params.motion], callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="alpha", label="α (gyro weight)", default_value=self.params.alpha,
                        min_value=0.0, max_value=1.0, callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="amp", label="Pitch amp (deg)", default_value=self.params.amp_deg,
                        min_value=5.0, max_value=60.0, callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="gyro_bias", label="Gyro bias (°/s)", default_value=self.params.gyro_bias_dps,
                        min_value=-3.0, max_value=3.0, callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="surge", label="Surge (m/s²)", default_value=self.params.surge_mps2,
                        min_value=-5.0, max_value=5.0, callback=self._on_change,
                    )
                    with dpg.group(tag="advanced_controls"):
                        dpg.add_separator()
                        dpg.add_text("Advanced")
                        dpg.add_slider_float(
                            tag="sine_hz", label="Sine Hz", default_value=self.params.sine_hz,
                            min_value=0.05, max_value=1.0, callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="duration", label="Duration (s)", default_value=self.params.duration_s,
                            min_value=4.0, max_value=30.0, callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="gyro_noise", label="Gyro noise (°/s)", default_value=self.params.gyro_noise_dps,
                            min_value=0.0, max_value=2.0, callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="accel_noise", label="Accel noise (m/s²)",
                            default_value=self.params.accel_noise_mps2,
                            min_value=0.0, max_value=1.0, callback=self._on_change,
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
                    with dpg.plot(label="Pitch estimates", height=400, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="t (s)", tag="pitch_t")
                        with dpg.plot_axis(dpg.mvYAxis, label="deg", tag="pitch_y"):
                            dpg.add_line_series([0.0], [0.0], label="true", tag="true_series")
                            dpg.add_line_series([0.0], [0.0], label="gyro only", tag="gyro_series")
                            dpg.add_line_series([0.0], [0.0], label="accel tilt", tag="accel_series")
                            dpg.add_line_series([0.0], [0.0], label="complementary", tag="comp_series")
                    with dpg.plot(label="Pitch error", height=340, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="t (s)", tag="err_t")
                        with dpg.plot_axis(dpg.mvYAxis, label="deg", tag="err_y"):
                            dpg.add_line_series([0.0], [0.0], label="gyro err", tag="err_gyro")
                            dpg.add_line_series([0.0], [0.0], label="accel err", tag="err_accel")
                            dpg.add_line_series([0.0], [0.0], label="comp err", tag="err_comp")

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        self._push_controls(self.params)
        self.refresh()
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()
        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: ComplementaryParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    ComplementaryApp(initial=params, scenario_id=scenario_id).run()
