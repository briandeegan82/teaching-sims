"""Dear PyGui desktop app for FMCW radar teaching."""

from __future__ import annotations

import dearpygui.dearpygui as dpg
import numpy as np

from teaching_sims.topics.fmcw.physics import (
    FMCWParams,
    FMCWTarget,
    FMCWWaveform,
    process_fmcw,
)
from teaching_sims.topics.fmcw.scenarios import SCENARIOS, get_scenario


RD_ROWS = 64
RD_COLS = 200

WAVE_LABELS = {"Sawtooth": FMCWWaveform.SAWTOOTH, "Triangle": FMCWWaveform.TRIANGLE}
LABEL_FOR_WAVE = {v: k for k, v in WAVE_LABELS.items()}


def _fxy(xs, ys):
    return [[float(v) for v in xs], [float(v) for v in ys]]


def _db_to_heat(rd_db: np.ndarray) -> list[float]:
    floor = float(max(np.percentile(rd_db, 20), -25.0))
    floor = min(floor, -12.0)
    span = max(0.0 - floor, 1.0)
    x = np.clip((rd_db - floor) / span, 0.0, 1.0)
    x = np.power(x, 0.75)
    return [float(v) for v in x.ravel()]


class FMCWApp:
    def __init__(self, initial: FMCWParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or FMCWParams()
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
            self._title = "FMCW radar"
            self._note = "Dechirped IF tones, range FFT, sawtooth coupling, triangle decoupling, RD maps."

    def _read_controls(self) -> FMCWParams:
        targets = (
            FMCWTarget(
                float(dpg.get_value("r1_m")),
                float(dpg.get_value("v1_mps")),
                snr_db=float(dpg.get_value("snr1_db")),
            ),
        )
        if dpg.get_value("t2_on"):
            targets = (
                targets[0],
                FMCWTarget(
                    float(dpg.get_value("r2_m")),
                    float(dpg.get_value("v2_mps")),
                    snr_db=float(dpg.get_value("snr2_db")),
                ),
            )
        return FMCWParams(
            bandwidth_hz=float(dpg.get_value("bw_mhz")) * 1e6,
            chirp_time_s=float(dpg.get_value("t_chirp_us")) * 1e-6,
            n_chirps=int(dpg.get_value("n_chirps")),
            sample_rate_hz=float(dpg.get_value("fs_mhz")) * 1e6,
            center_freq_hz=float(dpg.get_value("fc_ghz")) * 1e9,
            waveform=WAVE_LABELS[dpg.get_value("waveform")],
            targets=targets,
            noise_enabled=bool(dpg.get_value("noise_on")),
            range_window=bool(dpg.get_value("range_win")),
            doppler_window=bool(dpg.get_value("doppler_win")),
            seed=self._seed,
        )

    def _push_controls(self, p: FMCWParams) -> None:
        dpg.set_value("waveform", LABEL_FOR_WAVE[p.waveform])
        dpg.set_value("bw_mhz", p.bandwidth_hz / 1e6)
        dpg.set_value("t_chirp_us", p.chirp_time_s * 1e6)
        dpg.set_value("n_chirps", p.n_chirps)
        dpg.set_value("fs_mhz", p.sample_rate_hz / 1e6)
        dpg.set_value("fc_ghz", p.center_freq_hz / 1e9)
        dpg.set_value("noise_on", p.noise_enabled)
        dpg.set_value("range_win", p.range_window)
        dpg.set_value("doppler_win", p.doppler_window)
        dpg.set_value("r1_m", p.targets[0].range_m)
        dpg.set_value("v1_mps", p.targets[0].velocity_mps)
        dpg.set_value("snr1_db", p.targets[0].snr_db)
        if len(p.targets) > 1:
            dpg.set_value("t2_on", True)
            dpg.set_value("r2_m", p.targets[1].range_m)
            dpg.set_value("v2_mps", p.targets[1].velocity_mps)
            dpg.set_value("snr2_db", p.targets[1].snr_db)
        else:
            dpg.set_value("t2_on", False)
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

    def _ann(self, tag: str, label: str, x: float, y: float, offset=(8, 10)) -> None:
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
        dpg.add_plot_annotation(
            label=label,
            default_value=(float(x), float(y)),
            offset=offset,
            tag=tag,
            parent="rd_plot",
        )
        self._annotation_tags.append(tag)

    def refresh(self) -> None:
        try:
            self.params = self._read_controls()
        except ValueError as exc:
            dpg.set_value("status_text", f"Invalid settings: {exc}")
            return

        p = self.params
        out = process_fmcw(p)

        fb = out["fb_axis_hz"] / 1e6
        dpg.set_value("if_spec", _fxy(fb, out["spectrum0_db"]))
        dpg.set_axis_limits("if_x", 0.0, float(fb[-1]) if len(fb) else 1.0)
        dpg.set_axis_limits("if_y", -40.0, 1.0)

        r = out["range_m"]
        dpg.set_value("range_prof", _fxy(r, out["range_profile_db"]))
        r_max = min(float(r[-1]), float(out["max_unambiguous_range_m"]) * 1.05)
        dpg.set_axis_limits("rp_x", 0.0, r_max)
        dpg.set_axis_limits("rp_y", -40.0, 1.0)

        # RD heatmap (rows=Doppler, cols=range) — interpolate to fixed grid
        rd = out["rd_db"]
        v = out["velocity_mps"]
        # rd cols match rfftfreq length = len(r)
        n_r = min(len(r), rd.shape[1])
        r = r[:n_r]
        rd = rd[:, :n_r]
        r_disp = np.linspace(float(r[0]), float(min(r[-1], r_max)), RD_COLS)
        v_disp = np.linspace(float(v[0]), float(v[-1]), RD_ROWS)
        tmp = np.empty((rd.shape[0], RD_COLS), dtype=float)
        for i in range(rd.shape[0]):
            tmp[i] = np.interp(r_disp, r, rd[i])
        rd_disp = np.empty((RD_ROWS, RD_COLS), dtype=float)
        for j in range(RD_COLS):
            rd_disp[:, j] = np.interp(v_disp, v, tmp[:, j])

        dpg.configure_item(
            "rd_heat",
            bounds_min=(float(r_disp[0]), float(v_disp[0])),
            bounds_max=(float(r_disp[-1]), float(v_disp[-1])),
        )
        dpg.set_axis_limits("rd_x", float(r_disp[0]), float(r_disp[-1]))
        dpg.set_axis_limits("rd_y", float(v_disp[0]), float(v_disp[-1]))
        dpg.set_value("rd_heat", [_db_to_heat(rd_disp)])
        dpg.set_value(
            "zero_doppler",
            [[float(r_disp[0]), float(r_disp[-1])], [0.0, 0.0]],
        )

        self._clear_annotations()
        for i, tgt in enumerate(p.targets):
            self._ann(
                f"ann_t{i}",
                f"T{i+1} {tgt.range_m:.1f} m, {tgt.velocity_mps:.1f} m/s",
                tgt.range_m,
                tgt.velocity_mps,
                (8, -14 if i == 0 else 12),
            )

        extra = ""
        if out["sawtooth_bias"] is not None and p.waveform == FMCWWaveform.SAWTOOTH:
            sb = out["sawtooth_bias"]
            extra += (
                f"\nSawtooth beat→range: {sb['range_from_beat_m']:.2f} m "
                f"(true {sb['true_range_m']:.2f} m, v={sb['true_velocity_mps']:.1f} m/s)"
            )
        if out["triangle"] is not None and p.waveform == FMCWWaveform.TRIANGLE:
            tr = out["triangle"]
            extra += (
                f"\nTriangle solve: R≈{tr['range_m']:.2f} m, v≈{tr['velocity_mps']:.2f} m/s "
                f"(fb↑={tr['fb_up_hz']/1e3:.1f} kHz, fb↓={tr['fb_down_hz']/1e3:.1f} kHz)"
            )

        dpg.set_value(
            "status_text",
            (
                f"{LABEL_FOR_WAVE[p.waveform]}   B={p.bandwidth_hz/1e6:.0f} MHz   "
                f"T={p.chirp_time_s*1e6:.1f} µs   N={p.n_chirps}   fc={p.center_freq_hz/1e9:.1f} GHz\n"
                f"ΔR≈{out['range_resolution_m']:.2f} m   R_max≈{out['max_unambiguous_range_m']:.1f} m   "
                f"Δv≈{out['velocity_resolution_mps']:.2f} m/s   "
                f"v_unamb≈±{out['unambiguous_velocity_mps']:.1f} m/s"
                f"{extra}"
            ),
        )
        dpg.set_value("banner_title", self._title)
        dpg.set_value("banner_body", self._note)

    def _on_change(self, *_a, **_k) -> None:
        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims — FMCW Radar", width=1480, height=960)

        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.window(tag="primary", label="FMCW"):
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
                        tag="bw_mhz",
                        label="Bandwidth B (MHz)",
                        default_value=self.params.bandwidth_hz / 1e6,
                        min_value=50.0,
                        max_value=400.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="t_chirp_us",
                        label="Chirp time T (µs)",
                        default_value=self.params.chirp_time_s * 1e6,
                        min_value=10.0,
                        max_value=100.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="r1_m",
                        label="Target 1 range (m)",
                        default_value=self.params.targets[0].range_m,
                        min_value=5.0,
                        max_value=200.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="v1_mps",
                        label="Target 1 velocity (m/s)",
                        default_value=self.params.targets[0].velocity_mps,
                        min_value=-40.0,
                        max_value=40.0,
                        callback=self._on_change,
                    )
                    dpg.add_checkbox(
                        tag="t2_on",
                        label="Enable target 2",
                        default_value=len(self.params.targets) > 1,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="r2_m",
                        label="Target 2 range (m)",
                        default_value=self.params.targets[1].range_m if len(self.params.targets) > 1 else 80.0,
                        min_value=5.0,
                        max_value=200.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="v2_mps",
                        label="Target 2 velocity (m/s)",
                        default_value=self.params.targets[1].velocity_mps if len(self.params.targets) > 1 else -10.0,
                        min_value=-40.0,
                        max_value=40.0,
                        callback=self._on_change,
                    )

                    with dpg.group(tag="advanced_controls"):
                        dpg.add_separator()
                        dpg.add_text("Advanced")
                        dpg.add_slider_int(
                            tag="n_chirps",
                            label="Chirps in CPI",
                            default_value=self.params.n_chirps,
                            min_value=8,
                            max_value=128,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="fs_mhz",
                            label="IF sample rate (MHz)",
                            default_value=self.params.sample_rate_hz / 1e6,
                            min_value=1.0,
                            max_value=20.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="fc_ghz",
                            label="Center freq (GHz)",
                            default_value=self.params.center_freq_hz / 1e9,
                            min_value=24.0,
                            max_value=79.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="snr1_db",
                            label="Target 1 SNR (dB)",
                            default_value=self.params.targets[0].snr_db,
                            min_value=5.0,
                            max_value=40.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="snr2_db",
                            label="Target 2 SNR (dB)",
                            default_value=self.params.targets[1].snr_db if len(self.params.targets) > 1 else 22.0,
                            min_value=5.0,
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
                            tag="range_win",
                            label="Hann range window",
                            default_value=self.params.range_window,
                            callback=self._on_change,
                        )
                        dpg.add_checkbox(
                            tag="doppler_win",
                            label="Hann Doppler window",
                            default_value=self.params.doppler_window,
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
                    with dpg.group(horizontal=True):
                        with dpg.plot(label="IF spectrum (first chirp)", height=260, width=560):
                            dpg.add_plot_axis(dpg.mvXAxis, label="beat freq (MHz)", tag="if_x")
                            with dpg.plot_axis(dpg.mvYAxis, label="dB", tag="if_y"):
                                dpg.add_line_series([0.0], [0.0], label="|IF|", tag="if_spec")

                        with dpg.plot(label="Range profile", height=260, width=-1):
                            dpg.add_plot_axis(dpg.mvXAxis, label="range (m)", tag="rp_x")
                            with dpg.plot_axis(dpg.mvYAxis, label="dB", tag="rp_y"):
                                dpg.add_line_series([0.0], [0.0], label="profile", tag="range_prof")

                    with dpg.plot(
                        label="FMCW range–Doppler map",
                        height=420,
                        width=-1,
                        tag="rd_plot",
                    ):
                        dpg.add_plot_axis(dpg.mvXAxis, label="range (m)", tag="rd_x")
                        with dpg.plot_axis(dpg.mvYAxis, label="velocity (m/s)", tag="rd_y"):
                            dpg.add_heat_series(
                                [0.05] * (RD_ROWS * RD_COLS),
                                RD_ROWS,
                                RD_COLS,
                                scale_min=0.0,
                                scale_max=1.0,
                                bounds_min=(0.0, -40.0),
                                bounds_max=(150.0, 40.0),
                                tag="rd_heat",
                            )
                            dpg.add_line_series(
                                [0.0, 100.0], [0.0, 0.0], label="v=0", tag="zero_doppler"
                            )

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        self._push_controls(self.params)
        self.refresh()

        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()

        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: FMCWParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    FMCWApp(initial=params, scenario_id=scenario_id).run()
