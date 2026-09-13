# Demo launch scripts

Each script activates `.venv` and starts a demo. From the repo root:

```bash
./demos/phased-array.sh
./demos/beamforming.sh --scenario mvdr_adaptive_null
./demos/pulsed-ranging.sh --scenario lfm_compression
./demos/pulse-doppler.sh --scenario mti_reveals_target
./demos/cfar.sh --scenario fixed_vs_cfar_clutter
./demos/fmcw.sh --scenario triangle_decouple
./demos/sar.sh --scenario two_azimuth
```

Or use the CLI:

```bash
teaching-sims list
teaching-sims demo <topic> [--scenario ID] [--list-scenarios]
```
