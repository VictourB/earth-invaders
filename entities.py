import random

import pygame
import math

from pygame.transform import scale_by

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
    def __init__(self, surface, x, y, direction = -1):
        """direction: -1 for UP, 1 for down"""
        super().__init__(surface, x, y, scaling_factor=.5)

        self.rect.centerx = x
        if direction == -1:
            self.rect.bottom = y + 25
        else:
            self.rect.top = y

        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)

        self.speed = 700.0
        self.direction = direction

    def update(self, dt):
        self.pos_y += (self.speed * self.direction) * dt
        self.rect.y = int(self.pos_y)
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
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
    def __init__(self, surface, x, y, points=ENEMY_POINTS_NORMAL):
        super().__init__(surface, x, y, 2)

        self.image = pygame.transform.flip(self.image, False, True)
        self.points = points

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

class ShooterEnemy(Enemy):
    def __init__(self, surface, x, y, bullet_img):
        super().__init__(surface, x, y, points=ENEMY_POINTS_SHOOTER)
        self.bullet_img = bullet_img

        # ---- Shooting Setup
        self.shoot_timer = random.uniform(0.5, 2.0)
        self.shoot_interval = 2.5

    def update(self, speed_multiplier, dt, bullet_group):
        super().update(speed_multiplier, dt)

        self.shoot_timer -= dt
        if self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_interval + random.uniform(-0.5, 0.5)
            self.fire(bullet_group)

    def fire(self, bullet_group):
        b = Bullet(self.bullet_img, self.rect.centerx, self.rect.bottom, direction=1)
        bullet_group.add(b)

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y ,color, velocity=None, lifetime=0.5, size=8):
        super().__init__()
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))

        self.pos_x = float(x)
        self.pos_y = float(y)

        self.size = size
        self.color = color

        if velocity:
            self.vel_x, self.vel_y = velocity
        else:
            self.vel_x = random.uniform(-150, 150)
            self.vel_y = random.uniform(-150, 150)

        self.max_lifetime = lifetime
        self.lifetime = lifetime

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return

        # Move
        self.pos_x += self.vel_x * dt
        self.pos_y += self.vel_y * dt

        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        # Shrink over time: start at original size and go to 0
        current_size = max(1, int(self.size * (self.lifetime / self.max_lifetime)))
        self.image = pygame.Surface((current_size, current_size))
        self.image.fill(self.color)  # You'll need to store self.color and self.size in __init__

class UFO(Entity):
    def __init__(self, surface, side="left"):
        # side: "left" starts at x=0, moves right. "right" starts at x=width, moves left.
        y = 30
        x = -64 if side =='left' else SCREEN_WIDTH + 64
        super().__init__(surface, x, y, scaling_factor=2.0)

        self.points = random.choice([100, 200, 500])
        self.speed = 250.0
        self.direction = 1 if side == 'left' else -1

    def update(self, dt):
        self.pos_x += (self.speed * self.direction) * dt
        self.rect.x = int(self.pos_x)

        if (self.direction == 1 and self.rect.left > SCREEN_WIDTH) or (self.direction == -1 and self.rect.right < 0):
            self.kill()

