"""FFT (radix-2, Cooley-Tukey) for MicroPython."""
import math
from array import array


def reverse_bits(x, bits):
    """Reverse the lowest `bits` bits of x (bits = 3: 001 -> 100)."""
    r = 0
    for _ in range(bits):
        r = (r << 1) | (x & 1)
        x >>= 1
    return r


class FFT:
    """Magnitude spectrum of n real samples.

    :param n: number of samples, power of 2 (256, 512, 1024)
    """

    def __init__(self, n=512):
        self.n = n

        bits = 0                                    # log2(n) = number of stages
        while (1 << bits) < n:
            bits += 1

        # input goes in bit-reversed order, so the output comes out in order
        self.rev = array('H', [reverse_bits(i, bits) for i in range(n)])

        # twiddle factors W^k = cos - j*sin
        self.cos = array('f', [math.cos(2 * math.pi * k / n) for k in range(n // 2)])
        self.sin = array('f', [math.sin(2 * math.pi * k / n) for k in range(n // 2)])

        # Hann window, stops a tone from smearing into neighbouring bins
        self.window = array('f', [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1))
                                  for i in range(n)])

        self.re = array('f', [0] * n)               # real part
        self.im = array('f', [0] * n)               # imaginary part

    def compute(self, samples):
        """Return n/2 magnitudes. Bin k is at k * fs / n Hz."""
        n = self.n
        re, im = self.re, self.im

        # remove DC (1.65 V bias), apply window, load bit-reversed
        mean = sum(samples) / n
        for i in range(n):
            j = self.rev[i]
            re[j] = (samples[i] - mean) * self.window[i]
            im[j] = 0.0

        # butterfly stages: 2-point DFTs -> 4-point -> ... -> n-point
        size = 2
        while size <= n:
            half = size // 2
            step = n // size
            for start in range(0, n, size):
                for k in range(half):
                    a = start + k
                    b = a + half
                    c = self.cos[k * step]
                    s = self.sin[k * step]
                    tr = c * re[b] + s * im[b]      # t = W * x[b]
                    ti = c * im[b] - s * re[b]
                    re[b] = re[a] - tr              # x[b] = x[a] - t
                    im[b] = im[a] - ti
                    re[a] = re[a] + tr              # x[a] = x[a] + t
                    im[a] = im[a] + ti
            size *= 2

        # magnitudes, first half only (second half is a mirror for real input)
        return [math.sqrt(re[k] * re[k] + im[k] * im[k]) for k in range(n // 2)]