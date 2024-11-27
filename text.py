#!/usr/bin/env python3

from rpi_ws281x import *
import time
import signal
import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from math import sin, cos, pi

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

class TextDisplayController:
    def __init__(self):
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        self.TOTAL_WIDTH = 16 * NUM_PANELS
        self.PANEL_HEIGHT = 16
        self.running = True
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        print('\nShutting down gracefully...')
        self.running = False
        self.clear_strip()
        sys.exit(0)

    def get_pixel_index(self, x: int, y: int) -> int:
        if not (0 <= x < self.TOTAL_WIDTH and 0 <= y < self.PANEL_HEIGHT):
            return -1
        panel = x // 16
        local_x = x % 16
        if y % 2 == 1:  # Serpentine pattern
            local_x = 15 - local_x
        pixel_index = (panel * LED_PANEL_SIZE) + (y * 16) + local_x
        return pixel_index if 0 <= pixel_index < LED_COUNT else -1

    def clear_strip(self):
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

    def create_centered_text_image(self, text, color=(255, 255, 255)):
        # Create an image the size of our LED matrix
        img = Image.new('RGB', (self.TOTAL_WIDTH, self.PANEL_HEIGHT), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Try different font sizes to find the best fit
        font_size = self.PANEL_HEIGHT
        font = None
        text_width = self.TOTAL_WIDTH + 1  # Initialize larger than panel width
        
        while text_width > self.TOTAL_WIDTH and font_size > 8:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except:
                font = ImageFont.load_default()
                break
            
            # Get text size
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            if text_width > self.TOTAL_WIDTH:
                font_size -= 1
        
        if font:
            # Center the text
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            x = (self.TOTAL_WIDTH - text_width) // 2
            y = (self.PANEL_HEIGHT - text_height) // 2
            
            # Draw the text
            draw.text((x, y), text, font=font, fill=color)
        
        return img

    def pulse_animation(self, text, base_color=(255, 0, 0), duration=10):
        """Pulsing brightness animation."""
        img = self.create_centered_text_image(text, base_color)
        image_data = np.array(img)
        
        start_time = time.time()
        while self.running and (time.time() - start_time) < duration:
            # Calculate pulse intensity (0 to 1)
            t = time.time() - start_time
            intensity = (sin(t * 3) + 1) / 2 * 0.8 + 0.2  # Range 0.2 to 1.0
            
            # Apply intensity to image
            for x in range(self.TOTAL_WIDTH):
                for y in range(self.PANEL_HEIGHT):
                    r, g, b = [int(c * intensity) for c in image_data[y, x]]
                    pixel_index = self.get_pixel_index(x, y)
                    if pixel_index >= 0:
                        self.strip.setPixelColor(pixel_index, Color(r, g, b))
            
            self.strip.show()
            time.sleep(0.02)

    def rainbow_animation(self, text, duration=10):
        """Rainbow color cycling animation."""
        img = self.create_centered_text_image(text)
        image_data = np.array(img)
        
        start_time = time.time()
        while self.running and (time.time() - start_time) < duration:
            t = time.time() - start_time
            hue = (t * 0.2) % 1.0
            
            # Create rainbow color
            r, g, b = [int(c * 255) for c in self.hsv_to_rgb(hue, 1.0, 1.0)]
            
            for x in range(self.TOTAL_WIDTH):
                for y in range(self.PANEL_HEIGHT):
                    if any(image_data[y, x]):  # If pixel is not black
                        pixel_index = self.get_pixel_index(x, y)
                        if pixel_index >= 0:
                            self.strip.setPixelColor(pixel_index, Color(r, g, b))
            
            self.strip.show()
            time.sleep(0.02)

    def sparkle_animation(self, text, color=(255, 255, 255), duration=10):
        """Sparkling text animation."""
        img = self.create_centered_text_image(text, color)
        image_data = np.array(img)
        
        start_time = time.time()
        while self.running and (time.time() - start_time) < duration:
            # Create random sparkles
            sparkle_mask = np.random.random((self.PANEL_HEIGHT, self.TOTAL_WIDTH)) > 0.8
            
            for x in range(self.TOTAL_WIDTH):
                for y in range(self.PANEL_HEIGHT):
                    r, g, b = image_data[y, x]
                    if any((r, g, b)):  # If pixel is not black
                        intensity = 1.5 if sparkle_mask[y, x] else 1.0
                        r = min(255, int(r * intensity))
                        g = min(255, int(g * intensity))
                        b = min(255, int(b * intensity))
                        pixel_index = self.get_pixel_index(x, y)
                        if pixel_index >= 0:
                            self.strip.setPixelColor(pixel_index, Color(r, g, b))
            
            self.strip.show()
            time.sleep(0.05)

    def hsv_to_rgb(self, h, s, v):
        """Convert HSV color values to RGB."""
        if s == 0.0:
            return (v, v, v)
        
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i = i % 6
        
        if i == 0: return (v, t, p)
        if i == 1: return (q, v, p)
        if i == 2: return (p, v, t)
        if i == 3: return (p, q, v)
        if i == 4: return (t, p, v)
        if i == 5: return (v, p, q)

def main():
    controller = TextDisplayController()
    
    try:
        while True:
            print("\nCentered Text Display Menu:")
            print("1. Pulse Animation")
            print("2. Rainbow Animation")
            print("3. Sparkle Animation")
            print("4. Clear and Exit")
            
            choice = input("\nSelect an option (1-4): ").strip()
            
            if choice in ['1', '2', '3']:
                text = input("Enter text to display: ")
                if choice == '1':
                    color_choice = input("Choose color (R/G/B/W) [R]: ").upper() or 'R'
                    colors = {
                        'R': (255, 0, 0),
                        'G': (0, 255, 0),
                        'B': (0, 0, 255),
                        'W': (255, 255, 255)
                    }
                    color = colors.get(color_choice, (255, 0, 0))
                    controller.pulse_animation(text, color)
                elif choice == '2':
                    controller.rainbow_animation(text)
                elif choice == '3':
                    controller.sparkle_animation(text)
            elif choice == '4':
                controller.clear_strip()
                print("\nExiting...")
                break
            else:
                print("\nInvalid choice. Please select 1-4.")
    
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        controller.clear_strip()
        print("Goodbye!")

if __name__ == "__main__":
    main()