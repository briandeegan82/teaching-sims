# Demo launch scripts

Each script activates `.venv` and starts a demo. From the repo root:

### Radar

```bash
./demos/phased-array.sh
./demos/beamforming.sh --scenario mvdr_adaptive_null
./demos/pulsed-ranging.sh --scenario lfm_compression
./demos/pulse-doppler.sh --scenario mti_reveals_target
./demos/cfar.sh --scenario fixed_vs_cfar_clutter
./demos/fmcw.sh --scenario triangle_decouple
./demos/sar.sh --scenario two_azimuth
```

### IMU

```bash
./demos/accelerometer.sh --scenario static_tilt
./demos/gyroscope.sh --scenario bias_ramp
# tip: enable "Show 3D heading window" to compare truth vs gyro cubes
./demos/attitude.sh --scenario gimbal_lock_scan
./demos/complementary.sh --scenario balanced_sine
./demos/magnetometer.sh --scenario pitched_needs_tc
./demos/ins.sh --scenario accel_bias_straight
```

Or use the CLI:

```bash
teaching-sims list
teaching-sims demo <topic> [--scenario ID] [--list-scenarios]
```
