"""Standalone microphone module test (MAX4466 -> Pico W ADC0).

Modes:
  "sweep" - tries rising sample rates; used to find the working fs.
  "stats" - prints DC bias, p-p, RMS, measured fs per burst; used to check
            the bias, noise level, loudness range and clipping.
  "dump"  - prints raw samples; analyzed on the PC with fft_dump.py to get
            the spectrum (test tones, interference).

Wiring:
    VCC -> 3V3(OUT)   (pin 36)
    GND -> AGND       (pin 33)  (or any GND)
    OUT -> GP26/ADC0  (pin 31)
"""
import time
from microphone import Microphone

MODE = "stats"      # "stats", "dump" or "sweep"
FS = 8000
N = 256
SMPS_PWM = True     # Pico W: force the 3V3 regulator into PWM mode (less ripple).
                    # Set False to compare noise with the default power-save mode.

if SMPS_PWM:
    from machine import Pin
    Pin("WL_GPIO1", Pin.OUT).value(1)

# Sweep settings
SWEEP_FS = (8000, 12000, 16000, 20000, 24000, 32000, 40000, 50000)
SWEEP_N = 512        # realistic burst length for fs = 16 kHz
SWEEP_RUNS = 10      # bursts per rate; worst case is reported


def sweep():
    import gc
    print("Sample-rate sweep, N = %d, %d bursts per rate" % (SWEEP_N, SWEEP_RUNS))
    print("requested  nominal  measured(min)  late(max)  result")
    best = 0
    for fs in SWEEP_FS:
        m = Microphone(pin=26, fs=fs, n=SWEEP_N)
        worst_fs = 10 ** 9
        worst_late = 0
        for _ in range(SWEEP_RUNS):
            gc.collect()
            m.capture()
            worst_fs = min(worst_fs, m.fs_measured)
            worst_late = max(worst_late, m.late)
        ok = worst_late == 0 and worst_fs >= m.fs_nominal * 0.99
        if ok:
            best = m.fs_nominal
        print("%9d  %7d  %13d  %9d  %s" % (
            fs, m.fs_nominal, worst_fs, worst_late, "OK" if ok else "FAIL"))
        del m

    # Free-running: no waiting between samples, as fast as the loop goes.
    m = Microphone(pin=26, fs=1_000_000, n=SWEEP_N)
    m.capture()
    print("Free-running loop maximum: %d Hz" % m.fs_measured)
    print("Highest sustained rate: %d Hz -> spectrum up to %d Hz" % (best, best // 2))


if MODE == "sweep":
    sweep()
    raise SystemExit

mic = Microphone(pin=26, fs=FS, n=N)

print("Mic test, requested fs = %d Hz, N = %d, mode = %s" % (FS, N, MODE))

while True:
    buf = mic.capture()

    if MODE == "dump":
        for v in buf:
            print(v)
        print("# fs_measured = %d Hz" % mic.fs_measured)
        time.sleep(2)
    else:
        st = mic.stats()
        print("DC %.3f V | p-p %.3f V | RMS %.4f V | fs %d Hz | late %d%s" % (
            st["dc_v"], st["pp_v"], st["rms_v"], st["fs"], mic.late,
            " | CLIPPING" if st["clipping"] else ""))
        time.sleep_ms(200)
