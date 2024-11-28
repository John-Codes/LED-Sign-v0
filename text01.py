#!/usr/bin/env python3

from rpi_ws281x import *
import time
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import signal
import sys

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
    controller = TextDisplayController()
    controller.clear_display()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

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
        self.text_color = (0, 0, 255)  # Blue text

    def get_pixel_index(self, x: int, y: int) -> int:
        if not (0 <= x < self.DISPLAY_WIDTH and 0 <= y < self.DISPLAY_HEIGHT):
            return -1
            
        local_x = x % self.PANEL_WIDTH
        local_y = y % self.PANEL_HEIGHT
        panel_x = x // self.PANEL_WIDTH
        panel_y = y // self.PANEL_HEIGHT
        
        # Swap panel order within each row (0->1, 1->0)
        panel_x = 1 - panel_x
        
        if local_y % 2 == 1:
            local_x = self.PANEL_WIDTH - 1 - local_x
            
        panel_index = (panel_y * self.GRID_COLS) + panel_x
        panel_offset = panel_index * LED_PANEL_SIZE
        local_offset = (local_y * self.PANEL_WIDTH) + local_x
        
        return panel_offset + local_offset

    def clear_display(self):
        for i in range(LED_COUNT):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()

    def display_frame(self, image, offset=0):
        for y in range(self.DISPLAY_HEIGHT):
            for x in range(self.DISPLAY_WIDTH):
                img_y = y + offset
                if 0 <= img_y < image.shape[0]:
                    is_text = np.sum(image[img_y, x]) > 0
                    if is_text:
                        r, g, b = self.text_color
                    else:
                        r, g, b = (0, 0, 0)
                    
                    pixel_index = self.get_pixel_index(x, y)
                    if pixel_index >= 0:
                        self.strip.setPixelColor(pixel_index, Color(int(r), int(g), int(b)))
        self.strip.show()

    def scroll_text(self, text, scroll_speed=0.05):
        total_height = self.DISPLAY_HEIGHT * 3
        img = Image.new('RGB', (self.DISPLAY_WIDTH, total_height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.DISPLAY_WIDTH - text_width) // 2
        y = total_height - self.DISPLAY_HEIGHT
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        img_array = np.array(img)
        
        try:
            for offset in range(total_height - self.DISPLAY_HEIGHT, -1, -1):
                self.display_frame(img_array, offset)
                time.sleep(scroll_speed)
        except KeyboardInterrupt:
            self.clear_display()

def main():
    global controller
    controller = TextDisplayController()
    
    words = [
        "Metal",
        "Worker",
        "Avisos",
        "LED",
        "desde",
        "$500"
    ]
    
    while True:
        for word in words:
            controller.clear_display()
            time.sleep(0.2)
            controller.scroll_text(word, 0.05)
            time.sleep(1.0)

if __name__ == "__main__":
    main()