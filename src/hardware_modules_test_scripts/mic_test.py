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
from machine import Pin
from microphone import Microphone

MODE = "stats"      # "stats", "dump" or "sweep"
FS = 16000
N = 512

# Pico W: put the 3V3 regulator into PWM mode. Without this, its ripple
# shows up as a ~200 mV interfering tone in the mic signal.
Pin("WL_GPIO1", Pin.OUT).value(1)

if MODE == "sweep":
    print("fs requested -> measured")
    for fs in (8000, 12000, 16000, 20000, 24000, 32000, 40000):
        mic = Microphone(fs=fs, n=N)
        mic.capture()
        ok = mic.fs_measured >= fs * 0.98
        print("%6d -> %6d Hz  %s" % (fs, mic.fs_measured, "OK" if ok else "too fast"))

else:
    mic = Microphone(fs=FS, n=N)
    while True:
        mic.capture()
        if MODE == "dump":
            for v in mic.buf:
                print(v)
            print("# fs_measured = %d Hz" % mic.fs_measured)
            time.sleep(2)
        else:
            st = mic.stats()
            print("DC %.3f V | p-p %.3f V | RMS %.4f V | fs %d Hz%s" % (
                st["dc"], st["pp"], st["rms"], mic.fs_measured,
                " | CLIPPING" if st["clipping"] else ""))
            time.sleep_ms(200)