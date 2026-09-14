"""Dear PyGui desktop app for CFAR detection teaching."""

from __future__ import annotations

import dearpygui.dearpygui as dpg
import numpy as np

from teaching_sims.topics.cfar.physics import (
    CFARMethod,
    CFARParams,
    CFARTarget,
    process,
)
from teaching_sims.topics.cfar.scenarios import SCENARIOS, get_scenario


METHOD_LABELS = {
    "CA-CFAR": CFARMethod.CA,
    "OS-CFAR": CFARMethod.OS,
    "GO-CFAR": CFARMethod.GO,
    "SO-CFAR": CFARMethod.SO,
}
LABEL_FOR_METHOD = {v: k for k, v in METHOD_LABELS.items()}


def _fxy(xs, ys):
    return [[float(v) for v in xs], [float(v) for v in ys]]


class CFARApp:
    def __init__(self, initial: CFARParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or CFARParams()
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
            self._title = "CFAR detection"
            self._note = "Adaptive thresholds on a range profile: CA, OS, GO, and SO CFAR."

    def _read_controls(self) -> CFARParams:
        method = METHOD_LABELS[dpg.get_value("method")]
        targets = (
            CFARTarget(int(dpg.get_value("t1_cell")), snr_db=float(dpg.get_value("t1_snr"))),
        )
        if dpg.get_value("t2_on"):
            targets = (
                targets[0],
                CFARTarget(int(dpg.get_value("t2_cell")), snr_db=float(dpg.get_value("t2_snr"))),
            )
        # P_fa from log10 slider: -2 ... -5 -> 1e-2 ... 1e-5
        pfa = 10 ** float(dpg.get_value("pfa_exp"))
        return CFARParams(
            n_cells=int(dpg.get_value("n_cells")),
            n_train=int(dpg.get_value("n_train")),
            n_guard=int(dpg.get_value("n_guard")),
            pfa=pfa,
            method=method,
            os_rank=int(dpg.get_value("os_rank")),
            targets=targets,
            clutter_edge_enabled=bool(dpg.get_value("clutter_on")),
            clutter_edge_cell=int(dpg.get_value("clutter_cell")),
            clutter_ratio_db=float(dpg.get_value("clutter_db")),
            seed=self._seed,
        )

    def _push_controls(self, p: CFARParams) -> None:
        dpg.set_value("method", LABEL_FOR_METHOD[p.method])
        dpg.set_value("n_cells", p.n_cells)
        dpg.set_value("n_train", p.n_train)
        dpg.set_value("n_guard", p.n_guard)
        dpg.set_value("pfa_exp", float(np.log10(p.pfa)))
        dpg.set_value("os_rank", p.os_rank)
        dpg.set_value("clutter_on", p.clutter_edge_enabled)
        dpg.set_value("clutter_cell", p.clutter_edge_cell)
        dpg.set_value("clutter_db", p.clutter_ratio_db)
        dpg.set_value("t1_cell", p.targets[0].cell)
        dpg.set_value("t1_snr", p.targets[0].snr_db)
        if len(p.targets) > 1:
            dpg.set_value("t2_on", True)
            dpg.set_value("t2_cell", p.targets[1].cell)
            dpg.set_value("t2_snr", p.targets[1].snr_db)
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
            parent="cfar_plot",
        )
        self._annotation_tags.append(tag)

    def refresh(self) -> None:
        try:
            self.params = self._read_controls()
        except ValueError as exc:
            dpg.set_value("status_text", f"Invalid settings: {exc}")
            return

        p = self.params
        out = process(p)
        cells = np.arange(p.n_cells, dtype=float)
        pdb = out["power_db"]
        tdb = out["threshold_db"]
        fdb = out["fixed_threshold_db"]
        detected = out["detected"]

        dpg.set_value("power_series", _fxy(cells, pdb))
        # Replace NaN thresholds with a low sentinel so the line breaks visually
        t_plot = np.where(np.isfinite(tdb), tdb, np.nan)
        # Dear PyGui may not like NaN - use previous finite or floor
        t_fill = np.copy(t_plot)
        last = float(np.nanmin(pdb) - 5)
        for i, v in enumerate(t_fill):
            if np.isfinite(v):
                last = float(v)
            else:
                t_fill[i] = last
        dpg.set_value("thr_series", _fxy(cells, t_fill))
        dpg.set_value("fixed_series", _fxy(cells, fdb))
        dpg.configure_item("fixed_series", show=bool(dpg.get_value("show_fixed")))

        det_x = cells[detected]
        det_y = pdb[detected]
        if det_x.size:
            dpg.set_value("det_scatter", _fxy(det_x, det_y))
            dpg.configure_item("det_scatter", show=True)
        else:
            dpg.configure_item("det_scatter", show=False)

        dpg.set_axis_limits("cfar_x", 0, p.n_cells - 1)
        ymin = float(np.nanmin(pdb)) - 3
        ymax = float(np.nanmax(np.concatenate([pdb, t_fill]))) + 3
        dpg.set_axis_limits("cfar_y", ymin, ymax)

        if p.clutter_edge_enabled:
            dpg.set_value(
                "edge_marker",
                [[float(p.clutter_edge_cell), float(p.clutter_edge_cell)], [ymin, ymax]],
            )
            dpg.configure_item("edge_marker", show=True)
        else:
            dpg.configure_item("edge_marker", show=False)

        self._clear_annotations()
        for i, tgt in enumerate(p.targets):
            self._ann(
                f"ann_t{i}",
                f"T{i+1} cell {tgt.cell} ({tgt.snr_db:.0f} dB)",
                float(tgt.cell),
                float(pdb[tgt.cell]),
                (8, -14 if i == 0 else 12),
            )

        report = out["report"]
        dpg.set_value(
            "status_text",
            (
                f"{LABEL_FOR_METHOD[p.method]}   P_fa={p.pfa:.1e}   "
                f"train={p.n_train}/side   guard={p.n_guard}/side\n"
                f"Hits: {report['hits']}   Misses: {report['misses']}   "
                f"CFAR FAs: {report['false_alarms']}\n"
                f"Detections: {report['n_detections']}   alpha_CA~{out['alpha_ca']:.2f}"
            ),
        )
        dpg.set_value("banner_title", self._title)
        dpg.set_value("banner_body", self._note)

        # Window schematic data (relative positions)
        g, t = p.n_guard, p.n_train
        # Show CUT | guards | training as a simple stem sketch around 0
        schematic_x = list(range(-(t + g), t + g + 1))
        schematic_y = []
        for x in schematic_x:
            if x == 0:
                schematic_y.append(1.0)
            elif abs(x) <= g:
                schematic_y.append(0.35)
            else:
                schematic_y.append(0.7)
        dpg.set_value("window_series", _fxy(schematic_x, schematic_y))

    def _on_change(self, *_a, **_k) -> None:
        self.refresh()

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims - CFAR Detection", width=1480, height=920)

        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.theme() as thr_theme:
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, (255, 180, 60), category=dpg.mvThemeCat_Plots)
        with dpg.theme() as fixed_theme:
            with dpg.theme_component(dpg.mvLineSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, (160, 160, 170), category=dpg.mvThemeCat_Plots)
        with dpg.theme() as det_theme:
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, (80, 220, 120), category=dpg.mvThemeCat_Plots)

        with dpg.window(tag="primary", label="CFAR"):
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
                        tag="show_fixed",
                        label="Overlay fixed threshold",
                        default_value=True,
                        callback=self._on_change,
                    )
                    dpg.add_button(label="Resample noise", width=-1, callback=lambda: self._resample())
                    dpg.add_separator()
                    dpg.add_text("Core")
                    dpg.add_combo(
                        tag="method",
                        label="CFAR method",
                        items=list(METHOD_LABELS.keys()),
                        default_value=LABEL_FOR_METHOD[self.params.method],
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="pfa_exp",
                        label="log10(P_fa)",
                        default_value=float(np.log10(self.params.pfa)),
                        min_value=-5.0,
                        max_value=-1.5,
                        callback=self._on_change,
                    )
                    dpg.add_slider_int(
                        tag="n_train",
                        label="Training cells / side",
                        default_value=self.params.n_train,
                        min_value=4,
                        max_value=32,
                        callback=self._on_change,
                    )
                    dpg.add_slider_int(
                        tag="n_guard",
                        label="Guard cells / side",
                        default_value=self.params.n_guard,
                        min_value=0,
                        max_value=8,
                        callback=self._on_change,
                    )
                    dpg.add_slider_int(
                        tag="t1_cell",
                        label="Target 1 cell",
                        default_value=self.params.targets[0].cell,
                        min_value=20,
                        max_value=230,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="t1_snr",
                        label="Target 1 SNR (dB)",
                        default_value=self.params.targets[0].snr_db,
                        min_value=5.0,
                        max_value=35.0,
                        callback=self._on_change,
                    )
                    dpg.add_checkbox(
                        tag="t2_on",
                        label="Enable target 2",
                        default_value=len(self.params.targets) > 1,
                        callback=self._on_change,
                    )
                    dpg.add_slider_int(
                        tag="t2_cell",
                        label="Target 2 cell",
                        default_value=self.params.targets[1].cell if len(self.params.targets) > 1 else 160,
                        min_value=20,
                        max_value=230,
                        callback=self._on_change,
                    )
                    dpg.add_checkbox(
                        tag="clutter_on",
                        label="Clutter edge",
                        default_value=self.params.clutter_edge_enabled,
                        callback=self._on_change,
                    )

                    with dpg.group(tag="advanced_controls"):
                        dpg.add_separator()
                        dpg.add_text("Advanced")
                        dpg.add_slider_int(
                            tag="n_cells",
                            label="Profile length",
                            default_value=self.params.n_cells,
                            min_value=128,
                            max_value=512,
                            callback=self._on_change,
                        )
                        dpg.add_slider_int(
                            tag="os_rank",
                            label="OS rank k (k-th largest)",
                            default_value=self.params.os_rank,
                            min_value=1,
                            max_value=12,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="t2_snr",
                            label="Target 2 SNR (dB)",
                            default_value=self.params.targets[1].snr_db if len(self.params.targets) > 1 else 14.0,
                            min_value=5.0,
                            max_value=35.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_int(
                            tag="clutter_cell",
                            label="Clutter edge cell",
                            default_value=self.params.clutter_edge_cell,
                            min_value=40,
                            max_value=220,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="clutter_db",
                            label="Clutter step (dB)",
                            default_value=self.params.clutter_ratio_db,
                            min_value=3.0,
                            max_value=25.0,
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
                        label="Range profile (dB) with CFAR threshold",
                        height=480,
                        width=-1,
                        tag="cfar_plot",
                    ):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="range cell", tag="cfar_x")
                        with dpg.plot_axis(dpg.mvYAxis, label="power (dB)", tag="cfar_y"):
                            dpg.add_line_series([0.0], [0.0], label="power", tag="power_series")
                            thr = dpg.add_line_series([0.0], [0.0], label="CFAR threshold", tag="thr_series")
                            dpg.bind_item_theme(thr, thr_theme)
                            fix = dpg.add_line_series(
                                [0.0], [0.0], label="fixed threshold", tag="fixed_series"
                            )
                            dpg.bind_item_theme(fix, fixed_theme)
                            dpg.add_line_series(
                                [0.0, 0.0], [0.0, 1.0], label="clutter edge", tag="edge_marker", show=False
                            )
                            det = dpg.add_scatter_series(
                                [0.0], [0.0], label="detections", tag="det_scatter"
                            )
                            dpg.bind_item_theme(det, det_theme)

                    with dpg.plot(label="CFAR window schematic (CUT / guard / train)", height=220, width=-1):
                        dpg.add_plot_axis(dpg.mvXAxis, label="cell offset from CUT")
                        with dpg.plot_axis(dpg.mvYAxis, label="role"):
                            dpg.set_axis_limits(dpg.last_item(), 0, 1.2)
                            dpg.add_stem_series([0.0], [1.0], label="window", tag="window_series")

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        self._push_controls(self.params)
        self.refresh()

        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()

        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: CFARParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    CFARApp(initial=params, scenario_id=scenario_id).run()
