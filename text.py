#!/usr/bin/env python3

from rpi_ws281x import *
import time
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os

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

class TextDisplayController:
    def __init__(self):
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        
        # Define panel arrangement (2x2 grid)
        self.PANEL_WIDTH = 16
        self.PANEL_HEIGHT = 16
        self.GRID_COLS = 2  # 2 panels wide
        self.GRID_ROWS = 2  # 2 panels high
        
        # Calculate total display dimensions
        self.DISPLAY_WIDTH = self.PANEL_WIDTH * self.GRID_COLS   # 32 pixels wide
        self.DISPLAY_HEIGHT = self.PANEL_HEIGHT * self.GRID_ROWS # 32 pixels high

    def get_pixel_index(self, x: int, y: int) -> int:
        """
        Convert x,y coordinates to LED strip index for 2x2 panel arrangement.
        Panel layout (when viewed from front):
        [1][0]  (bottom row)
        [3][2]  (top row)
        But we'll index them in reverse order
        """
        if not (0 <= x < self.DISPLAY_WIDTH and 0 <= y < self.DISPLAY_HEIGHT):
            return -1

        # First, determine which panel we're in
        panel_x = x // self.PANEL_WIDTH
        panel_y = y // self.PANEL_HEIGHT
        
        # Calculate panel index (0-3) in reversed order
        if panel_y == 0:
            panel_index = 2 + panel_x  # Will be 2 or 3
        else:
            panel_index = panel_x      # Will be 0 or 1
            
        # Calculate local coordinates within the panel
        local_x = x % self.PANEL_WIDTH
        local_y = y % self.PANEL_HEIGHT
        
        # If we're on an odd row within the panel, reverse the x direction
        if local_y % 2 == 1:
            local_x = self.PANEL_WIDTH - 1 - local_x
            
        # Calculate final index
        panel_offset = panel_index * LED_PANEL_SIZE
        local_offset = (local_y * self.PANEL_WIDTH) + local_x
        
        return panel_offset + local_offset

    def clear_display(self):
        for i in range(LED_COUNT):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

    def create_text_image(self, text, font_size=10):
        """Create an image with centered text."""
        # Create image with double the resolution for better anti-aliasing
        scale = 2
        img = Image.new('RGB', (self.DISPLAY_WIDTH * scale, self.DISPLAY_HEIGHT * scale), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Try to load a simpler font first
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        
        font = None
        for path in font_paths:
            try:
                font = ImageFont.truetype(path, font_size * scale)
                break
            except:
                continue
                
        if font is None:
            font = ImageFont.load_default()
        
        # Get text size
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text
        x = ((self.DISPLAY_WIDTH * scale) - text_width) // 2
        y = ((self.DISPLAY_HEIGHT * scale) - text_height) // 2
        
        # Draw text in white for better visibility
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        # Resize back to original dimensions with anti-aliasing
        img = img.resize((self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT), Image.Resampling.LANCZOS)
        
        # Flip the entire image horizontally
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        
        return np.array(img)

    def display_text(self, text):
        """Display text centered on the LED matrix."""
        # Create image with fixed font size
        text_image = self.create_text_image(text, font_size=10)
        
        # Update all pixels
        for y in range(self.DISPLAY_HEIGHT):
            for x in range(self.DISPLAY_WIDTH):
                r, g, b = text_image[y, x]
                pixel_index = self.get_pixel_index(x, y)
                if pixel_index >= 0:
                    self.strip.setPixelColor(pixel_index, Color(r, g, b))
        
        self.strip.show()

def main():
    controller = TextDisplayController()
    
    try:
        text = "Metal"  # You can change this to any short text
        print(f"Displaying text: '{text}'. Press Ctrl+C to exit.")
        controller.clear_display()
        controller.display_text(text)
        
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        controller.clear_display()
    except Exception as e:
        print(f"Error: {e}")
        controller.clear_display()

if __name__ == "__main__":
    main()