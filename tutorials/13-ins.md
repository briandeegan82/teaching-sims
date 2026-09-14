# Tutorial 13 — Strapdown INS / dead reckoning

**Demo:** `teaching-sims demo ins`  
**Prerequisites:** Tutorials 08–12  
**Goal:** see how unaided inertial navigation grows error from gyro bias (attitude) and accel bias (velocity → position)

---

## 1. Principles

### 1.1 Strapdown idea

Sense \(\boldsymbol{\omega}\) and \(\mathbf{f}\) in **body** frame; propagate attitude; resolve specific force into navigation axes; integrate to velocity and position.

### 1.2 Error growth (planar teaching model)

| Error source | Integrates to |
| --- | --- |
| Accel bias | Velocity ramp → **quadratic** position |
| Gyro bias | Heading drift → wrong velocity direction → growing path error |

Without GNSS/vision/odometry aiding, unaided INS **diverges**.

---

## 2. UI map

| Element | Role |
| --- | --- |
| NE path | Truth vs dead-reckoned track |
| Position error | \(\sqrt{\Delta N^2+\Delta E^2}\) vs time |
| Heading | True vs estimated |
| Perfect attitude | Isolates accelerometer errors |

---

## 3. Guided walkthrough

### Experiment A — Perfect circle (~5 min)

1. Load **Perfect sensors (circle)**.
2. Paths nearly overlap.

### Experiment B — Accel bias (~5 min)

1. Load **Accel bias on straight path**.
2. Error grows roughly like \(t^2\).

### Experiment C — Gyro bias (~5 min)

1. Load **Gyro bias on a circle**.
2. Path spirals away as heading drifts.

### Experiment D — Combined (~5 min)

1. Load **Gyro + accel errors**.
2. Realistic short-term tactical IMU behaviour.

### Experiment E — Stop-and-go (~5 min)

1. Load **Stop-and-go**.
2. Even when “stopped,” bias still integrates.

---

## 4. Lab sheet

| Scenario | Dominant mechanism | Error shape |
| --- | --- | --- |
| Accel bias, perfect att | \(\delta a\) | ~quadratic |
| Gyro bias | \(\delta\omega\) | path warp |
| Quiet IMU | both small | slow growth |

---

## 5. Check your understanding

1. Why does GNSS/INS fusion reset error growth?
2. What does “perfect attitude” demonstrate in this demo?
3. Name two real-world aids besides GNSS.

---

## 6. Where to go next

You now have a full IMU track: sensors → attitude → fusion → heading → navigation. Optional extensions: Allan variance characterization, EKF AHRS, or Schuler dynamics for longer-range INS.
