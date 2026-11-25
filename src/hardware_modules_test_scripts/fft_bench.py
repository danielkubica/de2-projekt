"""FFT speed test on the Pico W.

Prints capture time, FFT time and the strongest frequency about twice
per second. Used to choose N (change it below and run again).
Play a test tone to check that the peak lands on the right frequency.

Needs microphone.py and fft.py on the board.
"""
import time
from machine import Pin
from microphone import Microphone
from fft import FFT

FS = 16000
N = 512         # 256, 512 or 1024

# Pico W: regulator to PWM mode (removes the ~8.7 kHz interference)
Pin("WL_GPIO1", Pin.OUT).value(1)

mic = Microphone(fs=FS, n=N)
fft = FFT(N)

print("N = %d, bin width = %.1f Hz" % (N, FS / N))

while True:
    t0 = time.ticks_us()
    mic.capture()
    t1 = time.ticks_us()
    mags = fft.compute(mic.buf)
    t2 = time.ticks_us()

    capture_ms = time.ticks_diff(t1, t0) / 1000
    fft_ms = time.ticks_diff(t2, t1) / 1000

    k_max = 1                                       # strongest bin, skip DC
    for k in range(2, N // 2):
        if mags[k] > mags[k_max]:
            k_max = k
    peak_hz = k_max * mic.fs_measured / N

    print("capture %.1f ms | fft %.1f ms | total %.1f ms | peak %d Hz" % (
        capture_ms, fft_ms, capture_ms + fft_ms, peak_hz))
    time.sleep_ms(500)