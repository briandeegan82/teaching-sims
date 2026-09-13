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
teaching-sims demo beamforming --scenario mvdr_adaptive_null
pytest
```

## Topics

| Topic | Status |
| --- | --- |
| Phased-array radar (ULA) | interactive + scenarios + lecture polish |
| Digital beamforming | conventional / null-steer / MVDR + Capon spectrum |
| Pulsed radar ranging | delay, resolution, LFM compression, PRI ambiguity |
| SAR / FFT imaging | planned |

## Layout

- `src/teaching_sims/core/` — shared helpers
- `src/teaching_sims/topics/<name>/` — physics + lecture scenarios
- `src/teaching_sims/ui/desktop/` — Dear PyGui apps
- `tests/` — physics unit tests

## Phased-array demo

```bash
teaching-sims demo phased-array
teaching-sims demo phased-array --scenario grating_lobes
```

Controls: \(N\), \(d/\lambda\), steer, RF vs design frequency, phase-shift vs TTD,
element pattern, phase bits. Presenter mode, array layout, pattern callouts,
phase-vs-TTD overlay.

## Beamforming demo

```bash
teaching-sims demo beamforming
teaching-sims demo beamforming --list-scenarios
```

Methods: conventional delay-and-sum, deterministic null steering, MVDR/Capon.
Panels: beampattern, Capon spectrum, weights, eigenvalues of \(R\), analytical SINR.
Scenarios cover interferer-in-sidelobe, adaptive nulling, resolution, and diagonal loading.

## Pulsed ranging demo

```bash
teaching-sims demo pulsed-ranging
teaching-sims demo pulsed-ranging --scenario lfm_compression
```

Covers echo delay \(\tau=2R/c\), range resolution, LFM pulse compression, matched-filter
SNR gain, and PRI range ambiguity. Overlay raw \(|r_x|\) vs matched-filter video.
