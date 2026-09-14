"""Subprocess entry point: owns the matplotlib/Qt main thread for the 3D cube."""

from __future__ import annotations

import json
import sys
import threading
from queue import Empty, Queue


def _configure_backend() -> None:
    import matplotlib

    for backend in ("QtAgg", "Qt5Agg", "TkAgg"):
        try:
            matplotlib.use(backend, force=True)
            return
        except Exception:
            continue
    raise RuntimeError(
        "No interactive matplotlib backend. Install PySide6: pip install PySide6"
    )


def _stdin_reader(queue: Queue) -> None:
    """Background thread: never block the Qt main thread on stdin."""
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            queue.put(msg)
            if msg.get("quit"):
                return
    except Exception:
        queue.put({"quit": True})


def main() -> int:
    _configure_backend()
    import matplotlib.pyplot as plt

    from teaching_sims.ui.external.cube_geometry import draw_cube_attitude

    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    if fig.canvas.manager is not None:
        fig.canvas.manager.set_window_title("Teaching Sims — body attitude (3D)")

    # Safe defaults so the first paint is valid before any parent message arrives.
    draw_cube_attitude(ax, 0.0, 0.0, 0.0)

    queue: Queue = Queue()
    reader = threading.Thread(target=_stdin_reader, args=(queue,), daemon=True)
    reader.start()

    sys.stdout.write("ready\n")
    sys.stdout.flush()

    def _on_timer() -> None:
        try:
            while True:
                msg = queue.get_nowait()
                if msg.get("quit"):
                    plt.close(fig)
                    return
                draw_cube_attitude(
                    ax,
                    float(msg["yaw"]),
                    float(msg["pitch"]),
                    float(msg["roll"]),
                )
                fig.canvas.draw_idle()
        except Empty:
            pass

    timer = fig.canvas.new_timer(interval=33)
    timer.add_callback(_on_timer)
    timer.start()

    # Block on the GUI main loop so mouse clicks / rotation stay on the Qt thread.
    plt.show(block=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
