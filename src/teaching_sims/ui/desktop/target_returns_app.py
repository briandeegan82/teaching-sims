"""Dear PyGui demo: radar returns for objects of various sizes and shapes."""

from __future__ import annotations

import time

import dearpygui.dearpygui as dpg
import numpy as np

from teaching_sims.topics.target_returns.physics import TargetReturnsParams, TargetShape, process
from teaching_sims.topics.target_returns.scenarios import SCENARIOS, get_scenario
from teaching_sims.ui.desktop.plot_utils import fxy as _fxy


DRAW_W = 420
DRAW_H = 220
WAVE_W = 980
WAVE_H = 260

SHAPE_LABELS = {
    "Sphere": TargetShape.SPHERE,
    "Flat plate": TargetShape.FLAT_PLATE,
    "Cylinder": TargetShape.CYLINDER,
    "Corner reflector": TargetShape.CORNER,
    "Extended body": TargetShape.EXTENDED,
}
LABEL_FOR_SHAPE = {v: k for k, v in SHAPE_LABELS.items()}

COMPARE_ORDER = [
    TargetShape.SPHERE,
    TargetShape.FLAT_PLATE,
    TargetShape.CYLINDER,
    TargetShape.CORNER,
    TargetShape.EXTENDED,
]
COMPARE_SHORT = {
    TargetShape.SPHERE: "sphere",
    TargetShape.FLAT_PLATE: "plate",
    TargetShape.CYLINDER: "cyl",
    TargetShape.CORNER: "corner",
    TargetShape.EXTENDED: "ext",
}


def _arrow(tip, tail, *, color, thickness: float = 2, size: int = 7, parent: str) -> None:
    """Dear PyGui draw_arrow uses (tip, tail) — tip is where the arrow points."""
    dpg.draw_arrow(tip, tail, color=color, thickness=thickness, size=size, parent=parent)


class TargetReturnsApp:
    def __init__(self, initial: TargetReturnsParams | None = None, scenario_id: str | None = None) -> None:
        self.params = initial or TargetReturnsParams()
        self.scenario_id = scenario_id
        self._presenter = False
        self._suppress = False
        self._seed = self.params.seed
        self._wave_playing = True
        self._wave_t0 = time.monotonic()
        self._wave_speed = 0.35
        self._wave_phase = 0.0
        if scenario_id:
            sc = get_scenario(scenario_id)
            self.params = sc.params
            self._seed = sc.params.seed
            self._title = sc.title
            self._note = f"{sc.teaching_point}\n{sc.notes}"
        else:
            self._title = "Target returns (size and shape)"
            self._note = (
                "RCS depends on shape, size, wavelength, and aspect. "
                "Watch wavefronts scatter: plates reflect specularly, spheres spread, corners send energy back."
            )

    def _sync_wave_speed(self) -> None:
        if dpg.does_item_exist("wave_speed"):
            self._wave_speed = max(0.05, float(dpg.get_value("wave_speed")))

    def _play_waves(self) -> None:
        self._sync_wave_speed()
        self._wave_playing = True
        # Re-anchor so phase is continuous
        self._wave_t0 = time.monotonic() - self._wave_phase / max(self._wave_speed, 1e-6)

    def _pause_waves(self) -> None:
        self._wave_playing = False

    def _on_wave_speed(self, *_a, **_k) -> None:
        if self._suppress:
            return
        old_speed = self._wave_speed
        self._sync_wave_speed()
        if self._wave_playing and old_speed > 0:
            self._wave_t0 = time.monotonic() - self._wave_phase / self._wave_speed

    def _tick(self) -> None:
        if not self._wave_playing:
            return
        self._sync_wave_speed()
        self._wave_phase = (time.monotonic() - self._wave_t0) * self._wave_speed
        self._draw_wavefronts(self.params, self._wave_phase)

    def _read_controls(self) -> TargetReturnsParams:
        return TargetReturnsParams(
            shape=SHAPE_LABELS[dpg.get_value("shape")],
            size_m=float(dpg.get_value("size_m")),
            size2_m=float(dpg.get_value("size2_m")),
            aspect_deg=float(dpg.get_value("aspect_deg")),
            range_m=float(dpg.get_value("range_km")) * 1e3,
            frequency_hz=float(dpg.get_value("freq_ghz")) * 1e9,
            snr_ref_db=float(dpg.get_value("snr_ref_db")),
            pulse_width_s=float(dpg.get_value("tp_us")) * 1e-6,
            sample_rate_hz=40e6,
            pri_s=100e-6,
            noise_enabled=bool(dpg.get_value("noise_on")),
            seed=self._seed,
        )

    def _push_controls(self, p: TargetReturnsParams) -> None:
        self._suppress = True
        try:
            dpg.set_value("shape", LABEL_FOR_SHAPE[p.shape])
            dpg.set_value("size_m", p.size_m)
            dpg.set_value("size2_m", p.size2_m)
            dpg.set_value("aspect_deg", p.aspect_deg)
            dpg.set_value("range_km", p.range_m / 1e3)
            dpg.set_value("freq_ghz", p.frequency_hz / 1e9)
            dpg.set_value("snr_ref_db", p.snr_ref_db)
            dpg.set_value("tp_us", p.pulse_width_s * 1e6)
            dpg.set_value("noise_on", p.noise_enabled)
        finally:
            self._suppress = False
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

    def _on_change(self, *_a, **_k) -> None:
        if self._suppress:
            return
        self.refresh()

    def _resample(self) -> None:
        self._seed += 1
        self.refresh()

    def _draw_shape(self, p: TargetReturnsParams) -> None:
        if not dpg.does_item_exist("shape_draw"):
            return
        dpg.delete_item("shape_draw", children_only=True)

        # Top-down view: radar LOS fixed from the right; object rotates with aspect.
        # aspect=0 -> face-on / broadside (normal points at radar); 90 -> edge-on / end-on.
        cx, cy = DRAW_W * 0.40, DRAW_H * 0.58
        asp = float(np.deg2rad(p.aspect_deg))
        c_a, s_a = float(np.cos(asp)), float(np.sin(asp))
        s = float(np.clip(p.size_m, 0.2, 8.0))
        s2 = float(np.clip(p.size2_m, 0.2, 8.0))

        los_col = (140, 220, 140, 255)
        obj_col = (90, 140, 200, 255)
        edge_col = (230, 230, 240, 255)
        normal_col = (255, 180, 80, 255)

        dpg.draw_text(
            (10, 8),
            f"Target: {LABEL_FOR_SHAPE[p.shape]}  (top-down)",
            size=15,
            color=(220, 220, 230),
            parent="shape_draw",
        )

        # Radar LOS (fixed): arrow points toward the target (left)
        _arrow((cx + 95, cy), (DRAW_W - 18, cy), color=los_col, thickness=2, size=8, parent="shape_draw")
        dpg.draw_text((DRAW_W - 100, cy - 22), "radar LOS", size=12, color=(160, 200, 160), parent="shape_draw")

        aspect_matters = p.shape in (
            TargetShape.FLAT_PLATE,
            TargetShape.CYLINDER,
            TargetShape.EXTENDED,
        )

        if p.shape == TargetShape.SPHERE:
            r = min(18.0 + 10.0 * s, 64.0)
            dpg.draw_circle((cx, cy), r, fill=obj_col, color=edge_col, thickness=2, parent="shape_draw")
            dpg.draw_text((10, 48), "Aspect has no effect (isotropic)", size=12, color=(180, 180, 160), parent="shape_draw")

        elif p.shape == TargetShape.CORNER:
            # Fixed open corner facing the radar
            dpg.draw_line((cx - 8, cy + 36), (cx + 50, cy + 10), color=normal_col, thickness=3, parent="shape_draw")
            dpg.draw_line((cx - 8, cy + 36), (cx + 50, cy + 55), color=normal_col, thickness=3, parent="shape_draw")
            dpg.draw_line((cx + 50, cy + 10), (cx + 50, cy + 55), color=normal_col, thickness=2, parent="shape_draw")
            dpg.draw_text((10, 48), "Aspect ignored (always bright model)", size=12, color=(180, 180, 160), parent="shape_draw")

        elif p.shape == TargetShape.FLAT_PLATE:
            # Thin plate in plan view: face along tangent, normal swings with aspect
            half_w = min(16.0 + 10.0 * s2, 70.0)
            nx, ny = c_a, -s_a  # surface normal (points at radar when aspect=0)
            tx, ty = s_a, c_a  # along the plate face
            face = [
                (cx + nx * 3 + tx * half_w, cy + ny * 3 + ty * half_w),
                (cx + nx * 3 - tx * half_w, cy + ny * 3 - ty * half_w),
                (cx - nx * 3 - tx * half_w, cy - ny * 3 - ty * half_w),
                (cx - nx * 3 + tx * half_w, cy - ny * 3 + ty * half_w),
            ]
            for i in range(4):
                dpg.draw_line(face[i], face[(i + 1) % 4], color=edge_col, thickness=2, parent="shape_draw")
            dpg.draw_line(face[0], face[1], color=obj_col, thickness=4, parent="shape_draw")
            _arrow(
                (cx + nx * 55, cy + ny * 55),
                (cx, cy),
                color=normal_col,
                thickness=2,
                size=7,
                parent="shape_draw",
            )
            dpg.draw_text(
                (cx + nx * 58, cy + ny * 58 - 8),
                "normal",
                size=12,
                color=normal_col[:3],
                parent="shape_draw",
            )

        elif p.shape == TargetShape.CYLINDER:
            # Axis: vertical at aspect 0 (broadside), along LOS at aspect 90 (end-on)
            ax, ay = s_a, -c_a
            length = min(30.0 + 12.0 * s2, 90.0)
            rad = min(10.0 + 5.0 * s, 28.0)
            rad_draw = rad * max(abs(c_a), 0.25)
            dpg.draw_line(
                (cx - ax * length, cy - ay * length),
                (cx + ax * length, cy + ay * length),
                color=edge_col,
                thickness=2,
                parent="shape_draw",
            )
            dpg.draw_line(
                (cx - ax * length * 0.85, cy - ay * length * 0.85),
                (cx + ax * length * 0.85, cy + ay * length * 0.85),
                color=obj_col,
                thickness=max(int(2 * rad_draw), 6),
                parent="shape_draw",
            )
            dpg.draw_circle(
                (cx - ax * length, cy - ay * length),
                rad_draw * 0.7,
                color=edge_col,
                fill=(70, 100, 140, 255),
                thickness=1,
                parent="shape_draw",
            )
            dpg.draw_circle(
                (cx + ax * length, cy + ay * length),
                rad_draw * 0.7,
                color=edge_col,
                fill=(70, 100, 140, 255),
                thickness=1,
                parent="shape_draw",
            )
            nx, ny = c_a, -s_a
            _arrow(
                (cx + nx * 50, cy + ny * 50),
                (cx, cy),
                color=normal_col,
                thickness=2,
                size=7,
                parent="shape_draw",
            )
            dpg.draw_text(
                (cx + nx * 52, cy + ny * 52 - 8),
                "broadside",
                size=12,
                color=normal_col[:3],
                parent="shape_draw",
            )

        else:  # EXTENDED body — long rectangle rotates from across-track to along-LOS
            length = min(36.0 + 2.5 * s, 120.0)
            width = min(14.0 + 3.0 * s2, 40.0)
            ax, ay = s_a, -c_a
            tx, ty = c_a, s_a
            hl, hw = length / 2, width / 2
            corners = [
                (cx + ax * hl + tx * hw, cy + ay * hl + ty * hw),
                (cx + ax * hl - tx * hw, cy + ay * hl - ty * hw),
                (cx - ax * hl - tx * hw, cy - ay * hl - ty * hw),
                (cx - ax * hl + tx * hw, cy - ay * hl + ty * hw),
            ]
            for i in range(4):
                dpg.draw_line(corners[i], corners[(i + 1) % 4], color=edge_col, thickness=2, parent="shape_draw")
            dpg.draw_line(corners[0], corners[1], color=(100, 130, 90, 255), thickness=3, parent="shape_draw")
            dpg.draw_text((cx - 18, cy - 6), "body", size=12, color=(240, 240, 240), parent="shape_draw")
            _arrow(
                (cx + ax * hl * 0.9, cy + ay * hl * 0.9),
                (cx - ax * hl * 0.2, cy - ay * hl * 0.2),
                color=normal_col,
                thickness=2,
                size=6,
                parent="shape_draw",
            )

        if aspect_matters:
            # Arc between LOS and normal to show aspect angle
            nx, ny = c_a, -s_a
            arc_r = 38.0
            n_seg = max(int(p.aspect_deg / 5) + 1, 2)
            prev = (cx + arc_r, cy)  # along LOS
            for i in range(1, n_seg + 1):
                ang = asp * i / n_seg
                pt = (cx + arc_r * np.cos(ang), cy - arc_r * np.sin(ang))
                dpg.draw_line(prev, pt, color=(200, 160, 80, 200), thickness=1, parent="shape_draw")
                prev = pt
            dpg.draw_text(
                (cx + 44, cy - 36),
                f"aspect {p.aspect_deg:.0f} deg",
                size=13,
                color=(255, 200, 120),
                parent="shape_draw",
            )

        dpg.draw_text(
            (10, DRAW_H - 28),
            f"size={p.size_m:.2f} m  size2={p.size2_m:.2f} m  aspect={p.aspect_deg:.0f} deg",
            size=12,
            color=(170, 170, 180),
            parent="shape_draw",
        )

    def _draw_wavefronts(self, p: TargetReturnsParams, phase: float) -> None:
        """Animate a single pulse: incident (radar->target), then echo (target->radar)."""
        if not dpg.does_item_exist("wave_draw"):
            return
        dpg.delete_item("wave_draw", children_only=True)

        cx, cy = WAVE_W * 0.36, WAVE_H * 0.56
        asp = float(np.deg2rad(p.aspect_deg))
        c_a, s_a = float(np.cos(asp)), float(np.sin(asp))
        nx, ny = c_a, -s_a
        nvec = np.array([nx, ny], dtype=float)
        nvec /= np.linalg.norm(nvec) + 1e-12

        # Propagation unit vectors in screen space (x right, y down)
        ki = np.array([-1.0, 0.0])  # incident: right -> left
        kr = ki - 2.0 * float(np.dot(ki, nvec)) * nvec
        kr_n = float(np.linalg.norm(kr))
        kr = kr / kr_n if kr_n > 1e-12 else np.array([1.0, 0.0])
        # Monostatic return strength proxy: how much of specular heads toward radar (+x)
        backscatter = float(max(kr[0], 0.0))

        radar_xy = np.array([WAVE_W - 48.0, cy])
        # Object "hit point" facing the radar
        r_obj = 28.0
        mode = ""
        if p.shape == TargetShape.SPHERE:
            r_obj = 32.0
            mode = "isotropic scatter after impact"
        elif p.shape == TargetShape.FLAT_PLATE:
            r_obj = 10.0
            mode = "specular reflection"
        elif p.shape == TargetShape.CYLINDER:
            r_obj = 14.0
            mode = "specular (broadside) / weak end-on"
        elif p.shape == TargetShape.CORNER:
            r_obj = 22.0
            mode = "retro-reflection back to radar"
            kr = np.array([1.0, 0.0])  # force return along LOS
            backscatter = 1.0
        else:
            r_obj = 20.0
            mode = "distributed scatter along body"

        hit_xy = np.array([cx + r_obj, cy])  # illuminated side (toward radar)

        dpg.draw_text(
            (10, 6),
            "Wavefront pulse  |  green = TO target   cyan/orange = echo FROM target",
            size=14,
            color=(210, 210, 220),
            parent="wave_draw",
        )
        dpg.draw_text((10, 26), f"{LABEL_FOR_SHAPE[p.shape]}: {mode}", size=13, color=(180, 200, 220), parent="wave_draw")

        # Radar marker on the right
        dpg.draw_circle((float(radar_xy[0]), float(radar_xy[1])), 12, fill=(70, 110, 70, 255), color=(180, 230, 180, 255), thickness=2, parent="wave_draw")
        dpg.draw_text((WAVE_W - 78, cy - 28), "RADAR", size=12, color=(180, 230, 180), parent="wave_draw")
        # Direction legend (explicit)
        # Direction legend: DPG arrows are (tip, tail)
        _arrow((WAVE_W - 140, 48), (WAVE_W - 40, 48), color=(120, 220, 140, 255), thickness=2, size=7, parent="wave_draw")
        dpg.draw_text((WAVE_W - 250, 40), "incident", size=12, color=(150, 210, 150), parent="wave_draw")
        _arrow((WAVE_W - 40, 70), (WAVE_W - 250, 70), color=(100, 200, 255, 255), thickness=2, size=7, parent="wave_draw")
        dpg.draw_text((WAVE_W - 340, 62), "echo", size=12, color=(140, 190, 230), parent="wave_draw")

        # --- Object silhouette ---
        if p.shape == TargetShape.SPHERE:
            dpg.draw_circle((cx, cy), r_obj, fill=(70, 100, 150, 255), color=(230, 230, 240, 255), thickness=2, parent="wave_draw")
        elif p.shape == TargetShape.FLAT_PLATE:
            tx, ty = s_a, c_a
            hw = 55.0
            face = [
                (cx + nx * 3 + tx * hw, cy + ny * 3 + ty * hw),
                (cx + nx * 3 - tx * hw, cy + ny * 3 - ty * hw),
                (cx - nx * 3 - tx * hw, cy - ny * 3 - ty * hw),
                (cx - nx * 3 + tx * hw, cy - ny * 3 + ty * hw),
            ]
            for i in range(4):
                dpg.draw_line(face[i], face[(i + 1) % 4], color=(230, 230, 240, 255), thickness=2, parent="wave_draw")
            dpg.draw_line(face[0], face[1], color=(90, 140, 200, 255), thickness=4, parent="wave_draw")
            _arrow((cx + nx * 40, cy + ny * 40), (cx, cy), color=(255, 180, 80, 255), thickness=2, size=6, parent="wave_draw")
        elif p.shape == TargetShape.CYLINDER:
            ax, ay = s_a, -c_a
            length = 48.0
            dpg.draw_line(
                (cx - ax * length, cy - ay * length),
                (cx + ax * length, cy + ay * length),
                color=(90, 140, 200, 255),
                thickness=14,
                parent="wave_draw",
            )
            _arrow((cx + nx * 40, cy + ny * 40), (cx, cy), color=(255, 180, 80, 255), thickness=2, size=6, parent="wave_draw")
        elif p.shape == TargetShape.CORNER:
            dpg.draw_line((cx - 5, cy + 28), (cx + 38, cy + 4), color=(255, 180, 80, 255), thickness=3, parent="wave_draw")
            dpg.draw_line((cx - 5, cy + 28), (cx + 38, cy + 48), color=(255, 180, 80, 255), thickness=3, parent="wave_draw")
            dpg.draw_line((cx + 38, cy + 4), (cx + 38, cy + 48), color=(255, 180, 80, 255), thickness=2, parent="wave_draw")
        else:
            ax, ay = s_a, -c_a
            tx, ty = c_a, s_a
            hl, hw = 55.0, 16.0
            corners = [
                (cx + ax * hl + tx * hw, cy + ay * hl + ty * hw),
                (cx + ax * hl - tx * hw, cy + ay * hl - ty * hw),
                (cx - ax * hl - tx * hw, cy - ay * hl - ty * hw),
                (cx - ax * hl + tx * hw, cy - ay * hl + ty * hw),
            ]
            for i in range(4):
                dpg.draw_line(corners[i], corners[(i + 1) % 4], color=(230, 230, 240, 255), thickness=2, parent="wave_draw")

        # Path guidelines
        dpg.draw_line(
            (float(radar_xy[0]) - 14, cy),
            (float(hit_xy[0]) + 4, cy),
            color=(90, 110, 90, 120),
            thickness=1,
            parent="wave_draw",
        )

        def _plane_at(center: np.ndarray, direction: np.ndarray, half: float, color, thick: int = 3) -> None:
            """Draw a wavefront segment perpendicular to ``direction``, with a chevron along it."""
            d = direction / (np.linalg.norm(direction) + 1e-12)
            t = np.array([-d[1], d[0]])
            p0 = center - t * half
            p1 = center + t * half
            dpg.draw_line((float(p0[0]), float(p0[1])), (float(p1[0]), float(p1[1])), color=color, thickness=thick, parent="wave_draw")
            tip = center + d * 14.0
            dpg.draw_line((float(p0[0]), float(p0[1])), (float(tip[0]), float(tip[1])), color=color, thickness=2, parent="wave_draw")
            dpg.draw_line((float(p1[0]), float(p1[1])), (float(tip[0]), float(tip[1])), color=color, thickness=2, parent="wave_draw")

        # Timeline: one pulse inbound, then echo outbound (no overlapping counter-propagating trains)
        cycle = 2.8  # seconds of phase units per bounce cycle
        tau = float(phase % cycle)
        t_hit = 0.45 * cycle
        travel_in = float(np.linalg.norm(radar_xy - hit_xy))

        if tau <= t_hit:
            # Incident pulse moving from radar toward target
            u = tau / t_hit
            pos = radar_xy + (hit_xy - radar_xy) * u
            _plane_at(pos, ki, 70.0, (120, 230, 140, 255), thick=4)
            # Ghost trail behind the pulse (still only inbound)
            for k in (1, 2):
                u2 = u - 0.08 * k
                if u2 < 0:
                    continue
                pos2 = radar_xy + (hit_xy - radar_xy) * u2
                alpha = 180 - 50 * k
                _plane_at(pos2, ki, 70.0 - 8 * k, (120, 230, 140, alpha), thick=2)
            dpg.draw_text((10, WAVE_H - 48), "Phase: incident pulse traveling TO the target", size=13, color=(160, 220, 160), parent="wave_draw")
        else:
            # Impact flash, then echo leaving the target
            u = (tau - t_hit) / (cycle - t_hit)
            dpg.draw_circle((cx, cy), r_obj + 6 + 10 * min(u * 3, 1.0), color=(255, 255, 180, int(120 * (1 - u))), thickness=2, parent="wave_draw")

            if p.shape == TargetShape.SPHERE:
                # Expanding ring — only the radar-facing arc is emphasized as "echo"
                rad = r_obj + 8 + u * (travel_in * 0.85)
                # Full faint ring
                dpg.draw_circle((cx, cy), rad, color=(100, 180, 220, 70), thickness=2, parent="wave_draw")
                # Bright arc toward radar (right side)
                n_arc = 16
                pts = []
                for i in range(n_arc + 1):
                    ang = -0.7 + 1.4 * i / n_arc  # radians about +x
                    pts.append((cx + rad * np.cos(ang), cy + rad * np.sin(ang)))
                for i in range(len(pts) - 1):
                    dpg.draw_line(pts[i], pts[i + 1], color=(100, 210, 255, 255), thickness=3, parent="wave_draw")
                # Chevron on arc midpoint (toward radar)
                mid = pts[len(pts) // 2]
                _arrow((float(mid[0]), float(mid[1])), (cx + rad * 0.55, cy), color=(100, 210, 255, 255), thickness=2, size=6, parent="wave_draw")
                dpg.draw_text((10, WAVE_H - 48), "Phase: scattered echo expanding; bright arc returns TO the radar", size=13, color=(140, 200, 240), parent="wave_draw")

            elif p.shape == TargetShape.CORNER:
                pos = hit_xy + np.array([1.0, 0.0]) * (u * travel_in)
                _plane_at(pos, np.array([1.0, 0.0]), 65.0, (255, 180, 80, 255), thick=4)
                for k in (1, 2):
                    u2 = u - 0.08 * k
                    if u2 < 0:
                        continue
                    pos2 = hit_xy + np.array([1.0, 0.0]) * (u2 * travel_in)
                    _plane_at(pos2, np.array([1.0, 0.0]), 65.0 - 8 * k, (255, 180, 80, 180 - 40 * k), thick=2)
                dpg.draw_text((10, WAVE_H - 48), "Phase: retro-reflected pulse traveling BACK to the radar", size=13, color=(255, 200, 120), parent="wave_draw")

            elif p.shape in (TargetShape.FLAT_PLATE, TargetShape.CYLINDER):
                # Specular echo along kr (opposite sense from incident when aspect ~ 0)
                span = travel_in * 0.95
                pos = np.array([cx, cy]) + kr * (r_obj + 8 + u * span)
                strength = max(backscatter, 0.12)
                half = 30.0 + 40.0 * strength
                col = (100, 210, 255, int(80 + 175 * strength))
                _plane_at(pos, kr, half, col, thick=4)
                for k in (1, 2):
                    u2 = u - 0.08 * k
                    if u2 < 0:
                        continue
                    pos2 = np.array([cx, cy]) + kr * (r_obj + 8 + u2 * span)
                    _plane_at(pos2, kr, half - 6 * k, (100, 210, 255, int((80 + 175 * strength) * (0.7 - 0.2 * k))), thick=2)
                # Draw specular path ray
                ray_end = np.array([cx, cy]) + kr * span
                dpg.draw_line((cx, cy), (float(ray_end[0]), float(ray_end[1])), color=(100, 210, 255, 100), thickness=1, parent="wave_draw")
                if backscatter < 0.35:
                    dpg.draw_text(
                        (10, WAVE_H - 48),
                        "Phase: specular echo leaves along the bounce direction (misses radar)",
                        size=13,
                        color=(255, 160, 120),
                        parent="wave_draw",
                    )
                else:
                    dpg.draw_text(
                        (10, WAVE_H - 48),
                        "Phase: specular echo traveling BACK toward the radar",
                        size=13,
                        color=(140, 200, 240),
                        parent="wave_draw",
                    )

            else:  # EXTENDED
                ax, ay = s_a, -c_a
                for frac in (-0.55, -0.15, 0.15, 0.55):
                    origin = np.array([cx + ax * 48.0 * frac, cy + ay * 48.0 * frac])
                    # Prefer return toward radar with a bit of spread
                    pos = origin + np.array([1.0, 0.15 * frac]) * (8 + u * travel_in * 0.75)
                    _plane_at(pos, np.array([1.0, 0.0]), 22.0, (100, 200, 255, 160), thick=2)
                dpg.draw_text(
                    (10, WAVE_H - 48),
                    "Phase: multiple echoes leaving toward the radar (range smear)",
                    size=13,
                    color=(140, 200, 240),
                    parent="wave_draw",
                )

        dpg.draw_text(
            (10, WAVE_H - 28),
            f"aspect={p.aspect_deg:.0f} deg   specular toward-radar={backscatter:.2f}   (pulse loops)",
            size=12,
            color=(170, 170, 180),
            parent="wave_draw",
        )

    def refresh(self) -> None:
        try:
            self.params = self._read_controls()
        except ValueError as exc:
            dpg.set_value("status_text", f"Invalid settings: {exc}")
            return

        out = process(self.params)
        r_km = np.asarray(out["range_m"], dtype=float) / 1e3
        env = np.asarray(out["envelope"], dtype=float)
        env_n = env / (float(np.max(env)) + 1e-30)

        dpg.set_value("echo_series", _fxy(r_km, env_n))
        # Zoom A-scope around the target
        r0 = self.params.range_m / 1e3
        span = max(0.4, 2.0 * float(out["extent_m"]) / 1e3 + 0.6)
        dpg.set_axis_limits("echo_x", max(0.0, r0 - span), r0 + span)
        dpg.set_axis_limits("echo_y", -0.05, 1.15)

        # RCS comparison (dBsm) as bar-like stems via line segments on a plot
        labels = [COMPARE_SHORT[s] for s in COMPARE_ORDER]
        dbsm = [float(out["compare_rcs_dbsm"][s.value]) for s in COMPARE_ORDER]
        xs = list(range(len(labels)))
        dpg.set_value("rcs_bars", [[float(x) for x in xs], dbsm])
        # Highlight selected shape
        sel = COMPARE_ORDER.index(self.params.shape)
        dpg.set_value("rcs_sel", [[float(sel)], [dbsm[sel]]])
        dpg.set_axis_limits("rcs_x", -0.5, len(labels) - 0.5)
        ymin = min(dbsm) - 5.0
        ymax = max(dbsm) + 5.0
        dpg.set_axis_limits("rcs_y", ymin, ymax)

        self._draw_shape(self.params)
        self._draw_wavefronts(self.params, self._wave_phase)

        dpg.set_value(
            "status_text",
            (
                f"RCS = {out['rcs_m2']:.3g} m^2  ({out['rcs_dbsm']:+.1f} dBsm)\n"
                f"Predicted SNR = {out['snr_db']:+.1f} dB   lambda = {1e3 * float(out['lambda_m']):.1f} mm\n"
                f"Range extent ~ {out['extent_m']:.1f} m   pulse resolution ~ {out['pulse_resolution_m']:.1f} m"
            ),
        )
        # Tick labels for RCS categories
        if dpg.does_item_exist("rcs_xlabel"):
            dpg.set_value("rcs_xlabel", "  ".join(f"{i}:{lab}" for i, lab in enumerate(labels)))

    def run(self) -> None:
        dpg.create_context()
        dpg.create_viewport(title="Teaching Sims - Target Returns (RCS)", width=1520, height=1040)
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
        dpg.bind_theme(global_theme)

        with dpg.window(tag="primary", label="Target returns"):
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
                    dpg.add_text("Target")
                    dpg.add_combo(
                        tag="shape",
                        label="Shape",
                        items=list(SHAPE_LABELS.keys()),
                        default_value=LABEL_FOR_SHAPE[self.params.shape],
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="size_m",
                        label="Size (m)",
                        default_value=self.params.size_m,
                        min_value=0.1,
                        max_value=50.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="size2_m",
                        label="Size 2 (m)",
                        default_value=self.params.size2_m,
                        min_value=0.1,
                        max_value=20.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="aspect_deg",
                        label="Aspect (deg)",
                        default_value=self.params.aspect_deg,
                        min_value=0.0,
                        max_value=90.0,
                        callback=self._on_change,
                    )
                    dpg.add_separator()
                    dpg.add_text("Wavefronts")
                    dpg.add_slider_float(
                        tag="wave_speed",
                        label="Wave speed",
                        default_value=self._wave_speed,
                        min_value=0.1,
                        max_value=1.5,
                        callback=self._on_wave_speed,
                    )
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Play waves", width=110, callback=lambda: self._play_waves())
                        dpg.add_button(label="Pause", width=80, callback=lambda: self._pause_waves())
                    dpg.add_slider_float(
                        tag="range_km",
                        label="Range (km)",
                        default_value=self.params.range_m / 1e3,
                        min_value=1.0,
                        max_value=20.0,
                        callback=self._on_change,
                    )
                    dpg.add_slider_float(
                        tag="freq_ghz",
                        label="Frequency (GHz)",
                        default_value=self.params.frequency_hz / 1e9,
                        min_value=1.0,
                        max_value=35.0,
                        callback=self._on_change,
                    )
                    with dpg.group(tag="advanced_controls"):
                        dpg.add_separator()
                        dpg.add_text("Advanced")
                        dpg.add_slider_float(
                            tag="tp_us",
                            label="Pulse width (us)",
                            default_value=self.params.pulse_width_s * 1e6,
                            min_value=0.1,
                            max_value=2.0,
                            callback=self._on_change,
                        )
                        dpg.add_slider_float(
                            tag="snr_ref_db",
                            label="SNR ref (dB @ 1 m^2)",
                            default_value=self.params.snr_ref_db,
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
                        dpg.add_button(label="Resample noise", width=-1, callback=lambda: self._resample())
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
                        dpg.add_drawlist(width=DRAW_W, height=DRAW_H, tag="shape_draw")
                        with dpg.plot(label="RCS comparison (dBsm)", height=DRAW_H, width=-1):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label="shape index", tag="rcs_x")
                            with dpg.plot_axis(dpg.mvYAxis, label="dBsm", tag="rcs_y"):
                                dpg.add_stem_series([0.0], [0.0], label="all shapes", tag="rcs_bars")
                                dpg.add_scatter_series([0.0], [0.0], label="selected", tag="rcs_sel")
                    dpg.add_text("0:sphere  1:plate  2:cyl  3:corner  4:ext", tag="rcs_xlabel")
                    dpg.add_drawlist(width=WAVE_W, height=WAVE_H, tag="wave_draw")
                    with dpg.plot(label="A-scope return (matched-filter envelope)", height=280, width=-1, tag="echo_plot"):
                        dpg.add_plot_legend()
                        dpg.add_plot_axis(dpg.mvXAxis, label="range (km)", tag="echo_x")
                        with dpg.plot_axis(dpg.mvYAxis, label="normalised |y|", tag="echo_y"):
                            dpg.add_line_series([0.0], [0.0], label="echo", tag="echo_series")

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        self._push_controls(self.params)
        self.refresh()
        while dpg.is_dearpygui_running():
            self._tick()
            dpg.render_dearpygui_frame()
        dpg.destroy_context()


def run_app(scenario_id: str | None = None, params: TargetReturnsParams | None = None) -> None:
    if scenario_id and params is None:
        params = get_scenario(scenario_id).params
    TargetReturnsApp(initial=params, scenario_id=scenario_id).run()
