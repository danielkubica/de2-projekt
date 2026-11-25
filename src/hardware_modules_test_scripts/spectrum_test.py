"""Spectrum test: prints the 84 bars in the shell, one line per frame.

One digit per bar (0 = empty .. 9 = full height), octave edges marked with |,
then the loudest bar in dBFS and the time of sample().
Use the dBFS value to set the gate: in silence it should stay below gate_db.

Needs microphone.py, fft.py and spectrum.py on the board.
"""
import time
from machine import Pin
from spectrum import Spectrum

FS = 16000
N = 512

# Pico W: regulator to PWM mode (removes the ~8.7 kHz interference)
Pin("WL_GPIO1", Pin.OUT).value(1)

spectrum = Spectrum(fs=FS, n=N)

labels = ["62.5", "125", "250", "500", "1k", "2k", "4k", "8k"]
print("".join(l + " " * (13 - len(l)) for l in labels))     # one label per octave edge

while True:
    t0 = time.ticks_ms()
    spectrum.sample()
    t1 = time.ticks_ms()

    bars = spectrum.get_bars()
    line = ""
    for i in range(len(bars)):
        if i % 12 == 0:
            line += "|"                         # octave edge
        line += str(bars[i] * 9 // spectrum.height)     # 0..height -> digit 0..9
    print("%s| top %d dBFS | %d ms" % (line, spectrum.top_db, time.ticks_diff(t1, t0)))