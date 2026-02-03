import pygame
import random
from pygame import mixer
from settings import *
from entities import Player, Bullet, Enemy

class GameManager:
    def __init__(self):
        # Pygame Initialization
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # ---- Assets ----
        self.main_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.assets = {
            "player": pygame.image.load(get_path("assets/spaceship_2.png",)).convert_alpha(),
            "enemy": pygame.image.load(get_path("assets/invadership.png",)).convert_alpha(),
            "bullet": pygame.image.load(get_path("assets/spaceMissile.png",)).convert_alpha(),
            "bg": pygame.image.load(get_path("assets/earth_background.png")).convert()
        }

        # ---- Audio ----
        self.bullet_sound = mixer.Sound(get_path("assets/audio/firing_sound.wav"))
        self.explosion_sound = mixer.Sound(get_path("assets/audio/explosion_sound.wav"))

        # ---- Music ----
        mixer.music.load(get_path("assets/audio/background_music.wav"))
        mixer.music.play(-1)

        # ---- Font ----
        self.font = pygame.font.Font("assets/font/PressStart2P-Regular.ttf", 32)
        self.over_font = pygame.font.Font("assets/font/PressStart2P-Regular.ttf", 45)

        # ---- Load Score ----
        self.high_score_file = get_path("highscore.txt")

        # ---- Post Processing Effects ----
        self.crt_texture = self.create_crt_lines()
        self.vignette = self.create_vignette()

        self.high_score = self.load_high_score()

        self.levels_per_difficulty = 50
        self.difficulty_step = 0.2

        self.hud_bullet = pygame.transform.scale_by(self.assets["bullet"], 0.75)
        self.hud_bullet_gray = self.hud_bullet.copy()
        self.hud_bullet_gray.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)

        self.reset_game()

    def reset_game(self):
        self.game_over = False
        self.score = 0
        self.level = 1
        self.speed_multiplier = 1.0

        self.max_bullet_stock = 3
        self.current_bullet_stock = 3
        self.bullet_recharge_time = 1.0  # Seconds per bullet
        self.recharge_timer = 0.0

        self.freeze_timer = 0.0
        self.shake_intensity = 0
        self.shake_decay = 0.9  # How fast the shake stops (0 to 1)

        # ---- Create Entities ----
        self.bullets = pygame.sprite.Group()
        self.player = Player(self.assets["player"])
        self.enemies = pygame.sprite.Group()

        self.spawn_enemies()
        self.load_high_score()

    def load_high_score(self):
        try:
            with open(self.high_score_file, "a+") as f:
                f.seek(0)
                content = f.read().strip()
                return int(content)
        except (FileNotFoundError, ValueError):
            return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            with open(self.high_score_file, "w") as f:
                f.write(str(self.high_score))

    def spawn_enemies(self):
        self.enemies.empty()
        self.update_difficulty()
        for _ in range(5 + self.level):
            x = random.randint(50, SCREEN_WIDTH - 100)
            y = random.randint(ENEMY_SPAWN_Y_MIN, ENEMY_SPAWN_Y_MAX)
            self.enemies.add(Enemy(self.assets["enemy"], x, y))

    def trigger_shake(self, intensity, duration= .5):
        self.shake_intensity = intensity
        self.freeze_timer = duration

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.game_over and self.current_bullet_stock > 0:
                    self.bullets.add(Bullet(self.assets["bullet"], self.player.rect.centerx, self.player.rect.top))
                    self.bullet_sound.play()
                    self.current_bullet_stock -= 1

                if self.game_over and event.key == pygame.K_r:
                    self.reset_game()

        return True

    def check_collisions(self):
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True, pygame.sprite.collide_mask)
        for hit in hits:
            self.score += 10
            self.explosion_sound.play()
            if not self.enemies:
                self.level += 1
                self.speed_multiplier += 0.2
                self.spawn_enemies()

        for enemy in self.enemies:
            if enemy.rect.y > COLLISION_DISTANCE:
                if not self.game_over and self.freeze_timer <= 0:
                    self.trigger_shake(30, 1.0)
                    self.save_high_score()
                break

    def draw_bullet_hud(self):
        start_x = 10
        start_y = SCREEN_HEIGHT * .92
        spacing = 30

        for i in range(self.max_bullet_stock):
            x = start_x + (i * spacing)

            if i < self.current_bullet_stock:
                # 1. We have this bullet - Draw normally
                self.screen.blit(self.hud_bullet, (x, start_y))

            elif i == self.current_bullet_stock:
                # 2. This is the bullet currently RECHARGING
                # Draw the gray base first
                self.screen.blit(self.hud_bullet_gray, (x, start_y))

                # Calculate how much of the "color" bullet to show from the bottom
                # progress is 0.0 to 1.0
                progress = self.recharge_timer / self.bullet_recharge_time

                height = self.hud_bullet.get_height()
                visible_height = int(height * progress)

                # Create a clipping rect for the "filled" part
                # Area: (left, top, width, height)
                # We want to show the bottom part of the sprite
                clip_rect = pygame.Rect(0, height - visible_height, self.hud_bullet.get_width(), visible_height)

                # Blit the colored bullet using the area parameter to only show the bottom
                self.screen.blit(self.hud_bullet, (x, start_y + (height - visible_height)), clip_rect)

            else:
                # 3. This bullet is empty and waiting its turn - Draw fully gray
                self.screen.blit(self.hud_bullet_gray, (x, start_y))

    def update_difficulty(self):
        """Speeds up the game after killing a certain amount of enemies"""
        self.speed_multiplier = 1.0 + (self.level - 1) * self.difficulty_step
        if self.level % 5 == 0:
            self.max_bullet_stock += 1
        print(f"Current Level: {self.level}")

    @staticmethod
    def create_crt_lines():
        crt_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        line_color = (10, 10, 10, 80)

        for y in range(0, SCREEN_HEIGHT, 3):
            pygame.draw.line(crt_surface, line_color, (0, y), (SCREEN_WIDTH, y))

        return crt_surface

    @staticmethod
    def create_vignette():
        vignette_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        for i in range(0,100,10):
            alpha = 150 - (i * 1.5)
            pygame.draw.rect(vignette_surface, (0, 0, 0, alpha),
                             vignette_surface.get_rect().inflate(-i*1.5, -i*1.5), 25, border_radius=10)

        return vignette_surface

    def draw(self):

        shake_offset_x, shake_offset_y = 0, 0

        if self.shake_intensity > 0.1:
            shake_offset_x = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
            shake_offset_y = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
            self.shake_intensity *= self.shake_decay
            if self.shake_intensity <= 0: self.shake_intensity = 0

        self.main_surface.blit(self.assets['bg'], (shake_offset_x, shake_offset_y))

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

        self.screen.fill((0, 0, 0))

        # Brighten Screen
        #brighten = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        #brighten.fill((25, 25, 25))  # Adjust these numbers to change brightness
        #self.main_surface.blit(brighten, (0 + shake_offset_x, 0 + shake_offset_y), special_flags=pygame.BLEND_RGB_ADD)

        # Chromatic Aberration
        self.screen.blit(self.main_surface, (-2 + shake_offset_x, 0 + shake_offset_y), special_flags=pygame.BLEND_RGB_ADD)
        self.screen.blit(self.main_surface, (2 + shake_offset_x, 0 + shake_offset_y), special_flags=pygame.BLEND_RGB_ADD)
        self.screen.blit(self.main_surface, (0 + shake_offset_x, 0 + shake_offset_y), special_flags=pygame.BLEND_RGB_MULT)

        # Post Processing Effects
        self.screen.blit(self.vignette, (0, 0))
        self.screen.blit(self.crt_texture, (0, 0))

        # Draw UI (On top of affects)
        score_txt = self.font.render(f"Score : {self.score}", True, (255, 255, 255))
        level_txt = self.font.render(f"Level : {self.level}", True, (255, 255, 255))
        hi_txt = self.font.render(f"Best  : {self.high_score}", True, (255, 215, 0))
        fps_val = int(self.clock.get_fps())
        fps_txt = self.font.render(f"FPS: {fps_val}", True, (0, 255, 0))  # Green text for performance
        self.screen.blit(fps_txt, (SCREEN_WIDTH - 250, 10))
        self.screen.blit(score_txt, (10, 10))
        self.screen.blit(level_txt, (10, 50))
        self.screen.blit(hi_txt, (10, 90))

        self.draw_bullet_hud()

        pygame.display.flip()

    def update(self, dt, keys):
        if self.freeze_timer > 0:
            self.freeze_timer -= dt
            if self.freeze_timer <= 0 and any(e.rect.y > COLLISION_DISTANCE for e in self.enemies):
                self.game_over = True
        else:
            if not self.game_over:
                self.player.update(dt, keys)
                self.bullets.update(dt)
                for enemy in self.enemies: enemy.update(self.speed_multiplier, dt)
                self.check_collisions()

                if self.current_bullet_stock < self.max_bullet_stock:
                    self.recharge_timer += dt
                    if self.recharge_timer >= self.bullet_recharge_time:
                        self.current_bullet_stock += 1
                        self.recharge_timer = 0.0  # Reset timer for the next bullet

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            keys = pygame.key.get_pressed()

            self.running = self.handle_events()
            self.update(dt, keys)
            self.draw()

        pygame.quit()

if __name__ == "__main__":
    game = GameManager()
    game.run()



