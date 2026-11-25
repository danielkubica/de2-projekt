"""FFT (Fast Fourier Transform) for MicroPython.

Turns n audio samples (time domain) into n/2 magnitudes (frequency domain):
how strong each frequency is in the recorded sound.

Algorithm: radix-2 Cooley-Tukey, iterative version.
Only uses the built-in modules math and array, no external libraries.
"""
import math
from array import array


def reverse_bits(x, bits):
    """Reverse the lowest `bits` bits of x.

    Example with bits = 3:  1 = 001 -> 100 = 4,   6 = 110 -> 011 = 3
    """
    r = 0
    for _ in range(bits):
        r = (r << 1) | (x & 1)    # take the lowest bit of x, append it to r
        x >>= 1                   # drop that bit from x
    return r


class FFT:
    """Magnitude spectrum of n real samples.

    :param n: number of samples, must be a power of 2 (256, 512, 1024 ...)
    """

    def __init__(self, n=512):
        # Everything here is computed ONCE, so compute() only does arithmetic.
        self.n = n

        # bits = log2(n), e.g. 512 -> 9. Also the number of FFT stages.
        bits = 0
        while (1 << bits) < n:
            bits += 1

        # Bit-reversal table.
        # The FFT keeps splitting the signal into even and odd samples, which
        # scrambles the order. Loading the input in bit-reversed order up front
        # makes the output come out in normal order (bin 0, 1, 2 ...).
        self.rev = array('H', [reverse_bits(i, bits) for i in range(n)])

        # Twiddle factors W^k = cos(2*pi*k/n) - j*sin(2*pi*k/n).
        # These are the "rotations" used in the butterflies. Only n/2 needed.
        self.cos = array('f', [math.cos(2 * math.pi * k / n) for k in range(n // 2)])
        self.sin = array('f', [math.sin(2 * math.pi * k / n) for k in range(n // 2)])

        # Hann window: a bell-shaped curve, 0 at both ends, 1 in the middle.
        # Multiplying the samples by it fades the burst in and out. Without it,
        # the sharp edges of the burst smear a single tone across many bins.
        self.window = array('f', [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1))
                                  for i in range(n)])

        # Working buffers: real and imaginary part of each point.
        # (MicroPython arrays can't hold complex numbers, so we keep two.)
        self.re = array('f', [0] * n)
        self.im = array('f', [0] * n)

    def compute(self, samples):
        """Return a list of n/2 magnitudes.

        Bin k corresponds to frequency k * fs / n
        (fs = 16 kHz, n = 512 -> 31.25 Hz per bin).
        """
        n = self.n
        re, im = self.re, self.im

        # --- Step 1: prepare the input ---------------------------------------
        # Remove DC: the mic sits at 1.65 V (about 32768 in ADC units).
        # That offset would show up as a huge bin 0, so subtract the average.
        mean = sum(samples) / n
        for i in range(n):
            j = self.rev[i]                                 # bit-reversed position
            re[j] = (samples[i] - mean) * self.window[i]    # remove DC, apply window
            im[j] = 0.0                                     # audio is real-valued

        # --- Step 2: butterflies ----------------------------------------------
        # Stage 1 combines pairs of samples into 2-point DFTs, stage 2 combines
        # those into 4-point DFTs, ... until one n-point DFT remains.
        # size = length of the DFTs being built in this stage (2, 4, 8 ... n)
        size = 2
        while size <= n:
            half = size // 2
            step = n // size      # how far to jump in the twiddle table per k
            for start in range(0, n, size):           # each block of this stage
                for k in range(half):                  # each butterfly in the block
                    a = start + k                      # top input
                    b = a + half                       # bottom input
                    c = self.cos[k * step]             # twiddle W = c - j*s
                    s = self.sin[k * step]

                    # t = W * x[b]   (complex multiplication written out)
                    tr = c * re[b] + s * im[b]
                    ti = c * im[b] - s * re[b]

                    # Butterfly: top = x[a] + t,  bottom = x[a] - t
                    re[b] = re[a] - tr
                    im[b] = im[a] - ti
                    re[a] = re[a] + tr
                    im[a] = im[a] + ti
            size *= 2

        # --- Step 3: magnitudes -----------------------------------------------
        # |X| = sqrt(re^2 + im^2). Only the first half is useful: for a real
        # signal the second half is a mirror image of the first.
        return [math.sqrt(re[k] * re[k] + im[k] * im[k]) for k in range(n // 2)]