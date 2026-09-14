# Tutorial 09 — Gyroscopes & rate integration

**Demo:** `teaching-sims demo gyroscope`  
**Prerequisites:** Tutorial 08 helpful  
**Goal:** integrate angular rate to angle; see bias → ramp and white rate noise → angle random walk

---

## 1. Principles

### 1.1 Rate to angle

\[
\hat\theta(t)=\int_0^t \omega_{\mathrm{meas}}(\tau)\,d\tau.
\]

### 1.2 Bias

If \(\omega_{\mathrm{meas}}=\omega+\varepsilon_b\), then angle error grows as \(\varepsilon_b\,t\) (unbounded without aiding).

### 1.3 Angle random walk (ARW)

White rate noise with density \(\sigma\) (often quoted in °/√h or °/√s) integrates to a random walk whose std grows like \(\sigma\sqrt{t}\).

---

## 2. UI map

| Element | Role |
| --- | --- |
| Rate plot | True vs measured ω |
| Angle plot | Truth vs integrated estimate |
| Error plot | \(\hat\theta-\theta\) |
| Compensate bias | Subtract known bias before integrate |
| 3D window | Dark cube = truth heading; orange = gyro \(\int\omega\) |
| View time / Play | Scrub or animate the 3D mismatch over the run |

---

## 3. Guided walkthrough

### Experiment A — Clean step turn (~5 min)

1. Load **Clean step turn**.
2. Angle tracks a 3 s turn closely.

### Experiment B — Bias ramp (~5 min)

1. Load **Bias → angle ramp**.
2. After motion stops, error keeps climbing.
3. Enable **Show 3D heading window** and press **Play** — truth (dark) stops turning; orange gyro cube keeps rotating.

### Experiment C — Compensation (~3 min)

1. Load **Bias compensated**.
2. Same bias, error collapses.
3. In 3D, the two cubes stay aligned through the turn.

### Experiment D — ARW (~5 min)

1. Load **Angle random walk** (zero true rate).
2. Angle wanders; resample to see new paths.
3. Scrub **View time** in 3D — truth stays fixed; orange heading wanders.

### Experiment E — Combined (~5 min)

1. Load **Noisy turn**.
2. Ramp + residual wander.

---

## 4. Lab sheet

| Trial | Bias | ARW | Final error trend |
| --- | --- | --- | --- |
| 1 | 0 | 0 | ~0 |
| 2 | 1.5 | 0 | linear in \(t\) |
| 3 | 1.5 + compensate | 0 | ~0 |
| 4 | 0 | high | \(\sim\sqrt{t}\) |

---

## 5. Check your understanding

1. Why can’t a gyro alone hold heading forever?
2. What does “calibrating bias” buy you, and what does it miss?
3. How does ARW differ from a constant bias in the error plot?

---

## 6. Next

Continue with [10 — Attitude representations](10-attitude.md).
