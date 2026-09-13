# Tutorial 05 — CFAR detection

**Demo:** `teaching-sims demo cfar`  
**Prerequisites:** Tutorial 03 (range profiles) helpful  
**Goal:** understand adaptive thresholds that hold false-alarm rate in unknown
noise / clutter; compare CA, OS, GO, and SO CFAR

---

## 1. Principles

### 1.1 Why not a fixed threshold?

For exponential noise power with known mean \(\sigma^2\),

\[
P_{\mathrm{fa}}=\exp(-T/\sigma^2)\quad\Rightarrow\quad T=-\sigma^2\ln P_{\mathrm{fa}}.
\]

If the local interference power changes (clutter edge, jamming, antenna pattern),
a threshold designed for clear noise creates **false-alarm floods** or **missed
detections**.

### 1.2 CFAR idea

Around each cell under test (CUT), exclude nearby **guard** cells (to avoid
self-contamination) and estimate interference from **training** cells. Scale the
estimate by a factor \(\alpha(P_{\mathrm{fa}},N)\) to get the threshold.

### 1.3 CA-CFAR (cell averaging)

\[
Z=\frac{1}{N}\sum_{i\in\mathrm{train}} x_i,\qquad T=\alpha Z,
\quad \alpha=N\big(P_{\mathrm{fa}}^{-1/N}-1\big)
\]

(for square-law / exponential samples; equivalent to scaling the *sum* by
\(P_{\mathrm{fa}}^{-1/N}-1\)). Sensitive when training cells contain other
targets (**masking**) or sit across a clutter edge.

### 1.4 OS-CFAR (ordered statistic)

Sort training samples and take the \(k\)-th largest. Outlying large samples (other
targets) influence the estimate less if \(k\) is chosen below the extremes — better
in multi-target scenes.

### 1.5 GO / SO CFAR

Split training into left and right means \(Z_L,Z_R\):

- **GO (greatest of):** \(Z=\max(Z_L,Z_R)\) — fewer FAs at clutter edges  
- **SO (smallest of):** \(Z=\min(Z_L,Z_R)\) — better detection near edges, more FAs  

---

## 2. UI map

| Element | Role |
| --- | --- |
| Power curve | Square-law range profile (dB) |
| CFAR threshold | Adaptive \(T\) vs cell |
| Fixed threshold | Noise-only design (flat) |
| Green markers | Cells exceeding CFAR threshold |
| Window schematic | CUT / guard / training layout |
| Status | Hits, misses, false alarms |

---

## 3. Guided walkthrough

Enable **Presenter mode**.

### Experiment A — CA-CFAR basics (~5 min)

1. Load **CA-CFAR two targets**.
2. Confirm both peaks exceed the orange CFAR threshold.
3. Toggle **Overlay fixed threshold** — in homogeneous noise both look similar.

**Expect:** adaptive threshold tracks the noise floor; detections on both targets.

### Experiment B — Clutter edge (~10 min)

1. Load **Clutter edge: fixed vs CFAR**.
2. With fixed threshold on, count green CFAR detections vs how often the **power
   curve** sits above the grey fixed line in the clutter region.
3. Note status **CFAR FAs** vs the obvious fixed-threshold flood.

**Expect:** fixed threshold fails in clutter; CA-CFAR raises \(T\) after the edge.

### Experiment C — Masking (~8 min)

1. Load **CA masking of a weak neighbour**.
2. Strong target in the training window of the weak one → weak peak missed.
3. Load **OS-CFAR recovers neighbour** (same geometry).

**Expect:** OS restores the weak detection more often than CA.

### Experiment D — GO at the edge (~5 min)

1. Load **GO-CFAR at a clutter edge**.
2. Switch method to **SO-CFAR** and compare FA counts near the edge.

**Expect:** GO is more conservative at the step edge.

### Experiment E — \(P_{\mathrm{fa}}\) tradeoff (~5 min)

1. Load **P_fa vs detections**.
2. Move **log10(P_fa)** from \(-4\) toward \(-2\).

**Expect:** threshold drops; weak target and FAs both increase.

---

## 4. Self-paced lab sheet

| Scenario | Method | Hits | Misses | CFAR FAs |
| --- | --- | --- | --- | --- |
| Two targets | CA | | | |
| Clutter edge | CA | | | |
| Same scene | fixed thr. FAs (visual) | — | — | |
| Masking pair | CA | | | |
| Masking pair | OS | | | |
| Clutter edge | GO | | | |
| Clutter edge | SO | | | |

Design: \(P_{\mathrm{fa}}=10^{-4}\), \(N=24\) training cells. Compute CA \(\alpha\).
Does the demo’s status \(\alpha\) match?

---

## 5. Check your understanding

1. Why are guard cells used?
2. Explain masking in one sentence.
3. When would you prefer GO over CA?
4. How would you extend this 1D CFAR to a range–Doppler map (2D CFAR)?

---

## 6. Where to go next

**FMCW** range–Doppler (automotive-style) or **SAR** imaging. CFAR is the usual
detection stage after those maps are formed.
