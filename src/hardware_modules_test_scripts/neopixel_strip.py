import time
import machine
import neopixel

# Configure the NeoPixel strip on GP16 with 8 LEDs (adjust 'NUM_LEDS' to match your strip length)
NUM_LEDS = 40
PIN_NUM = 16

pin = machine.Pin(PIN_NUM, machine.Pin.OUT)
np = neopixel.NeoPixel(pin, NUM_LEDS)

def color_wipe(color, wait_ms):
    """Wipes a color across the strip one LED at a time."""
    for i in range(NUM_LEDS):
        np[i] = color
        np.write()
        time.sleep_ms(wait_ms)

def rainbow_cycle(wait_ms):
    """Runs a smooth rainbow cycle across all LEDs."""
    for j in range(255):
        for i in range(NUM_LEDS):
            rc = (i * 256 // NUM_LEDS) + j
            # Simple color wheel mapping
            pos = rc & 255
            if pos < 85:
                np[i] = (pos * 3, 255 - pos * 3, 0)
            elif pos < 170:
                pos -= 85
                np[i] = (255 - pos * 3, 0, pos * 3)
            else:
                pos -= 170
                np[i] = (0, pos * 3, 255 - pos * 3)
        np.write()
        time.sleep_ms(wait_ms)

# Main loop running test patterns
print("Starting NeoPixel Test on Pico 2W...")

while True:
    # 1. Primary Color Chases (Brightness set to moderate level: 50, 0, 0 to avoid blinding light)
    color_wipe((50, 0, 0), 100)  # Red
    color_wipe((0, 50, 0), 100)  # Green
    color_wipe((0, 0, 50), 100)  # Blue
    color_wipe((0, 0, 0), 50)    # Off

    # 2. Run a short rainbow animation loop
    for _ in range(50):
        rainbow_cycle(10)
