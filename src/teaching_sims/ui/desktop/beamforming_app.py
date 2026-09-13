"""Dear PyGui desktop app for digital beamforming teaching."""

from __future__ import annotations

import dearpygui.dearpygui as dpg
import numpy as np

from teaching_sims.topics.beamforming.physics import (
    BeamformerMethod,
    BeamformerParams,
    apply_diagonal_loading,
    beampattern_db,
    beamformer_weights,
    capon_spectrum_db,
    conventional_weights,
    eigenvalues_db,
    output_sinr_db,
    sample_covariance,
)
from teaching_sims.topics.beamforming.scenarios import SCENARIOS, get_scenario


THETA = np.linspace(-90.0, 90.0, 721)
METHOD_LABELS = {
    "Conventional": BeamformerMethod.CONVENTIONAL,
    "MVDR": BeamformerMethod.MVDR,
    "Null steer": BeamformerMethod.NULL_STEER,
}
LABEL_FOR_METHOD = {v: k for k, v in METHOD_LABELS.items()}


def _fxy(xs, ys):
    return [[float(v) for v in xs], [float(v) for v in ys]]


class BeamformingApp:
    def __init__(self, initial: BeamformerParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or BeamformerParams()
        self.scenario_id = scenario_id
        self._compare = False
        self._presenter = False
        self._annotation_tags: list[str] = []
        self._seed_counter = self.params.seed
        if scenario_id:
            sc = get_scenario(scenario_id)
            self.params = sc.params
            self._compare = sc.compare_methods
            self._title = sc.title
            self._note = f"{sc.teaching_point}\n{sc.notes}"
        else:
            self._title = "Digital beamforming"
            self._note = "Conventional, null-steer, and MVDR on a ULA with an optional interferer."

    def _read_controls(self) -> BeamformerParams:
        method = METHOD_LABELS[dpg.get_value("method")]
        loading = float(dpg.get_value("loading_db"))
        # UI uses -40 as "off"
        if loading <= -39.5:
            loading = float(-np.inf)
        return BeamformerParams(
            n_elements=int(dpg.get_value("n_elements")),
            d_over_lambda=float(dpg.get_value("d_over_lambda")),
            look_deg=float(dpg.get_value("look_deg")),
            signal_deg=float(dpg.get_value("signal_deg")),
            interferer_deg=float(dpg.get_value("interferer_deg")),
            interferer_enabled=bool(dpg.get_value("interferer_on")),
            snr_db=float(dpg.get_value("snr_db")),
            inr_db=float(dpg.get_value("inr_db")),
            n_snapshots=int(dpg.get_value("n_snapshots")),
            method=method,
            null_deg=float(dpg.get_value("null_deg")),
            diagonal_loading_db=loading,
            seed=self._seed_counter,
        )

    def _push_controls(self, p: BeamformerParams) -> None:
        dpg.set_value("n_elements", p.n_elements)
        dpg.set_value("d_over_lambda", p.d_over_lambda)
        dpg.set_value("look_deg", p.look_deg)
        dpg.set_value("signal_deg", p.signal_deg)
        dpg.set_value("interferer_deg", p.interferer_deg)
        dpg.set_value("interferer_on", p.interferer_enabled)
        dpg.set_value("snr_db", p.snr_db)
        dpg.set_value("inr_db", p.inr_db)
        dpg.set_value("n_snapshots", p.n_snapshots)
        dpg.set_value("method", LABEL_FOR_METHOD[p.method])
        dpg.set_value("null_deg", p.null_deg)
        load = -40.0 if not np.isfinite(p.diagonal_loading_db) else p.diagonal_loading_db
        dpg.set_value("loading_db", load)
        self._seed_counter = p.seed

    def _apply_scenario(self, scenario_id: str) -> None:
        sc = get_scenario(scenario_id)
        self.scenario_id = scenario_id
        self.params = sc.params
        self._compare = sc.compare_methods
        self._title = sc.title
        self._note = f"{sc.teaching_point}\n{sc.notes}"
        self._push_controls(self.params)
        dpg.set_value("compare_methods", self._compare)
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
        self._seed_counter += 1
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
            parent="bf_pattern_plot",
        )
        self._annotation_tags.append(tag)

    def refresh(self) -> None:
        self.params = self._read_controls()
        self._compare = bool(dpg.get_value("compare_methods"))
        p = self.params

        R, _ = sample_covariance(p)
        w = beamformer_weights(p, R)
        pdb = beampattern_db(w, THETA, p.d_over_lambda)
        theta_f = [float(v) for v in THETA]
        dpg.set_value("pattern_series", [theta_f, [float(v) for v in pdb]])

        if self._compare:
            w_c = conventional_weights(p.look_deg, p.n_elements, p.d_over_lambda)
            pdb_c = beampattern_db(w_c, THETA, p.d_over_lambda)
            dpg.set_value("compare_series", [theta_f, [float(v) for v in pdb_c]])
            dpg.configure_item("compare_series", show=True)
        else:
            dpg.configure_item("compare_series", show=False)

        # Capon spectrum
        R_load = apply_diagonal_loading(R, p.diagonal_loading_db)
        cap = capon_spectrum_db(R_load, THETA, p.d_over_lambda)
        dpg.set_value("capon_series", [theta_f, [float(v) for v in cap]])

        # Markers: look / SOI / interferer
        def vline(tag: str, ang: float, show: bool) -> None:
            dpg.set_value(tag, [[float(ang), float(ang)], [-50.0, 1.0]])
            dpg.configure_item(tag, show=show)

        vline("look_marker", p.look_deg, True)
        vline("soi_marker", p.signal_deg, True)
        vline("intf_marker", p.interferer_deg, p.interferer_enabled)

        self._clear_annotations()
        self._ann("ann_look", f"look {p.look_deg:.1f}°", p.look_deg, 0.0, (8, -16))
        if p.interferer_enabled:
            y_i = float(np.interp(p.interferer_deg, THETA, pdb))
            self._ann("ann_intf", f"interferer {p.interferer_deg:.1f}°", p.interferer_deg, y_i, (8, 12))

        # Weights
        mag = np.abs(w)
        ph = np.rad2deg(np.unwrap(np.angle(w)))
        idx = list(range(len(w)))
        dpg.set_value("weight_mag", _fxy(idx, mag / (np.max(mag) + 1e-15)))
        dpg.set_value("weight_phase", _fxy(idx, ph))
        ph_min = float(np.min(ph)) if len(ph) else -180.0
        ph_max = float(np.max(ph)) if len(ph) else 180.0
        if abs(ph_max - ph_min) < 1.0:
            ph_min -= 10.0
            ph_max += 10.0
        pad = 0.12 * (ph_max - ph_min)
        dpg.set_axis_limits("weight_phase_y", ph_min - pad, ph_max + pad)
        dpg.set_axis_limits("weight_phase_x", -0.5, max(len(w) - 0.5, 0.5))

        # Eigenvalues
        ev = eigenvalues_db(R)
        dpg.set_value("eigs_series", _fxy(list(range(len(ev))), ev))
        ev_min = float(np.min(ev))
        ev_max = float(np.max(ev))
        ev_pad = 0.1 * max(ev_max - ev_min, 1.0)
        dpg.set_axis_limits("eigs_y", ev_min - ev_pad, ev_max + ev_pad)

        sinr = output_sinr_db(p, w)
        sinr_c = output_sinr_db(p, conventional_weights(p.look_deg, p.n_elements, p.d_over_lambda))
        load_txt = "off" if not np.isfinite(p.diagonal_loading_db) else f"{p.diagonal_loading_db:.1f} dB"
        dpg.set_value(
            "status_text",
            (
                f"Method: {LABEL_FOR_METHOD[p.method]}   N={p.n_elements}   "
                f"snapshots={p.n_snapshots}   loading={load_txt}\n"
                f"Analytical SINR: {sinr:.1f} dB"
                + (f"   (conventional would be {sinr_c:.1f} dB)" if p.method != BeamformerMethod.CONVENTIONAL else "")
                + f"\nSOI {p.signal_deg:.1f}° @ SNR {p.snr_db:.0f} dB"
                + (
                    f"   |   interferer {p.interferer_deg:.1f}° @ INR {p.inr_db:.0f} dB"
                    if p.interferer_enabled
                    else "   |   no interferer"
                )
            ),
        )
        dpg.set_value("banner_title", self._title)
        dpg.set_value("banner_body", self._note)

    def _on_change(self, *_a, **_k) -> None:
        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims — Digital Beamforming", width=1480, height=980)

        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.theme() as compare_theme:
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, (255, 120, 90), category=dpg.mvThemeCat_Plots)

        with dpg.window(tag="primary", label="Beamforming"):
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
                        tag="compare_methods",
                        label="Overlay conventional pattern",
                        default_value=self._compare,
                        callback=self._on_change,
                    )
                    dpg.add_button(label="Resample snapshots", width=-1, callback=lambda: self._resample())
                    dpg.add_separator()
                    dpg.add_text("Core")
                    dpg.add_combo(
                        tag="method",
                        label="Beamformer",
                        items=list(METHOD_LABELS.keys()),
                        default_value=LABEL_FOR_METHOD[self.params.method],
                        callback=self._on_change,
                    )
                    dpg.add_slider_int(
                        tag="n_elements",
                        label="N elements",
                        default_value=self.params.n_elements,
                        min_value=2,
                        max_value=32,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="d_over_lambda",
                        label="d / λ",
                        default_value=self.params.d_over_lambda,
                        min_value=0.25,
                        max_value=1.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="look_deg",
                        label="Look θ (deg)",
                        default_value=self.params.look_deg,
                        min_value=-60.0,
                        max_value=60.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="signal_deg",
                        label="SOI θ (deg)",
                        default_value=self.params.signal_deg,
                        min_value=-60.0,
                        max_value=60.0,
                        callback=self._on_change,
                    )
                    dpg.add_checkbox(
                        tag="interferer_on",
                        label="Enable interferer",
                        default_value=self.params.interferer_enabled,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="interferer_deg",
                        label="Interferer θ (deg)",
                        default_value=self.params.interferer_deg,
                        min_value=-60.0,
                        max_value=60.0,
                        callback=self._on_change,
                    )

                    with dpg.group(tag="advanced_controls"):
                        dpg.add_separator()
                        dpg.add_text("Advanced")
                        dpg.add_slider_float(
                            tag="snr_db",
                            label="SNR (dB)",
                            default_value=self.params.snr_db,
                            min_value=-5.0,
                            max_value=40.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="inr_db",
                            label="INR (dB)",
                            default_value=self.params.inr_db,
                            min_value=0.0,
                            max_value=40.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_int(
                            tag="n_snapshots",
                            label="Snapshots L",
                            default_value=self.params.n_snapshots,
                            min_value=8,
                            max_value=1000,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="null_deg",
                            label="Null-steer θ (deg)",
                            default_value=self.params.null_deg,
                            min_value=-60.0,
                            max_value=60.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="loading_db",
                            label="Diag. loading (dB, -40=off)",
                            default_value=(
                                -40.0
                                if not np.isfinite(self.params.diagonal_loading_db)
                                else self.params.diagonal_loading_db
                            ),
                            min_value=-40.0,
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
                    with dpg.plot(
                        label="Beampattern |wᴴa(θ)|² (dB)",
                        height=300,
                        width=-1,
                        tag="bf_pattern_plot",
                    ):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="θ (deg)", tag="bf_x")
                        dpg.set_axis_limits("bf_x", -90, 90)
                        with dpg.plot_axis(dpg.mvYAxis, label="dB", tag="bf_y"):
                            dpg.set_axis_limits("bf_y", -50, 1)
                            dpg.add_line_series(
                                list(THETA), [0.0] * len(THETA), label="pattern", tag="pattern_series"
                            )
                            cmp = dpg.add_line_series(
                                [0.0], [-100.0], label="conventional", tag="compare_series", show=False
                            )
                            dpg.bind_item_theme(cmp, compare_theme)
                            dpg.add_line_series([0, 0], [-50, 1], label="look", tag="look_marker")
                            dpg.add_line_series([0, 0], [-50, 1], label="SOI", tag="soi_marker")
                            dpg.add_line_series(
                                [0, 0], [-50, 1], label="interferer", tag="intf_marker", show=False
                            )

                    with dpg.group(horizontal=True):
                        with dpg.plot(label="Capon / MVDR spectrum", height=250, width=520):
                            dpg.add_plot_axis(dpg.mvXAxis, label="θ (deg)")
                            dpg.set_axis_limits(dpg.last_item(), -90, 90)
                            with dpg.plot_axis(dpg.mvYAxis, label="dB"):
                                dpg.set_axis_limits(dpg.last_item(), -40, 1)
                                dpg.add_line_series(
                                    list(THETA), [0.0] * len(THETA), label="Capon", tag="capon_series"
                                )

                        with dpg.plot(label="|w| (normalised)", height=250, width=320):
                            dpg.add_plot_axis(dpg.mvXAxis, label="element")
                            with dpg.plot_axis(dpg.mvYAxis, label="|w|"):
                                dpg.set_axis_limits(dpg.last_item(), 0.0, 1.15)
                                dpg.add_stem_series([0.0], [1.0], label="|w|", tag="weight_mag")

                        with dpg.plot(label="Eigenvalues of R (dB)", height=250, width=-1):
                            dpg.add_plot_axis(dpg.mvXAxis, label="index")
                            with dpg.plot_axis(dpg.mvYAxis, label="dB", tag="eigs_y"):
                                dpg.add_stem_series([0.0], [0.0], label="λ", tag="eigs_series")

                    with dpg.plot(label="∠w (unwrap, deg)", height=300, width=-1, tag="weight_phase_plot"):
                        dpg.add_plot_axis(dpg.mvXAxis, label="element", tag="weight_phase_x")
                        with dpg.plot_axis(dpg.mvYAxis, label="phase (deg)", tag="weight_phase_y"):
                            dpg.add_line_series([0.0], [0.0], label="∠w", tag="weight_phase")

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        self._push_controls(self.params)
        dpg.set_value("compare_methods", self._compare)
        self.refresh()

        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()

        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: BeamformerParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    BeamformingApp(initial=params, scenario_id=scenario_id).run()
