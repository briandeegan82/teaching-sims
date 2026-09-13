# Tutorial 06 — FMCW radar

**Demo:** `teaching-sims demo fmcw`  
**Prerequisites:** Tutorials 03–04 (ranging + Doppler) help  
**Goal:** connect chirp slope to beat frequency, see sawtooth range–Doppler
coupling, recover \((R,v)\) with a triangle waveform, and read an FMCW RD map

---

## 1. Principles

### 1.1 Dechirp / beat frequency

An FMCW transmit chirp with bandwidth \(B\) and duration \(T\) has slope
\(S=B/T\). After mixing the echo with the TX replica (dechirp), a stationary
target at range \(R\) produces an IF tone

\[
f_b=\frac{2SR}{c}\qquad\Rightarrow\qquad R=\frac{c\,f_b}{2S}.
\]

Range resolution is the same as pulsed LFM compression: \(\Delta R=c/(2B)\).

### 1.2 Maximum range (IF Nyquist)

If \(f_b\) exceeds \(f_s/2\), the tone aliases. With \(f_b=2SR/c\),

\[
R_{\max}\approx\frac{f_s\,c}{4S}.
\]

### 1.3 Sawtooth + motion (range–Doppler coupling)

For a closing target, the beat on an up-chirp is approximately

\[
f_b\approx\frac{2SR}{c}+\frac{2v}{\lambda}.
\]

Naive conversion \(R=c f_b/(2S)\) is **biased** by Doppler. A CPI of chirps still
forms a range–Doppler map via a second FFT, but single-chirp ranging is wrong
for movers.

### 1.4 Triangle up / down

Alternate up and down sweeps:

\[
f_{b\uparrow}=\frac{2SR}{c}+\frac{2v}{\lambda},\qquad
f_{b\downarrow}=\frac{2SR}{c}-\frac{2v}{\lambda}.
\]

Then \(R\) from the average beat and \(v\) from the difference — the classic
automotive decoupling trick.

### 1.5 Automotive RD map

Stack chirps (slow time), FFT along fast time (range) then slow time (Doppler).
This is the map behind many 77 GHz demo videos.

---

## 2. UI map

| Panel | Meaning |
| --- | --- |
| IF spectrum | First-chirp beat tones |
| Range profile | Mean range FFT over the CPI |
| RD map | 2D FFT image (range vs velocity) |
| Status | \(\Delta R\), \(R_{\max}\), coupling / triangle solve |

---

## 3. Guided walkthrough

### Experiment A — Stationary beat (~5 min)

1. Load **Stationary target beat tone**.
2. Match IF peak → range profile peak → annotation.

### Experiment B — Resolution (~8 min)

1. Load **Range resolution (two targets)** (1 m spacing, \(\Delta R\approx1.5\,\mathrm{m}\)).
2. Raise **Bandwidth B** until two peaks appear.

### Experiment C — Sawtooth coupling (~8 min)

1. Load **Sawtooth range–Doppler coupling**.
2. Read status “beat→range” vs true 40 m.
3. Watch the RD peak at the true velocity — map is fine; single-chirp \(R\) is not.

### Experiment D — Triangle solve (~8 min)

1. Load **Triangle up/down decoupling**.
2. Confirm status \(R,v\) match the true target.

### Experiment E — RD map (~5 min)

1. Load **FMCW range–Doppler map**.
2. Identify two cells.

### Experiment F — Nyquist fold (~5 min)

1. Load **IF Nyquist / max range**.
2. Note \(R_{\max}\); peak is aliased if \(R>R_{\max}\). Raise IF sample rate to fix.

---

## 4. Lab sheet

| Scene | Measured peak \(R\) or \((R,v)\) | Notes |
| --- | --- | --- |
| Stationary 50 m | | |
| Two targets @ 40 & 41 m, low B | | merged? |
| Same, high B | | |
| Sawtooth 40 m @ 30 m/s | beat→R = | bias |
| Triangle same target | solved (R,v) | |
| Nyquist case | apparent R | |

---

## 5. Check your understanding

1. Derive \(f_b=2SR/c\) from a delay \(\tau=2R/c\) on a linear chirp.
2. Why does sawtooth coupling matter for ADAS corner radars?
3. How does triangle processing trade timeline / PRF versus sawtooth CPI Doppler?
4. Where would you place CFAR on this processing chain?

---

## 6. Next

**SAR stripmap** is the remaining high-impact imaging topic in the roadmap.
