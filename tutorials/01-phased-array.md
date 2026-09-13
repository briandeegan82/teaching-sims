# Tutorial 01 — Phased-array antennas

**Demo:** `teaching-sims demo phased-array`  
**Audience:** graduate / advanced undergraduate, mixed RF background  
**Goal:** connect interference → array factor → electronic steering → practical
limits (grating lobes, squint, quantization)

---

## 1. Principles

### 1.1 From two sources to an array

Two coherent radiators produce an interference pattern. At angle \(\theta\) from
broadside, the path difference between elements spaced by \(d\) is
\(d\sin\theta\), so the phase difference is

\[
\psi = kd\sin\theta = \frac{2\pi}{\lambda}\,d\sin\theta.
\]

Constructive interference (a *main beam*) occurs where the applied excitation
phases cancel \(\psi\). An \(N\)-element uniform linear array (ULA) is the same
idea with \(N\) controllable phases.

### 1.2 Array factor

For complex weights \(w_n = |w_n|e^{j\phi_n}\) on elements at positions \(x_n\),

\[
\mathrm{AF}(\theta)=\sum_{n=0}^{N-1} w_n\,
\exp\!\big(j\,k x_n\sin\theta\big).
\]

The demo plots the **power pattern** \(|\mathrm{AF}|^2\) in dB (peak-normalised).
The half-power beamwidth (HPBW) shrinks as the electrical aperture \(Nd/\lambda\)
grows — roughly

\[
\mathrm{HPBW}\approx 0.886\,\frac{\lambda}{Nd}\quad\text{(radians, broadside, uniform weights)}.
\]

### 1.3 Electronic steering

To steer the beam to \(\theta_0\), apply a progressive phase

\[
\phi_n = -k\,x_n\sin\theta_0
\]

(narrowband **phase-shift** beamforming). The hardware does not move; only the
excitation phases change. In the demo, the yellow arrow on the array layout and
the vertical “steer” marker on the pattern show \(\theta_0\).

### 1.4 Grating lobes

If \(d\) is too large, more than one angle can satisfy the same progressive-phase
condition. A useful rule of thumb: keep \(d\le\lambda/2\) to avoid visible grating
lobes over \(|\theta|\le 90^\circ\). When scanning to \(\theta_0\), the stricter
condition is approximately

\[
\frac{d}{\lambda}\le \frac{1}{1+|\sin\theta_0|}.
\]

### 1.5 Phase shift vs true time delay (TTD)

Phase weights designed at frequency \(f_0\) only “point” correctly near \(f_0\).
At another RF frequency the beam **squints**. True time delay applies

\[
\tau_n = -\frac{x_n\sin\theta_0}{c},
\]

which is correct across bandwidth (within the model). The compare overlay in the
demo plots phase-shift and TTD patterns together.

### 1.6 Phase quantization

Real phase shifters have finite bits. Quantizing \(\phi_n\) creates pointing error
and raised spurious lobes. Fewer bits → uglier patterns.

---

## 2. UI map

| Panel / control | What it shows |
| --- | --- |
| Array factor (dB) | Far-field power pattern vs \(\theta\) |
| Callouts | Main beam, grating lobes, nulls |
| Array layout | Elements coloured by phase; phasor arrows; steer cue |
| Element phase | Unwrapped \(\phi_n\) vs position |
| Wavefront snapshot | Near-field interference cartoon \(\mathrm{Re}\{E\}\) |
| Presenter mode | Hides advanced controls |
| Compare phase vs TTD | Overlay true-time-delay pattern |

**Core sliders:** \(N\), \(d/\lambda_\mathrm{design}\), steer \(\theta_0\), steering mode.  
**Advanced:** RF frequency, design frequency \(f_0\), phase bits, \(\cos\theta\) element
pattern, Hann taper, auto-sweep animations.

---

## 3. Guided walkthrough (lecture path)

Enable **Presenter mode**. Work the scenarios in order.

### Experiment A — Interference basics (~5 min)

1. Click **Two-element interference** (or run
   `teaching-sims demo phased-array --scenario interference_basics`).
2. Observe two broad lobes / deep nulls — this is Young-type interference.
3. Increase **N elements** to 4, then 8 without changing spacing.

**Expect:** a clearer main beam and lower relative sidelobes as \(N\) grows.

**Ask the room:** “Is a phased array doing anything other than *controlled*
interference?”

### Experiment B — Electronic steering (~8 min)

1. Load **Electronic beam steering**.
2. Watch auto-sweep, or drag **Steer \(\theta_0\)** yourself.
3. Look at the **array layout**: phasor arrows should show a progressive phase
   tilt that tracks the yellow steer arrow.
4. Confirm the pattern peak tracks the steer marker (status line prints peak and
   HPBW).

**Expect:** main lobe moves without changing geometry; element phases become a
nearly linear ramp vs \(x\).

### Experiment C — Beamwidth vs aperture (~5 min)

1. Load **Beamwidth vs aperture** (auto-grows \(N\)).
2. Read HPBW from the status text as \(N\) increases.

**Expect:** HPBW falls roughly as \(1/N\).

**Optional:** turn off auto-grow, set \(N=8\), and enable **Hann amplitude taper**.
Sidelobes drop; the main beam widens slightly (classic taper tradeoff).

### Experiment D — Grating lobes (~10 min)

1. Load **Grating lobes (\(d>\lambda/2\))**.
2. Note callouts labelling extra peaks near the theoretical grating angles.
3. Drop **\(d/\lambda\)** from \(0.9\) → \(0.5\) at the same steer angle.

**Expect:** the extra “main” beams disappear once spacing is safe.

**Challenge:** at \(d/\lambda=0.7\), how far can you scan before a grating lobe
enters visible space? Compare with the formula in §1.4.

### Experiment E — Phase vs TTD / beam squint (~10 min)

1. Load **Phase shift vs true time delay** (compare overlay turns on).
2. With **Phase shift** selected, sweep **RF freq** away from **Design freq \(f_0\)**.
3. Switch steering mode to **True time delay** and repeat.

**Expect:** phase-shift peak walks away from \(\theta_0\) (squint); TTD peak stays
put.

### Experiment F — Quantized phase (~5 min)

1. Load **Phase quantization** (starts at 2 bits).
2. Raise **Phase bits** \(2\to 3\to 4\to 0\) (0 = continuous).

**Expect:** spurious lobes fall and pointing cleans up as bits increase.

---

## 4. Self-paced lab sheet

Complete and note values (approximate is fine):

| Task | Measurement | Your value |
| --- | --- | --- |
| \(N=8\), \(d/\lambda=0.5\), \(\theta_0=0^\circ\) | HPBW | |
| Same, \(\theta_0=30^\circ\) | Peak angle | |
| \(d/\lambda=1.0\), \(\theta_0=0^\circ\) | Angle of strongest grating-like peak | |
| Phase shift, \(f_0=10\,\mathrm{GHz}\), \(f=14\,\mathrm{GHz}\), \(\theta_0=40^\circ\) | Peak angle | |
| Same geometry, TTD | Peak angle | |
| \(N=16\), \(\theta_0=30^\circ\), 2-bit phase | Highest sidelobe / spur (dB) | |
| Same, continuous phase | Highest sidelobe (dB) | |

---

## 5. Check your understanding

1. Why does \(d>\lambda/2\) create grating lobes, in spatial-frequency language?
2. Why does Hann taper widen HPBW while lowering sidelobes?
3. A wideband waveform is steered with phase shifters designed at band centre.
   What goes wrong at the band edges, and what hardware fixes it?
4. How is the **wavefront snapshot** related to (but not the same as) the
   far-field array factor?

---

## 6. Bridge to the next tutorial

The transmit array factor you just explored is the same mathematics as a
**conventional receive beamformer** with weights \(w\propto a(\theta_0)\).
Tutorial 02 adds interferers, covariance estimation, and adaptive MVDR nulls.
