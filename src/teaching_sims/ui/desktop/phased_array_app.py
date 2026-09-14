"""Dear PyGui desktop app for phased-array teaching."""

from __future__ import annotations

from dataclasses import replace

import dearpygui.dearpygui as dpg
import numpy as np

from teaching_sims.topics.phased_array.features import pattern_features
from teaching_sims.topics.phased_array.physics import (
    ArrayParams,
    SteeringMode,
    element_positions,
    grating_lobe_hint,
    half_power_beamwidth_deg,
    pattern_db,
    peak_angle_deg,
    steering_phases,
    wavefront_field,
)
from teaching_sims.topics.phased_array.scenarios import SCENARIOS, get_scenario
from teaching_sims.ui.desktop.plot_utils import HEAT_FORMAT


THETA = np.linspace(-90.0, 90.0, 721)
WAVE_NX, WAVE_NZ = 160, 120
ARRAY_DRAW_W = 520
ARRAY_DRAW_H = 150


def _phase_to_rgb(phase_rad: float) -> tuple[int, int, int]:
    """Map phase to a saturated hue (HSV -> RGB bytes)."""
    h = (np.rad2deg(phase_rad) % 360.0) / 60.0
    i = int(np.floor(h)) % 6
    f = h - np.floor(h)
    q = int(255 * (1.0 - f))
    t = int(255 * f)
    table = (
        (255, t, 0),
        (q, 255, 0),
        (0, 255, t),
        (0, q, 255),
        (t, 0, 255),
        (255, 0, q),
    )
    return table[i]


def _fseries(xs, ys) -> list:
    return [[float(v) for v in xs], [float(v) for v in ys]]


class PhasedArrayApp:
    def __init__(self, initial: ArrayParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or ArrayParams()
        self.scenario_id = scenario_id
        self._anim_t = 0.0
        self._anim_dir = 1.0
        self._animate_steer = False
        self._animate_n = False
        self._wave_t = 0.0
        self._presenter = False
        self._compare_ttd = False
        self._annotation_tags: list[str] = []
        if scenario_id:
            sc = get_scenario(scenario_id)
            self.params = sc.params
            self._animate_steer = sc.animate_steer
            self._animate_n = sc.animate_n
            self._scenario_title = sc.title
            self._scenario_note = f"{sc.teaching_point}\n{sc.notes}"
        else:
            self._scenario_title = "Interactive ULA demo"
            self._scenario_note = (
                "Adjust N, spacing, and steer angle. Use scenarios for lecture beats."
            )

    # --- param helpers -------------------------------------------------
    def _read_controls(self) -> ArrayParams:
        mode = dpg.get_value("steer_mode")
        bits = int(dpg.get_value("phase_bits"))
        return ArrayParams(
            n_elements=int(dpg.get_value("n_elements")),
            d_over_lambda=float(dpg.get_value("d_over_lambda")),
            frequency_hz=float(dpg.get_value("freq_ghz")) * 1e9,
            design_frequency_hz=float(dpg.get_value("design_freq_ghz")) * 1e9,
            steer_deg=float(dpg.get_value("steer_deg")),
            steering_mode=SteeringMode.PHASE_SHIFT
            if mode == "Phase shift"
            else SteeringMode.TRUE_TIME_DELAY,
            element_pattern=bool(dpg.get_value("element_pattern")),
            phase_bits=None if bits <= 0 else bits,
            amplitude_taper="hann" if dpg.get_value("taper_hann") else "uniform",
        )

    def _push_controls(self, p: ArrayParams) -> None:
        dpg.set_value("n_elements", p.n_elements)
        dpg.set_value("d_over_lambda", p.d_over_lambda)
        dpg.set_value("freq_ghz", p.frequency_hz / 1e9)
        dpg.set_value(
            "design_freq_ghz",
            (p.design_frequency_hz or p.frequency_hz) / 1e9,
        )
        dpg.set_value("steer_deg", p.steer_deg)
        dpg.set_value(
            "steer_mode",
            "Phase shift"
            if p.steering_mode == SteeringMode.PHASE_SHIFT
            else "True time delay",
        )
        dpg.set_value("element_pattern", p.element_pattern)
        dpg.set_value("phase_bits", 0 if p.phase_bits is None else p.phase_bits)
        dpg.set_value("taper_hann", p.amplitude_taper == "hann")

    def _apply_scenario(self, scenario_id: str) -> None:
        sc = get_scenario(scenario_id)
        self.scenario_id = scenario_id
        self.params = sc.params
        self._animate_steer = sc.animate_steer
        self._animate_n = sc.animate_n
        self._scenario_title = sc.title
        self._scenario_note = f"{sc.teaching_point}\n{sc.notes}"
        self._push_controls(self.params)
        dpg.set_value("banner_title", self._scenario_title)
        dpg.set_value("banner_body", self._scenario_note)
        dpg.set_value("scenario_text", self._scenario_note)
        dpg.set_value("auto_steer", self._animate_steer)
        dpg.set_value("auto_n", self._animate_n)
        # Squint scenario benefits from compare overlay.
        if scenario_id == "phase_vs_ttd":
            dpg.set_value("compare_ttd", True)
            self._compare_ttd = True
        self.refresh()

    def _set_presenter(self, _sender=None, app_data=None, _user_data=None) -> None:
        self._presenter = bool(app_data if app_data is not None else dpg.get_value("presenter_mode"))
        dpg.configure_item("advanced_controls", show=not self._presenter)
        dpg.configure_item("banner_panel", show=True)
        dpg.configure_item(
            "banner_body",
            wrap=900 if self._presenter else 300,
        )
        # Larger banner area in presenter mode via child height.
        dpg.configure_item("banner_panel", height=110 if self._presenter else 72)
        self.refresh()

    def _clear_annotations(self) -> None:
        for tag in self._annotation_tags:
            if dpg.does_item_exist(tag):
                dpg.delete_item(tag)
        self._annotation_tags.clear()

    def _add_annotation(self, tag: str, label: str, x: float, y: float, offset=(12, 12)) -> None:
        if dpg.does_item_exist(tag):
            dpg.delete_item(tag)
        dpg.add_plot_annotation(
            label=label,
            default_value=(float(x), float(y)),
            offset=offset,
            tag=tag,
            parent="pattern_plot",
        )
        self._annotation_tags.append(tag)

    def _draw_array_layout(self, p: ArrayParams) -> None:
        if not dpg.does_item_exist("array_draw"):
            return
        dpg.delete_item("array_draw", children_only=True)

        xs = element_positions(p)
        phases = steering_phases(p)
        n = len(xs)
        pad = 36.0
        y0 = ARRAY_DRAW_H * 0.58
        if n == 1:
            px = np.array([ARRAY_DRAW_W * 0.5])
        else:
            span = ARRAY_DRAW_W - 2 * pad
            xmin, xmax = float(xs[0]), float(xs[-1])
            px = pad + (xs - xmin) / (xmax - xmin + 1e-15) * span

        # Baseline
        dpg.draw_line(
            (pad * 0.4, y0),
            (ARRAY_DRAW_W - pad * 0.4, y0),
            color=(90, 90, 100, 255),
            thickness=2,
            parent="array_draw",
        )
        dpg.draw_text(
            (8, 8),
            "Array layout  (colour / arrow = excitation phase)",
            color=(200, 200, 210, 255),
            size=14,
            parent="array_draw",
        )
        # Broadside arrow (z)
        dpg.draw_arrow(
            (ARRAY_DRAW_W * 0.5, y0 - 8),
            (ARRAY_DRAW_W * 0.5, 28),
            color=(160, 160, 170, 255),
            thickness=1,
            size=6,
            parent="array_draw",
        )
        dpg.draw_text(
            (ARRAY_DRAW_W * 0.5 + 6, 22),
            "broadside",
            color=(150, 150, 160, 255),
            size=12,
            parent="array_draw",
        )

        arrow_len = 28.0
        for i, (xpix, ph) in enumerate(zip(px, phases)):
            rgb = _phase_to_rgb(float(ph))
            r = 9 if n <= 24 else 6
            dpg.draw_circle(
                (float(xpix), y0),
                r,
                color=(255, 255, 255, 255),
                fill=(*rgb, 255),
                thickness=1,
                parent="array_draw",
            )
            # Phase phasor arrow (0 deg = +x for visual variety of progressive phase)
            dx = arrow_len * np.cos(ph)
            dy = -arrow_len * np.sin(ph)
            dpg.draw_arrow(
                (float(xpix), y0),
                (float(xpix + dx), float(y0 + dy)),
                color=(*rgb, 255),
                thickness=2,
                size=5,
                parent="array_draw",
            )
            if n <= 16:
                dpg.draw_text(
                    (float(xpix) - 6, y0 + 14),
                    str(i),
                    color=(180, 180, 190, 255),
                    size=11,
                    parent="array_draw",
                )

        # Steer cue (from array center toward commanded theta₀; up = broadside)
        steer = np.deg2rad(p.steer_deg)
        cx, cy = ARRAY_DRAW_W * 0.5, y0 - 10
        length = 55.0
        ex = cx + length * np.sin(steer)
        ey = cy - length * np.cos(steer)
        dpg.draw_arrow(
            (cx, cy),
            (float(ex), float(ey)),
            color=(255, 210, 80, 255),
            thickness=2,
            size=8,
            parent="array_draw",
        )
        dpg.draw_text(
            (10, ARRAY_DRAW_H - 22),
            f"steer theta₀ = {p.steer_deg:.1f} deg   N = {p.n_elements}   d/λ = {p.d_over_lambda:.2f}",
            color=(210, 210, 220, 255),
            size=13,
            parent="array_draw",
        )

    # --- plotting ------------------------------------------------------
    def refresh(self) -> None:
        self.params = self._read_controls()
        self._compare_ttd = bool(dpg.get_value("compare_ttd"))
        p = self.params
        pdb = pattern_db(THETA, p)
        theta_f = [float(v) for v in THETA]
        dpg.set_value("pattern_series", [theta_f, [float(v) for v in pdb]])

        # Compare overlay: same geometry, true-time-delay steering
        if self._compare_ttd:
            p_ttd = replace(p, steering_mode=SteeringMode.TRUE_TIME_DELAY)
            pdb_ttd = pattern_db(THETA, p_ttd)
            dpg.set_value("compare_series", [theta_f, [float(v) for v in pdb_ttd]])
            dpg.configure_item("compare_series", show=True)
        else:
            dpg.set_value("compare_series", [[0.0], [-100.0]])
            dpg.configure_item("compare_series", show=False)

        dpg.set_value("m3db_series", [theta_f, [-3.0] * len(THETA)])
        dpg.set_value(
            "steer_marker",
            [[float(p.steer_deg), float(p.steer_deg)], [-40.0, 0.0]],
        )

        feat = pattern_features(p, THETA)
        # Scatter callouts
        peak_x = [feat.main_peak_deg, *feat.grating_peaks_deg]
        peak_y = [
            float(np.interp(a, THETA, pdb))
            for a in peak_x
        ]
        null_x = list(feat.nulls_deg)
        null_y = [float(np.interp(a, THETA, pdb)) for a in null_x]
        dpg.set_value("peak_scatter", _fseries(peak_x or [0.0], peak_y or [-100.0]))
        dpg.set_value("null_scatter", _fseries(null_x or [0.0], null_y or [-100.0]))
        dpg.configure_item("peak_scatter", show=bool(peak_x))
        dpg.configure_item("null_scatter", show=bool(null_x))

        self._clear_annotations()
        self._add_annotation(
            "ann_main",
            f"main {feat.main_peak_deg:.1f} deg",
            feat.main_peak_deg,
            float(np.interp(feat.main_peak_deg, THETA, pdb)),
            offset=(10, -18),
        )
        for i, g in enumerate(feat.grating_peaks_deg[:3]):
            self._add_annotation(
                f"ann_grat_{i}",
                f"grating {g:.1f} deg",
                g,
                float(np.interp(g, THETA, pdb)),
                offset=(10, 14),
            )
        for i, nang in enumerate(feat.nulls_deg[:2]):
            self._add_annotation(
                f"ann_null_{i}",
                "null",
                nang,
                float(np.interp(nang, THETA, pdb)),
                offset=(-30, 10),
            )

        xs = element_positions(p)
        phases = np.rad2deg(np.unwrap(steering_phases(p)))
        dpg.set_value(
            "phase_series",
            [[float(v) for v in xs * 1e3], [float(v) for v in phases]],
        )
        self._draw_array_layout(p)

        x_m, z_m, field = wavefront_field(p, nx=WAVE_NX, nz=WAVE_NZ, t=self._wave_t)
        amp = float(np.max(np.abs(field))) + 1e-12
        img = (np.asarray(field, dtype=float) / amp + 1.0) * 0.5
        x_mm = x_m * 1e3
        z_mm = z_m * 1e3
        dpg.configure_item(
            "wave_heat",
            bounds_min=(float(x_mm[0]), float(z_mm[0])),
            bounds_max=(float(x_mm[-1]), float(z_mm[-1])),
        )
        dpg.set_axis_limits("wx", float(x_mm[0]), float(x_mm[-1]))
        dpg.set_axis_limits("wz", float(z_mm[0]), float(z_mm[-1]))
        dpg.set_value("wave_heat", [[float(v) for v in img.ravel()]])

        hpbw = half_power_beamwidth_deg(p)
        peak = peak_angle_deg(p)
        hint = grating_lobe_hint(p)
        compare_note = ""
        if self._compare_ttd:
            p_ttd = replace(p, steering_mode=SteeringMode.TRUE_TIME_DELAY)
            compare_note = (
                f"\nCompare: phase peak~{peak:.1f} deg vs TTD peak~{peak_angle_deg(p_ttd):.1f} deg"
            )
        dpg.set_value(
            "status_text",
            (
                f"N={p.n_elements}  d/λ_design={p.d_over_lambda:.2f}  "
                f"f={p.frequency_hz/1e9:.2f} GHz  steer={p.steer_deg:.1f} deg\n"
                f"Peak ~ {peak:.1f} deg   HPBW ~ {hpbw:.1f} deg\n"
                f"{hint}{compare_note}"
            ),
        )
        dpg.set_value("banner_title", self._scenario_title)
        dpg.set_value("banner_body", self._scenario_note)

    def _on_change(self, _sender=None, _app_data=None, _user_data=None) -> None:
        self._animate_steer = bool(dpg.get_value("auto_steer"))
        self._animate_n = bool(dpg.get_value("auto_n"))
        self._compare_ttd = bool(dpg.get_value("compare_ttd"))
        self.refresh()

    def _tick(self) -> None:
        self._wave_t += 0.015

        if self._animate_steer:
            steer = float(dpg.get_value("steer_deg")) + self._anim_dir * 0.35
            if steer > 50:
                steer = 50
                self._anim_dir = -1.0
            elif steer < -50:
                steer = -50
                self._anim_dir = 1.0
            dpg.set_value("steer_deg", steer)

        if self._animate_n:
            self._anim_t += 0.05
            if self._anim_t >= 1.0:
                self._anim_t = 0.0
                n = int(dpg.get_value("n_elements")) + 2
                if n > 32:
                    n = 4
                dpg.set_value("n_elements", n)

        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.configure_app(docking=False)
        dpg.create_viewport(title="Teaching Sims - Phased Array Radar", width=1480, height=920)

        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.theme() as peak_theme:
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, (255, 200, 60), category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, (255, 200, 60), category=dpg.mvThemeCat_Plots)
        with dpg.theme() as null_theme:
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, (120, 200, 255), category=dpg.mvThemeCat_Plots)
                dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, (120, 200, 255), category=dpg.mvThemeCat_Plots)
        with dpg.theme() as compare_theme:
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, (255, 120, 90), category=dpg.mvThemeCat_Plots)

        with dpg.window(tag="primary", label="Phased Array"):
            # Presenter banner
            with dpg.child_window(tag="banner_panel", height=72, border=True):
                dpg.add_text(self._scenario_title, tag="banner_title")
                dpg.add_text(self._scenario_note, tag="banner_body", wrap=900)

            with dpg.group(horizontal=True):
                # ---- controls ----
                with dpg.child_window(width=340, border=True):
                    dpg.add_checkbox(
                        tag="presenter_mode",
                        label="Presenter mode (hide advanced)",
                        default_value=False,
                        callback=self._set_presenter,
                    )
                    dpg.add_checkbox(
                        tag="compare_ttd",
                        label="Compare overlay: phase vs TTD",
                        default_value=False,
                        callback=self._on_change,
                    )
                    dpg.add_separator()
                    dpg.add_text("Core controls")
                    dpg.add_slider_int(
                        tag="n_elements",
                        label="N elements",
                        default_value=self.params.n_elements,
                        min_value=1,
                        max_value=64,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="d_over_lambda",
                        label="d / λ_design",
                        default_value=self.params.d_over_lambda,
                        min_value=0.15,
                        max_value=1.5,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="steer_deg",
                        label="Steer theta₀ (deg)",
                        default_value=self.params.steer_deg,
                        min_value=-60.0,
                        max_value=60.0,
                        callback=self._on_change,
                    )
                    dpg.add_combo(
                        tag="steer_mode",
                        label="Steering",
                        items=["Phase shift", "True time delay"],
                        default_value=(
                            "Phase shift"
                            if self.params.steering_mode == SteeringMode.PHASE_SHIFT
                            else "True time delay"
                        ),
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
                            max_value=20.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="design_freq_ghz",
                            label="Design freq f₀ (GHz)",
                            default_value=(
                                self.params.design_frequency_hz or self.params.frequency_hz
                            )
                            / 1e9,
                            min_value=1.0,
                            max_value=20.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_int(
                            tag="phase_bits",
                            label="Phase bits (0=continuous)",
                            default_value=(
                                0 if self.params.phase_bits is None else self.params.phase_bits
                            ),
                            min_value=0,
                            max_value=6,
                            callback=self._on_change,
                        )
                        dpg.add_checkbox(
                            tag="element_pattern",
                            label="costheta element pattern",
                            default_value=self.params.element_pattern,
                            callback=self._on_change,
                        )
                        dpg.add_checkbox(
                            tag="taper_hann",
                            label="Hann amplitude taper",
                            default_value=self.params.amplitude_taper == "hann",
                            callback=self._on_change,
                        )
                        dpg.add_checkbox(
                            tag="auto_steer",
                            label="Auto-sweep steer",
                            default_value=self._animate_steer,
                            callback=self._on_change,
                        )
                        dpg.add_checkbox(
                            tag="auto_n",
                            label="Auto-grow N",
                            default_value=self._animate_n,
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
                    dpg.add_text("Notes", bullet=True)
                    dpg.add_text(self._scenario_note, tag="scenario_text", wrap=300)
                    dpg.add_separator()
                    dpg.add_text("", tag="status_text", wrap=300)

                # ---- plots ----
                with dpg.child_window(border=False):
                    with dpg.plot(
                        label="Array factor (dB)",
                        height=340,
                        width=-1,
                        tag="pattern_plot",
                    ):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="theta (deg)", tag="pat_x")
                        dpg.set_axis_limits("pat_x", -90, 90)
                        with dpg.plot_axis(dpg.mvYAxis, label="|AF|^2 (dB)", tag="pat_y"):
                            dpg.set_axis_limits("pat_y", -40, 1)
                            dpg.add_line_series(
                                list(THETA),
                                [0.0] * len(THETA),
                                label="pattern",
                                tag="pattern_series",
                            )
                            cmp = dpg.add_line_series(
                                [0.0],
                                [-100.0],
                                label="TTD compare",
                                tag="compare_series",
                                show=False,
                            )
                            dpg.bind_item_theme(cmp, compare_theme)
                            dpg.add_line_series(
                                list(THETA),
                                [-3.0] * len(THETA),
                                label="-3 dB",
                                tag="m3db_series",
                            )
                            dpg.add_line_series(
                                [0.0, 0.0],
                                [-40.0, 0.0],
                                label="steer",
                                tag="steer_marker",
                            )
                            pk = dpg.add_scatter_series(
                                [0.0],
                                [0.0],
                                label="peaks",
                                tag="peak_scatter",
                            )
                            dpg.bind_item_theme(pk, peak_theme)
                            nu = dpg.add_scatter_series(
                                [0.0],
                                [-40.0],
                                label="nulls",
                                tag="null_scatter",
                            )
                            dpg.bind_item_theme(nu, null_theme)

                    dpg.add_drawlist(
                        width=ARRAY_DRAW_W,
                        height=ARRAY_DRAW_H,
                        tag="array_draw",
                    )

                    with dpg.group(horizontal=True):
                        with dpg.plot(label="Element phase (unwrap, deg)", height=300, width=480):
                            dpg.add_plot_axis(dpg.mvXAxis, label="x (mm)")
                            with dpg.plot_axis(dpg.mvYAxis, label="phase (deg)"):
                                dpg.add_line_series(
                                    [0.0],
                                    [0.0],
                                    label="phi_n",
                                    tag="phase_series",
                                )

                        with dpg.plot(label="Wavefront snapshot Re{E}", height=300, width=-1):
                            dpg.add_plot_axis(dpg.mvXAxis, label="x (mm)", tag="wx")
                            with dpg.plot_axis(dpg.mvYAxis, label="z range (mm)", tag="wz"):
                                dpg.add_heat_series(
                                    [0.5] * (WAVE_NX * WAVE_NZ),
                                    WAVE_NZ,
                                    WAVE_NX,
                                    scale_min=0.0,
                                    scale_max=1.0,
                                    bounds_min=(0.0, 0.0),
                                    bounds_max=(float(WAVE_NX), float(WAVE_NZ)),
                                    format=HEAT_FORMAT,
                                    tag="wave_heat",
                                )

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        self._push_controls(self.params)
        self.refresh()

        while dpg.is_dearpygui_running():
            self._tick()
            dpg.render_dearpygui_frame()

        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: ArrayParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    PhasedArrayApp(initial=params, scenario_id=scenario_id).run()
