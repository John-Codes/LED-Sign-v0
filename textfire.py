#!/usr/bin/env python3

from rpi_ws281x import *
import time
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import signal
import sys
import random

LED_PANEL_SIZE = 256
NUM_PANELS = 4
LED_COUNT = LED_PANEL_SIZE * NUM_PANELS
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 5
LED_INVERT = False
LED_CHANNEL = 0

def signal_handler(sig, frame):
    print('\nStopping animation...')
    controller.clear_display()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class FireTextDisplayController:
    def __init__(self):
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        
        self.PANEL_WIDTH = 16
        self.PANEL_HEIGHT = 16
        self.NUM_PANELS = 4
        
        # Configure for horizontal layout
        self.DISPLAY_WIDTH = self.PANEL_WIDTH * self.NUM_PANELS  # 64 pixels wide
        self.DISPLAY_HEIGHT = self.PANEL_HEIGHT                  # 16 pixels high
        
        # Fire animation settings
        self.fire_colors = [
            (255, 0, 0),      # Red
            (255, 60, 0),     # Orange-Red
            (255, 120, 0),    # Orange
            (255, 180, 0),    # Yellow-Orange
            (255, 220, 0),    # Yellow
        ]
        self.animation_speed = 0.05
        self.fire_intensity = 0.7  # Controls how active the fire effect is
        
        # Font settings
        self.font_paths = [
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        ]
        self.max_font_size = 16
        self.min_font_size = 12
        self.margin = 1

    def get_fire_color(self, y_pos, time_value):
        """Generate fire color based on position and time"""
        # Add some randomness to create flickering effect
        flicker = random.random() * self.fire_intensity
        
        # Base color selection on vertical position and time
        color_index = int((y_pos / self.DISPLAY_HEIGHT + flicker + time_value) * len(self.fire_colors)) % len(self.fire_colors)
        
        # Interpolate between two colors for smoother effect
        color1 = self.fire_colors[color_index]
        color2 = self.fire_colors[(color_index + 1) % len(self.fire_colors)]
        
        blend = random.random() * 0.3 + 0.7  # Random blend factor with bias towards color1
        
        return tuple(int(c1 * blend + c2 * (1 - blend)) for c1, c2 in zip(color1, color2))

    def get_pixel_index(self, x: int, y: int) -> int:
        if not (0 <= x < self.DISPLAY_WIDTH and 0 <= y < self.DISPLAY_HEIGHT):
            return -1
            
        # Flip Y coordinate for display orientation
        y = self.DISPLAY_HEIGHT - 1 - y
            
        panel_x = x // self.PANEL_WIDTH
        local_x = x % self.PANEL_WIDTH
        local_y = y
        
        # Alternate row direction within each panel
        if local_y % 2 == 1:
            local_x = self.PANEL_WIDTH - 1 - local_x
            
        panel_offset = panel_x * LED_PANEL_SIZE
        local_offset = (local_y * self.PANEL_WIDTH) + local_x
        
        return panel_offset + local_offset

    def clear_display(self):
        """Clear the LED display"""
        for i in range(LED_COUNT):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

    def get_font(self, size):
        """Try multiple fonts until finding one that works"""
        for font_path in self.font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        
        print("Warning: Could not load any preferred fonts, using default")
        return ImageFont.load_default()

    def calculate_text_size(self, text, font_size, char_spacing_ratio=0.15):
        """Calculate total width and height of text with given font size and spacing"""
        font = self.get_font(font_size)
        total_width = 0
        max_height = 0
        
        for char in text:
            bbox = font.getbbox(char)
            char_width = bbox[2] - bbox[0]
            char_height = bbox[3] - bbox[1]
            total_width += char_width
            max_height = max(max_height, char_height)
        
        char_spacing = int(font_size * char_spacing_ratio)
        total_width += char_spacing * (len(text) - 1)
        
        return total_width, max_height

    def find_optimal_font_size(self, text):
        """Find the largest font size that will fit the text height-wise"""
        max_height = self.DISPLAY_HEIGHT - (self.margin * 2)
        
        low = self.min_font_size
        high = self.max_font_size
        optimal_size = low
        
        while low <= high:
            mid = (low + high) // 2
            _, height = self.calculate_text_size(text, mid)
            
            if height <= max_height:
                optimal_size = mid
                low = mid + 1
            else:
                high = mid - 1
        
        return optimal_size

    def display_frame(self, image, offset=0, animation_time=0):
        """Display a single frame with fire animation"""
        for y in range(self.DISPLAY_HEIGHT):
            for x in range(self.DISPLAY_WIDTH):
                img_x = x + offset
                if 0 <= img_x < image.shape[1]:
                    is_text = np.sum(image[y, img_x]) > 0
                    if is_text:
                        r, g, b = self.get_fire_color(y, animation_time)
                    else:
                        r, g, b = (0, 0, 0)
                    
                    pixel_index = self.get_pixel_index(x, y)
                    if pixel_index >= 0:
                        self.strip.setPixelColor(pixel_index, Color(int(r), int(g), int(b)))
        self.strip.show()

    def draw_text(self, draw, text, font, y_position):
        """Draw text with proper spacing"""
        char_spacing = int(font.size * 0.15)
        
        x_position = self.DISPLAY_WIDTH
        
        for char in text:
            bbox = font.getbbox(char)
            char_width = bbox[2] - bbox[0]
            draw.text((x_position, y_position), char, fill=(255, 255, 255), font=font)
            x_position += char_width + char_spacing
        
        return x_position - self.DISPLAY_WIDTH

    def scroll_text(self, text, scroll_speed=0.05):
        """Scroll text horizontally from right to left with fire effect"""
        total_width = self.DISPLAY_WIDTH * 3
        img = Image.new('RGB', (total_width, self.DISPLAY_HEIGHT), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        font_size = self.find_optimal_font_size(text)
        font = self.get_font(font_size)
        
        _, text_height = self.calculate_text_size(text, font_size)
        y = (self.DISPLAY_HEIGHT - text_height) // 2
        
        text_width = self.draw_text(draw, text, font, y)
        
        img_array = np.array(img)
        animation_time = 0
        
        try:
            for offset in range(total_width - self.DISPLAY_WIDTH + text_width):
                self.display_frame(img_array, offset, animation_time)
                time.sleep(scroll_speed)
                animation_time += scroll_speed
                
        except KeyboardInterrupt:
            self.clear_display()

    def display_text_sequence(self, words, scroll_speed=0.05):
        """Display a sequence of text messages"""
        try:
            if isinstance(words, str):
                words = [words]
            
            while True:
                for word in words:
                    self.clear_display()
                    self.scroll_text(word.upper(), scroll_speed)
                
        except KeyboardInterrupt:
            print("\nSequence interrupted by user")
            self.clear_display()
        except Exception as e:
            print(f"Error in sequence: {e}")
            self.clear_display()

def main():
    global controller
    controller = FireTextDisplayController()
    
    words = [
        "Metal",
        "Worker",
        "Avisos",
        "LED",
        "desde",
        "$500"
    ]
    
    controller.display_text_sequence(
        words,
        scroll_speed=0.05
    )

if __name__ == "__main__":
    main()