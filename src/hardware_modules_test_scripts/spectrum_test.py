"""Spectrum test: prints the bars in the shell.

Fast mode (DETAIL = False): one line per frame, one digit per bar
(0 = empty .. 9 = full), octave edges marked with |.
Detail mode (DETAIL = True): once per second, every bar with its
start frequency [Hz] and level [dBFS], one octave per row.

Needs microphone.py, fft.py and spectrum.py on the board.
"""
import time
from machine import Pin
from spectrum import Spectrum

FS = 16000
N = 512
N_BARS = 42         # 7 octaves x 6 bars
DETAIL = True       # True = frequencies and dBFS, False = digit line

# Pico W: regulator to PWM mode (removes the ~8.7 kHz interference)
Pin("WL_GPIO1", Pin.OUT).value(1)

spectrum = Spectrum(fs=FS, n=N, n_bars=N_BARS)
freqs = spectrum.get_freqs()
per_octave = N_BARS // 7

if not DETAIL:
    print("62.5   125    250    500    1k     2k     4k     8k Hz")

while True:
    t0 = time.ticks_ms()
    spectrum.sample()
    t1 = time.ticks_ms()

    if DETAIL:
        db = spectrum.get_db()
        print("--- frame, %d ms ---" % time.ticks_diff(t1, t0))
        for row in range(0, N_BARS, per_octave):          # one octave per row
            line = ""
            for i in range(row, row + per_octave):
                line += "%5d Hz %4d dB | " % (round(freqs[i]), round(db[i]))
            print(line)
        time.sleep(1)
    else:
        bars = spectrum.get_bars()
        line = ""
        for i in range(N_BARS):
            if i % per_octave == 0:
                line += "|"                                # octave edge
            line += str(int(bars[i] * 9))                  # 0..1 -> digit 0..9
        print(line + "|  " + str(time.ticks_diff(t1, t0)) + " ms")