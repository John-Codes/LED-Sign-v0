#!/usr/bin/env python3

from rpi_ws281x import *
import time
from PIL import Image, ImageDraw
import numpy as np

# propper pannel mapping

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

class BallDisplayController:
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
        Physical panel layout:
        [2][3]  (top row)
        [0][1]  (bottom row)
        """
        if not (0 <= x < self.DISPLAY_WIDTH and 0 <= y < self.DISPLAY_HEIGHT):
            return -1
        
        # Determine which panel we're in
        panel_x = x // self.PANEL_WIDTH
        panel_y = y // self.PANEL_HEIGHT
        
        # Remap the panel indices to match physical layout
        # If we're in the top row (panel_y == 0), use panels 2 and 3
        # If we're in the bottom row (panel_y == 1), use panels 0 and 1
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

    def create_ball_image(self):
        """Create an image with a centered ball for the 32x32 display."""
        img = Image.new('RGB', (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate the center of the entire 32x32 display
        center_x = self.DISPLAY_WIDTH // 2   # 16
        center_y = self.DISPLAY_HEIGHT // 2  # 16
        
        # Draw a ball that spans across panels
        radius = 6  # Adjusted for better visibility
        bbox = [
            center_x - radius,     # Left edge
            center_y - radius,     # Top edge
            center_x + radius,     # Right edge
            center_y + radius      # Bottom edge
        ]
        
        # Draw the ball in blue
        draw.ellipse(bbox, fill=(0, 0, 255))
        
        return np.array(img)

    def display_ball(self):
        ball_image = self.create_ball_image()
        
        # Update all pixels
        for y in range(self.DISPLAY_HEIGHT):
            for x in range(self.DISPLAY_WIDTH):
                r, g, b = ball_image[y, x]
                pixel_index = self.get_pixel_index(x, y)
                if pixel_index >= 0:
                    self.strip.setPixelColor(pixel_index, Color(r, g, b))
        
        self.strip.show()

def main():
    controller = BallDisplayController()
    
    try:
        print("Displaying centered blue ball on 32x32 LED matrix. Press Ctrl+C to exit.")
        controller.clear_display()
        controller.display_ball()
        
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