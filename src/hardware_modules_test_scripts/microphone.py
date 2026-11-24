"""Analog microphone module (e.g. MAX4466) on a Raspberry Pi Pico W ADC pin.

Captures fixed-rate bursts of samples into a buffer and reports basic
signal statistics. Spectral analysis lives elsewhere (SpectrumAnalyzer).
"""
from machine import ADC, Pin
from array import array
import time
import micropython

VREF = 3.3
FULL_SCALE = 65535          # read_u16() range (12-bit ADC scaled to 16 bits)
CLIP_LOW = 1000             # raw codes near the rails count as clipping
CLIP_HIGH = FULL_SCALE - 1000


class Microphone:
    """Burst sampler for an analog mic module with a mid-supply biased output.

    :param pin: ADC-capable GPIO (26, 27 or 28)
    :param fs: requested sample rate in Hz
    :param n: samples per burst
    """

    def __init__(self, pin=26, fs=8000, n=256):
        self._adc = ADC(Pin(pin))
        self.fs = fs
        self.n = n
        self._period_us = max(1, 1_000_000 // fs)
        self.fs_nominal = 1_000_000 // self._period_us  # fs after rounding to whole us
        self.buf = array('H', [0] * n)
        self.fs_measured = 0
        self.late = 0   # samples taken > half a period late in the last burst

    @micropython.native
    def capture(self):
        """Fill the buffer with one burst of n samples. Blocks for ~n/fs s
        (256 samples at 8 kHz = 32 ms). Returns the buffer."""
        buf = self.buf
        read = self._adc.read_u16
        period = self._period_us
        ticks_us = time.ticks_us
        ticks_diff = time.ticks_diff
        ticks_add = time.ticks_add

        late_thr = period // 2
        late = 0
        t0 = ticks_us()
        t_next = t0
        t_last = t0
        for i in range(self.n):
            now = ticks_us()
            while ticks_diff(now, t_next) < 0:
                now = ticks_us()
            if ticks_diff(now, t_next) > late_thr:
                late += 1
            t_last = now
            buf[i] = read()
            t_next = ticks_add(t_next, period)

        self.late = late
        span = ticks_diff(t_last, t0)
        if span > 0:
            self.fs_measured = (self.n - 1) * 1_000_000 // span
        return buf

    def stats(self, buf=None):
        """Return a dict with DC bias, peak-to-peak, AC RMS (volts) and
        a clipping flag for the given buffer (default: last capture)."""
        b = self.buf if buf is None else buf
        n = len(b)
        s = 0
        mn = FULL_SCALE
        mx = 0
        for v in b:
            s += v
            if v < mn:
                mn = v
            if v > mx:
                mx = v
        mean = s / n
        acc = 0.0
        for v in b:
            d = v - mean
            acc += d * d
        rms = (acc / n) ** 0.5

        k = VREF / FULL_SCALE
        return {
            "dc_v": mean * k,
            "pp_v": (mx - mn) * k,
            "rms_v": rms * k,
            "min_raw": mn,
            "max_raw": mx,
            "clipping": mn < CLIP_LOW or mx > CLIP_HIGH,
            "fs": self.fs_measured,
        }
