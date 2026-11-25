"""Audio spectrum: mic -> FFT -> 84 bar heights in pixels (0..height) for the display.

    spectrum = Spectrum()
    while True:
        spectrum.sample()
        display.draw(spectrum.get_bars())

Bars are log-spaced, 12 per octave: each bar is 2^(1/12) times higher than
the previous one (62.5 Hz .. 8 kHz at fs = 16 kHz).
"""

import math
from microphone import Microphone
from fft import FFT


class Spectrum:
    """7 octaves (fs/256 .. fs/2, i.e. 62.5 Hz .. 8 kHz at fs = 16 kHz),
    12 log-spaced bars per octave = 84 bars. Each bar = band energy in dBFS,
    shown relative to the loudest bar of the frame."""

    def __init__(self, pin=26, fs=16000, n=512, bars_per_octave=12,
                 height=30, range_db=40, gate_db=-45):
        # n = samples per burst = FFT length (power of 2)
        # height: bar height in pixels for a full bar
        # range_db: how far below the loudest bar a bar is shown as empty
        # gate_db: if even the loudest bar is below this, show nothing
        self.mic = Microphone(pin, fs, n)
        self.fft = FFT(n)
        self.height = height
        self.range_db = range_db
        self.gate_db = gate_db
        self.n_bars = 7 * bars_per_octave

        # real sample rate (the sample period is a whole number of us)
        fs = 1_000_000 / self.mic.period_us
        bin_hz = fs / n                         # width of one FFT bin
        f_low = fs / 2 / 128                    # 7 octaves below fs/2

        # dBFS = decibels relative to full scale: 0 dBFS = a sine using the whole
        # ADC range (amplitude 32768 = 1.65 V), quieter signals are negative
        # (-20 dBFS = 1/10 of that amplitude, -40 dBFS = 1/100).
        # FFT magnitude -> amplitude as a fraction of full scale
        # (4 / n undoes the FFT gain with the Hann window, 32768 = full-scale amplitude)
        self.to_fs = 4 / n / 32768

        # FFT bins of each bar: first[i] .. last[i] - 1
        # bar i goes from f_low * 2^(i/12) to f_low * 2^((i+1)/12)
        self.first = []
        self.last = []
        for i in range(self.n_bars):
            f1 = f_low * 2 ** (i / bars_per_octave)
            f2 = f_low * 2 ** ((i + 1) / bars_per_octave)
            k1 = int(f1 / bin_hz + 0.5)
            k2 = int(f2 / bin_hz + 0.5)
            if k2 <= k1:
                k2 = k1 + 1             # bar narrower than one bin -> nearest bin
            self.first.append(k1)
            self.last.append(k2)

        self.bars = [0] * self.n_bars
        self.top_db = -200              # loudest bar of the last frame [dBFS]

    def sample(self):
        # record one burst and compute the bars (blocks for capture + FFT)
        self.mic.capture()
        mags = self.fft.compute(self.mic.buf)

        # band energy of each bar in dBFS:
        #   a = |X(k)| * to_fs        (fraction of full scale, 1.0 = full-scale sine)
        #   power = sum of a^2 over the bar's bins
        #   dBFS = 10 * log10(power)
        db = []
        for i in range(self.n_bars):
            power = 0.0
            for k in range(self.first[i], self.last[i]):
                a = mags[k] * self.to_fs
                power += a * a
            db.append(4.343 * math.log(power + 1e-20))     # 10*log10 = 4.343*ln

        # normalise to the loudest bar: top -> height, top - range_db -> 0
        top = max(db)
        self.top_db = top
        if top < self.gate_db:                          # only background noise
            for i in range(self.n_bars):
                self.bars[i] = 0
            return
        bottom = top - self.range_db
        for i in range(self.n_bars):
            value = (db[i] - bottom) / self.range_db    # 0..1
            value = max(0.0, min(1.0, value))
            self.bars[i] = int(value * self.height + 0.5)  # -> whole pixels

    def get_bars(self):
        # 84 bar heights in pixels (0..height), lowest frequency first
        return self.bars