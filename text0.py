#!/usr/bin/env python3

from rpi_ws281x import *
import time
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import colorsys
import math
from enum import Enum
import random

class AnimationStyle(Enum):
    SOLID = "solid"
    RAINBOW = "rainbow"
    PULSE = "pulse"
    ALTERNATE = "alternate"
    GRADIENT = "gradient"
    WAVE = "wave"

LED_PANEL_SIZE = 256
NUM_PANELS = 4
LED_COUNT = LED_PANEL_SIZE * NUM_PANELS
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 5
LED_INVERT = False
LED_CHANNEL = 0

class Star:
    def __init__(self, x, y, brightness=1.0, speed=1.0):
        self.x = x
        self.y = y
        self.brightness = brightness
        self.speed = speed
        self.color = self.random_color()

    def random_color(self):
        colors = [
            (255, 255, 200),  # Warm white
            (200, 200, 255),  # Cool white
            (255, 200, 200),  # Pink
            (200, 255, 200),  # Mint
        ]
        return random.choice(colors)

    def update(self, t):
        self.brightness = (math.sin(t * self.speed) + 1) / 2

    def get_color(self):
        return tuple(int(c * self.brightness) for c in self.color)

class StarAnimation:
    def __init__(self, width, height, num_stars=30):
        self.width = width
        self.height = height
        self.stars = []
        for _ in range(num_stars):
            x = random.randint(0, width-1)
            y = random.randint(0, height-1)
            speed = random.uniform(1.0, 3.0)
            self.stars.append(Star(x, y, speed=speed))

    def render(self, t):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for star in self.stars:
            star.update(t)
            color = star.get_color()
            frame[star.y, star.x] = color
        return frame

class TextDisplayController:
    def __init__(self):
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        
        self.PANEL_WIDTH = 16
        self.PANEL_HEIGHT = 16
        self.GRID_COLS = 2
        self.GRID_ROWS = 2
        
        self.DISPLAY_WIDTH = self.PANEL_WIDTH * self.GRID_COLS
        self.DISPLAY_HEIGHT = self.PANEL_HEIGHT * self.GRID_ROWS
        
        self.current_animation = AnimationStyle.SOLID
        self.primary_color = (128, 0, 0)
        self.secondary_color = (0, 0, 128)
        self.animation_speed = 0.05
        
        self.star_animation = StarAnimation(self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT)

    def set_colors(self, primary_color, secondary_color=None):
        self.primary_color = primary_color
        self.secondary_color = secondary_color or primary_color
        
    def set_animation(self, animation_style: AnimationStyle):
        self.current_animation = animation_style

    def get_pixel_index(self, x: int, y: int) -> int:
        if not (0 <= x < self.DISPLAY_WIDTH and 0 <= y < self.DISPLAY_HEIGHT):
            return -1

        panel_x = x // self.PANEL_WIDTH
        panel_y = y // self.PANEL_HEIGHT
        
        panel_index = (panel_y * self.GRID_COLS) + panel_x
            
        local_x = x % self.PANEL_WIDTH
        local_y = y % self.PANEL_HEIGHT
        
        if local_y % 2 == 1:
            local_x = self.PANEL_WIDTH - 1 - local_x
            
        panel_offset = panel_index * LED_PANEL_SIZE
        local_offset = (local_y * self.PANEL_WIDTH) + local_x
        
        return panel_offset + local_offset

    def clear_display(self):
        for i in range(LED_COUNT):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

    def apply_color_animation(self, base_color, x, y, t):
        r, g, b = base_color
        
        if self.current_animation == AnimationStyle.SOLID:
            return r, g, b
            
        elif self.current_animation == AnimationStyle.RAINBOW:
            hue = (y + t) / 30.0
            rgb = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue % 1.0, 1.0, 0.5))
            return rgb
            
        elif self.current_animation == AnimationStyle.PULSE:
            intensity = (math.sin(t * 2) + 1) / 2
            return (int(r * intensity), int(g * intensity), int(b * intensity))
            
        elif self.current_animation == AnimationStyle.ALTERNATE:
            if int(t) % 2 == 0:
                return self.primary_color
            return self.secondary_color
            
        elif self.current_animation == AnimationStyle.GRADIENT:
            ratio = (math.sin(t + y / 10) + 1) / 2
            r = int(self.primary_color[0] * ratio + self.secondary_color[0] * (1 - ratio))
            g = int(self.primary_color[1] * ratio + self.secondary_color[1] * (1 - ratio))
            b = int(self.primary_color[2] * ratio + self.secondary_color[2] * (1 - ratio))
            return (r, g, b)
            
        elif self.current_animation == AnimationStyle.WAVE:
            wave = math.sin(y / 5 - t * 3)
            if wave > 0:
                return self.primary_color
            return self.secondary_color
            
        return base_color

    def display_frame_animated(self, image, offset=0, animation_time=0):
        for y in range(self.DISPLAY_HEIGHT):
            for x in range(self.DISPLAY_WIDTH):
                img_y = y + offset
                if 0 <= img_y < image.shape[0]:
                    is_text = np.sum(image[img_y, x]) > 700
                    
                    if is_text:
                        r, g, b = self.apply_color_animation(self.primary_color, x, y, animation_time)
                    else:
                        r, g, b = image[img_y, x]
                    
                    pixel_index = self.get_pixel_index(x, y)
                    if pixel_index >= 0:
                        self.strip.setPixelColor(pixel_index, Color(int(r), int(g), int(b)))
        
        self.strip.show()

    def create_text_image(self, text, total_height):
        img = Image.new('RGB', (self.DISPLAY_WIDTH, total_height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        font = ImageFont.load_default()
        for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
            try:
                font = ImageFont.truetype(path, 12)
                break
            except:
                continue

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.DISPLAY_WIDTH - text_width) // 2
        y = total_height - self.DISPLAY_HEIGHT
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        return np.array(img)

    def scroll_text_animated(self, text, scroll_speed=0.05):
        total_height = self.DISPLAY_HEIGHT * 3
        img_array = self.create_text_image(text, total_height)
        animation_time = 0
        
        try:
            for offset in range(total_height - self.DISPLAY_HEIGHT, -1, -1):
                window = img_array[offset:offset + self.DISPLAY_HEIGHT]
                self.display_frame_animated(window, 0, animation_time)
                time.sleep(scroll_speed)
                animation_time += scroll_speed
        except Exception as e:
            print(f"Error while scrolling: {e}")
            self.clear_display()

    def display_star_animation(self, duration=3.0):
        start_time = time.time()
        while time.time() - start_time < duration:
            animation_time = time.time() - start_time
            frame = self.star_animation.render(animation_time)
            self.display_frame_animated(frame, 0, animation_time)
            time.sleep(0.05)

    def display_static_text(self, text):
        img = Image.new('RGB', (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        font = ImageFont.load_default()
        for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
            try:
                font = ImageFont.truetype(path, 12)
                break
            except:
                continue

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (self.DISPLAY_WIDTH - text_width) // 2
        y = (self.DISPLAY_HEIGHT - text_height) // 2
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        img_array = np.array(img)
        animation_time = 0
        
        for _ in range(20):
            self.display_frame_animated(img_array, 0, animation_time)
            time.sleep(0.05)
            animation_time += 0.05

    def display_sequence_animated(self, words, scroll_speed=0.05, pause_time=1.0):
        try:
            while True:
                for word in words:
                    self.clear_display()
                    time.sleep(0.2)
                    
                    if len(word) > 4:
                        self.scroll_text_animated(word, scroll_speed)
                    else:
                        self.display_static_text(word)
                    
                    self.display_star_animation(duration=2.0)
                    time.sleep(pause_time)
                    
        except KeyboardInterrupt:
            print("\nSequence interrupted by user")
            self.clear_display()
        except Exception as e:
            print(f"Error in sequence: {e}")
            self.clear_display()

def main():
    controller = TextDisplayController()
    
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    
    words = [
        "Metal",
        "Worker",
        "Avisos",
        "LED",
        "desde",
        "$500"
    ]
    
    try:
        print("Starting animated display sequence. Press Ctrl+C to exit.")
        controller.clear_display()
        
        controller.set_colors(RED, BLUE)
        controller.set_animation(AnimationStyle.RAINBOW)
        
        controller.display_sequence_animated(words)
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        controller.clear_display()
    except Exception as e:
        print(f"Error: {e}")
        controller.clear_display()

if __name__ == "__main__":
    main()