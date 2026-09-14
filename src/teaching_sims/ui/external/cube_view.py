"""External 3D cube viewer (subprocess) for body attitude."""

from __future__ import annotations

import json
import os
import select
import subprocess
import sys
import time

from teaching_sims.ui.external.cube_geometry import (
    cube_vertices_body,
    draw_cube_attitude,
    rotate_body_to_plot,
)

__all__ = [
    "CubeAttitudeView",
    "cube_vertices_body",
    "rotate_body_to_plot",
    "draw_cube_attitude",
]


class CubeAttitudeView:
    """Matplotlib 3D window in a child process (avoids DPG thread/GUI conflicts)."""

    def __init__(self) -> None:
        self._enabled = False
        self._proc: subprocess.Popen[str] | None = None
        self.last_error: str | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self._enabled:
            return
        self._enabled = enabled
        self.last_error = None
        if enabled:
            self._start()
        else:
            self.close()

    def _wait_for_ready(self, proc: subprocess.Popen[str], timeout_s: float = 8.0) -> bool:
        """Non-blocking wait for the child 'ready' handshake."""
        if proc.stdout is None:
            return False
        fd = proc.stdout.fileno()
        buf = ""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                return False
            ready, _, _ = select.select([fd], [], [], 0.05)
            if ready:
                chunk = os.read(fd, 4096)
                if not chunk:
                    return False
                buf += chunk.decode(errors="replace")
                if "ready" in buf:
                    return True
        return False

    def _start(self) -> None:
        self.close()
        try:
            self._proc = subprocess.Popen(
                [sys.executable, "-m", "teaching_sims.ui.external.cube_viewer_process"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            self.last_error = f"Could not start 3D viewer: {exc}"
            self._enabled = False
            return

        proc = self._proc
        assert proc is not None
        if not self._wait_for_ready(proc):
            err = ""
            if proc.stderr is not None:
                try:
                    err = proc.stderr.read()
                except OSError:
                    pass
            if proc.poll() is not None and not err:
                err = "viewer process exited during startup"
            self.last_error = f"3D viewer failed to start:\n{(err or 'timeout waiting for ready').strip()}"
            self.close()
            self._enabled = False
            return

        self.last_error = None

    def close(self) -> None:
        proc = self._proc
        self._proc = None
        if proc is None:
            return
        if proc.poll() is None:
            try:
                if proc.stdin:
                    proc.stdin.write(json.dumps({"quit": True}) + "\n")
                    proc.stdin.flush()
                proc.wait(timeout=2.0)
            except Exception:
                proc.kill()
                proc.wait(timeout=1.0)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass

    def update(
        self,
        yaw_deg: float,
        pitch_deg: float,
        roll_deg: float,
        *,
        force: bool = False,
    ) -> None:
        del force
        if not self._enabled:
            return
        if self._proc is None or self._proc.poll() is not None:
            self.last_error = "3D viewer process is not running"
            self._enabled = False
            return

        msg = json.dumps(
            {"yaw": float(yaw_deg), "pitch": float(pitch_deg), "roll": float(roll_deg)}
        ) + "\n"
        try:
            assert self._proc.stdin is not None
            self._proc.stdin.write(msg)
            self._proc.stdin.flush()
            self.last_error = None
        except (BrokenPipeError, OSError) as exc:
            self.last_error = f"Lost connection to 3D viewer: {exc}"
            self.close()
            self._enabled = False
