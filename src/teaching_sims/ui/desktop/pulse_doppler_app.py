"""Dear PyGui desktop app for pulse-Doppler / MTI teaching."""

from __future__ import annotations

import dearpygui.dearpygui as dpg
import numpy as np

from teaching_sims.topics.pulse_doppler.physics import (
    MovingTarget,
    PulseDopplerParams,
    apparent_velocity_mps,
    range_doppler_map,
)
from teaching_sims.topics.pulse_doppler.scenarios import SCENARIOS, get_scenario


RD_ROWS = 64   # Doppler display bins
RD_COLS = 220  # Range display bins


def _fxy(xs, ys):
    return [[float(v) for v in xs], [float(v) for v in ys]]


def _db_to_heat(rd_db: np.ndarray, floor_db: float | None = None) -> list[float]:
    """Map dB image to 0..1 for Dear PyGui.

    Uses a high floor so noise does not look like texture; peaks and the
    clutter ridge remain visible.
    """
    if floor_db is None:
        # Keep ~25 dB of dynamic range under the peak (peak is 0 dB).
        floor_db = float(max(np.percentile(rd_db, 20), -25.0))
        floor_db = min(floor_db, -12.0)
    span = max(0.0 - floor_db, 1.0)
    x = (rd_db - floor_db) / span
    x = np.clip(x, 0.0, 1.0)
    # Gamma lift so mid sidelobes stay visible without washing out the peak.
    x = np.power(x, 0.75)
    return [float(v) for v in x.ravel()]


class PulseDopplerApp:
    def __init__(self, initial: PulseDopplerParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or PulseDopplerParams()
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
            self._title = "Pulse-Doppler / MTI"
            self._note = "Range–Doppler maps, clutter, two-pulse MTI, and PRF velocity ambiguity."

    def _read_controls(self) -> PulseDopplerParams:
        targets = (
            MovingTarget(
                float(dpg.get_value("r1_m")),
                float(dpg.get_value("v1_mps")),
                snr_db=float(dpg.get_value("snr1_db")),
            ),
        )
        if dpg.get_value("target2_on"):
            targets = (
                targets[0],
                MovingTarget(
                    float(dpg.get_value("r2_m")),
                    float(dpg.get_value("v2_mps")),
                    snr_db=float(dpg.get_value("snr2_db")),
                ),
            )
        return PulseDopplerParams(
            n_pulses=int(dpg.get_value("n_pulses")),
            pri_s=float(dpg.get_value("pri_us")) * 1e-6,
            frequency_hz=float(dpg.get_value("freq_ghz")) * 1e9,
            bandwidth_hz=float(dpg.get_value("bw_mhz")) * 1e6,
            sample_rate_hz=float(dpg.get_value("fs_mhz")) * 1e6,
            targets=targets,
            clutter_enabled=bool(dpg.get_value("clutter_on")),
            clutter_cnr_db=float(dpg.get_value("cnr_db")),
            clutter_width_mps=float(dpg.get_value("clutter_width")),
            noise_enabled=bool(dpg.get_value("noise_on")),
            mti_canceller=bool(dpg.get_value("mti_on")),
            doppler_window=bool(dpg.get_value("hann_on")),
            seed=self._seed,
        )

    def _push_controls(self, p: PulseDopplerParams) -> None:
        dpg.set_value("n_pulses", p.n_pulses)
        dpg.set_value("pri_us", p.pri_s * 1e6)
        dpg.set_value("freq_ghz", p.frequency_hz / 1e9)
        dpg.set_value("bw_mhz", p.bandwidth_hz / 1e6)
        dpg.set_value("fs_mhz", p.sample_rate_hz / 1e6)
        dpg.set_value("clutter_on", p.clutter_enabled)
        dpg.set_value("cnr_db", p.clutter_cnr_db)
        dpg.set_value("clutter_width", p.clutter_width_mps)
        dpg.set_value("noise_on", p.noise_enabled)
        dpg.set_value("mti_on", p.mti_canceller)
        dpg.set_value("hann_on", p.doppler_window)
        if p.targets:
            dpg.set_value("r1_m", p.targets[0].range_m)
            dpg.set_value("v1_mps", p.targets[0].velocity_mps)
            dpg.set_value("snr1_db", p.targets[0].snr_db)
        if len(p.targets) > 1:
            dpg.set_value("target2_on", True)
            dpg.set_value("r2_m", p.targets[1].range_m)
            dpg.set_value("v2_mps", p.targets[1].velocity_mps)
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
            parent="rd_plot",
        )
        self._annotation_tags.append(tag)

    def refresh(self) -> None:
        self.params = self._read_controls()
        p = self.params
        out = range_doppler_map(p)
        r = out["range_m"]
        v = out["velocity_mps"]
        rd = out["rd_db"]

        # Interpolate onto fixed display grid for stable heat series
        r_disp = np.linspace(float(r[0]), float(r[-1]), RD_COLS)
        v_disp = np.linspace(float(v[0]), float(v[-1]), RD_ROWS)
        # rd rows = Doppler, cols = range
        # np.interp only 1D — do separable interp
        tmp = np.empty((rd.shape[0], RD_COLS), dtype=float)
        for i in range(rd.shape[0]):
            tmp[i] = np.interp(r_disp, r, rd[i])
        rd_disp = np.empty((RD_ROWS, RD_COLS), dtype=float)
        for j in range(RD_COLS):
            rd_disp[:, j] = np.interp(v_disp, v, tmp[:, j])

        dpg.configure_item(
            "rd_heat",
            bounds_min=(float(r_disp[0]) / 1e3, float(v_disp[0])),
            bounds_max=(float(r_disp[-1]) / 1e3, float(v_disp[-1])),
        )
        dpg.set_axis_limits("rd_x", float(r_disp[0]) / 1e3, float(r_disp[-1]) / 1e3)
        dpg.set_axis_limits("rd_y", float(v_disp[0]), float(v_disp[-1]))
        dpg.set_value("rd_heat", [_db_to_heat(rd_disp)])

        # Zero-Doppler guide
        dpg.set_value(
            "zero_doppler",
            [[float(r_disp[0]) / 1e3, float(r_disp[-1]) / 1e3], [0.0, 0.0]],
        )

        # Doppler cut at target-1 range
        r_cut = p.targets[0].range_m if p.targets else float(r[len(r) // 2])
        i_r = int(np.argmin(np.abs(r - r_cut)))
        dpg.set_value("doppler_cut", _fxy(v, rd[:, i_r]))
        dpg.set_axis_limits("dop_x", float(v[0]), float(v[-1]))
        dpg.set_axis_limits("dop_y", -40.0, 1.0)

        # Range cut at target-1 apparent velocity
        if p.targets:
            v_cut = apparent_velocity_mps(p.targets[0].velocity_mps, p)
        else:
            v_cut = 0.0
        i_v = int(np.argmin(np.abs(v - v_cut)))
        dpg.set_value("range_cut", _fxy(r / 1e3, rd[i_v, :]))
        dpg.set_axis_limits("rng_x", float(r[0]) / 1e3, float(r[-1]) / 1e3)
        dpg.set_axis_limits("rng_y", -40.0, 1.0)

        self._clear_annotations()
        for i, tgt in enumerate(p.targets):
            r_app = tgt.range_m % p.unambiguous_range_m
            v_app = apparent_velocity_mps(tgt.velocity_mps, p)
            self._ann(
                f"ann_t{i}",
                f"T{i+1} {tgt.range_m/1e3:.2f} km, {tgt.velocity_mps:.0f} m/s"
                + (f" → {v_app:.0f} m/s" if abs(v_app - tgt.velocity_mps) > 1 else ""),
                r_app / 1e3,
                v_app,
                (8, -14 if i == 0 else 12),
            )

        mti = "ON" if p.mti_canceller else "OFF"
        dpg.set_value(
            "status_text",
            (
                f"PRF={p.prf_hz:.0f} Hz   N={p.n_pulses}   f={p.frequency_hz/1e9:.1f} GHz   MTI={mti}\n"
                f"ΔR≈{out['range_resolution_m']:.1f} m   Δv≈{out['velocity_resolution_mps']:.2f} m/s\n"
                f"R_unamb≈{out['unambiguous_range_m']/1e3:.2f} km   "
                f"v_unamb≈±{out['unambiguous_velocity_mps']:.1f} m/s"
            ),
        )
        dpg.set_value("banner_title", self._title)
        dpg.set_value("banner_body", self._note)

    def _on_change(self, *_a, **_k) -> None:
        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims — Pulse-Doppler / MTI", width=1480, height=960)

        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.window(tag="primary", label="Pulse-Doppler"):
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
                        tag="mti_on",
                        label="Two-pulse MTI canceller",
                        default_value=self.params.mti_canceller,
                        callback=self._on_change,
                    )
                    dpg.add_button(label="Resample noise/clutter", width=-1, callback=lambda: self._resample())
                    dpg.add_separator()
                    dpg.add_text("Core")
                    dpg.add_slider_int(
                        tag="n_pulses",
                        label="Pulses in CPI (N)",
                        default_value=self.params.n_pulses,
                        min_value=8,
                        max_value=128,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="pri_us",
                        label="PRI (µs)",
                        default_value=self.params.pri_s * 1e6,
                        min_value=50.0,
                        max_value=400.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="r1_m",
                        label="Target 1 range (m)",
                        default_value=self.params.targets[0].range_m if self.params.targets else 3000.0,
                        min_value=500.0,
                        max_value=14000.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="v1_mps",
                        label="Target 1 velocity (m/s)",
                        default_value=self.params.targets[0].velocity_mps if self.params.targets else 30.0,
                        min_value=-150.0,
                        max_value=150.0,
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
                        default_value=self.params.targets[1].range_m if len(self.params.targets) > 1 else 3000.0,
                        min_value=500.0,
                        max_value=14000.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="v2_mps",
                        label="Target 2 velocity (m/s)",
                        default_value=self.params.targets[1].velocity_mps if len(self.params.targets) > 1 else -20.0,
                        min_value=-150.0,
                        max_value=150.0,
                        callback=self._on_change,
                    )
                    dpg.add_checkbox(
                        tag="clutter_on",
                        label="Ground clutter",
                        default_value=self.params.clutter_enabled,
                        callback=self._on_change,
                    )

                    with dpg.group(tag="advanced_controls"):
                        dpg.add_separator()
                        dpg.add_text("Advanced")
                        dpg.add_slider_float(
                            tag="freq_ghz",
                            label="RF freq (GHz)",
                            default_value=self.params.frequency_hz / 1e9,
                            min_value=1.0,
                            max_value=18.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="bw_mhz",
                            label="Bandwidth (MHz)",
                            default_value=self.params.bandwidth_hz / 1e6,
                            min_value=1.0,
                            max_value=20.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="fs_mhz",
                            label="Range sample rate (MHz)",
                            default_value=self.params.sample_rate_hz / 1e6,
                            min_value=5.0,
                            max_value=40.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="cnr_db",
                            label="Clutter CNR (dB)",
                            default_value=self.params.clutter_cnr_db,
                            min_value=0.0,
                            max_value=45.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="clutter_width",
                            label="Clutter σ_v (m/s)",
                            default_value=self.params.clutter_width_mps,
                            min_value=0.2,
                            max_value=8.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="snr1_db",
                            label="Target 1 SNR (dB)",
                            default_value=self.params.targets[0].snr_db if self.params.targets else 18.0,
                            min_value=0.0,
                            max_value=40.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="snr2_db",
                            label="Target 2 SNR (dB)",
                            default_value=self.params.targets[1].snr_db if len(self.params.targets) > 1 else 18.0,
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
                    with dpg.plot(
                        label="Range–Doppler map (dB, peak-norm.)",
                        height=420,
                        width=-1,
                        tag="rd_plot",
                    ):
                        dpg.add_plot_axis(dpg.mvXAxis, label="range (km)", tag="rd_x")
                        with dpg.plot_axis(dpg.mvYAxis, label="velocity (m/s)", tag="rd_y"):
                            dpg.add_heat_series(
                                [0.05] * (RD_ROWS * RD_COLS),
                                RD_ROWS,
                                RD_COLS,
                                scale_min=0.0,
                                scale_max=1.0,
                                bounds_min=(0.0, -50.0),
                                bounds_max=(15.0, 50.0),
                                tag="rd_heat",
                            )
                            dpg.add_line_series(
                                [0.0, 10.0],
                                [0.0, 0.0],
                                label="v=0",
                                tag="zero_doppler",
                            )

                    with dpg.group(horizontal=True):
                        with dpg.plot(label="Doppler cut at T1 range", height=280, width=560):
                            dpg.add_plot_axis(dpg.mvXAxis, label="velocity (m/s)", tag="dop_x")
                            with dpg.plot_axis(dpg.mvYAxis, label="dB", tag="dop_y"):
                                dpg.add_line_series([0.0], [0.0], label="cut", tag="doppler_cut")

                        with dpg.plot(label="Range cut at T1 apparent velocity", height=280, width=-1):
                            dpg.add_plot_axis(dpg.mvXAxis, label="range (km)", tag="rng_x")
                            with dpg.plot_axis(dpg.mvYAxis, label="dB", tag="rng_y"):
                                dpg.add_line_series([0.0], [0.0], label="cut", tag="range_cut")

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        self._push_controls(self.params)
        self.refresh()

        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()

        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: PulseDopplerParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    PulseDopplerApp(initial=params, scenario_id=scenario_id).run()
