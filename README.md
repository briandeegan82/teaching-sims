# Teaching Sims

Interactive Dear PyGui simulations for graduate teaching. Two tracks:

- **Radar** — arrays through stripmap SAR  
- **IMU / navigation** — accelerometers through unaided strapdown INS  

Physics cores are UI-agnostic; each topic ships with lecture scenarios and a tutorial.

## Quick start

```bash
cd ~/teaching-sims
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

teaching-sims list
teaching-sims demo accelerometer
teaching-sims demo phased-array
pytest
```

## Course map — Radar

| # | Demo | Tutorial | Launch |
| --- | --- | --- | --- |
| 1 | Phased-array ULA | [01](tutorials/01-phased-array.md) | `teaching-sims demo phased-array` |
| 2 | Digital beamforming | [02](tutorials/02-beamforming.md) | `teaching-sims demo beamforming` |
| 3 | Pulsed ranging | [03](tutorials/03-pulsed-ranging.md) | `teaching-sims demo pulsed-ranging` |
| 4 | Pulse-Doppler / MTI | [04](tutorials/04-pulse-doppler.md) | `teaching-sims demo pulse-doppler` |
| 5 | CFAR detection | [05](tutorials/05-cfar.md) | `teaching-sims demo cfar` |
| 6 | FMCW radar | [06](tutorials/06-fmcw.md) | `teaching-sims demo fmcw` |
| 7 | Stripmap SAR | [07](tutorials/07-sar.md) | `teaching-sims demo sar` |

## Course map — IMU

| # | Demo | Tutorial | Launch |
| --- | --- | --- | --- |
| 8 | MEMS comb-drive sensing | [14](tutorials/14-mems-accel.md) | `teaching-sims demo mems-accel` |
| 9 | Accelerometer / tilt | [08](tutorials/08-accelerometer.md) | `teaching-sims demo accelerometer` |
| 10 | Gyroscope / integration | [09](tutorials/09-gyroscope.md) | `teaching-sims demo gyroscope` |
| 11 | Attitude (Euler/DCM/quat) | [10](tutorials/10-attitude.md) | `teaching-sims demo attitude` |
| 12 | Complementary filter | [11](tutorials/11-complementary.md) | `teaching-sims demo complementary` |
| 13 | Magnetometer / heading | [12](tutorials/12-magnetometer.md) | `teaching-sims demo magnetometer` |
| 14 | Strapdown INS | [13](tutorials/13-ins.md) | `teaching-sims demo ins` |

List scenarios for any demo:

```bash
teaching-sims demo complementary --list-scenarios
```

Shell shortcuts live in [`demos/`](demos/README.md).

## Tips

- Enable **Presenter mode** when projecting.
- Use **Lecture scenarios** as the talk track; sliders are for exploration.
- Radar angles are from **broadside** (\(0^\circ\) = array / look normal).
- IMU attitudes use aerospace **ZYX** yaw–pitch–roll; gravity level reads \(f_z\approx-g\).
- Optional **3D attitude windows** (accelerometer / gyroscope) need `matplotlib` + `PySide6`
  (already in package dependencies). Checkbox in the left panel opens an external Qt window.

## Layout

```text
src/teaching_sims/
  core/           shared constants (RF + IMU)
  topics/*/       physics + scenarios per demo
  ui/desktop/     Dear PyGui apps
  ui/external/    optional matplotlib 3D viewers
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
