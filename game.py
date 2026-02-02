import pygame
import random
import math
import os
import sys
from pygame import mixer

#-------- Configuration
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
PLAYER_START = (SCREEN_WIDTH / 2, SCREEN_HEIGHT * .85)
ENEMY_SPAWN_Y_RANGE = (20, 250)
COLLISION_DISTANCE = int(SCREEN_HEIGHT * .75)
FPS = 60
#-------- Asset Handling
BASE_PATH = os.path.abspath(os.path.dirname(__file__))



def get_path(filename):
    return os.path.join(BASE_PATH, filename)

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
        self.rect.y -= self.speed * dt
        if self.rect.y < -32:
            self.kill()

class Player(Entity):
    def __init__(self, surface):
        super().__init__(surface, PLAYER_START[0], PLAYER_START[1], 2)

        self.pos_x = float(PLAYER_START[0])
        self.pos_y = float(PLAYER_START[1])

        # 3. Sync the rect one last time
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        self.speed = 500.0
        self.velocity = 0.0

    def move(self, direction):
        self.velocity = direction * self.speed

    def update(self, dt):
        # Position = Speed * Time
        self.pos_x += self.velocity * dt
        self.rect.x = int(self.pos_x)  # Sync rect to the float position

        # Keep player on screen
        if self.rect.x < 0:
            self.rect.x = 0
            self.pos_x = 0.0
        elif self.rect.x > SCREEN_WIDTH - self.rect.width:
            self.rect.x = SCREEN_WIDTH - self.rect.width
            self.pos_x = float(self.rect.x)

class Enemy(Entity):
    def __init__(self, surface, x, y):
        super().__init__(surface,
                         x,
                         y,
                         2)

        self.image = pygame.transform.flip(self.image, False, True)

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

class GameManager:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.main_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Earth Invaders")


        self.background = pygame.image.load(get_path("assets/earth_background.png")).convert()
        self.bullet_sound = mixer.Sound(get_path("assets/audio/firing_sound"))
        self.explosion_sound = mixer.Sound(get_path("assets/audio/explosion_sound"))

        self.font = pygame.font.SysFont("pressstart2p", 32)
        self.over_font = pygame.font.SysFont("pressstart2p", 45)

        mixer.music.load(get_path("assets/audio/background_music.wav"))
        mixer.music.play(-1)

        self.assets = {}
        self.preload_assets()

        self.crt_texture = self.create_crt_lines()
        self.vignette = self.create_vignette()

        self.clock = pygame.time.Clock()
        self.score = 0
        self.game_over = False

        self.player = Player(self.assets["player"])

        self.enemies = pygame.sprite.Group()

        for _ in range(6):
            # Pass the group so the new enemy can check for neighbors
            safe_x, safe_y = self.create_safe_spawn(self.enemies, 64, 64)

            new_enemy = Enemy(self.assets["enemy"], safe_x, safe_y)
            self.enemies.add(new_enemy)

        self.bullets = pygame.sprite.Group()

        self.high_score_file = get_path("highscore.txt")
        self.high_score = self.load_high_score()
        self.level = 1
        self.difficulty_multiplier = 1.0

    def preload_assets(self):
        """Load images once and store them in a dictionary."""
        asset_files = {
            "player": "assets/spaceship_2.png",
            "enemy": "assets/invadership.png",
            "bullet": "assets/spaceMissile.png"
        }

        for name, path in asset_files.items():
            # Load, convert, and store
            surface = pygame.image.load(get_path(path)).convert_alpha()

            # If you want to keep your bounding_rect logic from the original Entity class:
            actual_area = surface.get_bounding_rect()
            self.assets[name] = surface.subsurface(actual_area)

    def update_difficulty(self):
        new_level = (self.score // 10) + 1
        if new_level > self.level:
            self.level = new_level

            self.difficulty_multiplier = 1.0 + (self.level - 1) * 0.2
            print(f"Level Up! Current Level: {self.level}")

    def load_high_score(self):
        try:
            with open(self.high_score_file, "r") as f:
                return int(f.read())
        except (FileNotFoundError, ValueError):
            return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            with open(self.high_score_file, "w") as f:
                f.write(str(self.high_score))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if self.game_over and event.key == pygame.K_r:
                    self.reset_game()

            if not self.game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT: self.player.move(-1)
                    if event.key == pygame.K_RIGHT: self.player.move(1)
                    if event.key == pygame.K_SPACE:
                        if len(self.bullets) < 3:
                            self.bullets.add(Bullet(self.assets["bullet"], self.player.rect.centerx, self.player.rect.top))
                            self.bullet_sound.play()

                if event.type == pygame.KEYUP:
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        self.player.move(0)
        return True

    def check_collisions(self):
        for enemy in self.enemies:
            collided_bullets = pygame.sprite.spritecollide(enemy, self.bullets, True, pygame.sprite.collide_mask)
            if collided_bullets:
                self.explosion_sound.play()
                self.score += 1

                # Find a NEW safe spot for the respawn
                nx, ny = self.create_safe_spawn(self.enemies, enemy.rect.width, enemy.rect.height)

                # Reset the enemy with these new coordinates
                enemy.reset(nx, ny)

            if enemy.rect.y > COLLISION_DISTANCE:
                self.game_over = True
                self.save_high_score()
                break

    def reset_game(self):
        self.score = 0
        self.level = 1
        self.difficulty_multiplier = 1.0
        self.game_over = False

        self.enemies.empty()
        self.bullets.empty()

        self.player = Player(self.assets["player"])
        self.enemies = pygame.sprite.Group()

        for _ in range(6):
            # Pass the group so the new enemy can check for neighbors
            safe_x, safe_y = self.create_safe_spawn(self.enemies, 64, 64)

            new_enemy = Enemy(self.assets["enemy"], safe_x, safe_y)
            self.enemies.add(new_enemy)


    def create_crt_lines(self):
        crt_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        line_color = (10, 10, 10, 80)

        for y in range(0, SCREEN_HEIGHT, 3):
            pygame.draw.line(crt_surface, line_color, (0, y), (SCREEN_WIDTH, y))

        return crt_surface

    def create_vignette(self):
        vignette_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        for i in range(0,100,10):
            alpha = 150 - (i * 1.5)
            pygame.draw.rect(vignette_surface, (0, 0, 0, alpha),
                             vignette_surface.get_rect().inflate(-i*1.5, -i*1.5), 25, border_radius=10)

        return vignette_surface

    def create_safe_spawn(self, existing_enemies, width, height):
        max_attempts = 50
        for _ in range(max_attempts):
            rx = random.randint(0, SCREEN_WIDTH - width)
            ry = random.randint(*ENEMY_SPAWN_Y_RANGE)

            candidate_rect = pygame.Rect(rx, ry, width, height)

            overlap = False
            for enemy in existing_enemies:
                if candidate_rect.colliderect(enemy.rect):
                    overlap = True
                    break

            if not overlap:
                return rx, ry

        return random.randint(0, SCREEN_WIDTH - width), random.randint(*ENEMY_SPAWN_Y_RANGE)


    def draw(self):

        self.main_surface.blit(self.background, (0, 0))

        brighten = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        brighten.fill((25, 25, 25))  # Adjust these numbers to change brightness
        self.main_surface.blit(brighten, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        #self.screen.blit(self.background, (0, 0))

        if random.randint(0, 100) > 90:
            flicker = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flicker.set_alpha(random.randint(5,12))
            flicker.fill((150, 150, 150))
            self.screen.blit(flicker, (0, 0))

        if not self.game_over:
            self.main_surface.blit(self.player.image, self.player.rect)
            self.enemies.draw(self.main_surface)
            self.bullets.draw(self.main_surface)

        if self.game_over:
            # Game Over Overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            self.main_surface.blit(overlay, (0, 0))

            msg_surface = self.over_font.render("EARTH HAS FALLEN", True, (200, 200, 200))
            text_rect = msg_surface.get_rect()
            text_rect.center = (int(SCREEN_WIDTH / 2), int(SCREEN_HEIGHT / 2))
            self.main_surface.blit(msg_surface, text_rect)

            restart_surface = self.font.render("Press R to try again", True, (200, 200, 200))
            restart_rect = restart_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.main_surface.blit(restart_surface, restart_rect)

        self.screen.fill((0,0,0))
        self.screen.blit(self.main_surface, (-2, 0), special_flags=pygame.BLEND_RGB_ADD)
        self.screen.blit(self.main_surface, (2, 0), special_flags=pygame.BLEND_RGB_ADD)
        self.screen.blit(self.main_surface, (0, 0), special_flags=pygame.BLEND_RGB_MULT)




        self.screen.blit(self.vignette, (0, 0))
        self.screen.blit(self.crt_texture, (0, 0))


        score_txt = self.font.render(f"Score : {self.score}", True, (255, 255, 255))
        level_txt = self.font.render(f"Level : {self.level}", True, (255, 255, 255))
        hi_txt = self.font.render(f"Best  : {self.high_score}", True, (255, 215, 0))
        self.screen.blit(score_txt, (10, 10))
        self.screen.blit(level_txt, (10, 50))
        self.screen.blit(hi_txt, (10, 90))

        fps_val = int(self.clock.get_fps())
        fps_txt = self.font.render(f"FPS: {fps_val}", True, (0, 255, 0))  # Green text for performance
        self.screen.blit(fps_txt, (SCREEN_WIDTH - 250, 10))


        pygame.display.update()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            running = self.handle_events()
            if not self.game_over:
                self.update_difficulty()
                self.player.update(dt)
                self.enemies.update(self.difficulty_multiplier, dt)

                self.bullets.update(dt)
                self.check_collisions()

            self.draw()
        pygame.quit()

if __name__ == "__main__":
    game = GameManager()
    game.run()



