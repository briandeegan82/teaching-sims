"""Dear PyGui desktop app for stripmap SAR teaching."""

from __future__ import annotations

import dearpygui.dearpygui as dpg
import numpy as np

from teaching_sims.topics.sar.physics import SARParams, SARPointTarget, process_sar
from teaching_sims.topics.sar.scenarios import SCENARIOS, get_scenario
from teaching_sims.ui.desktop.plot_utils import HEAT_FORMAT


IMG_ROWS = 160  # azimuth display
IMG_COLS = 220  # range display


def _fxy(xs, ys):
    return [[float(v) for v in xs], [float(v) for v in ys]]


def _db_to_heat(img_db: np.ndarray) -> list[float]:
    floor = float(max(np.percentile(img_db, 30), -30.0))
    floor = min(floor, -12.0)
    span = max(0.0 - floor, 1.0)
    x = np.clip((img_db - floor) / span, 0.0, 1.0)
    return [float(v) for v in np.power(x, 0.7).ravel()]


def _crop_and_resample(
    img: np.ndarray,
    x_m: np.ndarray,
    r_m: np.ndarray,
    *,
    x_half: float,
    r_center: float,
    r_half: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Crop to ROI and resample onto fixed display grid (rows=x, cols=r)."""
    x_mask = (x_m >= -x_half) & (x_m <= x_half)
    r_mask = (r_m >= r_center - r_half) & (r_m <= r_center + r_half)
    if not np.any(x_mask):
        x_mask[:] = True
    if not np.any(r_mask):
        r_mask[:] = True
    sub = img[np.ix_(x_mask, r_mask)]
    xs = x_m[x_mask]
    rs = r_m[r_mask]
    x_disp = np.linspace(float(xs[0]), float(xs[-1]), IMG_ROWS)
    r_disp = np.linspace(float(rs[0]), float(rs[-1]), IMG_COLS)
    tmp = np.empty((sub.shape[0], IMG_COLS), dtype=float)
    for i in range(sub.shape[0]):
        tmp[i] = np.interp(r_disp, rs, sub[i])
    out = np.empty((IMG_ROWS, IMG_COLS), dtype=float)
    for j in range(IMG_COLS):
        out[:, j] = np.interp(x_disp, xs, tmp[:, j])
    return out, x_disp, r_disp


class SARApp:
    def __init__(self, initial: SARParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or SARParams()
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
            self._title = "Stripmap SAR"
            self._note = "Range compression + azimuth deramp/FFT focusing of point targets."

    def _read_controls(self) -> SARParams:
        targets = (
            SARPointTarget(
                float(dpg.get_value("x1_m")),
                float(dpg.get_value("y1_m")),
                rcs_db=float(dpg.get_value("rcs1_db")),
            ),
        )
        if dpg.get_value("t2_on"):
            targets = (
                targets[0],
                SARPointTarget(
                    float(dpg.get_value("x2_m")),
                    float(dpg.get_value("y2_m")),
                    rcs_db=float(dpg.get_value("rcs2_db")),
                ),
            )
        return SARParams(
            altitude_m=float(dpg.get_value("alt_m")),
            velocity_mps=float(dpg.get_value("vel_mps")),
            center_freq_hz=float(dpg.get_value("fc_ghz")) * 1e9,
            bandwidth_hz=float(dpg.get_value("bw_mhz")) * 1e6,
            pulse_width_s=float(dpg.get_value("tp_us")) * 1e-6,
            prf_hz=float(dpg.get_value("prf_hz")),
            n_pulses=int(dpg.get_value("n_pulses")),
            sample_rate_hz=float(dpg.get_value("fs_mhz")) * 1e6,
            targets=targets,
            noise_enabled=bool(dpg.get_value("noise_on")),
            noise_snr_db=float(dpg.get_value("snr_db")),
            azimuth_window=bool(dpg.get_value("az_win")),
            seed=self._seed,
        )

    def _push_controls(self, p: SARParams) -> None:
        dpg.set_value("alt_m", p.altitude_m)
        dpg.set_value("vel_mps", p.velocity_mps)
        dpg.set_value("fc_ghz", p.center_freq_hz / 1e9)
        dpg.set_value("bw_mhz", p.bandwidth_hz / 1e6)
        dpg.set_value("tp_us", p.pulse_width_s * 1e6)
        dpg.set_value("prf_hz", p.prf_hz)
        dpg.set_value("n_pulses", p.n_pulses)
        dpg.set_value("fs_mhz", p.sample_rate_hz / 1e6)
        dpg.set_value("noise_on", p.noise_enabled)
        dpg.set_value("snr_db", p.noise_snr_db)
        dpg.set_value("az_win", p.azimuth_window)
        dpg.set_value("x1_m", p.targets[0].x_m)
        dpg.set_value("y1_m", p.targets[0].y_m)
        dpg.set_value("rcs1_db", p.targets[0].rcs_db)
        if len(p.targets) > 1:
            dpg.set_value("t2_on", True)
            dpg.set_value("x2_m", p.targets[1].x_m)
            dpg.set_value("y2_m", p.targets[1].y_m)
            dpg.set_value("rcs2_db", p.targets[1].rcs_db)
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
            parent="focused_plot",
        )
        self._annotation_tags.append(tag)

    def refresh(self) -> None:
        try:
            self.params = self._read_controls()
        except ValueError as exc:
            dpg.set_value("status_text", f"Invalid settings: {exc}")
            return

        p = self.params
        out = process_sar(p)
        x = out["x_m"]
        r = out["range_m"]
        focused = out["image_db"]
        unf = out["unfocused_db"]

        y0 = float(np.mean([t.y_m for t in p.targets]))
        r0 = float(np.hypot(p.altitude_m, y0))
        x_half = max(120.0, 3.0 * max(abs(t.x_m) for t in p.targets) + 40.0)
        r_half = max(80.0, 5.0 * p.range_resolution_m + 40.0)

        f_img, x_d, r_d = _crop_and_resample(
            focused, x, r, x_half=x_half, r_center=r0, r_half=r_half
        )
        u_img, _, _ = _crop_and_resample(
            unf, x, r, x_half=x_half, r_center=r0, r_half=r_half
        )

        for tag, img in (("focused_heat", f_img), ("unfocused_heat", u_img)):
            dpg.configure_item(
                tag,
                bounds_min=(float(r_d[0]), float(x_d[0])),
                bounds_max=(float(r_d[-1]), float(x_d[-1])),
            )
            dpg.set_value(tag, [_db_to_heat(img)])

        dpg.set_axis_limits("foc_x", float(r_d[0]), float(r_d[-1]))
        dpg.set_axis_limits("foc_y", float(x_d[0]), float(x_d[-1]))
        dpg.set_axis_limits("unf_x", float(r_d[0]), float(r_d[-1]))
        dpg.set_axis_limits("unf_y", float(x_d[0]), float(x_d[-1]))

        # Range cut through x~0
        i0 = int(np.argmin(np.abs(x)))
        dpg.set_value("range_cut", _fxy(r, focused[i0, :]))
        dpg.set_axis_limits("rc_x", float(r_d[0]), float(r_d[-1]))
        dpg.set_axis_limits("rc_y", -40.0, 1.0)

        # Azimuth cut through scene centre range
        j0 = int(np.argmin(np.abs(r - r0)))
        dpg.set_value("az_cut", _fxy(x, focused[:, j0]))
        dpg.set_axis_limits("ac_x", float(x_d[0]), float(x_d[-1]))
        dpg.set_axis_limits("ac_y", -40.0, 1.0)

        self._clear_annotations()
        for i, tgt in enumerate(p.targets):
            r_t = float(np.hypot(p.altitude_m, tgt.y_m))
            self._ann(
                f"ann_t{i}",
                f"T{i+1} x={tgt.x_m:.0f} m",
                r_t,
                tgt.x_m,
                (8, -14 if i == 0 else 12),
            )

        dpg.set_value(
            "status_text",
            (
                f"v={p.velocity_mps:.0f} m/s   h={p.altitude_m:.0f} m   "
                f"B={p.bandwidth_hz/1e6:.0f} MHz   N={p.n_pulses}   PRF={p.prf_hz:.0f} Hz\n"
                f"ΔR~{out['range_resolution_m']:.2f} m   Δx~{out['azimuth_resolution_m']:.2f} m   "
                f"L_sa~{out['synthetic_aperture_m']:.0f} m   R0~{out['R0_m']:.0f} m"
            ),
        )
        dpg.set_value("banner_title", self._title)
        dpg.set_value("banner_body", self._note)

    def _on_change(self, *_a, **_k) -> None:
        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims - Stripmap SAR", width=1500, height=980)

        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.window(tag="primary", label="SAR"):
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
                    dpg.add_slider_int(
                        tag="n_pulses",
                        label="Pulses (aperture)",
                        default_value=self.params.n_pulses,
                        min_value=32,
                        max_value=512,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="bw_mhz",
                        label="Bandwidth B (MHz)",
                        default_value=self.params.bandwidth_hz / 1e6,
                        min_value=10.0,
                        max_value=150.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="x1_m",
                        label="Target 1 azimuth x (m)",
                        default_value=self.params.targets[0].x_m,
                        min_value=-100.0,
                        max_value=100.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="y1_m",
                        label="Target 1 ground range y (m)",
                        default_value=self.params.targets[0].y_m,
                        min_value=4000.0,
                        max_value=12000.0,
                        callback=self._on_change,
                    )
                    dpg.add_checkbox(
                        tag="t2_on",
                        label="Enable target 2",
                        default_value=len(self.params.targets) > 1,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="x2_m",
                        label="Target 2 azimuth x (m)",
                        default_value=self.params.targets[1].x_m if len(self.params.targets) > 1 else 40.0,
                        min_value=-100.0,
                        max_value=100.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="y2_m",
                        label="Target 2 ground range y (m)",
                        default_value=self.params.targets[1].y_m if len(self.params.targets) > 1 else 8050.0,
                        min_value=4000.0,
                        max_value=12000.0,
                        callback=self._on_change,
                    )

                    with dpg.group(tag="advanced_controls"):
                        dpg.add_separator()
                        dpg.add_text("Advanced")
                        dpg.add_slider_float(
                            tag="vel_mps",
                            label="Platform speed (m/s)",
                            default_value=self.params.velocity_mps,
                            min_value=50.0,
                            max_value=250.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="alt_m",
                            label="Altitude (m)",
                            default_value=self.params.altitude_m,
                            min_value=2000.0,
                            max_value=10000.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="fc_ghz",
                            label="Center freq (GHz)",
                            default_value=self.params.center_freq_hz / 1e9,
                            min_value=1.0,
                            max_value=10.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="prf_hz",
                            label="PRF (Hz)",
                            default_value=self.params.prf_hz,
                            min_value=200.0,
                            max_value=2000.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="tp_us",
                            label="Pulse width (us)",
                            default_value=self.params.pulse_width_s * 1e6,
                            min_value=1.0,
                            max_value=20.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="fs_mhz",
                            label="Sample rate (MHz)",
                            default_value=self.params.sample_rate_hz / 1e6,
                            min_value=30.0,
                            max_value=120.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="snr_db",
                            label="Ref SNR (dB)",
                            default_value=self.params.noise_snr_db,
                            min_value=10.0,
                            max_value=40.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="rcs1_db",
                            label="Target 1 RCS (dB)",
                            default_value=self.params.targets[0].rcs_db,
                            min_value=-10.0,
                            max_value=10.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="rcs2_db",
                            label="Target 2 RCS (dB)",
                            default_value=self.params.targets[1].rcs_db if len(self.params.targets) > 1 else 0.0,
                            min_value=-10.0,
                            max_value=10.0,
                            callback=self._on_change,
                        )
                        dpg.add_checkbox(
                            tag="noise_on",
                            label="Noise",
                            default_value=self.params.noise_enabled,
                            callback=self._on_change,
                        )
                        dpg.add_checkbox(
                            tag="az_win",
                            label="Azimuth Hann window",
                            default_value=self.params.azimuth_window,
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
                        with dpg.plot(
                            label="Focused SAR image",
                            height=360,
                            width=560,
                            tag="focused_plot",
                        ):
                            dpg.add_plot_axis(dpg.mvXAxis, label="slant range (m)", tag="foc_x")
                            with dpg.plot_axis(dpg.mvYAxis, label="azimuth x (m)", tag="foc_y"):
                                dpg.add_heat_series(
                                    [0.05] * (IMG_ROWS * IMG_COLS),
                                    IMG_ROWS,
                                    IMG_COLS,
                                    scale_min=0.0,
                                    scale_max=1.0,
                                    bounds_min=(9000.0, -100.0),
                                    bounds_max=(9800.0, 100.0),
                                    format=HEAT_FORMAT,
                                    tag="focused_heat",
                                )

                        with dpg.plot(label="Unfocused (range-compressed only)", height=360, width=-1):
                            dpg.add_plot_axis(dpg.mvXAxis, label="slant range (m)", tag="unf_x")
                            with dpg.plot_axis(dpg.mvYAxis, label="azimuth x (m)", tag="unf_y"):
                                dpg.add_heat_series(
                                    [0.05] * (IMG_ROWS * IMG_COLS),
                                    IMG_ROWS,
                                    IMG_COLS,
                                    scale_min=0.0,
                                    scale_max=1.0,
                                    bounds_min=(9000.0, -100.0),
                                    bounds_max=(9800.0, 100.0),
                                    format=HEAT_FORMAT,
                                    tag="unfocused_heat",
                                )

                    with dpg.group(horizontal=True):
                        with dpg.plot(label="Range cut (x~0)", height=240, width=560):
                            dpg.add_plot_axis(dpg.mvXAxis, label="slant range (m)", tag="rc_x")
                            with dpg.plot_axis(dpg.mvYAxis, label="dB", tag="rc_y"):
                                dpg.add_line_series([0.0], [0.0], label="cut", tag="range_cut")

                        with dpg.plot(label="Azimuth cut (scene centre range)", height=240, width=-1):
                            dpg.add_plot_axis(dpg.mvXAxis, label="azimuth x (m)", tag="ac_x")
                            with dpg.plot_axis(dpg.mvYAxis, label="dB", tag="ac_y"):
                                dpg.add_line_series([0.0], [0.0], label="cut", tag="az_cut")

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        self._push_controls(self.params)
        self.refresh()

        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()

        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: SARParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    SARApp(initial=params, scenario_id=scenario_id).run()
