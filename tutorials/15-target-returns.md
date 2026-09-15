# Tutorial 15 — Target returns (size, shape, and RCS)

**Demo:** `teaching-sims demo target-returns`  
**Prerequisites:** [03 — Pulsed ranging](03-pulsed-ranging.md)  
**Goal:** see how object **size** and **shape** change radar cross section (RCS) and the A-scope echo

---

## 1. Principles

### 1.1 Radar cross section

RCS \(\sigma\) (m² or dBsm) is the equivalent isotropic area that would produce the same scattered power. It depends on:

- geometry (sphere, plate, cylinder, corner, …)
- size relative to wavelength \(\lambda\)
- aspect angle
- material (this demo assumes perfect conductors)

### 1.2 Canonical teaching formulas (optical / geometric regime)

| Shape | Approximate monostatic \(\sigma\) |
| --- | --- |
| Sphere (radius \(a\)) | \(\pi a^2\) |
| Flat plate (area \(A\), broadside) | \(4\pi A^2/\lambda^2\) |
| Cylinder (radius \(a\), length \(L\)) | \(2\pi a L^2/\lambda\) |
| Trihedral corner (edge \(a\)) | \(12\pi a^4/\lambda^2\) |

A plate or cylinder also collapses off broadside (\(\propto\cos^2\theta\) in this demo).

### 1.3 Radar equation (amplitude)

Received SNR scales as

\[
\mathrm{SNR}\propto\frac{\sigma}{R^4}.
\]

Doubling range costs about **12 dB**. Shape/size enter only through \(\sigma\).

### 1.4 Echo shape

- Compact targets (sphere, corner) look nearly **point-like** after a short pulse.
- An **extended** body along the line of sight **smears** energy in range: the blob widens and the peak falls even if total RCS is similar.

---

## 2. UI map

| Element | Role |
| --- | --- |
| Shape / Size / Size 2 / Aspect | Select and size the target |
| Range / Frequency | Set \(R\) and \(\lambda=c/f\) |
| Shape sketch | Top-down view: object rotates with aspect; orange arrow = normal / long axis |
| Wavefronts | Pulsed animation: green incident TO target, then cyan/orange echo FROM target (not simultaneous trains) |
| RCS comparison | dBsm bars for all shapes at the current size/aspect |
| A-scope | Matched-filter envelope vs range |
| Lecture scenarios | Scripted size / shape / range / smear checkpoints |

---

## 3. Experiments

### Experiment A — Sphere size (~3 min)

1. Load **Sphere size scaling**.
2. Increase **Size** and watch RCS (dBsm) and echo peak grow.

### Experiment B — Plate vs sphere (~4 min)

1. Load **Plate vs sphere (broadside)**.
2. Note how much larger the plate bar is than the sphere at the same characteristic size.
3. Teaching point: specular geometry beats “physical area” intuition.

### Experiment C — Corner boost (~3 min)

1. Load **Corner reflector boost**.
2. A half-metre edge can outshine a much larger sphere — why calibration targets use corners.

### Experiment D — Aspect collapse (~4 min)

1. Load **Plate aspect collapse**, then drag **Aspect** from 0 toward 90.
2. Watch RCS and echo amplitude fall.

### Experiment E — Range law (~3 min)

1. Load **Range law (1/R^4)**.
2. Halve **Range** and confirm the echo rises by about 12 dB in the status SNR.

### Experiment F — Extended smear (~5 min)

1. Load **Extended target smear**.
2. Compare the wide, lower peak blob to a corner of similar strength.
3. Ask: would CFAR still flag this as one detection or several?

---

## 4. Checkpoint questions

1. Why can a flat plate have far larger RCS than a sphere of similar physical size?
2. What happens to plate RCS as aspect leaves broadside?
3. How many dB does SNR lose when range doubles (same target)?
4. Why does an extended body look different on an A-scope than a corner with similar \(\sigma\)?

---

## 5. Next

Continue with [04 — Pulse-Doppler](04-pulse-doppler.md) for moving targets, or [05 — CFAR](05-cfar.md) for detecting weak returns in noise.
