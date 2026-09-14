# Tutorial 11 — Complementary filter attitude

**Demo:** `teaching-sims demo complementary`  
**Prerequisites:** Tutorials 08–10  
**Goal:** fuse gyro (wideband) with accelerometer tilt (low-frequency absolute) using a complementary filter

---

## 1. Principles

### 1.1 The trade

| Sensor | Strength | Weakness |
| --- | --- | --- |
| Gyro integrate | Smooth, fast dynamics | Bias → drift |
| Accel tilt | Absolute (static) | Noise; spoofed by linear accel |

### 1.2 Complementary filter (1-DOF)

\[
\hat\theta_k=\alpha\,(\hat\theta_{k-1}+\omega_k\Delta t)+(1-\alpha)\,\theta_{\mathrm{accel},k}.
\]

\(\alpha\) near 1 trusts the gyro; smaller \(\alpha\) trusts the accelerometer more.

---

## 2. UI map

| Element | Role |
| --- | --- |
| Pitch estimates | Truth, gyro-only, accel, complementary |
| Error plot | Each estimator vs truth |
| α slider | Gyro weight |
| Surge | Contaminates accel tilt |

---

## 3. Guided walkthrough

### Experiment A — Balanced (~5 min)

1. Load **Balanced sine pitch**.
2. Complementary RMS beats gyro-only despite bias.

### Experiment B — Trust gyro (~4 min)

1. Load **Trust the gyro** (α≈1).
2. Drift returns.

### Experiment C — Trust accel (~4 min)

1. Load **Trust the accelerometer**.
2. Noisy / laggy but bounded.

### Experiment D — Surge (~6 min)

1. Load **Surge spoofs accel**.
2. Raise α during surge; lower it afterward (conceptually).

### Experiment E — Step (~4 min)

1. Load **Step pitch**.
2. Trade overshoot vs lag with α.

---

## 4. Lab sheet

| α | Gyro bias | Surge | Best estimator |
| --- | --- | --- | --- |
| 0.98 | on | 0 | complementary |
| 0.999 | on | 0 | (still drifts) |
| 0.5 | on | 0 | accel-ish |
| 0.9 | low | on | gyro-weighted |

---

## 5. Check your understanding

1. Why is this called “complementary”?
2. What breaks the accelerometer absolute reference?
3. How does this relate to a Kalman filter AHRS?

---

## 6. Next

Continue with [12 — Magnetometer heading](12-magnetometer.md).
