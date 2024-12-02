#!/usr/bin/env python3

from rpi_ws281x import *
import time
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import signal
import sys
import colorsys
import os
import math
import random
import urllib.request
import tempfile

# LED Configuration
LED_PANEL_SIZE = 256
NUM_PANELS = 4
LED_COUNT = LED_PANEL_SIZE * NUM_PANELS
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 5
LED_INVERT = False
LED_CHANNEL = 0

# Font URL - modern, clean font good for LED displays
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/pressstart2p/PressStart2P-Regular.ttf"

def signal_handler(sig, frame):
    print('\nStopping animation...')
    controller.clear_display()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class LEDDisplayController:
    def __init__(self, animation_params=None):
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        
        # Display configuration
        self.PANEL_WIDTH = 16
        self.PANEL_HEIGHT = 16
        self.NUM_PANELS = 4
        self.DISPLAY_WIDTH = self.PANEL_WIDTH * self.NUM_PANELS
        self.DISPLAY_HEIGHT = self.PANEL_HEIGHT
        
        # Font settings - 10% smaller than original 16
        self.char_size = 14
        self.char_spacing = 1
        self.word_spacing = 11  # Slightly reduced for proportion
        self.extra_end_space = 28  # Slightly reduced for proportion
        
        # Default animation parameters
        default_params = {
            'rainbow_speed': 5.0,
            'wave_speed': 3.0,
            'color_density': 0.6,
            'brightness_pulse': 1.5,
            'sparkle_intensity': 0.25,
            'color_shift': 0.1,
            'wave_amplitude': 0.2,
            'scroll_speed': 0.05,
            'time_increment': 0.2,
            'base_brightness': 0.85,
            'saturation': 0.85,
            'sparkle_amount': 0.4
        }
        
        # Update with user-provided parameters if any
        self.animation_params = default_params
        if animation_params:
            self.animation_params.update(animation_params)
        
        # Download and set up font
        self.font_path = self.download_font()

    def download_font(self):
        """Download and save the modern font"""
        try:
            temp_font = tempfile.NamedTemporaryFile(delete=False, suffix='.ttf')
            print("Downloading modern font...")
            urllib.request.urlretrieve(FONT_URL, temp_font.name)
            print("Font downloaded successfully!")
            return temp_font.name
        except Exception as e:
            print(f"Error downloading font: {e}")
            return None

    def get_super_rainbow(self, x, y, time_value):
        """Generate dynamic rainbow effect"""
        base_hue = (x * self.animation_params['color_density'] + 
                   time_value * self.animation_params['rainbow_speed']) / self.DISPLAY_WIDTH
        
        wave1 = math.sin(time_value * self.animation_params['wave_speed'] + x / 6) * self.animation_params['wave_amplitude']
        wave2 = math.cos(time_value * self.animation_params['wave_speed'] * 0.7 + y / 3) * self.animation_params['wave_amplitude']
        wave3 = math.sin((time_value * self.animation_params['wave_speed'] * 0.5 + x / 10) * 2) * self.animation_params['wave_amplitude'] * 0.5
        
        color_shift = math.sin(time_value * self.animation_params['color_shift']) * 0.2
        
        hue = (base_hue + wave1 + wave2 + wave3 + color_shift + time_value * 0.05) % 1.0
        saturation = self.animation_params['saturation'] + math.sin(time_value * 2 + x / 15) * 0.15
        
        base_brightness = self.animation_params['base_brightness']
        pulse1 = math.sin(time_value * 3) * 0.15
        pulse2 = math.cos(time_value * 4 + x / 20) * 0.1
        pulse3 = math.sin(time_value * 2.5 + y / 15) * 0.1
        brightness = min(1.0, base_brightness + pulse1 + pulse2 + pulse3)
        
        if random.random() < self.animation_params['sparkle_intensity']:
            brightness = min(1.0, brightness + random.uniform(0.2, self.animation_params['sparkle_amount']))
        
        rgb = colorsys.hsv_to_rgb(hue, saturation, brightness)
        return tuple(int(c * 255) for c in rgb)

    def get_pixel_index(self, x, y):
        if not (0 <= x < self.DISPLAY_WIDTH and 0 <= y < self.DISPLAY_HEIGHT):
            return -1
        
        y = self.DISPLAY_HEIGHT - 1 - y
        panel_x = x // self.PANEL_WIDTH
        local_x = x % self.PANEL_WIDTH
        local_y = y
        
        if local_y % 2 == 1:
            local_x = self.PANEL_WIDTH - 1 - local_x
            
        panel_offset = panel_x * LED_PANEL_SIZE
        local_offset = (local_y * self.PANEL_WIDTH) + local_x
        
        return panel_offset + local_offset

    def clear_display(self):
        for i in range(LED_COUNT):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

    def get_font(self):
        if self.font_path and os.path.exists(self.font_path):
            try:
                return ImageFont.truetype(self.font_path, self.char_size)
            except Exception as e:
                print(f"Error loading font: {e}")
        return ImageFont.load_default()

    def prepare_text_image(self, words):
        """Prepare text image with perfect vertical centering"""
        font = self.get_font()
        total_width = self.DISPLAY_WIDTH
        
        # Get accurate height for text line
        test_string = "".join(set("".join(words).upper()))
        max_ascent = 0
        max_descent = 0
        
        # Find max ascent and descent for precise vertical centering
        for char in test_string:
            bbox = font.getbbox(char)
            max_ascent = max(max_ascent, -bbox[1])  # Convert negative ascent to positive
            max_descent = max(max_descent, bbox[3])
        
        total_height = max_ascent + max_descent
        
        # Calculate total width needed
        for word in words:
            bbox = font.getbbox(word.upper())
            word_width = bbox[2] + (len(word) - 1) * self.char_spacing
            total_width += word_width + self.word_spacing
        
        total_width += self.extra_end_space
        
        # Create image
        img = Image.new('RGB', (total_width, self.DISPLAY_HEIGHT), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate vertical position for exact centering
        y_offset = (self.DISPLAY_HEIGHT - total_height) // 2 + max_ascent
        
        # Draw text
        x_pos = self.DISPLAY_WIDTH
        for word in words:
            word_upper = word.upper()
            for char in word_upper:
                # Draw character perfectly centered
                draw.text((x_pos, y_offset - max_ascent), char, fill=(255, 255, 255), font=font)
                char_bbox = font.getbbox(char)
                x_pos += char_bbox[2] + self.char_spacing
            x_pos += self.word_spacing
        
        return np.array(img), total_width

    def display_frame(self, image, offset=0, time_value=0):
        """Display frame with dynamic effects"""
        for y in range(self.DISPLAY_HEIGHT):
            for x in range(self.DISPLAY_WIDTH):
                img_x = x + offset
                if 0 <= img_x < image.shape[1]:
                    is_text = np.sum(image[y, img_x]) > 0
                    if is_text:
                        r, g, b = self.get_super_rainbow(x, y, time_value)
                    else:
                        r, g, b = (0, 0, 0)
                    
                    pixel_index = self.get_pixel_index(x, y)
                    if pixel_index >= 0:
                        self.strip.setPixelColor(pixel_index, Color(int(r), int(g), int(b)))
        self.strip.show()

    def scroll_text(self, words):
        """Scroll text with effects"""
        try:
            img_array, total_width = self.prepare_text_image(words)
            time_value = 0
            
            while True:
                for offset in range(total_width):
                    self.display_frame(img_array, offset, time_value)
                    time.sleep(self.animation_params['scroll_speed'])
                    time_value += self.animation_params['time_increment']
                
        except KeyboardInterrupt:
            self.clear_display()
        except Exception as e:
            print(f"Error in scroll: {e}")
            self.clear_display()

def main():
    # Example animation parameters with smoother defaults
    animation_params = {
        'rainbow_speed': 3.0,        # Speed of rainbow color change
        'wave_speed': 2.0,          # Speed of wave motion
        'color_density': 0.5,       # Density of rainbow colors
        'sparkle_intensity': 0.2,   # Probability of sparkle effect
        'scroll_speed': 0.03,       # Text scrolling speed
        'time_increment': 0.15,     # Time increment for animation
        'base_brightness': 0.85,    # Base brightness level
        'saturation': 0.85,        # Color saturation
        'sparkle_amount': 0.4      # Amount of sparkle effect
    }

    global controller
    controller = LEDDisplayController(animation_params=animation_params)
    
    words = [
        "Metal",
        "Worker",
        "Avisos",
        "LED",
        "desde",
        "$500"
    ]
    
    controller.scroll_text(words)

if __name__ == "__main__":
    main()