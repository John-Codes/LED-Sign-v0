#!/usr/bin/env python3

from rpi_ws281x import *
import time

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

class PanelOrientationTest:
    def __init__(self):
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        
    def clear_display(self):
        for i in range(LED_COUNT):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

    def set_pixel_in_panel(self, panel, x, y, color):
        """Set a pixel within a specific panel (each panel is 16x16)"""
        if not (0 <= x < 16 and 0 <= y < 16):
            return
            
        # Calculate base index for the panel
        base_index = panel * 256
        
        # If on an odd row, reverse x direction due to serpentine pattern
        if y % 2 == 1:
            x = 15 - x
            
        index = base_index + (y * 16) + x
        self.strip.setPixelColor(index, color)

    def draw_orientation_pattern(self):
        # Colors
        RED = Color(255, 0, 0)
        GREEN = Color(0, 255, 0)
        BLUE = Color(0, 0, 255)
        YELLOW = Color(255, 255, 0)
        
        # For each panel
        for panel in range(4):
            # Draw an arrow pointing UP
            # Vertical line
            for y in range(8, 16):
                self.set_pixel_in_panel(panel, 8, y, RED)
            
            # Arrow head
            self.set_pixel_in_panel(panel, 8, 8, RED)
            self.set_pixel_in_panel(panel, 7, 9, RED)
            self.set_pixel_in_panel(panel, 9, 9, RED)
            
            # Draw panel number in top-left corner
            # Simple digit representation
            if panel == 0:
                self.set_pixel_in_panel(panel, 2, 2, GREEN)
            elif panel == 1:
                self.set_pixel_in_panel(panel, 1, 2, BLUE)
                self.set_pixel_in_panel(panel, 2, 2, BLUE)
            elif panel == 2:
                self.set_pixel_in_panel(panel, 1, 2, YELLOW)
                self.set_pixel_in_panel(panel, 2, 2, YELLOW)
                self.set_pixel_in_panel(panel, 3, 2, YELLOW)
            else:  # panel 3
                self.set_pixel_in_panel(panel, 1, 2, GREEN)
                self.set_pixel_in_panel(panel, 2, 2, GREEN)
                self.set_pixel_in_panel(panel, 3, 2, GREEN)
                self.set_pixel_in_panel(panel, 4, 2, GREEN)

        self.strip.show()

def main():
    tester = PanelOrientationTest()
    
    try:
        print("Displaying orientation test pattern. Press Ctrl+C to exit.")
        print("Look for:")
        print("- Panel 0: Single GREEN dot in corner + RED arrow")
        print("- Panel 1: Two BLUE dots in corner + RED arrow")
        print("- Panel 2: Three YELLOW dots in corner + RED arrow")
        print("- Panel 3: Four GREEN dots in corner + RED arrow")
        print("The RED arrow should point UP on each panel")
        
        tester.clear_display()
        tester.draw_orientation_pattern()
        
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        tester.clear_display()
    except Exception as e:
        print(f"Error: {e}")
        tester.clear_display()

if __name__ == "__main__":
    main()