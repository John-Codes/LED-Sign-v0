# star_effects.py

import random
import math
import colorsys
import numpy as np

class Star:
    def __init__(self, x, y, brightness, star_type='primary'):
        self.x = x
        self.y = y
        self.brightness = brightness
        self.twinkle_phase = random.random() * 2 * math.pi
        self.type = star_type
        
        # Color properties with safe brightness levels
        self.color_shift_speed = random.random() * 0.5 + 0.3
        
        # Different properties based on star type
        if star_type == 'primary':
            self.twinkle_speed = 1.5 + random.random() * 3
            self.color_speed = 0.3 + random.random() * 1.0
            self.base_hue = random.random()
            self.color_range = 0.4 + random.random() * 0.6
            self.max_brightness = 0.4 + random.random() * 0.2  # Safer brightness level
            self.saturation = 0.9  # High but not max saturation
            self.value = 0.7  # Reduced value for safety
        else:  # background star
            self.twinkle_speed = (0.5 + random.random() * 1.5) * 0.7
            self.color_speed = 0.2 + random.random() * 0.6
            self.base_hue = random.random()
            self.color_range = 0.2 + random.random() * 0.4
            self.max_brightness = 0.2 + random.random() * 0.2  # Lower brightness for background
            self.saturation = 0.7
            self.value = 0.5
            
        self.color_phase = random.random() * 2 * math.pi
        self.color = self.get_random_vibrant_color()

    def get_random_vibrant_color(self):
        """Generate a random vibrant color with safe brightness"""
        vibrant_hues = [
            0.0,   # Red
            0.05,  # Red-Orange
            0.1,   # Orange
            0.15,  # Orange-Yellow
            0.2,   # Yellow
            0.3,   # Green-Yellow
            0.4,   # Green
            0.5,   # Turquoise
            0.6,   # Blue
            0.7,   # Blue-Purple
            0.8,   # Purple
            0.9    # Pink
        ]
        hue = random.choice(vibrant_hues)
        rgb = colorsys.hsv_to_rgb(hue, 0.9, 0.7)  # Reduced value for safety
        return tuple(int(c * 255) for c in rgb)

    def update(self, t):
        # Update brightness with twinkle effect
        self.brightness = (math.sin(self.twinkle_phase + t * self.twinkle_speed) + 1) / 2
        self.brightness *= self.max_brightness

        # Color changing
        time_factor = t * self.color_shift_speed
        hue_shift = math.sin(time_factor) * 0.5 + 0.5
        current_hue = (self.base_hue + hue_shift * self.color_range) % 1.0
        
        rgb = colorsys.hsv_to_rgb(current_hue, self.saturation, self.value)
        self.color = tuple(int(c * 255) for c in rgb)

class StarryBackground:
    def __init__(self, width, height, num_primary_stars=50):
        self.width = width
        self.height = height
        self.stars = []
        self.background_phase = 0
        self.background_speed = 0.05
        self.init_stars(num_primary_stars)

    def init_stars(self, num_primary_stars):
        """Initialize both primary and background stars"""
        # Create primary (brighter) stars
        for _ in range(num_primary_stars):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            brightness = random.random() * 0.4 + 0.2  # Reduced brightness range
            self.stars.append(Star(x, y, brightness, 'primary'))

        # Create background (dimmer) stars
        num_background_stars = num_primary_stars
        for _ in range(num_background_stars):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            brightness = random.random() * 0.2 + 0.1  # Very low brightness for background
            self.stars.append(Star(x, y, brightness, 'background'))

    def get_background_color(self, t):
        """Generate dynamic background color"""
        return (0, 0, 1)  # Very slight blue tint

    def apply_effect(self, pixel_array, t):
        """Apply star and background effects to pixel array"""
        bg_color = self.get_background_color(t)
        mask = pixel_array.sum(axis=2) == 0
        pixel_array[mask] = bg_color

        # Update and draw stars with safe brightness levels
        for star in self.stars:
            star.update(t)
            if pixel_array[star.y, star.x].sum() <= 15:
                r, g, b = star.color
                brightness = star.brightness * 10  # Reduced max brightness
                pixel_array[star.y, star.x] = [
                    min(255, int(r * brightness/255)),
                    min(255, int(g * brightness/255)),
                    min(255, int(b * brightness/255))
                ]

        return pixel_array

    def add_shooting_star(self):
        start_x = random.randint(0, self.width - 1)
        start_y = 0
        brightness = random.random() * 0.4 + 0.2  # Safe brightness for shooting stars
        self.stars.append(Star(start_x, start_y, brightness, 'shooting'))

    def remove_star(self, index):
        if 0 <= index < len(self.stars):
            self.stars.pop(index)

    def adjust_star_density(self, num_primary_stars):
        self.stars.clear()
        self.init_stars(num_primary_stars)