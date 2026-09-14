# Tutorial 08 — Accelerometers & specific force

**Demo:** `teaching-sims demo accelerometer`  
**Prerequisites:** none  
**Goal:** understand what an accelerometer measures, how static tilt is recovered, and why bias / linear accel / vibration spoil naïve attitude

---

## 1. Principles

### 1.1 Specific force

An accelerometer measures **specific force** \(\mathbf{f}=\mathbf{a}-\mathbf{g}\) (non-gravitational acceleration), not “acceleration” in everyday language. At rest on a level surface in NED,

\[
\mathbf{f}\approx[0,\,0,\,-g].
\]

### 1.2 Static tilt

For a quasi-static platform,

\[
\phi=\operatorname{atan2}(f_y,-f_z),\qquad
\theta=\operatorname{atan2}(-f_x,\sqrt{f_y^2+f_z^2}).
\]

### 1.3 Failure modes

| Effect | Looks like |
| --- | --- |
| Constant bias | Static attitude error |
| True linear accel | Fake tilt |
| Vibration | Noisy instantaneous tilt (mean often OK) |

---

## 2. UI map

| Element | Role |
| --- | --- |
| fx, fy, fz | Noisy body specific force |
| Yaw / roll / pitch | Commanded body attitude (ZYX) |
| 3D window checkbox | External matplotlib cube + body axes |
| Roll/pitch est | Instantaneous tilt from accel (no yaw) |
| Truth lines | Commanded roll/pitch |
| Status | Mean estimate vs truth |

---

## 3. Guided walkthrough

Enable **Presenter mode**.

### Experiment A — Level plate (~5 min)

1. Load **Level plate**.
2. Confirm \(f_z\approx-9.81\), tilt ≈ 0°.

### Experiment B — Static tilt + 3D cube (~5 min)

1. Load **Static tilt**.
2. Enable **Show 3D attitude window**.
3. Match mean estimate to commanded roll/pitch.
4. Move **Yaw** — cube rotates, but fx/fy/fz and tilt estimates stay the same.

### Experiment C — Bias (~5 min)

1. Load **Bias looks like tilt**.
2. Truth is level — estimate is not.

### Experiment D — Surge (~5 min)

1. Load **Linear accel contamination**.
2. Forward \(a_x\) spoofs pitch.

### Experiment E — Vibration (~5 min)

1. Load **Vibration vs averaging**.
2. Instantaneous tilt jitters; mean recovers.

---

## 4. Lab sheet

| Trial | Setting | Observation |
| --- | --- | --- |
| 1 | Level | \(f_z\approx-g\) |
| 2 | Pitch 20° | Mean pitch ≈ 20° |
| 3 | Bias X = 0.5 | Pitch error |
| 4 | Surge 2 m/s² | Fake pitch |

---

## 5. Check your understanding

1. Why doesn’t a parked car’s accelerometer read zero?
2. Can you tell bias from true tilt with only an accelerometer?
3. When is averaging tilt estimates valid?

---

## 6. Next

Continue with [09 — Gyroscopes](09-gyroscope.md).
