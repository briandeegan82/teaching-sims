# Teaching Sims

Interactive desktop simulations for graduate teaching. Physics cores are
UI-agnostic; the first front-end is **Dear PyGui**.

## Quick start

```bash
cd ~/teaching-sims
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

teaching-sims demo phased-array
teaching-sims demo beamforming
teaching-sims demo pulsed-ranging
teaching-sims demo pulse-doppler
teaching-sims demo cfar
pytest
```

## Tutorials

- [Tutorials index](tutorials/README.md)
- [01 — Phased-array antennas](tutorials/01-phased-array.md)
- [02 — Digital beamforming](tutorials/02-beamforming.md)
- [03 — Pulsed radar ranging](tutorials/03-pulsed-ranging.md)
- [04 — Pulse-Doppler / MTI](tutorials/04-pulse-doppler.md)
- [05 — CFAR detection](tutorials/05-cfar.md)

## Topics

| Topic | Status |
| --- | --- |
| Phased-array radar (ULA) | interactive + scenarios + lecture polish |
| Digital beamforming | conventional / null-steer / MVDR + Capon spectrum |
| Pulsed radar ranging | delay, resolution, LFM compression, PRI ambiguity |
| Pulse-Doppler / MTI | range–Doppler maps, clutter, MTI, velocity ambiguity |
| CFAR detection | CA / OS / GO / SO on range profiles |
| FMCW / SAR | planned |

## Layout

- `src/teaching_sims/core/` — shared helpers
- `src/teaching_sims/topics/<name>/` — physics + lecture scenarios
- `src/teaching_sims/ui/desktop/` — Dear PyGui apps
- `tests/` — physics unit tests
- `tutorials/` — principles + guided experiments

## Demos

```bash
teaching-sims demo phased-array
teaching-sims demo beamforming --scenario mvdr_adaptive_null
teaching-sims demo pulsed-ranging --scenario lfm_compression
teaching-sims demo pulse-doppler --scenario mti_reveals_target
teaching-sims demo cfar --scenario fixed_vs_cfar_clutter
```
