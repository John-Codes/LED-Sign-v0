#!/usr/bin/env python3

from rpi_ws281x import *
import time
import random
import math
import colorsys
import numpy as np
import signal
import sys

LED_PANEL_SIZE = 256
NUM_PANELS = 4
LED_COUNT = LED_PANEL_SIZE * NUM_PANELS
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 50
LED_INVERT = False
LED_CHANNEL = 0

class Shark:
    def __init__(self, x, y, length, speed):
        self.x = x
        self.y = y
        self.length = length
        self.speed = speed
        self.angle = 0
        self.tail_phase = random.random() * 2 * math.pi
        self.tail_speed = 0.5 + random.random() * 1.5
        self.color = (0, 0, 255)  # Blue color for the shark
        self.bite_phase = 0
        self.bite_speed = 0.1

    def update(self, t):
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)
        self.tail_phase += self.tail_speed * t
        self.bite_phase += self.bite_speed * t
        return self.x, self.y

    def draw(self, controller):
        for i in range(self.length):
            tail_x = int(self.x - i * math.cos(self.angle))
            tail_y = int(self.y - i * math.sin(self.angle))
            tail_brightness = (math.sin(self.tail_phase + i * 0.2) + 1) / 2
            color = tuple(int(c * tail_brightness) for c in self.color)
            pixel_index = controller.get_pixel_index(tail_x, tail_y)
            if pixel_index >= 0:
                controller.strip.setPixelColor(pixel_index, Color(*color))

        # Draw the bite effect
        if self.bite_phase < 1:
            for y in range(controller.DISPLAY_HEIGHT):
                for x in range(controller.DISPLAY_WIDTH):
                    dist = math.sqrt((x - self.x)**2 + (y - self.y)**2)
                    if dist < 5:
                        brightness = (math.sin(self.bite_phase * math.pi) + 1) / 2
                        color = tuple(int(c * brightness) for c in self.color)
                        pixel_index = controller.get_pixel_index(x, y)
                        if pixel_index >= 0:
                            controller.strip.setPixelColor(pixel_index, Color(*color))

class Bubble:
    def __init__(self, x, y, speed, size):
        self.x = x
        self.y = y
        self.speed = speed
        self.size = size
        self.color = (255, 255, 255)  # White color for bubbles

    def update(self):
        self.y -= self.speed
        return self.x, self.y

    def draw(self, controller):
        for dy in range(-self.size, self.size + 1):
            for dx in range(-self.size, self.size + 1):
                if dx*dx + dy*dy <= self.size*self.size:
                    pixel_index = controller.get_pixel_index(int(self.x) + dx, int(self.y) + dy)
                    if pixel_index >= 0:
                        controller.strip.setPixelColor(pixel_index, Color(*self.color))

class SharkController:
    def __init__(self):
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        
        self.PANEL_WIDTH = 16
        self.PANEL_HEIGHT = 16
        self.GRID_COLS = 2
        self.GRID_ROWS = 2
        
        self.DISPLAY_WIDTH = self.PANEL_WIDTH * self.GRID_COLS
        self.DISPLAY_HEIGHT = self.PANEL_HEIGHT * self.GRID_ROWS
        
        self.shark = Shark(self.DISPLAY_WIDTH // 2, self.DISPLAY_HEIGHT // 2, 10, 1)
        self.bubbles = []
        self.last_bubble = 0
        self.bubble_interval = 0.5
        self.max_bubbles = 10
        
        self.background_phase = 0
        self.background_speed = 0.1

    def get_background_color(self, x, y, t):
        hue = (math.sin(t * 0.1) + 1) / 2
        wave = math.sin(self.background_phase + t * self.background_speed)
        base_intensity = (wave + 1) * 0.5 * 0.15
        
        intensity = base_intensity
        
        rgb = colorsys.hsv_to_rgb(hue, 0.8, intensity)
        return tuple(int(c * 255) for c in rgb)

    def get_pixel_index(self, x, y):
        if not (0 <= x < self.DISPLAY_WIDTH and 0 <= y < self.DISPLAY_HEIGHT):
            return -1
            
        panel_x = x // self.PANEL_WIDTH
        panel_y = y // self.PANEL_HEIGHT
        local_x = (self.PANEL_WIDTH - 1) - (x % self.PANEL_WIDTH)
        local_y = y % self.PANEL_HEIGHT
        
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

    def add_bubble(self):
        x = random.randint(0, self.DISPLAY_WIDTH - 1)
        y = self.DISPLAY_HEIGHT
        speed = 1 + random.random() * 2
        size = random.randint(1, 3)
        if len(self.bubbles) < self.max_bubbles:
            self.bubbles.append(Bubble(x, y, speed, size))

    def update_display(self, t):
        for y in range(self.DISPLAY_HEIGHT):
            for x in range(self.DISPLAY_WIDTH):
                bg_color = self.get_background_color(x, y, t)
                pixel_index = self.get_pixel_index(x, y)
                if pixel_index >= 0:
                    self.strip.setPixelColor(pixel_index, Color(*bg_color))

        self.shark.update(t)
        self.shark.draw(self)

        self.bubbles = [bubble for bubble in self.bubbles if bubble.y > 0]
        
        for bubble in self.bubbles:
            bubble.update()
            bubble.draw(self)

        if t - self.last_bubble > self.bubble_interval:
            if random.random() < 0.6:
                self.add_bubble()
                self.last_bubble = t

        self.strip.show()

def signal_handler(sig, frame):
    print('\nStopping animation...')
    controller.clear_display()
    sys.exit(0)

def main():
    global controller
    controller = SharkController()
    signal.signal(signal.SIGINT, signal_handler)
    
    start_time = time.time()
    try:
        while True:
            current_time = time.time() - start_time
            controller.update_display(current_time)
            time.sleep(0.03)
    except KeyboardInterrupt:
        controller.clear_display()

if __name__ == "__main__":
    main()