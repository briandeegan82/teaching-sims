# Tutorial 10 — Attitude: Euler, DCM, quaternion

**Demo:** `teaching-sims demo attitude`  
**Prerequisites:** Tutorials 08–09  
**Goal:** connect yaw-pitch-roll, direction cosine matrices, and quaternions; see gimbal lock

---

## 1. Principles

### 1.1 ZYX Euler

Aerospace attitude often uses yaw \(\psi\), pitch \(\theta\), roll \(\phi\) (ZYX). The DCM \(R_{nb}\) maps body vectors into NED; its columns are the body unit axes in NED.

### 1.2 Quaternion

A unit quaternion \(q=[w,x,y,z]\) parameterizes the same rotation without the Euler singularity. Round-trip Euler → quat → DCM → Euler works away from \(\theta=\pm90^\circ\).

### 1.3 Gimbal lock

When \(\cos\theta\to0\), yaw and roll are no longer independently observable from the DCM — extraction couples them.

---

## 2. UI map

| Element | Role |
| --- | --- |
| NE top view | Body X/Y (and Z projection) |
| Pitch scan plot | Extracted Euler vs commanded pitch |
| Status | Quaternion + det(DCM) |

---

## 3. Guided walkthrough

### Experiment A — Level heading (~4 min)

1. Load **Level heading**.
2. Rotate yaw: X/Y sweep the horizontal plane.

### Experiment B — Pitch (~4 min)

1. Load **Nose-up pitch**.
2. Body X lifts out of the NE plane.

### Experiment C — Gimbal lock (~8 min)

1. Load **Gimbal-lock scan**.
2. Watch extracted yaw/roll jump near \(\pm90^\circ\) pitch.

### Experiment D — Quaternion (~5 min)

1. Load **Quaternion round-trip**.
2. Confirm status Euler←quat matches the sliders.

---

## 4. Lab sheet

| Pose | Observation |
| --- | --- |
| Yaw 45°, level | X points NE diagonal |
| Pitch 30° | X has Down component |
| Pitch scan | Singular near ±90° |

---

## 5. Check your understanding

1. What does \(\det(R)=1\) tell you?
2. Why do flight codes often propagate quaternions, not Euler angles?
3. Is gimbal lock a physical lock of the vehicle?

---

## 6. Next

Continue with [11 — Complementary filter](11-complementary.md).
