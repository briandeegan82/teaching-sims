# Tutorial 07 — Stripmap SAR

**Demo:** `teaching-sims demo sar`  
**Prerequisites:** pulsed LFM ranging + Doppler/FMCW intuition help  
**Goal:** see how motion synthesises a long aperture, and how range then azimuth
compression focuses point targets

---

## 1. Principles

### 1.1 Geometry

A side-looking platform flies along \(x\) at speed \(v\), altitude \(h\). A
scatterer at ground coordinates \((x_t,y_t)\) has slant range

\[
R(x)=\sqrt{(x-x_t)^2+h^2+y_t^2}.
\]

As the radar flies past, \(R(x)\) is approximately hyperbolic — the classic SAR
range history / “smiles” in the data.

### 1.2 Range compression

Each pulse is an LFM. Matched filtering (as in Tutorial 03) focuses the fast-time
dimension to slant-range resolution

\[
\Delta R\approx\frac{c}{2B}.
\]

After this step alone the target is still smeared along azimuth (unfocused
panel).

### 1.3 Synthetic aperture and azimuth resolution

Collecting \(N\) pulses synthesises an aperture of length
\(L_\mathrm{sa}\approx v(N-1)/\mathrm{PRF}\). Broadside stripmap resolution is
roughly

\[
\Delta x\approx\frac{\lambda R_0}{2 L_\mathrm{sa}}.
\]

Longer flight / more pulses → finer along-track detail (until other limits).

### 1.4 Azimuth focusing (teaching processor)

For a reference range \(R_0\), the azimuth phase history is an LFM with rate
\(K_a\approx 2v^2/(\lambda R_0)\). This demo **deramps** with a reference chirp
and FFTs (SPECAN-style). A target at \(x_0\) becomes a tone at
\(f_d=K_a x_0/v\), mapped back to \(x_0=f_d v/K_a\).

Real SAR processors (RDA, CSA, ω-k) handle range migration more carefully; this
model is intentionally compact for lecture demos.

---

## 2. UI map

| Panel | Meaning |
| --- | --- |
| Focused image | After range + azimuth compression |
| Unfocused | Range-compressed only (azimuth streaks) |
| Range / azimuth cuts | 1D slices through the focused image |
| Status | \(\Delta R\), \(\Delta x\), \(L_\mathrm{sa}\), \(R_0\) |

Axes: horizontal = **slant range**, vertical = **along-track \(x\)**.

---

## 3. Guided walkthrough

### Experiment A — Single point (~5 min)

1. Load **Single point target**.
2. Compare unfocused streak vs focused bright cell.

### Experiment B — Azimuth pair (~8 min)

1. Load **Two targets in azimuth**.
2. Confirm two focused peaks near \(x=\pm 30\,\mathrm{m}\).

### Experiment C — Range resolution (~8 min)

1. Load **Two targets in range** (coarse \(B\)).
2. Raise **Bandwidth** until slant-range peaks split.

### Experiment D — Aperture length (~8 min)

1. Load **Aperture length vs Δx** (short CPI).
2. Increase **Pulses (aperture)** and watch \(\Delta x\) and the pair resolve.

### Experiment E — Unfocused vs focused (~5 min)

1. Load **Unfocused vs focused**.
2. Use cuts to show energy collapsed only after azimuth processing.

---

## 4. Lab sheet

| Scene | Measured peak(s) | \(\Delta R\), \(\Delta x\) (status) |
| --- | --- | --- |
| Single point | | |
| Azimuth ±30 m | | |
| Range pair, low B | | |
| Range pair, high B | | |
| Short vs long aperture | | |

Compute \(\Delta x\approx\lambda R_0/(2L_\mathrm{sa})\) from status numbers — does
it match the observed mainlobe width on the azimuth cut?

---

## 5. Check your understanding

1. Why does a real antenna alone not achieve the same \(\Delta x\) as \(L_\mathrm{sa}\)?
2. What is range cell migration, and when does this demo’s single-\(R_0\) deramp fail?
3. How do PRF limits relate to Doppler bandwidth and azimuth aliasing?
4. Where would CFAR run on a SAR image product?

---

## 6. Course wrap

You now have a full intro path: **steer → adapt → range → Doppler → detect →
FMCW → SAR**. Natural enrichments later: ambiguity functions, monopulse, STAP.
