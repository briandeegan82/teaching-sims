# Tutorial 12 — Magnetometer & tilt-compensated heading

**Demo:** `teaching-sims demo magnetometer`  
**Prerequisites:** Tutorials 10–11  
**Goal:** form magnetic heading from body field components; apply tilt compensation; see hard/soft-iron errors

---

## 1. Principles

### 1.1 Level heading

With pitch=roll=0,

\[
\psi=\operatorname{atan2}(-b_y,\,b_x).
\]

### 1.2 Tilt compensation

Rotate the measured field back to the horizontal using known roll/pitch, then take \(\operatorname{atan2}\) on the horizontal components. Without this, the vertical Earth field leaks into heading when pitched/banked.

### 1.3 Distortions

- **Hard iron:** constant body bias → offset circle in \((b_x,b_y)\).
- **Soft iron:** anisotropic scaling → ellipse; heading error varies with yaw.

---

## 2. UI map

| Element | Role |
| --- | --- |
| Polar locus | \((b_x,b_y)\) over a yaw sweep |
| Heading plot | Raw vs tilt-compensated vs truth |
| Error plot | Selected estimator error vs yaw |

---

## 3. Guided walkthrough

### Experiment A — Level sweep (~5 min)

1. Load **Level yaw sweep**.
2. Locus is a centered circle; heading tracks.

### Experiment B — Pitch without TC (~5 min)

1. Load **Pitch needs tilt compensation**.
2. Large heading error vs yaw.

### Experiment C — Enable TC (~3 min)

1. Load **Tilt-compensated pitch** (or toggle the checkbox).
2. RMS error collapses.

### Experiment D — Hard iron (~5 min)

1. Load **Hard-iron offset**.
2. Locus off-center; heading biased.

### Experiment E — Soft iron (~5 min)

1. Load **Soft-iron distortion**.
2. Ellipse + yaw-dependent error.

---

## 4. Lab sheet

| Case | Tilt-comp | RMS error |
| --- | --- | --- |
| Level | on/off | small |
| Pitch 25°, TC off | off | large |
| Pitch 25°, TC on | on | small |
| Hard iron | on | elevated |

---

## 5. Check your understanding

1. Why do phones ask you to “wave in a figure-8” when calibrating?
2. Does tilt compensation need an accelerometer or AHRS?
3. Magnetic heading ≠ true north — what is the missing term?

---

## 6. Next

Finish with [13 — Strapdown INS](13-ins.md).
