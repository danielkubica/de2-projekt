"""Analog microphone module (MAX4466) on a Raspberry Pi Pico W ADC pin."""

from machine import ADC, Pin
from array import array
import time
import micropython

VREF = 3.3
FULL_SCALE = 65535      # read_u16() range


class Microphone:
    """Samples the microphone in bursts of n samples at a fixed rate."""

    def __init__(self, pin=26, fs=16000, n=512):
        """
        Initialize the ADC and the sample buffer.

        :param pin: ADC pin (26, 27 or 28).
        :param fs: Sample rate in Hz.
        :param n: Samples per burst.
        """
        self.adc = ADC(Pin(pin))
        self.n = n
        self.period_us = 1_000_000 // fs
        self.buf = array('H', [0] * n)
        self.fs_measured = 0

    @micropython.native
    def capture(self):
        """
        Record one burst of n samples into `self.buf`.
        Blocks for n / fs seconds (512 samples at 16 kHz = 32 ms).

        :return: The sample buffer.
        """
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
        """
        Statistics of the last burst.

        :return: Dictionary with DC level, peak-to-peak and AC RMS
                 (all in volts) and a clipping flag.
        """
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

    def signal_ok(self):
        """
        Check that the mic is connected: its output sits at Vcc/2 (~1.65 V).
        A disconnected input floats somewhere else.

        :return: `True` if the DC level of the last burst is 1.2..2.1 V.
        """
        dc = sum(self.buf) / self.n * VREF / FULL_SCALE
        return 1.2 < dc < 2.1