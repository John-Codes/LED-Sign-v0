#!/usr/bin/env python3

from rpi_ws281x import *
import time
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import signal
import sys
import colorsys
import os
from typing import List, Tuple, Optional
import math

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

def signal_handler(sig, frame):
    print('\nStopping animation...')
    controller.clear_display()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class ColorPalette:
    """Modern color palettes for text effects"""
    NEON = [
        (255, 0, 128),    # Hot Pink
        (0, 255, 255),    # Cyan
        (255, 0, 255),    # Magenta
        (0, 255, 128)     # Bright Mint
    ]
    
    SUNRISE = [
        (255, 99, 71),    # Tomato Red
        (255, 127, 80),   # Coral
        (255, 165, 0),    # Orange
        (255, 192, 203)   # Pink
    ]
    
    OCEAN = [
        (0, 191, 255),    # Deep Sky Blue
        (30, 144, 255),   # Dodge Blue
        (0, 255, 255),    # Cyan
        (127, 255, 212)   # Aquamarine
    ]

class TextEffect:
    """Text animation effects"""
    RAINBOW = "rainbow"
    GRADIENT = "gradient"
    PULSE = "pulse"
    WAVE = "wave"
    SPARKLE = "sparkle"

class ModernTextDisplayController:
    def __init__(self):
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        
        # Display configuration
        self.PANEL_WIDTH = 16
        self.PANEL_HEIGHT = 16
        self.NUM_PANELS = 4
        self.DISPLAY_WIDTH = self.PANEL_WIDTH * self.NUM_PANELS
        self.DISPLAY_HEIGHT = self.PANEL_HEIGHT
        
        # Animation settings
        self.animation_speed = 30.0
        self.effect_intensity = 1.0
        self.current_effect = TextEffect.RAINBOW
        self.current_palette = ColorPalette.NEON
        
        # Modern styling
        self.char_spacing = 3
        self.word_spacing = self.DISPLAY_WIDTH // 5
        self.vertical_offset = 0
        self.brightness_factor = 1.0
        
        # Font configuration
        self.font_paths = [
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        ]
        self.font_path = self.find_available_font()
        self.font_size_range = (12, 15)

    def find_available_font(self) -> Optional[str]:
        """Find the first available modern font"""
        for font_path in self.font_paths:
            if os.path.exists(font_path):
                try:
                    ImageFont.truetype(font_path, 12)
                    print(f"Using modern font: {os.path.basename(font_path)}")
                    return font_path
                except Exception:
                    continue
        print("Using default font")
        return None

    def get_wave_color(self, x: int, y: int, time_value: float) -> Tuple[int, int, int]:
        """Create a wave effect with modern color palette"""
        wave = math.sin(x / 10 + time_value) * math.cos(y / 8 + time_value)
        color_idx = int((wave + 1) * len(self.current_palette) / 2) % len(self.current_palette)
        return self.current_palette[color_idx]

    def get_sparkle_color(self, color: Tuple[int, int, int], time_value: float) -> Tuple[int, int, int]:
        """Add sparkle effect to color"""
        sparkle = abs(math.sin(time_value * 10)) * 0.3 + 0.7
        return tuple(int(c * sparkle) for c in color)

    def apply_effect(self, x: int, y: int, time_value: float) -> Tuple[int, int, int]:
        """Apply selected modern effect to pixel"""
        if self.current_effect == TextEffect.RAINBOW:
            hue = (x + time_value * self.animation_speed) / (self.DISPLAY_WIDTH * 2)
            return tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue % 1.0, 1.0, 1.0))
        elif self.current_effect == TextEffect.WAVE:
            return self.get_wave_color(x, y, time_value)
        elif self.current_effect == TextEffect.SPARKLE:
            base_color = self.current_palette[int(time_value * 2) % len(self.current_palette)]
            return self.get_sparkle_color(base_color, time_value)
        elif self.current_effect == TextEffect.PULSE:
            intensity = (math.sin(time_value * 4) * 0.3 + 0.7) * self.brightness_factor
            color_idx = int(time_value) % len(self.current_palette)
            return tuple(int(c * intensity) for c in self.current_palette[color_idx])
        return (255, 255, 255)

    def prepare_modern_text(self, words: List[str]) -> Tuple[np.ndarray, int]:
        """Prepare text with modern styling and effects"""
        font_size = self.font_size_range[0]
        font = ImageFont.truetype(self.font_path, font_size) if self.font_path else ImageFont.load_default()
        
        # Calculate dimensions
        total_width = self.DISPLAY_WIDTH
        for word in words:
            bbox = font.getbbox(word.upper())
            word_width = bbox[2] - bbox[0] + (len(word) - 1) * self.char_spacing
            total_width += word_width + self.word_spacing
        
        # Create image with modern styling
        img = Image.new('RGB', (total_width, self.DISPLAY_HEIGHT), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        x_pos = self.DISPLAY_WIDTH
        for word in words:
            for char in word.upper():
                bbox = font.getbbox(char)
                char_width = bbox[2] - bbox[0]
                y_pos = (self.DISPLAY_HEIGHT - (bbox[3] - bbox[1])) // 2 + self.vertical_offset
                
                draw.text((x_pos, y_pos), char, fill=(255, 255, 255), font=font)
                x_pos += char_width + self.char_spacing
            x_pos += self.word_spacing - self.char_spacing
        
        return np.array(img), total_width

    def display_modern_frame(self, image: np.ndarray, offset: int = 0, time_value: float = 0):
        """Display a frame with modern effects"""
        for y in range(self.DISPLAY_HEIGHT):
            for x in range(self.DISPLAY_WIDTH):
                img_x = x + offset
                if 0 <= img_x < image.shape[1]:
                    if np.sum(image[y, img_x]) > 0:
                        color = self.apply_effect(x, y, time_value)
                    else:
                        color = (0, 0, 0)
                    
                    pixel_index = self.get_pixel_index(x, y)
                    if pixel_index >= 0:
                        self.strip.setPixelColor(pixel_index, Color(*color))
        
        self.strip.show()

    def scroll_modern(self, words: List[str], scroll_speed: float = 0.05):
        """Scroll text with modern effects"""
        try:
            img_array, total_width = self.prepare_modern_text(words)
            time_value = 0
            
            while True:
                for offset in range(total_width):
                    self.display_modern_frame(img_array, offset, time_value)
                    time.sleep(scroll_speed)
                    time_value += scroll_speed
                
        except KeyboardInterrupt:
            self.clear_display()
        except Exception as e:
            print(f"Error in modern scroll: {e}")
            self.clear_display()

    def get_pixel_index(self, x: int, y: int) -> int:
        """Get LED strip index for given coordinates"""
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
        """Clear the LED display"""
        for i in range(LED_COUNT):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

def main():
    global controller
    controller = ModernTextDisplayController()
    
    # Example usage with different effects
    words = [
        "Metal",
        "Worker",
        "Avisos",
        "LED",
        "desde",
        "$500"
    ]
    
    # Set modern styling
    controller.current_effect = TextEffect.WAVE
    controller.current_palette = ColorPalette.NEON
    controller.animation_speed = 25.0
    controller.brightness_factor = 0.9
    
    # Start scrolling with modern effects
    controller.scroll_modern(
        words,
        scroll_speed=0.05
    )

if __name__ == "__main__":
    main()