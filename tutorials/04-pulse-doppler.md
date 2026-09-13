# Tutorial 04 — Pulse-Doppler and MTI

**Demo:** `teaching-sims demo pulse-doppler`  
**Prerequisites:** Tutorial 03 (pulsed ranging)  
**Goal:** form a range–Doppler map, see clutter vs movers, apply two-pulse MTI,
and recognise PRF velocity ambiguity

---

## 1. Principles

### 1.1 Fast time vs slow time

After range processing, each pulse gives a **range profile**. Stacking \(N\)
pulses from a coherent processing interval (CPI) builds a matrix

\[
X[n,k]=\text{complex video at pulse }n,\ \text{range bin }k.
\]

- **Fast time** → range  
- **Slow time** (pulse index × PRI) → Doppler / radial velocity  

### 1.2 Doppler and radial velocity

For wavelength \(\lambda\) and radial closing speed \(v\) (toward the radar),

\[
f_d=\frac{2v}{\lambda}\qquad\Rightarrow\qquad v=\frac{\lambda f_d}{2}.
\]

A slow-time FFT (often with a Hann window) yields a **range–Doppler map**.

### 1.3 Ambiguous velocity

Sampling at the PRF means Doppler aliases:

\[
|f_d|<\frac{\mathrm{PRF}}{2}\quad\Rightarrow\quad
|v|<v_\mathrm{unamb}=\frac{\lambda\cdot\mathrm{PRF}}{4}.
\]

Faster targets **fold** into \(\pm v_\mathrm{unamb}\).

### 1.4 Clutter and MTI

Stationary (or wind-blown) clutter concentrates near **zero Doppler**. A simple
**two-pulse canceller**

\[
y[n]=x[n]-x[n-1]
\]

is a high-pass filter along slow time: it notches DC clutter and passes movers.
More advanced MTI / pulse-Doppler filters exist; this demo uses the two-pulse
case for clarity.

### 1.5 Resolution

\[
\Delta R\approx\frac{c}{2B},\qquad
\Delta v\approx\frac{\lambda\cdot\mathrm{PRF}}{2N}.
\]

Longer CPIs (larger \(N\)) sharpen Doppler at the cost of update time / motion
smear.

---

## 2. UI map

| Panel | Meaning |
| --- | --- |
| Range–Doppler map | Power vs range (km) and velocity (m/s) |
| Doppler cut | Slice at target-1 range |
| Range cut | Slice at target-1 *apparent* velocity |
| Two-pulse MTI | Enable/disable canceller before the FFT |
| Annotations | True target range/velocity (and fold if ambiguous) |

Status text reports PRF, \(\Delta R\), \(\Delta v\), \(R_\mathrm{unamb}\), \(v_\mathrm{unamb}\).

---

## 3. Guided walkthrough

Enable **Presenter mode**.

### Experiment A — Single mover (~5 min)

1. Load **Single moving target**.
2. Find the bright cell; match range and velocity annotations.
3. Change velocity and watch the peak move on the Doppler axis.

**Expect:** one peak away from zero Doppler when clutter is off.

### Experiment B — Clutter masks a slow target (~8 min)

1. Load **Clutter masks a slow target**.
2. Note the bright zero-Doppler ridge; the slow mover is hard to see.
3. Raise target velocity gradually until it peeks out of clutter.

**Expect:** slow targets compete with clutter; separation in Doppler is survival.

### Experiment C — MTI reveals the mover (~8 min)

1. Load **MTI reveals the mover**.
2. With MTI on, clutter ridge collapses; the mover stands out.
3. Toggle **Two-pulse MTI** off/on.

**Expect:** MTI is a zero-Doppler notch — great for clutter, harmful to *very*
slow targets that also sit near DC.

### Experiment D — Two velocities, one range (~5 min)

1. Load **Two velocities at one range**.
2. Confirm one range cut shows two Doppler peaks.

**Expect:** Doppler FFT separates co-range targets with different radial speeds.

### Experiment E — Doppler ambiguity (~8 min)

1. Load **Doppler ambiguity (PRF fold)**.
2. Read \(v_\mathrm{unamb}\) from the status line and the annotation’s folded
   velocity.
3. Increase PRF (shorter PRI) until the apparent velocity matches the true 120 m/s.

**Expect:** aliases until PRF is high enough (trade vs range ambiguity from
Tutorial 03).

### Experiment F — CPI resolution (~8 min)

1. Load **CPI length vs Doppler resolution** (\(N=16\), two close velocities).
2. Raise **N pulses** until the Doppler cut shows two clear peaks.

**Expect:** \(\Delta v\) falls as \(1/N\).

---

## 4. Self-paced lab sheet

| Scene | True \((R,v)\) | Measured peak | \(v_\mathrm{unamb}\) | Notes |
| --- | --- | --- | --- | --- |
| Single mover | | | | |
| Clutter, MTI off | | | | visible? Y/N |
| Same, MTI on | | | | |
| Ambiguity case | 2.5 km, 120 m/s | | | folded? |
| CPI \(N=16\) vs \(N=64\) | two v at 3.2 km | | | resolved? |

Design trade: you need \(v_\mathrm{unamb}\ge 80\,\mathrm{m/s}\) at X-band
(\(10\,\mathrm{GHz}\)) and \(R_\mathrm{unamb}\ge 10\,\mathrm{km}\). Is one PRF
enough? What staggered-PRF idea would you mention in a viva?

---

## 5. Check your understanding

1. Why is the factor **2** in \(f_d=2v/\lambda\)?
2. Explain range ambiguity vs Doppler ambiguity as dual sampling limits (PRI vs
   PRF).
3. Sketch the frequency response of a two-pulse canceller.
4. What happens to an airborne platform’s mainlobe clutter Doppler, and why is
   *platform*-aware STAP a next step beyond this demo?

---

## 6. Where to go next

Natural follow-ons: **CFAR** on RD maps, **FMCW** range–Doppler, then **SAR**
(azimuth compression). This demo closes the loop from “how far” (Tutorial 03)
to “how far and how fast.”
