# sound.py
import pygame
import os

class Sound:
    def __init__(self, path):
        self.path = path
        self.sound = None
        try:
            if os.path.exists(path):
                self.sound = pygame.mixer.Sound(path)
            else:
                print(f"Sound file not found: {path}")
        except pygame.error as e:
            print(f"Could not load sound {path}: {e}")

    def play(self):
        if self.sound:
            try:
                self.sound.play()
            except pygame.error as e:
                print(f"Could not play sound: {e}")