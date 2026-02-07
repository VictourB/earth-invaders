import os

# --- Screen & Display ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Earth Invaders"

# --- Gameplay ---
PLAYER_START_X = SCREEN_WIDTH / 2
PLAYER_START_Y = SCREEN_HEIGHT * 0.85
COLLISION_DISTANCE = int(SCREEN_HEIGHT * 0.85)
ENEMY_SPAWN_Y_MIN = 20
ENEMY_SPAWN_Y_MAX = 250

# --- Player Physics ---
PLAYER_ACCEL = 45.0
PLAYER_FRICTION = 0.5
PLAYER_MAX_SPEED = 600

# --- Colors ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GOLD = (255, 215, 0)
CYAN = (0, 255, 255)
GRAY_HUD = (150, 150, 150)
SPACE_COLOR = (24, 20, 37)


DANGER_COLOR = (255, 0, 0) # Red



# --- Asset Paths ---
BASE_PATH = os.path.abspath(os.path.dirname(__file__))

# --- Scoring ---
ENEMY_POINTS_NORMAL = 10
ENEMY_POINTS_SHOOTER = 50
ENEMY_POINTS_UFO = 200 # Baseline or random

def get_path(filename):
    """Helper to join paths relative to this file."""
    return os.path.join(BASE_PATH, filename)

# settings.py
FONT_MAIN = get_path("assets/font/PressStart2P-Regular.ttf")
FONT_SIZE_HUD = 24
FONT_SIZE_TITLE = 64