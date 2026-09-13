# Teaching Sims

Interactive Dear PyGui simulations for graduate radar teaching. Physics cores
are UI-agnostic; each topic ships with lecture scenarios and a tutorial.

## Quick start

```bash
cd ~/teaching-sims
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

teaching-sims list
teaching-sims demo phased-array
pytest
```

## Course map

| # | Demo | Tutorial | Launch |
| --- | --- | --- | --- |
| 1 | Phased-array ULA | [01](tutorials/01-phased-array.md) | `teaching-sims demo phased-array` |
| 2 | Digital beamforming | [02](tutorials/02-beamforming.md) | `teaching-sims demo beamforming` |
| 3 | Pulsed ranging | [03](tutorials/03-pulsed-ranging.md) | `teaching-sims demo pulsed-ranging` |
| 4 | Pulse-Doppler / MTI | [04](tutorials/04-pulse-doppler.md) | `teaching-sims demo pulse-doppler` |
| 5 | CFAR detection | [05](tutorials/05-cfar.md) | `teaching-sims demo cfar` |
| 6 | FMCW radar | [06](tutorials/06-fmcw.md) | `teaching-sims demo fmcw` |
| 7 | Stripmap SAR | [07](tutorials/07-sar.md) | `teaching-sims demo sar` |

List scenarios for any demo:

```bash
teaching-sims demo cfar --list-scenarios
```

Shell shortcuts live in [`demos/`](demos/README.md).

## Tips

- Enable **Presenter mode** when projecting.
- Use **Lecture scenarios** as the talk track; sliders are for exploration.
- Angles are from **broadside** (\(0^\circ\) = array / look normal).

## Layout

```text
src/teaching_sims/
  core/           shared constants
  topics/*/       physics + scenarios per demo
  ui/desktop/     Dear PyGui apps
  ui/cli.py       teaching-sims entry point
tutorials/        principles + walkthroughs
tests/            physics unit tests
demos/            one-liner launch scripts
```

## Develop

```bash
pip install -e ".[dev]"
pytest
```
