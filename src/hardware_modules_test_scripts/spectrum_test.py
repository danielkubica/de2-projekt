"""Spectrum test: prints the 42 bar values in the shell.

Each line is one frame: one digit per bar (0 = empty .. 9 = full),
lowest frequency on the left, octave edges marked with |.
Play a tone - the high digits should move with its frequency.

Needs microphone.py, fft.py and spectrum.py on the board.
"""
import time
from machine import Pin
from spectrum import Spectrum

FS = 16000
N = 512
N_BARS = 42         # 7 octaves x 6 bars

# Pico W: regulator to PWM mode (removes the ~8.7 kHz interference)
Pin("WL_GPIO1", Pin.OUT).value(1)

spectrum = Spectrum(fs=FS, n=N, n_bars=N_BARS)
per_octave = N_BARS // 7

print("62.5   125    250    500    1k     2k     4k     8k Hz")

while True:
    t0 = time.ticks_ms()
    spectrum.sample()
    t1 = time.ticks_ms()

    bars = spectrum.get_bars()
    line = ""
    for i in range(N_BARS):
        if i % per_octave == 0:
            line += "|"                         # octave edge
        line += str(int(bars[i] * 9))           # 0..1 -> digit 0..9
    print(line + "|  " + str(time.ticks_diff(t1, t0)) + " ms")