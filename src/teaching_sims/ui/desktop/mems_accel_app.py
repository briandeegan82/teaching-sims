"""Dear PyGui demo: MEMS comb-drive accelerometer (how IMU accel sensing works)."""

from __future__ import annotations

import time

import dearpygui.dearpygui as dpg
import numpy as np

from teaching_sims.topics.mems_accel.physics import Excitation, MEMSAccelParams, process
from teaching_sims.topics.mems_accel.scenarios import SCENARIOS, get_scenario
from teaching_sims.ui.desktop.plot_utils import fit_axes, fxy as _fxy


DRAW_W = 720
DRAW_H = 280

EXC_LABELS = {
    "At rest": Excitation.REST,
    "Constant accel": Excitation.CONSTANT,
    "Impulse": Excitation.IMPULSE,
    "Step": Excitation.STEP,
    "Sine": Excitation.SINE,
}
LABEL_FOR_EXC = {v: k for k, v in EXC_LABELS.items()}


class MEMSAccelApp:
    def __init__(self, initial: MEMSAccelParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or MEMSAccelParams()
        self.scenario_id = scenario_id
        self._presenter = False
        self._suppress = False
        self._out: dict[str, object] | None = None
        self._playing = False
        self._play_t0: float | None = None
        self._play_speed = 0.03  # very slow-mo so impulse ring-down is visible
        if scenario_id:
            sc = get_scenario(scenario_id)
            self.params = sc.params
            self._title = sc.title
            self._note = f"{sc.teaching_point}\n{sc.notes}"
        else:
            self._title = "MEMS comb-drive accelerometer"
            self._note = (
                "Proof mass + suspension springs + interdigitated fingers. "
                "Bias vs impulse change the sensed signal in different ways."
            )

    def _read_controls(self) -> MEMSAccelParams:
        return MEMSAccelParams(
            excitation=EXC_LABELS[dpg.get_value("excitation")],
            a_const_mps2=float(dpg.get_value("a_const")),
            impulse_amp_mps2=float(dpg.get_value("imp_amp")),
            impulse_width_s=float(dpg.get_value("imp_w")) * 1e-3,
            zeta=float(dpg.get_value("zeta")),
            output_bias_mps2=float(dpg.get_value("out_bias")),
            mech_offset_um=float(dpg.get_value("mech_off")),
            duration_s=float(dpg.get_value("duration")),
            gap0_um=float(dpg.get_value("gap0")),
            fs_hz=20_000.0,
        )

    def _push_controls(self, p: MEMSAccelParams) -> None:
        self._suppress = True
        try:
            dpg.set_value("excitation", LABEL_FOR_EXC[p.excitation])
            dpg.set_value("a_const", p.a_const_mps2)
            dpg.set_value("imp_amp", p.impulse_amp_mps2)
            dpg.set_value("imp_w", p.impulse_width_s * 1e3)
            dpg.set_value("zeta", p.zeta)
            dpg.set_value("out_bias", p.output_bias_mps2)
            dpg.set_value("mech_off", p.mech_offset_um)
            dpg.set_value("duration", p.duration_s)
            dpg.set_value("gap0", p.gap0_um)
        finally:
            self._suppress = False

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
        if self._out is not None:
            self._set_view_time(0.0 if sc.id.startswith("impulse") or sc.id.startswith("over") else float(np.asarray(self._out["t_s"])[-1]))
            if "impulse" in sc.id or sc.id.startswith("over"):
                self._play()

    def _set_presenter(self, _s=None, app_data=None, _u=None) -> None:
        self._presenter = bool(app_data if app_data is not None else dpg.get_value("presenter_mode"))
        dpg.configure_item("advanced_controls", show=not self._presenter)
        dpg.configure_item("banner_panel", height=110 if self._presenter else 72)

    def _play(self) -> None:
        self._playing = True
        self._sync_play_speed()
        self._play_t0 = time.monotonic()
        if dpg.does_item_exist("view_t"):
            dpg.set_value("view_t", 0.0)

    def _pause(self) -> None:
        self._playing = False

    def _sync_play_speed(self) -> None:
        if dpg.does_item_exist("play_speed"):
            self._play_speed = max(0.01, float(dpg.get_value("play_speed")))

    def _on_play_speed(self, *_a, **_k) -> None:
        if self._suppress:
            return
        self._sync_play_speed()
        # Keep the current view time continuous when speed changes mid-play
        if self._playing and self._play_t0 is not None and dpg.does_item_exist("view_t"):
            t_now = float(dpg.get_value("view_t"))
            if self._play_speed > 0:
                self._play_t0 = time.monotonic() - t_now / self._play_speed

    def _on_scrub(self, *_a, **_k) -> None:
        if self._suppress or self._out is None:
            return
        self._playing = False
        self._set_view_time(float(dpg.get_value("view_t")))

    def _on_change(self, *_a, **_k) -> None:
        if self._suppress:
            return
        self._playing = False
        self.refresh()

    def _index_at(self, t_query: float) -> int:
        assert self._out is not None
        t = np.asarray(self._out["t_s"], dtype=float)
        t_query = float(np.clip(t_query, float(t[0]), float(t[-1])))
        i = int(np.searchsorted(t, t_query, side="right") - 1)
        return int(np.clip(i, 0, len(t) - 1))

    def _set_view_time(self, t_query: float) -> None:
        if self._out is None:
            return
        t = np.asarray(self._out["t_s"], dtype=float)
        i = self._index_at(t_query)
        if dpg.does_item_exist("view_t"):
            self._suppress = True
            try:
                dpg.set_value("view_t", float(t[i]))
            finally:
                self._suppress = False
        x_um = float(np.asarray(self._out["x_um"])[i])
        self._draw_comb(x_um, float(self.params.gap0_um))
        ti = float(t[i])

        def _cursor(tag: str, *series: str) -> None:
            if not dpg.does_item_exist(tag):
                return
            ys = [np.asarray(self._out[s], dtype=float) for s in series]
            y = np.concatenate(ys)
            pad = 0.05 * (float(np.max(y)) - float(np.min(y)) + 1e-9)
            dpg.set_value(tag, [[ti, ti], [float(np.min(y)) - pad, float(np.max(y)) + pad]])

        _cursor("a_cursor", "a_ext_mps2", "a_meas_mps2")
        _cursor("x_cursor", "x_um")
        _cursor("c_cursor", "c1_fF", "c2_fF", "dc_fF")

    def _tick(self) -> None:
        if not self._playing or self._out is None:
            return
        t = np.asarray(self._out["t_s"], dtype=float)
        if self._play_t0 is None:
            self._play_t0 = time.monotonic()
        elapsed = (time.monotonic() - self._play_t0) * self._play_speed
        if elapsed >= float(t[-1]):
            self._set_view_time(float(t[-1]))
            self._playing = False
            return
        self._set_view_time(elapsed)

    def _draw_comb(self, x_um: float, gap0_um: float) -> None:
        if not dpg.does_item_exist("comb_draw"):
            return
        dpg.delete_item("comb_draw", children_only=True)

        # Map micrometers of proof-mass motion to pixels (exaggerated for teaching).
        # Fixed electrodes stay on the substrate; only the mass + moving fingers shift.
        scale = 28.0  # px per um
        dx = float(np.clip(x_um * scale, -55.0, 55.0))
        frame_cx = DRAW_W * 0.5
        mass_cx = frame_cx + dx
        cy = DRAW_H * 0.52
        mass_h = 34.0

        fixed_col = (200, 200, 210, 255)
        moving_col = (255, 180, 80, 255)
        mass_col = (90, 140, 200, 255)
        rail_col = (55, 55, 65, 255)
        rail_edge = (180, 180, 190, 255)

        dpg.draw_text(
            (10, 8),
            "Silicon substrate - horizontal sense axis (comb drive)",
            size=15,
            color=(210, 210, 220),
            parent="comb_draw",
        )
        dpg.draw_text(
            (10, 28),
            f"proof-mass displacement x = {x_um:+.3f} um   (gap0 = {gap0_um:.2f} um)",
            size=13,
            color=(170, 170, 180),
            parent="comb_draw",
        )

        # Comb geometry: alternate fixed / moving fingers with a visible air gap.
        # pitch must leave finger_w + 2*air_gap between neighbors.
        n_fixed = 8
        finger_w = 7.0
        air_gap = 5.0
        pitch = 2.0 * (finger_w + air_gap)  # fixed-to-fixed spacing
        overlap = 22.0  # how far fingers nest past each other along Y
        tip_clear = 6.0  # clearance from opposing backbone
        rail_h = 14.0

        comb_half = 0.5 * (n_fixed - 1) * pitch
        mass_w = 2.0 * (comb_half + 0.5 * pitch) + finger_w
        fixed_xs = [frame_cx - comb_half + i * pitch for i in range(n_fixed)]
        # Moving fingers sit in the gaps between fixed fingers (and one past each end)
        moving_xs = [frame_cx - comb_half - 0.5 * pitch + i * pitch + dx for i in range(n_fixed + 1)]

        # Anchors + suspension (anchors fixed; beams stretch to moving mass)
        for ax_x, side in ((70.0, -1), (DRAW_W - 70.0, 1)):
            dpg.draw_rectangle(
                (ax_x - 22, cy - 55),
                (ax_x + 22, cy - 30),
                fill=(70, 70, 80, 255),
                color=rail_edge,
                parent="comb_draw",
            )
            dpg.draw_rectangle(
                (ax_x - 22, cy + 30),
                (ax_x + 22, cy + 55),
                fill=(70, 70, 80, 255),
                color=rail_edge,
                parent="comb_draw",
            )
            mx = mass_cx - side * mass_w * 0.5
            dpg.draw_line(
                (ax_x, cy - 42),
                (mx, cy - mass_h * 0.5),
                color=(160, 200, 255, 255),
                thickness=2,
                parent="comb_draw",
            )
            dpg.draw_line(
                (ax_x, cy + 42),
                (mx, cy + mass_h * 0.5),
                color=(160, 200, 255, 255),
                thickness=2,
                parent="comb_draw",
            )
            dpg.draw_text((ax_x - 24, cy - 72), "ANCHOR", size=11, color=(180, 180, 190), parent="comb_draw")

        dpg.draw_text((80, cy - 8), "SUSPENSION", size=11, color=(150, 190, 240), parent="comb_draw")

        mass_top = cy - mass_h * 0.5
        mass_bot = cy + mass_h * 0.5
        top_rail_y0 = mass_top - tip_clear - overlap - rail_h
        top_rail_y1 = top_rail_y0 + rail_h
        bot_rail_y0 = mass_bot + tip_clear + overlap
        bot_rail_y1 = bot_rail_y0 + rail_h
        rail_x0 = frame_cx - comb_half - 0.5 * pitch - 12.0
        rail_x1 = frame_cx + comb_half + 0.5 * pitch + 12.0

        def _finger(x: float, y0: float, y1: float, color) -> None:
            dpg.draw_rectangle(
                (x - finger_w * 0.5, y0),
                (x + finger_w * 0.5, y1),
                fill=color,
                color=(40, 40, 45, 255),
                thickness=1,
                parent="comb_draw",
            )

        # Top / bottom fixed backbones (bars only — not a filled comb block)
        dpg.draw_rectangle(
            (rail_x0, top_rail_y0),
            (rail_x1, top_rail_y1),
            fill=rail_col,
            color=rail_edge,
            parent="comb_draw",
        )
        dpg.draw_rectangle(
            (rail_x0, bot_rail_y0),
            (rail_x1, bot_rail_y1),
            fill=rail_col,
            color=rail_edge,
            parent="comb_draw",
        )

        # Fixed fingers: hang from rails toward the mass, tip stops short of mass face
        for fx in fixed_xs:
            _finger(fx, top_rail_y1, mass_top - tip_clear, fixed_col)
            _finger(fx, mass_bot + tip_clear, bot_rail_y0, fixed_col)

        # Movable mass body
        dpg.draw_rectangle(
            (mass_cx - mass_w * 0.5, mass_top),
            (mass_cx + mass_w * 0.5, mass_bot),
            fill=mass_col,
            color=(230, 230, 240, 255),
            thickness=2,
            parent="comb_draw",
        )
        dpg.draw_text((mass_cx - 48, cy - 6), "MOVABLE MASS", size=12, color=(240, 240, 250), parent="comb_draw")

        # Moving fingers: project from mass into the gaps between fixed fingers
        for mx in moving_xs:
            _finger(mx, mass_top - overlap, mass_top, moving_col)
            _finger(mx, mass_bot, mass_bot + overlap, moving_col)

        dpg.draw_text((DRAW_W - 210, 48), "FIXED ELECTRODES", size=12, color=fixed_col[:3], parent="comb_draw")
        dpg.draw_text((DRAW_W - 210, 66), "MOVING ELECTRODES", size=12, color=moving_col[:3], parent="comb_draw")
        dpg.draw_text((DRAW_W - 210, 90), "CAPACITANCE SENSING", size=12, color=(160, 220, 160), parent="comb_draw")

        # Sense-axis arrow (fixed frame)
        dpg.draw_arrow(
            (frame_cx - 80, 50),
            (frame_cx + 80, 50),
            color=(220, 220, 230, 255),
            thickness=2,
            size=8,
            parent="comb_draw",
        )

    def refresh(self) -> None:
        try:
            self.params = self._read_controls()
        except ValueError as exc:
            dpg.set_value("status_text", f"Invalid settings: {exc}")
            return

        out = process(self.params)
        self._out = out
        t = out["t_s"]
        dpg.set_value("a_ext", _fxy(t, out["a_ext_mps2"]))
        dpg.set_value("a_meas", _fxy(t, out["a_meas_mps2"]))
        dpg.set_value("x_series", _fxy(t, out["x_um"]))
        dpg.set_value("c1_series", _fxy(t, out["c1_fF"]))
        dpg.set_value("c2_series", _fxy(t, out["c2_fF"]))
        dpg.set_value("dc_series", _fxy(t, out["dc_fF"]))
        fit_axes("a_t", "a_y", "x_t", "x_y", "c_t", "c_y")

        if dpg.does_item_exist("view_t"):
            self._suppress = True
            try:
                dpg.configure_item("view_t", max_value=float(np.asarray(t)[-1]))
                if not self._playing:
                    dpg.set_value("view_t", float(np.asarray(t)[-1]))
            finally:
                self._suppress = False

        t_view = float(dpg.get_value("view_t")) if dpg.does_item_exist("view_t") else float(np.asarray(t)[-1])
        self._set_view_time(t_view)

        dpg.set_value(
            "status_text",
            (
                f"Resonant f0 ~ {out['f0_hz']:.0f} Hz   zeta={out['zeta']:.2f}\n"
                f"Final x={out['x_final_um']:+.3f} um   a_meas={out['a_meas_final']:+.2f} m/s^2\n"
                f"Output bias={self.params.output_bias_mps2:+.2f}   mech offset={self.params.mech_offset_um:+.3f} um"
            ),
        )

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims - MEMS Comb-Drive Accelerometer", width=1520, height=980)
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.window(tag="primary", label="MEMS accelerometer"):
            with dpg.child_window(tag="banner_panel", height=72, border=True):
                dpg.add_text(self._title, tag="banner_title")
                dpg.add_text(self._note, tag="banner_body", wrap=1100)

            with dpg.group(horizontal=True):
                with dpg.child_window(width=350, border=True):
                    dpg.add_checkbox(
                        tag="presenter_mode",
                        label="Presenter mode (hide advanced)",
                        default_value=False,
                        callback=self._set_presenter,
                    )
                    dpg.add_separator()
                    dpg.add_text("Playback")
                    dpg.add_slider_float(
                        tag="view_t",
                        label="View time (s)",
                        default_value=self.params.duration_s,
                        min_value=0.0,
                        max_value=self.params.duration_s,
                        callback=self._on_scrub,
                    )
                    dpg.add_slider_float(
                        tag="play_speed",
                        label="Speed (x realtime)",
                        default_value=self._play_speed,
                        min_value=0.005,
                        max_value=0.5,
                        callback=self._on_play_speed,
                    )
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Play", width=100, callback=lambda: self._play())
                        dpg.add_button(label="Pause", width=100, callback=lambda: self._pause())
                    dpg.add_separator()
                    dpg.add_text("Excitation")
                    dpg.add_combo(
                        tag="excitation",
                        label="Type",
                        items=list(EXC_LABELS.keys()),
                        default_value=LABEL_FOR_EXC[self.params.excitation],
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="a_const",
                        label="Constant / step a (m/s^2)",
                        default_value=self.params.a_const_mps2,
                        min_value=-20.0,
                        max_value=20.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="imp_amp",
                        label="Impulse amp (m/s^2)",
                        default_value=self.params.impulse_amp_mps2,
                        min_value=5.0,
                        max_value=80.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="zeta",
                        label="Damping zeta",
                        default_value=self.params.zeta,
                        min_value=0.05,
                        max_value=1.5,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="out_bias",
                        label="Output bias (m/s^2)",
                        default_value=self.params.output_bias_mps2,
                        min_value=-5.0,
                        max_value=5.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="mech_off",
                        label="Mech. offset (um)",
                        default_value=self.params.mech_offset_um,
                        min_value=-0.5,
                        max_value=0.5,
                        callback=self._on_change,
                    )
                    with dpg.group(tag="advanced_controls"):
                        dpg.add_separator()
                        dpg.add_text("Advanced")
                        dpg.add_slider_float(
                            tag="imp_w",
                            label="Impulse width (ms)",
                            default_value=self.params.impulse_width_s * 1e3,
                            min_value=0.5,
                            max_value=10.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="duration",
                            label="Duration (s)",
                            default_value=self.params.duration_s,
                            min_value=0.1,
                            max_value=0.6,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="gap0",
                            label="Nominal gap (um)",
                            default_value=self.params.gap0_um,
                            min_value=1.0,
                            max_value=4.0,
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
                    dpg.add_drawlist(width=DRAW_W, height=DRAW_H, tag="comb_draw")
                    with dpg.plot(label="External accel vs measured accel", height=200, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="t (s)", tag="a_t")
                        with dpg.plot_axis(dpg.mvYAxis, label="m/s^2", tag="a_y"):
                            dpg.add_line_series([0.0], [0.0], label="a_ext", tag="a_ext")
                            dpg.add_line_series([0.0], [0.0], label="a_meas", tag="a_meas")
                            dpg.add_line_series([0.0, 0.0], [-1.0, 1.0], label="t cursor", tag="a_cursor")
                    with dpg.plot(label="Proof-mass displacement", height=180, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="t (s)", tag="x_t")
                        with dpg.plot_axis(dpg.mvYAxis, label="x (um)", tag="x_y"):
                            dpg.add_line_series([0.0], [0.0], label="x", tag="x_series")
                            dpg.add_line_series([0.0, 0.0], [-1.0, 1.0], label="t cursor", tag="x_cursor")
                    with dpg.plot(label="Comb capacitances", height=200, width=-1):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="t (s)", tag="c_t")
                        with dpg.plot_axis(dpg.mvYAxis, label="fF", tag="c_y"):
                            dpg.add_line_series([0.0], [0.0], label="C1", tag="c1_series")
                            dpg.add_line_series([0.0], [0.0], label="C2", tag="c2_series")
                            dpg.add_line_series([0.0], [0.0], label="C1-C2", tag="dc_series")
                            dpg.add_line_series([0.0, 0.0], [-1.0, 1.0], label="t cursor", tag="c_cursor")

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        self._push_controls(self.params)
        self.refresh()
        while dpg.is_dearpygui_running():
            self._tick()
            dpg.render_dearpygui_frame()
        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: MEMSAccelParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    MEMSAccelApp(initial=params, scenario_id=scenario_id).run()
