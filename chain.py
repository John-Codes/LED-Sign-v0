#!/usr/bin/env python3
#sudo $(which python3) chain.py
from rpi_ws281x import *
import time
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# LED configuration
LED_PANEL_SIZE = 256    # 16x16 matrix = 256 LEDs per panel
NUM_PANELS     = 4      # Number of LED panels
LED_COUNT      = LED_PANEL_SIZE * NUM_PANELS
LED_PIN        = 18
LED_FREQ_HZ    = 800000
LED_DMA        = 10
LED_BRIGHTNESS = 80
LED_INVERT     = False
LED_CHANNEL    = 0

def get_pixel_index(x, y, panel):
    """Convert x,y coordinates to LED strip index for a specific panel."""
    if not (0 <= x < 16 and 0 <= y < 16):
        return -1
        
    # Handle serpentine pattern
    if y % 2 == 1:
        x = 15 - x
        
    # Calculate index
    index = (panel * LED_PANEL_SIZE) + (y * 16) + x
    return index if 0 <= index < LED_COUNT else -1

def create_number_image(number):
    """Create a 16x16 image with a centered number."""
    img = Image.new('RGB', (16, 16), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a larger font size
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Draw the number
    text = str(number)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (16 - text_width) // 2
    y = (16 - text_height) // 2
    
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    return np.array(img)

def display_panel_numbers():
    # Initialize the LED strip
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    
    try:
        # Clear all panels first
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        
        # Create and display numbers for each panel
        for panel in range(NUM_PANELS):
            number = panel + 1  # Convert to 1-based numbering
            number_image = create_number_image(number)
            
            # Display the number on the panel
            for y in range(16):
                for x in range(16):
                    r, g, b = number_image[y, x]
                    pixel_index = get_pixel_index(x, y, panel)
                    if pixel_index >= 0:
                        strip.setPixelColor(pixel_index, Color(r, g, b))
        
        strip.show()
        print("Displaying panel numbers. Press Ctrl+C to exit.")
        print("Panel 1 = First in chain (DIN)")
        print("Panel 2 = Second in chain")
        print("Panel 3 = Third in chain")
        print("Panel 4 = Fourth in chain")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        # Clear display on exit
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        print("\nExiting...")

if __name__ == "__main__":
    print("\nTesting LED panel chain order...")
    print("Numbers will show the order in the chain (1 = DIN connection)")
    display_panel_numbers()