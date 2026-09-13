"""Dear PyGui desktop app for pulsed radar ranging."""

from __future__ import annotations

import dearpygui.dearpygui as dpg
import numpy as np

from teaching_sims.topics.pulsed_ranging.physics import (
    PulseRadarParams,
    Target,
    WaveformType,
    detect_peaks,
    process_video,
)
from teaching_sims.topics.pulsed_ranging.scenarios import SCENARIOS, get_scenario


WAVE_LABELS = {"Rect pulse": WaveformType.RECT, "LFM chirp": WaveformType.LFM}
LABEL_FOR_WAVE = {v: k for k, v in WAVE_LABELS.items()}


def _fxy(xs, ys):
    return [[float(v) for v in xs], [float(v) for v in ys]]


class PulsedRangingApp:
    def __init__(self, initial: PulseRadarParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or PulseRadarParams()
        self.scenario_id = scenario_id
        self._presenter = False
        self._seed = self.params.seed
        self._annotation_tags: list[str] = []
        if scenario_id:
            sc = get_scenario(scenario_id)
            self.params = sc.params
            self._title = sc.title
            self._note = f"{sc.teaching_point}\n{sc.notes}"
        else:
            self._title = "Pulsed radar ranging"
            self._note = "Delay ↔ range, resolution, pulse compression, and PRI ambiguity."

    def _read_controls(self) -> PulseRadarParams:
        wave = WAVE_LABELS[dpg.get_value("waveform")]
        targets = (
            Target(float(dpg.get_value("r1_m")), snr_db=float(dpg.get_value("snr1_db"))),
        )
        if dpg.get_value("target2_on"):
            targets = (
                targets[0],
                Target(float(dpg.get_value("r2_m")), snr_db=float(dpg.get_value("snr2_db"))),
            )
        tp = float(dpg.get_value("tp_us")) * 1e-6
        pri = float(dpg.get_value("pri_us")) * 1e-6
        if pri <= tp * 1.05:
            pri = tp * 2.0
            dpg.set_value("pri_us", pri * 1e6)
        return PulseRadarParams(
            waveform=wave,
            pulse_width_s=tp,
            bandwidth_hz=float(dpg.get_value("bw_mhz")) * 1e6,
            pri_s=pri,
            sample_rate_hz=float(dpg.get_value("fs_mhz")) * 1e6,
            targets=targets,
            noise_enabled=bool(dpg.get_value("noise_on")),
            matched_filter=bool(dpg.get_value("mf_on")),
            window_hann=bool(dpg.get_value("hann_on")),
            seed=self._seed,
        )

    def _push_controls(self, p: PulseRadarParams) -> None:
        dpg.set_value("waveform", LABEL_FOR_WAVE[p.waveform])
        dpg.set_value("tp_us", p.pulse_width_s * 1e6)
        dpg.set_value("bw_mhz", p.bandwidth_hz / 1e6)
        dpg.set_value("pri_us", p.pri_s * 1e6)
        dpg.set_value("fs_mhz", p.sample_rate_hz / 1e6)
        dpg.set_value("mf_on", p.matched_filter)
        dpg.set_value("noise_on", p.noise_enabled)
        dpg.set_value("hann_on", p.window_hann)
        dpg.set_value("r1_m", p.targets[0].range_m)
        dpg.set_value("snr1_db", p.targets[0].snr_db)
        if len(p.targets) > 1:
            dpg.set_value("target2_on", True)
            dpg.set_value("r2_m", p.targets[1].range_m)
            dpg.set_value("snr2_db", p.targets[1].snr_db)
        else:
            dpg.set_value("target2_on", False)
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
        self.refresh()

    def _resample(self) -> None:
        self._seed += 1
        self.refresh()

    def _clear_annotations(self) -> None:
        for tag in self._annotation_tags:
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)
        self._annotation_tags.clear()

    def _ann(self, tag: str, label: str, x: float, y: float, offset=(10, 10)) -> None:
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
        dpg.add_plot_annotation(
            label=label,
            default_value=(float(x), float(y)),
            offset=offset,
            tag=tag,
            parent="range_plot",
        )
        self._annotation_tags.append(tag)

    def refresh(self) -> None:
        self.params = self._read_controls()
        p = self.params
        out = process_video(p)

        t_tx = out["t_tx_s"] * 1e6
        tx_i = np.real(out["tx"])
        tx_q = np.imag(out["tx"])
        dpg.set_value("tx_i", _fxy(t_tx, tx_i))
        dpg.set_value("tx_q", _fxy(t_tx, tx_q))
        dpg.set_axis_limits("tx_x", 0.0, max(float(t_tx[-1]) if len(t_tx) else 1.0, 0.1))
        amp = max(float(np.max(np.abs(out["tx"]))), 1e-6)
        dpg.set_axis_limits("tx_y", -1.15 * amp, 1.15 * amp)

        r = out["range_m"] / 1e3  # km
        env = out["envelope"]
        env_n = env / (float(np.max(env)) + 1e-30)
        dpg.set_value("range_series", _fxy(r, env_n))

        # Raw |rx| for comparison (always computed)
        raw = np.abs(out["rx"])
        raw_n = raw / (float(np.max(raw)) + 1e-30)
        dpg.set_value("raw_series", _fxy(r, raw_n))
        dpg.configure_item("raw_series", show=bool(dpg.get_value("show_raw")))

        r_max = float(r[-1]) if len(r) else 1.0
        dpg.set_axis_limits("range_x", 0.0, r_max)
        dpg.set_axis_limits("range_y", -0.05, 1.15)

        # Resolution bar around first target
        dr_km = float(out["range_resolution_m"]) / 1e3
        r0 = p.targets[0].range_m / 1e3
        dpg.set_value(
            "res_band",
            [[r0 - 0.5 * dr_km, r0 + 0.5 * dr_km, r0 + 0.5 * dr_km, r0 - 0.5 * dr_km],
             [0.0, 0.0, 1.05, 1.05]],
        )

        # True target markers
        self._clear_annotations()
        for i, tr in enumerate(p.targets):
            # Apparent range after PRI fold
            r_unamb = float(out["max_unambiguous_range_m"])
            apparent = tr.range_m % r_unamb
            x = apparent / 1e3
            y = float(np.interp(x, r, env_n)) if len(r) else 0.5
            dpg.set_value(
                f"tgt_marker_{i}",
                [[x, x], [0.0, 1.05]],
            )
            dpg.configure_item(f"tgt_marker_{i}", show=True)
            label = f"T{i+1} true {tr.range_m/1e3:.2f} km"
            if abs(apparent - tr.range_m) > 1.0:
                label += f" → {apparent/1e3:.2f} km"
            self._ann(f"ann_t{i}", label, x, max(y, 0.2), (8, -14 if i == 0 else 12))

        for i in range(len(p.targets), 2):
            dpg.configure_item(f"tgt_marker_{i}", show=False)

        peaks_r, peaks_a = detect_peaks(env, out["range_m"])
        if len(peaks_r):
            dpg.set_value(
                "peak_scatter",
                _fxy(peaks_r / 1e3, peaks_a / (float(np.max(env)) + 1e-30)),
            )
            dpg.configure_item("peak_scatter", show=True)
        else:
            dpg.configure_item("peak_scatter", show=False)

        # Spectro-ish: instantaneous freq of TX for LFM teaching
        if p.waveform == WaveformType.LFM and len(out["tx"]) > 4:
            ph = np.unwrap(np.angle(out["tx"]))
            # fd ≈ (1/2π) dφ/dt
            fi = np.diff(ph) * p.sample_rate_hz / (2.0 * np.pi)
            ti = out["t_tx_s"][:-1] * 1e6
            dpg.set_value("inst_freq", _fxy(ti, fi / 1e6))
            dpg.configure_item("inst_freq_plot", show=True)
            dpg.set_axis_limits("if_x", 0.0, float(ti[-1]) if len(ti) else 1.0)
            dpg.set_axis_limits(
                "if_y",
                float(np.min(fi) / 1e6) - 0.5,
                float(np.max(fi) / 1e6) + 0.5,
            )
        else:
            dpg.configure_item("inst_freq_plot", show=False)

        mf = "ON" if p.matched_filter else "OFF"
        dpg.set_value(
            "status_text",
            (
                f"Waveform: {LABEL_FOR_WAVE[p.waveform]}   Tp={p.pulse_width_s*1e6:.2f} µs   "
                f"B={p.bandwidth_hz/1e6:.1f} MHz   PRI={p.pri_s*1e6:.1f} µs\n"
                f"ΔR ≈ {out['range_resolution_m']:.1f} m    "
                f"R_unamb ≈ {out['max_unambiguous_range_m']/1e3:.2f} km    "
                f"Matched filter: {mf}"
            ),
        )
        dpg.set_value("banner_title", self._title)
        dpg.set_value("banner_body", self._note)

    def _on_change(self, *_a, **_k) -> None:
        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims — Pulsed Radar Ranging", width=1480, height=960)

        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.theme() as raw_theme:
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, (160, 160, 170), category=dpg.mvThemeCat_Plots)
        with dpg.theme() as peak_theme:
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, (255, 200, 60), category=dpg.mvThemeCat_Plots)

        with dpg.window(tag="primary", label="Pulsed ranging"):
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
                        tag="show_raw",
                        label="Overlay raw |rx| (pre-MF)",
                        default_value=False,
                        callback=self._on_change,
                    )
                    dpg.add_button(label="Resample noise", width=-1, callback=lambda: self._resample())
                    dpg.add_separator()
                    dpg.add_text("Core")
                    dpg.add_combo(
                        tag="waveform",
                        label="Waveform",
                        items=list(WAVE_LABELS.keys()),
                        default_value=LABEL_FOR_WAVE[self.params.waveform],
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="tp_us",
                        label="Pulse width Tp (µs)",
                        default_value=self.params.pulse_width_s * 1e6,
                        min_value=0.2,
                        max_value=40.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="r1_m",
                        label="Target 1 range (m)",
                        default_value=self.params.targets[0].range_m,
                        min_value=100.0,
                        max_value=20000.0,
                        callback=self._on_change,
                    )
                    dpg.add_checkbox(
                        tag="target2_on",
                        label="Enable target 2",
                        default_value=len(self.params.targets) > 1,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="r2_m",
                        label="Target 2 range (m)",
                        default_value=(
                            self.params.targets[1].range_m if len(self.params.targets) > 1 else 2500.0
                        ),
                        min_value=100.0,
                        max_value=20000.0,
                        callback=self._on_change,
                    )
                    dpg.add_checkbox(
                        tag="mf_on",
                        label="Matched filter",
                        default_value=self.params.matched_filter,
                        callback=self._on_change,
                    )

                    with dpg.group(tag="advanced_controls"):
                        dpg.add_separator()
                        dpg.add_text("Advanced")
                        dpg.add_slider_float(
                            tag="bw_mhz",
                            label="LFM bandwidth B (MHz)",
                            default_value=self.params.bandwidth_hz / 1e6,
                            min_value=1.0,
                            max_value=40.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="pri_us",
                            label="PRI (µs)",
                            default_value=self.params.pri_s * 1e6,
                            min_value=20.0,
                            max_value=400.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="fs_mhz",
                            label="Sample rate (MHz)",
                            default_value=self.params.sample_rate_hz / 1e6,
                            min_value=10.0,
                            max_value=100.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="snr1_db",
                            label="Target 1 SNR (dB)",
                            default_value=self.params.targets[0].snr_db,
                            min_value=0.0,
                            max_value=40.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="snr2_db",
                            label="Target 2 SNR (dB)",
                            default_value=(
                                self.params.targets[1].snr_db if len(self.params.targets) > 1 else 25.0
                            ),
                            min_value=0.0,
                            max_value=40.0,
                            callback=self._on_change,
                        )
                        dpg.add_checkbox(
                            tag="noise_on",
                            label="Noise",
                            default_value=self.params.noise_enabled,
                            callback=self._on_change,
                        )
                        dpg.add_checkbox(
                            tag="hann_on",
                            label="Hann window on TX",
                            default_value=self.params.window_hann,
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
                    with dpg.plot(label="Range profile (normalised envelope)", height=360, width=-1, tag="range_plot"):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="range (km)", tag="range_x")
                        with dpg.plot_axis(dpg.mvYAxis, label="amplitude", tag="range_y"):
                            dpg.add_line_series([0.0], [0.0], label="video", tag="range_series")
                            raw = dpg.add_line_series(
                                [0.0], [0.0], label="raw |rx|", tag="raw_series", show=False
                            )
                            dpg.bind_item_theme(raw, raw_theme)
                            dpg.add_line_series([0, 0], [0, 1], label="T1", tag="tgt_marker_0")
                            dpg.add_line_series([0, 0], [0, 1], label="T2", tag="tgt_marker_1", show=False)
                            # resolution band as a faint closed loop
                            dpg.add_line_series(
                                [0, 0.1, 0.1, 0],
                                [0, 0, 1, 1],
                                label="ΔR about T1",
                                tag="res_band",
                            )
                            pk = dpg.add_scatter_series([0.0], [0.0], label="peaks", tag="peak_scatter")
                            dpg.bind_item_theme(pk, peak_theme)

                    with dpg.group(horizontal=True):
                        with dpg.plot(label="TX baseband (I/Q)", height=280, width=700):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label="t (µs)", tag="tx_x")
                            with dpg.plot_axis(dpg.mvYAxis, label="amp", tag="tx_y"):
                                dpg.add_line_series([0.0], [0.0], label="I", tag="tx_i")
                                dpg.add_line_series([0.0], [0.0], label="Q", tag="tx_q")

                        with dpg.plot(
                            label="LFM instantaneous freq (MHz)",
                            height=280,
                            width=-1,
                            tag="inst_freq_plot",
                            show=False,
                        ):
                            dpg.add_plot_axis(dpg.mvXAxis, label="t (µs)", tag="if_x")
                            with dpg.plot_axis(dpg.mvYAxis, label="f (MHz)", tag="if_y"):
                                dpg.add_line_series([0.0], [0.0], label="f_i(t)", tag="inst_freq")

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        self._push_controls(self.params)
        self.refresh()

        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()

        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: PulseRadarParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    PulsedRangingApp(initial=params, scenario_id=scenario_id).run()
