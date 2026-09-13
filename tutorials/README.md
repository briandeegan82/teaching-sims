# Tutorials

Hands-on guides for the Teaching Sims demos. Each tutorial explains the
underlying principles, maps them to the UI, and walks through experiments you
can run in lecture or self-paced lab.

| Tutorial | Demo command | Time (approx.) |
| --- | --- | --- |
| [01 — Phased-array antennas](01-phased-array.md) | `teaching-sims demo phased-array` | 45–60 min |
| [02 — Digital beamforming](02-beamforming.md) | `teaching-sims demo beamforming` | 45–60 min |
| [03 — Pulsed radar ranging](03-pulsed-ranging.md) | `teaching-sims demo pulsed-ranging` | 40–55 min |

## Before you start

```bash
cd ~/teaching-sims
source .venv/bin/activate
# if needed:
pip install -e ".[dev]"
```

Tips that apply to every demo:

- Turn on **Presenter mode** when projecting — it hides advanced sliders and
  keeps the teaching banner readable.
- Use the built-in **Lecture scenarios** buttons as checkpoints; they load a
  curated parameter set and teaching point.
- Angles are measured from **broadside** (array normal = \(0^\circ\)).

Suggested course order: phased array → beamforming → pulsed ranging.
