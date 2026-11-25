"""Audio spectrum: mic -> FFT -> n_bars values (0..1) for the display.

    spectrum = Spectrum(fs=16000, n=512, n_bars=42)
    while True:
        spectrum.sample()
        display.draw(spectrum.get_bars())
"""

import math
from microphone import Microphone
from fft import FFT


class Spectrum:
    """Records the mic and computes n_bars log-spaced bar heights (0..1)."""

    def __init__(self, pin=26, fs=16000, n=512, n_bars=42, db_floor=-60, db_ceil=-15):
        # n = samples per burst = FFT length
        # db_floor -> empty bar, db_ceil -> full bar (dBFS)
        self.mic = Microphone(pin, fs, n)
        self.fft = FFT(n)
        self.n_bars = n_bars
        self.db_floor = db_floor
        self.db_ceil = db_ceil

        # FFT magnitude -> amplitude as a fraction of full scale
        # (4 / n undoes the FFT gain with the Hann window, 32768 = full-scale amplitude)
        self.to_fs = 4 / n / 32768

        # FFT bins of each bar: first[i] .. last[i] - 1
        # bars are log-spaced over 7 octaves (62.5 Hz .. 8 kHz at fs = 16 kHz)
        bin_hz = fs / n
        f_low = fs / 2 / 128
        self.first = []
        self.last = []
        for i in range(n_bars):
            f1 = f_low * 128 ** (i / n_bars)            # bar start [Hz]
            f2 = f_low * 128 ** ((i + 1) / n_bars)      # bar end [Hz]
            k1 = int(f1 / bin_hz + 0.5)
            k2 = int(f2 / bin_hz + 0.5)
            if k2 <= k1:
                k2 = k1 + 1                 # bass bar narrower than one bin -> nearest bin
            self.first.append(k1)
            self.last.append(k2)

        self.bars = [0.0] * n_bars

    def sample(self):
        # record one burst and compute the bars (blocks for capture + FFT)
        self.mic.capture()
        mags = self.fft.compute(self.mic.buf)

        for i in range(self.n_bars):
            # sum of power of the bar's bins
            power = 0.0
            for k in range(self.first[i], self.last[i]):
                a = mags[k] * self.to_fs
                power += a * a

            # to dBFS: 10 * log10(power) = 4.343 * ln(power), 1e-20 avoids log(0)
            db = 4.343 * math.log(power + 1e-20)

            # db_floor -> 0, db_ceil -> 1, clipped to 0..1
            value = (db - self.db_floor) / (self.db_ceil - self.db_floor)
            self.bars[i] = max(0.0, min(1.0, value))

    def get_bars(self):
        # n_bars values 0..1, lowest frequency first
        return self.bars