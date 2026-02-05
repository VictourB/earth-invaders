import pygame
import math
from settings import *

class Entity(pygame.sprite.Sprite):
    def __init__(self, surface, x, y, scaling_factor=1.0):
        super().__init__()
        self.image = surface

        if scaling_factor != 1.0:
            self.image = pygame.transform.scale_by(self.image, scaling_factor)

        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()

        self.pos_x = float(x)
        self.pos_y = float(y)

        self.rect.topleft = (int(self.pos_x), int(self.pos_y))

        # Sync rect
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

class Bullet(Entity):
    def __init__(self, surface, x, y):
        super().__init__(surface, x, y, scaling_factor=.5)

        self.rect.centerx = x
        self.rect.bottom = y + 25

        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)

        self.speed = 700.0

    def update(self, dt):
        self.pos_y -= self.speed * dt
        self.rect.y -= self.speed * dt
        if self.rect.y < -32:
            self.kill()

class Player(Entity):
    def __init__(self, surface):
        super().__init__(surface, PLAYER_START_X, PLAYER_START_Y, 2)
        self.original_image = pygame.transform.scale_by(surface, 2)

        self.accel = PLAYER_ACCEL
        self.friction = PLAYER_FRICTION
        self.max_speed = PLAYER_MAX_SPEED
        self.velocity = 0.0

    def move(self, dt):
        # Speed Cap
        if abs(self.velocity) > self.max_speed:
            self.velocity = math.copysign(self.max_speed, self.velocity)

        # Apply Velocity
        self.pos_x += self.velocity * dt

        # 5. Boundary Check
        if self.pos_x < 0:
            self.pos_x = 0
            self.velocity = 0
        elif self.pos_x > SCREEN_WIDTH - self.rect.width:
            self.pos_x = SCREEN_WIDTH - self.rect.width
            self.velocity = 0

        # Tilt
        tilt_angle = -(self.velocity / self.max_speed) * 15
        self.image = pygame.transform.rotate(self.original_image, tilt_angle)

        # Hitbox update
        self.rect = self.image.get_rect(center=self.rect.center)
        self.rect.x = int(self.pos_x)

    def handle_input(self, keys):
        # Handle Input
        if keys[pygame.K_LEFT]:
            self.velocity -= self.accel
        elif keys[pygame.K_RIGHT]:
            self.velocity += self.accel
        else:
            # Friction (linear lerp)
            if self.velocity > 0:
                self.velocity = max(0, self.velocity - self.accel * self.friction)
            if self.velocity < 0:
                self.velocity = min(0, self.velocity + self.accel * self.friction)

    def update(self, dt, keys):
        self.handle_input(keys)
        self.move(dt)

class Enemy(Entity):
    def __init__(self, surface, x, y):
        super().__init__(surface, x, y, 2)

        self.image = pygame.transform.flip(self.image, False, True)

        # Override initial positions from super
        self.pos_x = float(x)
        self.pos_y = float(y)

        self.base_vx = 300.0
        self.vx = float(self.base_vx)
        self.vy  = 32.0

    def update(self, speed_multiplier, dt):
        current_speed = self.base_vx * float(speed_multiplier)

        direction = 1.0 if self.vx > 0 else -1.0
        self.vx = current_speed * direction

        self.pos_x += self.vx * dt

        # Boundary Checks
        if self.pos_x <= 0:
            self.pos_x = 0.0
            self.vx = abs(self.vx)
            self.pos_y += self.vy
        elif self.pos_x >= float(SCREEN_WIDTH - self.rect.width):
            self.pos_x = float(SCREEN_WIDTH - self.rect.width)
            self.vx = -abs(self.vx)
            self.pos_y += self.vy

        self.rect.x = round(self.pos_x)
        self.rect.y = round(self.pos_y)

    def reset(self, x, y):
        # 2. Update the Floats
        self.pos_x = float(x)
        self.pos_y = float(y)

        # 3. Update the Rect
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)