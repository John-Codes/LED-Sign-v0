#!/usr/bin/env python3

from rpi_ws281x import *
import time
import cv2
import numpy as np

# LED matrix configuration
LED_PANEL_SIZE = 256
NUM_PANELS = 4
LED_COUNT = LED_PANEL_SIZE * NUM_PANELS
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 50
LED_INVERT = False
LED_CHANNEL = 0

class VideoDisplayController:
    def __init__(self):
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        
        self.PANEL_WIDTH = 16
        self.PANEL_HEIGHT = 16
        self.GRID_COLS = 2
        self.GRID_ROWS = 2
        
        self.DISPLAY_WIDTH = self.PANEL_WIDTH * self.GRID_COLS
        self.DISPLAY_HEIGHT = self.PANEL_HEIGHT * self.GRID_ROWS

    def get_pixel_index(self, x: int, y: int) -> int:
        if not (0 <= x < self.DISPLAY_WIDTH and 0 <= y < self.DISPLAY_HEIGHT):
            return -1

        panel_x = x // self.PANEL_WIDTH
        panel_y = y // self.PANEL_HEIGHT
        
        if panel_y == 0:
            panel_index = 2 + panel_x
        else:
            panel_index = panel_x
            
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

    def display_frame(self, frame):
        for y in range(self.DISPLAY_HEIGHT):
            for x in range(self.DISPLAY_WIDTH):
                r, g, b = frame[y, x]
                pixel_index = self.get_pixel_index(x, y)
                if pixel_index >= 0:
                    self.strip.setPixelColor(pixel_index, Color(int(r), int(g), int(b)))
        self.strip.show()

    def play_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Could not open video.")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = 1.0 / fps

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Resize the frame to fit the LED matrix
                frame = cv2.resize(frame, (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                self.display_frame(frame)
                time.sleep(frame_delay)

        except KeyboardInterrupt:
            print("\nVideo playback interrupted by user")
        finally:
            cap.release()
            self.clear_display()

def main():
    controller = VideoDisplayController()
    
    video_path = "your_video_file.mp4"  # Replace with your video file path
    
    try:
        print("Starting video playback. Press Ctrl+C to exit.")
        controller.play_video(video_path)
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        controller.clear_display()
    except Exception as e:
        print(f"Error: {e}")
        controller.clear_display()

if __name__ == "__main__":
    main()