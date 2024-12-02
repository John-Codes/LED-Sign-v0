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

class Circle:
    def __init__(self, x, y, radius, color_speed, base_hue):
        self.x = x
        self.y = y
        self.radius = radius
        self.color_speed = color_speed
        self.base_hue = base_hue
        self.pulse_phase = random.random() * 2 * math.pi
        self.pulse_speed = 0.5 + random.random() * 1.5
        self.max_brightness = 0.4 + random.random() * 0.2

    def get_color(self, t):
        hue = (self.base_hue + t * self.color_speed) % 1.0
        rgb = colorsys.hsv_to_rgb(hue, 0.9, 0.7)
        return tuple(int(c * 255) for c in rgb)

    def update(self, t):
        self.radius = 2 + 3 * (math.sin(self.pulse_phase + t * self.pulse_speed) + 1) / 2
        self.brightness = (math.sin(self.pulse_phase + t * self.pulse_speed) + 1) / 2
        self.brightness *= self.max_brightness
        return self.get_color(t)

class Comet:
    def __init__(self, x, y, speed, angle, trail_length, color):
        self.x = x
        self.y = y
        self.speed = speed
        self.angle = angle
        self.trail_length = trail_length
        self.color = color
        self.life = 0
        self.max_life = 100

    def update(self):
        self.life += self.speed
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        brightness = max(0, 1 - self.life / self.max_life)
        return tuple(int(c * brightness) for c in self.color)

class CircleController:
    def __init__(self):
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        
        self.PANEL_WIDTH = 16
        self.PANEL_HEIGHT = 16
        self.GRID_COLS = 2
        self.GRID_ROWS = 2
        
        self.DISPLAY_WIDTH = self.PANEL_WIDTH * self.GRID_COLS
        self.DISPLAY_HEIGHT = self.PANEL_HEIGHT * self.GRID_ROWS
        
        self.circles = []
        self.comets = []
        self.last_comet = 0
        self.comet_interval = 0.5
        self.max_comets = 5
        
        self.background_phase = 0
        self.background_speed = 0.1
        
        self.init_circles(80)

    def init_circles(self, num_circles):
        for _ in range(num_circles):
            x = random.randint(0, self.DISPLAY_WIDTH - 1)
            y = random.randint(0, self.DISPLAY_HEIGHT - 1)
            radius = 2 + random.random() * 3
            color_speed = 0.3 + random.random() * 1.0
            base_hue = random.random()
            self.circles.append(Circle(x, y, radius, color_speed, base_hue))

    def add_comet(self):
        edge = random.choice(['top', 'left', 'right'])
        if edge == 'top':
            x = random.randint(0, self.DISPLAY_WIDTH)
            y = -5
        elif edge == 'left':
            x = -5
            y = random.randint(0, self.DISPLAY_HEIGHT)
        else:
            x = self.DISPLAY_WIDTH + 5
            y = random.randint(0, self.DISPLAY_HEIGHT)

        speed = 3 + random.random() * 4
        angle = random.random() * 2 * math.pi
        trail_length = random.randint(3, 6)
        color = self.get_comet_color()
        
        if len(self.comets) < self.max_comets:
            self.comets.append(Comet(x, y, speed, angle, trail_length, color))

    def get_comet_color(self):
        colors = [
            (255, 255, 255),  # White
            (255, 200, 200),  # Pinkish
            (200, 200, 255),  # Bluish
            (255, 255, 200)   # Yellowish
        ]
        return random.choice(colors)

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

    def update_display(self, t):
        for y in range(self.DISPLAY_HEIGHT):
            for x in range(self.DISPLAY_WIDTH):
                bg_color = self.get_background_color(x, y, t)
                pixel_index = self.get_pixel_index(x, y)
                if pixel_index >= 0:
                    self.strip.setPixelColor(pixel_index, Color(*bg_color))

        for circle in self.circles:
            r, g, b = circle.update(t)
            for dy in range(-int(circle.radius), int(circle.radius) + 1):
                for dx in range(-int(circle.radius), int(circle.radius) + 1):
                    if dx*dx + dy*dy <= circle.radius*circle.radius:
                        pixel_index = self.get_pixel_index(int(circle.x) + dx, int(circle.y) + dy)
                        if pixel_index >= 0:
                            self.strip.setPixelColor(pixel_index, Color(int(r * circle.brightness), int(g * circle.brightness), int(b * circle.brightness)))

        self.comets = [comet for comet in self.comets if comet.life < comet.max_life]
        
        for comet in self.comets:
            r, g, b = comet.update()
            for i in range(comet.trail_length):
                trail_x = int(comet.x - i * math.cos(comet.angle))
                trail_y = int(comet.y - i * math.sin(comet.angle))
                pixel_index = self.get_pixel_index(trail_x, trail_y)
                if pixel_index >= 0:
                    trail_brightness = (comet.trail_length - i) / comet.trail_length
                    color = tuple(int(c * trail_brightness) for c in (r, g, b))
                    self.strip.setPixelColor(pixel_index, Color(*color))

        if t - self.last_comet > self.comet_interval:
            if random.random() < 0.6:
                self.add_comet()
                self.last_comet = t

        self.strip.show()

def signal_handler(sig, frame):
    print('\nStopping animation...')
    controller.clear_display()
    sys.exit(0)

def main():
    global controller
    controller = CircleController()
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