"""Analog microphone module (MAX4466) on a Raspberry Pi Pico W ADC pin."""
from machine import ADC, Pin
from array import array
import time
import micropython

VREF = 3.3
FULL_SCALE = 65535      # read_u16() range


class Microphone:
    """Samples the microphone in bursts of n samples at a fixed rate.

    :param pin: ADC pin (26, 27 or 28)
    :param fs: sample rate in Hz
    :param n: samples per burst
    """

    def __init__(self, pin=26, fs=16000, n=512):
        self.adc = ADC(Pin(pin))
        self.n = n
        self.period_us = 1_000_000 // fs
        self.buf = array('H', [0] * n)
        self.fs_measured = 0

    @micropython.native
    def capture(self):
        """Record one burst of n samples into self.buf and return it."""
        t0 = time.ticks_us()
        t_next = t0
        for i in range(self.n):
            while time.ticks_diff(time.ticks_us(), t_next) < 0:
                pass                                    # wait for the next sample time
            self.buf[i] = self.adc.read_u16()
            t_next = time.ticks_add(t_next, self.period_us)
        elapsed = time.ticks_diff(time.ticks_us(), t0)
        self.fs_measured = self.n * 1_000_000 // elapsed
        return self.buf

    def stats(self):
        """Return DC level, peak-to-peak and AC RMS of the last burst, in volts,
        and whether the signal clipped."""
        b = self.buf
        mean = sum(b) / self.n
        rms = (sum((v - mean) ** 2 for v in b) / self.n) ** 0.5
        k = VREF / FULL_SCALE
        return {
            "dc": mean * k,
            "pp": (max(b) - min(b)) * k,
            "rms": rms * k,
            "clipping": min(b) < 1000 or max(b) > FULL_SCALE - 1000,
        }