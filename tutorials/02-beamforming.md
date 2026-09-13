# Tutorial 02 — Digital beamforming

**Demo:** `teaching-sims demo beamforming`  
**Prerequisites:** Tutorial 01 (array factor / steering vector intuition)  
**Goal:** contrast conventional delay-and-sum, deterministic null steering, and
MVDR; read beampatterns, Capon spectra, weights, and SINR

---

## 1. Principles

### 1.1 Steering vector and conventional beamforming

For a narrowband ULA, the response to a unit plane wave from angle \(\theta\) is
the steering vector \(a(\theta)\in\mathbb{C}^N\) (same phase progression as
Tutorial 01).

**Conventional / Bartlett / delay-and-sum** weights looking at \(\theta_\ell\) are

\[
w_\mathrm{conv}=\frac{a(\theta_\ell)}{N}.
\]

The **beampattern** is \(B(\theta)=|w^H a(\theta)|^2\). With these weights it is
essentially the array factor from Tutorial 01. Looking in the right direction
does **not** remove a strong interferer that sits in a sidelobe.

### 1.2 Snapshot model and sample covariance

With signal-of-interest (SOI), optional interferer, and white noise,

\[
x[\ell]=s[\ell]\,a(\theta_s)+i[\ell]\,a(\theta_i)+n[\ell],\qquad
\hat R=\frac{1}{L}\sum_{\ell=1}^{L}x[\ell]x[\ell]^H.
\]

Eigenvalues of \(\hat R\) show how many strong spatial sources are present
(plus the noise floor).

### 1.3 Deterministic null steering

If \(\theta_i\) is known, project it out of the look steering vector:

\[
w \propto \Big(I-\frac{a_i a_i^H}{\|a_i\|^2}\Big)a(\theta_\ell),
\]

then normalise for unity gain on the look direction. This is model-based, not
data-adaptive.

### 1.4 MVDR (Capon) beamformer

Minimise output power subject to unity gain on the look direction:

\[
\min_w\, w^H R w \quad\mathrm{s.t.}\quad w^H a(\theta_\ell)=1
\quad\Rightarrow\quad
w_\mathrm{MVDR}=\frac{R^{-1}a}{a^H R^{-1}a}.
\]

MVDR places **adaptive nulls** toward interferers encoded in \(R\), while
protecting the look direction. The related **Capon spectrum**

\[
P(\theta)=\frac{1}{a(\theta)^H R^{-1}a(\theta)}
\]

is a high-resolution spatial spectrum (useful for seeing closely spaced
sources).

### 1.5 Diagonal loading

With few snapshots, \(\hat R\) can be ill-conditioned and MVDR becomes brittle
(deep random nulls, SOI cancellation). **Diagonal loading** replaces \(R\) by
\(R+\sigma_\mathrm{load}^2 I\), trading some adaptivity for robustness.

### 1.6 SINR

The status panel reports an **analytical SINR** for the current weights under
the single-interferer + white-noise model. Use it to quantify “looks better on
the plot” in dB.

---

## 2. UI map

| Panel | Role |
| --- | --- |
| Beampattern | \(|w^H a(\theta)|^2\) for the selected method |
| Overlay conventional | Compare adaptive / null-steer vs DAS |
| Capon spectrum | \(P(\theta)\) from \(\hat R\) |
| \|w\| and ∠w | Weight magnitudes and unwrapped phases |
| Eigenvalues of \(R\) | Spatial degrees of freedom / source count |
| Resample snapshots | New noise / signal realisation |

**Markers:** look direction, SOI angle, interferer angle.

---

## 3. Guided walkthrough

Enable **Presenter mode**.

### Experiment A — Conventional look (~5 min)

1. Load **Conventional delay-and-sum**.
2. Move **Look \(\theta\)** and **SOI \(\theta\)** together (matched case).
3. Optionally mismatch SOI vs look by \(10^\circ\) and watch the pattern vs SINR.

**Expect:** pattern peak follows the look direction; this is Tutorial 01 in
receive clothing.

**Talking point:** “Transmit AF and receive DAS are the same inner product.”

### Experiment B — Interferer in a sidelobe (~8 min)

1. Load **Strong interferer in a sidelobe**.
2. Note INR ≫ SNR and the interferer marker near a sidelobe.
3. Read **Analytical SINR** — it should be poor despite a correct look angle.
4. Optionally raise INR further.

**Expect:** beampattern still looks “fine,” but SINR collapses. A pretty pattern
is not enough.

### Experiment C — MVDR adaptive null (~10 min)

1. Load **MVDR adaptive null** (conventional overlay on).
2. Compare orange conventional curve vs MVDR: MVDR should notch near the
   interferer.
3. Read SINR vs the parenthetical “conventional would be …” value.
4. Click **Resample snapshots** a few times — the null stays near the interferer
   but fine structure changes with \(\hat R\).

**Expect:** large SINR improvement; null tracks the interferer without you typing
its angle into the weight formula (the data did).

### Experiment D — Deterministic null vs MVDR (~8 min)

1. Load **Deterministic null steering**.
2. Confirm a deep null at **Null-steer \(\theta\)**.
3. Move the **interferer** away from that null angle — SINR falls.
4. Switch method to **MVDR** without changing geometry.

**Expect:** fixed null only helps when the model angle matches; MVDR re-learns
the null from \(R\).

### Experiment E — Two-source resolution (~8 min)

1. Load **Resolving two close sources**.
2. Compare **beampattern** width vs **Capon spectrum** peaks.
3. Move interferer angle toward the SOI until Capon peaks merge; then separate
   them again.

**Expect:** Capon resolves closer spacings than the conventional beamwidth
suggests (within SNR / snapshot limits).

### Experiment F — Diagonal loading (~8 min)

1. Load **Diagonal loading** (few snapshots).
2. Set loading to **−40 (off)** and note erratic pattern / fragile nulls.
3. Raise loading toward **0 dB** and watch the pattern stabilise (null softens).

**Expect:** robustness↑, adaptivity↓ — the classic loading tradeoff.

---

## 4. Self-paced lab sheet

Scene: \(N=8\), look = SOI = \(0^\circ\), interferer \(35^\circ\), SNR \(10\,\mathrm{dB}\),
INR \(25\,\mathrm{dB}\), \(L=256\) snapshots.

| Method | SINR (dB) | Depth near \(35^\circ\) (dB) | Notes |
| --- | --- | --- | --- |
| Conventional | | | |
| Null steer at \(35^\circ\) | | | |
| MVDR | | | |
| MVDR, \(L=20\), loading off | | | |
| MVDR, \(L=20\), loading −10 dB | | | |

Extra: with MVDR, set look = \(0^\circ\) but SOI = \(5^\circ\) (look mismatch). What
happens to SINR and why is this dangerous in practice?

---

## 5. Check your understanding

1. Write the MVDR optimisation in words a non-specialist can follow.
2. Why can Capon’s spectrum beat Rayleigh beamwidth, and when does it fail?
3. If the SOI is strong and included in \(\hat R\), what can MVDR do to the SOI
   (signal cancellation), and how do practitioners mitigate it?
4. How many large eigenvalues do you expect for “SOI + one interferer + white
   noise” on an 8-element array?

---

## 6. Bridge to the next tutorial

Beamforming answers *which direction*. Pulsed ranging answers *how far*.
Tutorial 03 moves to the time/delay domain: pulses, matched filters, and PRI
ambiguity.
