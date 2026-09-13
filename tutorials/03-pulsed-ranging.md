# Tutorial 03 — Pulsed radar ranging

**Demo:** `teaching-sims demo pulsed-ranging`  
**Goal:** map echo delay to range, see resolution limits, use LFM pulse
compression, and recognise PRI range ambiguity

---

## 1. Principles

### 1.1 Delay and range

A pulse reflected from a target at range \(R\) returns after round-trip delay

\[
\tau=\frac{2R}{c}\qquad\Rightarrow\qquad R=\frac{c\tau}{2}.
\]

The demo’s horizontal axis is already converted to range (km). Markers show
true target ranges (and the folded/apparent range when ambiguity occurs).

### 1.2 Range resolution (simple pulse)

Two equal-strength echoes are usually separable if their delay difference
exceeds about one pulse width \(T_p\):

\[
\Delta R \approx \frac{c\,T_p}{2}.
\]

Shorter pulses improve resolution but reduce average energy if peak power is
limited — the classic radar tradeoff that pulse compression addresses.

### 1.3 Matched filter

For known transmit waveform \(s(t)\) in additive white noise, the filter that
maximises SNR is matched to \(s(t)\) (correlation with the TX waveform). The
demo can show **raw** \(|r_x|\) and **matched-filter video** on the same range
axis.

### 1.4 LFM pulse compression

A linear frequency modulated (LFM / chirp) pulse of duration \(T_p\) and sweep
bandwidth \(B\) has a matched-filter mainlobe width on the order of \(1/B\), so

\[
\Delta R \approx \frac{c}{2B}
\]

**after** compression — even if \(T_p\) is long. You keep energy (\(T_p\)) and
gain resolution (\(B\)). The instantaneous-frequency panel shows the chirp
ramp when LFM is selected.

### 1.5 Maximum unambiguous range

Pulses repeat every PRI (pulse repetition interval). Delays larger than one PRI
fold back into the display window:

\[
R_\mathrm{unamb}=\frac{c\cdot\mathrm{PRI}}{2},\qquad
R_\mathrm{apparent}=R \bmod R_\mathrm{unamb}.
\]

A target farther than \(R_\mathrm{unamb}\) can look like a much closer one.

---

## 2. UI map

| Control / panel | Meaning |
| --- | --- |
| Range profile | Normalised envelope vs range (MF video by default) |
| Overlay raw \|rx\| | Pre-matched-filter magnitude |
| ΔR about T1 | Resolution width centred on target 1 |
| TX baseband I/Q | Complex envelope of the pulse |
| LFM instantaneous freq | Chirp \(f_i(t)\) when applicable |
| Matched filter checkbox | Toggle compression / MF on or off |
| PRI, \(T_p\), \(B\) | Ambiguity and resolution knobs |

Status text reports \(\Delta R\), \(R_\mathrm{unamb}\), and MF state.

---

## 3. Guided walkthrough

Enable **Presenter mode**.

### Experiment A — Single echo delay (~5 min)

1. Load **Single echo delay** (or
   `teaching-sims demo pulsed-ranging --scenario single_echo`).
2. Read the peak location; confirm it matches the **T1** marker near \(2\,\mathrm{km}\).
3. Move **Target 1 range** and verify the peak follows \(R=c\tau/2\).

**Expect:** one clear peak at the commanded range.

**Ask:** “If the display were in time (µs), how would you convert a cursor
reading to metres?”

### Experiment B — Unresolved vs resolved pair (~10 min)

1. Load **Unresolved targets (coarse pulse)**.
2. Note \(\Delta R\) in the status line (~300 m) vs 150 m target spacing — one
   blob.
3. Load **Resolved by shorter pulse** (same geometry, shorter \(T_p\)).

**Expect:** two peaks appear once \(\Delta R\) drops below the separation.

**Optional free-play:** from the unresolved scene, shorten \(T_p\) yourself until
the peaks split; record the \(T_p\) where you first “call” them resolved.

### Experiment C — LFM pulse compression (~12 min)

1. Load **LFM pulse compression**.
2. With **Matched filter ON**, confirm two targets ~120 m apart are separable
   even though \(T_p=20\,\mu\mathrm{s}\) would be terrible as a plain rectangle
   (\(\Delta R \approx c T_p/2 \approx 3\,\mathrm{km}\)).
3. Turn **Matched filter OFF** and enable **Overlay raw \|rx\|**.
4. Turn MF back **ON**.

**Expect:** raw video is a long smear; MF collapses energy into narrow peaks
with resolution \(\sim c/(2B)\).

5. Open advanced controls and change **LFM bandwidth \(B\)**. Larger \(B\) →
   sharper peaks.

### Experiment D — Matched-filter SNR gain (~5 min)

1. Load **Matched-filter SNR gain** (weaker target).
2. Toggle MF off/on and/or overlay raw video.
3. Use **Resample noise** to see variability.

**Expect:** the peak is much easier to see after MF — this is SNR gain from
coherent correlation, not magic.

### Experiment E — Range ambiguity (~8 min)

1. Load **Range ambiguity (PRI fold)**.
2. Note true range \(10\,\mathrm{km}\) but \(R_\mathrm{unamb}\approx 7.5\,\mathrm{km}\).
3. Confirm the displayed peak sits at the **folded** range (~2.5 km) while the
   annotation still reports the true range.

**Expect:** apparent range \(\neq\) true range when \(R>R_\mathrm{unamb}\).

**Challenge:** increase PRI until \(R_\mathrm{unamb}>10\,\mathrm{km}\) and watch the
peak jump to the true location.

---

## 4. Self-paced lab sheet

| Experiment | Parameter | Observed peak range(s) | \(\Delta R\) (status) | Pass criterion |
| --- | --- | --- | --- | --- |
| Single echo | \(R=2\,\mathrm{km}\) | | | within ~50 m |
| Unresolved pair | \(T_p=2\,\mu\mathrm{s}\), 150 m spacing | | | single merged peak |
| Resolved pair | \(T_p=0.4\,\mu\mathrm{s}\) | | | two distinct peaks |
| LFM MF on | \(B=10\,\mathrm{MHz}\), 120 m spacing | | | two peaks |
| LFM MF off | same | | | unresolved smear |
| Ambiguity | \(R=10\,\mathrm{km}\), PRI \(50\,\mu\mathrm{s}\) | | | peak near \(R\bmod R_\mathrm{unamb}\) |

Design question: you need \(\Delta R\le 15\,\mathrm{m}\) and average power set by
\(T_p\ge 10\,\mu\mathrm{s}\). Can a rectangle pulse do it? What LFM bandwidth
would you choose instead?

---

## 5. Check your understanding

1. Derive \(R=c\tau/2\) from first principles (draw the round trip).
2. Why does pulse compression need a **matched** filter (or equivalent
   correlation), not just “any” bandpass filter?
3. A radar advertises fine range resolution and a high PRF. What ambiguity
   problem should you immediately suspect?
4. How do windowing (Hann on TX) and bandwidth jointly affect sidelobes vs
   mainlobe width after compression?

---

## 6. Where to go next

Natural extensions in this repo’s roadmap: **SAR / FFT imaging** (range +
azimuth via Doppler/history), and coupling a pulsed ranger with the
beamforming demo (angle + range). For now, you have the three pillars of many
intro radar courses: *steer*, *adapt*, and *range*.
