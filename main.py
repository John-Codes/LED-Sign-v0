#!/usr/bin/env python3

from rpi_ws281x import *
import time
import signal
import sys
from math import sin, cos, pi, sqrt, exp
from typing import Tuple, List, Optional
import colorsys

# LED configuration
LED_PANEL_SIZE = 256    # 16x16 matrix = 256 LEDs per panel
NUM_PANELS     = 4      # Number of LED panels
LED_COUNT      = LED_PANEL_SIZE * NUM_PANELS
LED_PIN        = 18
LED_FREQ_HZ    = 800000
LED_DMA        = 10
LED_BRIGHTNESS = 100
LED_INVERT     = False
LED_CHANNEL    = 0

class NeoPixelController:
    def __init__(self):
        """Initialize the NeoPixel controller with configuration and setup signal handlers."""
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        self.TOTAL_WIDTH = 16 * NUM_PANELS  # Total width of all panels combined
        self.PANEL_WIDTH = 16
        self.PANEL_HEIGHT = 16
        self.running = True
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully."""
        print('\nShutting down gracefully...')
        self.running = False
        self.clear_strip()
        sys.exit(0)

    def get_pixel_index(self, x: int, y: int) -> int:
        """
        Convert global x,y coordinates to LED index with enhanced boundary checking.
        
        Args:
            x: Global X coordinate across all panels
            y: Y coordinate within a panel
            
        Returns:
            LED index or -1 if coordinates are out of bounds
        """
        if not (0 <= x < self.TOTAL_WIDTH and 0 <= y < self.PANEL_HEIGHT):
            return -1
        panel = x // 16
        local_x = x % 16
        # Handle serpentine pattern if your panels use it
        if y % 2 == 1:
            local_x = 15 - local_x
        pixel_index = (panel * LED_PANEL_SIZE) + (y * 16) + local_x
        return pixel_index if 0 <= pixel_index < LED_COUNT else -1

    def clear_strip(self):
        """Clear all pixels on the strip."""
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

    def set_pixel(self, x: int, y: int, color: int):
        """Safely set a pixel color with boundary checking."""
        pixel_index = self.get_pixel_index(x, y)
        if pixel_index >= 0:
            self.strip.setPixelColor(pixel_index, color)

    def hsv_to_color(self, h: float, s: float, v: float) -> int:
        """Convert HSV values to Color value."""
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return Color(int(r * 255), int(g * 255), int(b * 255))

    def interference_waves(self, cycles: int = 3):
        """Create an interference pattern from multiple wave sources with enhanced color transitions."""
        sources = [
            (0, 8),           # Left edge, middle
            (self.TOTAL_WIDTH-1, 8),  # Right edge, middle
            (self.TOTAL_WIDTH//2, 0), # Center top
            (self.TOTAL_WIDTH//2, 15) # Center bottom
        ]
        
        start_time = time.time()
        while self.running and (time.time() - start_time) < (cycles * 10):
            t = (time.time() - start_time) * 2
            for x in range(self.TOTAL_WIDTH):
                for y in range(16):
                    intensity = sum(
                        sin(sqrt((x - src_x)**2 + (y - src_y)**2) * 0.5 - t) 
                        * exp(-sqrt((x - src_x)**2 + (y - src_y)**2) * 0.1)
                        for src_x, src_y in sources
                    )
                    
                    # Normalize and create dynamic color using HSV
                    intensity = (intensity + len(sources)) / (2 * len(sources))
                    hue = (t / 10.0) % 1.0
                    color = self.hsv_to_color(hue, 1.0, intensity)
                    self.set_pixel(x, y, color)
            
            self.strip.show()
            time.sleep(0.03)

    def expanding_circles(self, cycles: int = 3):
        """Create expanding circles with dynamic color patterns."""
        center_points = [(8 + (16 * i), 8) for i in range(NUM_PANELS)]
        
        start_time = time.time()
        while self.running and (time.time() - start_time) < (cycles * 10):
            t = (time.time() - start_time) * 2
            radius = (t % 15) * 2
            
            for x in range(self.TOTAL_WIDTH):
                for y in range(16):
                    max_intensity = max(
                        exp(-(sqrt((x - cx)**2 + (y - cy)**2) - radius)**2 / 4.0)
                        for cx, cy in center_points
                    )
                    
                    hue = (t / 10.0 + x / self.TOTAL_WIDTH) % 1.0
                    color = self.hsv_to_color(hue, 1.0, max_intensity)
                    self.set_pixel(x, y, color)
            
            self.strip.show()
            time.sleep(0.03)

    def snake_effect(self, length: int = 20, cycles: int = 2):
        """Create a snake that moves across all panels with dynamic coloring."""
        trail = []
        y = 8
        
        def get_trail_color(pos: int, t: float) -> int:
            distance = length - pos
            intensity = 1.0 - (distance / length)
            if intensity <= 0:
                return Color(0, 0, 0)
            hue = (t + pos / length) % 1.0
            return self.hsv_to_color(hue, 1.0, intensity)
        
        start_time = time.time()
        while self.running and (time.time() - start_time) < (cycles * 15):
            t = (time.time() - start_time) / 5.0
            x = int((t * 20) % (self.TOTAL_WIDTH + length * 2)) - length
            
            if 0 <= x < self.TOTAL_WIDTH:
                trail.insert(0, (x, y))
            while len(trail) > length:
                trail.pop()
            
            self.clear_strip()
            
            for i, (trail_x, trail_y) in enumerate(trail):
                if 0 <= trail_x < self.TOTAL_WIDTH:
                    color = get_trail_color(i, t)
                    for dy in [-1, 0, 1]:
                        new_y = trail_y + dy
                        if 0 <= new_y < 16:
                            intensity = 1.0 if dy == 0 else 0.5
                            r = (color >> 16) & 0xFF
                            g = (color >> 8) & 0xFF
                            b = color & 0xFF
                            glow_color = Color(
                                int(r * intensity),
                                int(g * intensity),
                                int(b * intensity)
                            )
                            self.set_pixel(trail_x, new_y, glow_color)
            
            self.strip.show()
            time.sleep(0.03)

    def color_bars_test(self, cycles: int = 3):
        """Create smooth color bar transitions across all panels."""
        start_time = time.time()
        while self.running and (time.time() - start_time) < (cycles * 10):
            t = (time.time() - start_time) * 2
            offset = int(t * 10) % self.TOTAL_WIDTH
            
            for x in range(self.TOTAL_WIDTH):
                hue = ((x + offset) % self.TOTAL_WIDTH) / self.TOTAL_WIDTH
                color = self.hsv_to_color(hue, 1.0, 1.0)
                
                for y in range(16):
                    self.set_pixel(x, y, color)
            
            self.strip.show()
            time.sleep(0.03)

    def bouncing_ball(self, cycles: int = 3):
        """Create a physically accurate bouncing ball animation."""
        x = float(self.TOTAL_WIDTH // 2)
        y = float(8)
        dx = 4.0
        dy = 1.5
        gravity = 0.15
        bounce_damping = 0.9
        edge_damping = 0.98
        trail = []
        
        start_time = time.time()
        while self.running and (time.time() - start_time) < (cycles * 10):
            # Physics update
            x += dx
            y += dy
            dy += gravity
            
            # Boundary collisions
            if y > self.PANEL_HEIGHT - 1:
                y = self.PANEL_HEIGHT - 1
                dy = -dy * bounce_damping
                dx *= edge_damping
            
            if y < 0:
                y = 0
                dy = -dy * bounce_damping
                dx *= edge_damping
            
            if x >= self.TOTAL_WIDTH - 1:
                x = self.TOTAL_WIDTH - 1
                dx = -dx * bounce_damping
            
            if x < 0:
                x = 0
                dx = -dx * bounce_damping
            
            # Update trail
            trail.insert(0, (x, y))
            trail = trail[:8]
            
            # Render
            self.clear_strip()
            t = time.time() - start_time
            
            for i, (trail_x, trail_y) in enumerate(trail):
                intensity = 1.0 - (i / len(trail))
                hue = (t / 3.0 + i / len(trail)) % 1.0
                color = self.hsv_to_color(hue, 1.0, intensity)
                
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        px = int(trail_x + dx)
                        py = int(trail_y + dy)
                        if 0 <= px < self.TOTAL_WIDTH and 0 <= py < self.PANEL_HEIGHT:
                            glow_intensity = intensity / (1 + sqrt(dx*dx + dy*dy))
                            glow_color = self.hsv_to_color(hue, 1.0, glow_intensity)
                            self.set_pixel(px, py, glow_color)
            
            self.strip.show()
            time.sleep(0.02)

def main():
    controller = NeoPixelController()
    
    try:
        while True:
            print("\nLED Panel Animation Menu:")
            print("1. Interference Waves")
            print("2. Expanding Circles")
            print("3. Snake Effect")
            print("4. Color Bars Test")
            print("5. Bouncing Ball")
            print("6. Run All Animations")
            print("7. Clear and Exit")
            
            choice = input("\nSelect an animation (1-7): ").strip()
            
            if choice == '1':
                controller.interference_waves()
            elif choice == '2':
                controller.expanding_circles()
            elif choice == '3':
                controller.snake_effect()
            elif choice == '4':
                controller.color_bars_test()
            elif choice == '5':
                controller.bouncing_ball()
            elif choice == '6':
                print("\nRunning all animations in sequence...")
                controller.interference_waves(2)
                controller.expanding_circles(2)
                controller.snake_effect(2)
                controller.color_bars_test(2)
                controller.bouncing_ball(2)
            elif choice == '7':
                controller.clear_strip()
                print("\nExiting...")
                break
            else:
                print("\nInvalid choice. Please select 1-7.")
    
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        controller.clear_strip()
        print("Goodbye!")

if __name__ == "__main__":
    main()