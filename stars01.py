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

class Planet:
    def __init__(self, display_width, display_height):
        edge = random.choice(['top', 'left', 'right', 'bottom'])
        if edge == 'top':
            self.initial_x = random.randint(0, display_width)
            self.initial_y = -5
        elif edge == 'left':
            self.initial_x = -5
            self.initial_y = random.randint(0, display_height)
        elif edge == 'right':
            self.initial_x = display_width + 5
            self.initial_y = random.randint(0, display_height)
        else:  # bottom
            self.initial_x = random.randint(0, display_width)
            self.initial_y = display_height + 5
            
        self.x = self.initial_x
        self.y = self.initial_y
        self.speed = 0.5 + random.random() * 2
        self.angle = random.random() * 2 * math.pi
        self.size = random.randint(1, 5)
        self.life = 0
        self.max_life = display_width * 3
        
        planet_types = [
            (0.0, 1.0, 1.0),    # Red
            (0.1, 0.8, 0.9),    # Orange
            (0.3, 0.7, 1.0),    # Green
            (0.6, 0.9, 0.8),    # Blue
            (0.8, 0.7, 0.9),    # Purple
            (0.95, 0.6, 1.0),   # Pink
            (random.random(), 0.8 + random.random() * 0.2, 0.6 + random.random() * 0.4)  # Random
        ]
        
        self.hue, self.saturation, self.value = random.choice(planet_types)
        self.color = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(self.hue, self.saturation, self.value))
        
        self.glow_size = self.size + random.randint(1, 3)
        self.glow_brightness = 0.3 + random.random() * 0.4

    def update(self):
        self.life += self.speed
        self.x = self.initial_x + math.cos(self.angle) * self.life
        self.y = self.initial_y + math.sin(self.angle) * self.life
        return not (self.life > self.max_life)

class Star:
    def __init__(self, x, y, brightness, star_type='primary'):
        self.x = x
        self.y = y
        self.brightness = brightness
        self.twinkle_phase = random.random() * 2 * math.pi
        self.type = star_type
        
        if star_type == 'primary':
            self.twinkle_speed = 1.5 + random.random() * 3
            self.color_speed = 0.3 + random.random() * 1.0
            self.base_hue = random.random()
            self.max_brightness = 0.4 + random.random() * 0.2
        elif star_type == 'shooting':
            self.speed = 3 + random.random() * 4
            self.angle = random.random() * 2 * math.pi
            self.trail_length = random.randint(3, 6)
            self.life = 0
            self.max_life = self.DISPLAY_WIDTH * 1.5
            self.max_brightness = 0.9
            self.color = self.get_shooting_star_color()
        else:  # background
            self.twinkle_speed = 0.5 + random.random() * 1.5
            self.color_speed = 0.2 + random.random() * 0.6
            self.base_hue = random.random()
            self.max_brightness = 0.2 + random.random() * 0.2
            
        if star_type != 'shooting':
            self.color = self.get_color()

    def get_shooting_star_color(self):
        colors = [
            (255, 255, 255),  # White
            (255, 200, 200),  # Pinkish
            (200, 200, 255),  # Bluish
            (255, 255, 200)   # Yellowish
        ]
        return random.choice(colors)

    def get_color(self):
        rgb = colorsys.hsv_to_rgb(self.base_hue, 0.9, 0.7)
        return tuple(int(c * 255) for c in rgb)

    def update(self, t):
        if self.type == 'shooting':
            self.life += self.speed
            self.x = self.initial_x + math.cos(self.angle) * self.life
            self.y = self.initial_y + math.sin(self.angle) * self.life
            brightness = max(0, 1 - self.life/self.max_life)
            return tuple(int(c * brightness * self.max_brightness) for c in self.color)
            
        self.brightness = (math.sin(self.twinkle_phase + t * self.twinkle_speed) + 1) / 2
        self.brightness *= self.max_brightness
        return tuple(int(c * self.brightness) for c in self.color)

class StarController:
    def __init__(self):
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        
        self.PANEL_WIDTH = 16
        self.PANEL_HEIGHT = 16
        self.GRID_COLS = 2
        self.GRID_ROWS = 2
        
        self.DISPLAY_WIDTH = self.PANEL_WIDTH * self.GRID_COLS
        self.DISPLAY_HEIGHT = self.PANEL_HEIGHT * self.GRID_ROWS
        
        Star.DISPLAY_WIDTH = self.DISPLAY_WIDTH
        Star.DISPLAY_HEIGHT = self.DISPLAY_HEIGHT
        
        self.stars = []
        self.shooting_stars = []
        self.planets = []
        self.last_shooting_star = 0
        self.last_planet = 0
        self.shooting_star_interval = 0.5
        self.planet_interval = 2.0
        self.max_shooting_stars = 5
        self.max_planets = 8
        
        self.background_phase = 0
        self.background_speed = 0.1
        
        self.intensity_map = np.ones((self.DISPLAY_HEIGHT, self.DISPLAY_WIDTH))
        self.init_stars(80)

    def init_stars(self, num_stars):
        for _ in range(num_stars):
            x = random.randint(0, self.DISPLAY_WIDTH - 1)
            y = random.randint(0, self.DISPLAY_HEIGHT - 1)
            brightness = random.random() * 0.4 + 0.2
            self.stars.append(Star(x, y, brightness, 'primary' if random.random() > 0.5 else 'background'))

    def add_shooting_star(self):
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

        star = Star(0, 0, 1.0, 'shooting')
        star.initial_x = x
        star.initial_y = y
        
        if len(self.shooting_stars) < self.max_shooting_stars:
            self.shooting_stars.append(star)

    def add_planet(self):
        if len(self.planets) < self.max_planets and random.random() < 0.4:
            self.planets.append(Planet(self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT))
            self.last_planet = time.time()

    def update_intensity_map(self):
        for y in range(self.DISPLAY_HEIGHT):
            for x in range(self.DISPLAY_WIDTH):
                if random.random() < 0.001:
                    self.intensity_map[y, x] = random.random() * 0.5
                else:
                    self.intensity_map[y, x] = min(1.0, self.intensity_map[y, x] + 0.01)

    def get_background_color(self, x, y, t):
        hue = (math.sin(t * 0.1) + 1) / 2
        wave = math.sin(self.background_phase + t * self.background_speed)
        base_intensity = (wave + 1) * 0.5 * 0.15
        
        intensity = base_intensity * self.intensity_map[y, x]
        
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
        self.update_intensity_map()
        
        for y in range(self.DISPLAY_HEIGHT):
            for x in range(self.DISPLAY_WIDTH):
                bg_color = self.get_background_color(x, y, t)
                pixel_index = self.get_pixel_index(x, y)
                if pixel_index >= 0:
                    self.strip.setPixelColor(pixel_index, Color(*bg_color))

        for star in self.stars:
            r, g, b = star.update(t)
            pixel_index = self.get_pixel_index(int(star.x), int(star.y))
            if pixel_index >= 0:
                self.strip.setPixelColor(pixel_index, Color(r, g, b))

        self.shooting_stars = [star for star in self.shooting_stars 
                             if star.life < star.max_life]
        
        for star in self.shooting_stars:
            r, g, b = star.update(t)
            for i in range(star.trail_length):
                trail_x = int(star.x - i * math.cos(star.angle))
                trail_y = int(star.y - i * math.sin(star.angle))
                pixel_index = self.get_pixel_index(trail_x, trail_y)
                if pixel_index >= 0:
                    trail_brightness = (star.trail_length - i) / star.trail_length
                    color = tuple(int(c * trail_brightness) for c in (r, g, b))
                    self.strip.setPixelColor(pixel_index, Color(*color))

        self.planets = [planet for planet in self.planets if planet.update()]
        
        for planet in self.planets:
            for gx in range(int(planet.x - planet.glow_size), int(planet.x + planet.glow_size + 1)):
                for gy in range(int(planet.y - planet.glow_size), int(planet.y + planet.glow_size + 1)):
                    distance = math.sqrt((gx - planet.x)**2 + (gy - planet.y)**2)
                    if distance <= planet.glow_size:
                        brightness = (planet.glow_size - distance) / planet.glow_size * planet.glow_brightness
                        color = tuple(int(c * brightness) for c in planet.color)
                        pixel_index = self.get_pixel_index(gx, gy)
                        if pixel_index >= 0:
                            self.strip.setPixelColor(pixel_index, Color(*color))
            
            for dx in range(-planet.size, planet.size + 1):
                for dy in range(-planet.size, planet.size + 1):
                    if dx*dx + dy*dy <= planet.size*planet.size:
                        pixel_index = self.get_pixel_index(int(planet.x + dx), int(planet.y + dy))
                        if pixel_index >= 0:
                            self.strip.setPixelColor(pixel_index, Color(*planet.color))

        if t - self.last_shooting_star > self.shooting_star_interval:
            if random.random() < 0.6:
                self.add_shooting_star()
                self.last_shooting_star = t

        current_time = time.time()
        if current_time - self.last_planet > self.planet_interval:
            self.add_planet()

        self.strip.show()

def signal_handler(sig, frame):
    print('\nStopping animation...')
    controller.clear_display()
    sys.exit(0)

def main():
    global controller
    controller = StarController()
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