import pygame
import random
from pygame import mixer
from settings import *
from entities import Player, Bullet, Enemy
from fx import PostProcessor

class GameManager:
    def __init__(self):
        # Pygame Initialization
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.fx = PostProcessor()

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
        self.high_score = self.load_high_score()

        self.levels_per_difficulty = 50
        self.difficulty_step = 0.2

        self.hud_bullet = pygame.transform.scale_by(self.assets["bullet"], 0.75)
        self.hud_bullet_gray = self.hud_bullet.copy()
        self.hud_bullet_gray.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)

        # ---- State Machine
        self.state = "MENU" # MENU, PLAYING, PAUSED, GAME_OVER
        self.menu_options = ["DEFEND EARTH", "QUIT"]
        self.menu_index = 0

        self.reset_game_state_vars()

    def reset_game_state_vars(self):
        """Resets variables, but does not necessarily start the game logic immediately."""
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

        if self.state == "PLAYING":
            self.spawn_enemies()

    def start_new_game(self):
        """Called when selecting Start from menu or Restarting."""
        self.state = "PLAYING"
        self.reset_game_state_vars()
        self.load_high_score()

    def load_high_score(self):
        try:
            with open(self.high_score_file, "a+") as f:
                f.seek(0)
                content = f.read().strip()
                return int(content) if content else 0
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

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                # ---- Menu
                if self.state == "MENU":
                    if event.key == pygame.K_UP:
                        self.menu_index = (self.menu_index - 1) % len(self.menu_options)
                    elif event.key == pygame.K_DOWN:
                        self.menu_index = (self.menu_index + 1) % len(self.menu_options)
                    elif event.key == pygame.K_RETURN:
                        if self.menu_index == 0:  # Start
                            self.start_new_game()
                        elif self.menu_index == 1:  # Quit
                            return False

                # ---- PLAYING
                elif self.state == "PLAYING":
                    if event.key == pygame.K_ESCAPE: # or pygame.K_p:
                        self.state = "PAUSED"



                    elif event.key == pygame.K_SPACE and self.current_bullet_stock > 0:
                        self.bullets.add(Bullet(self.assets["bullet"], self.player.rect.centerx, self.player.rect.top))
                        self.bullet_sound.play()
                        self.current_bullet_stock -= 1

                # ---- PAUSED
                elif self.state == "PAUSED":
                    if event.key == pygame.K_ESCAPE: # or event.key == pygame.K_p:
                        self.state = "PLAYING"
                    elif event.key == pygame.K_q:
                        self.state = "MENU"

                # ---- GAME OVER
                elif self.state == 'GAME_OVER':
                    if event.key == pygame.K_r:
                        self.start_new_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "MENU"

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
                if self.state == "PLAYING" and self.freeze_timer <= 0:
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
                self.main_surface.blit(self.hud_bullet, (x, start_y))

            elif i == self.current_bullet_stock:
                # 2. This is the bullet currently RECHARGING
                # Draw the gray base first
                self.main_surface.blit(self.hud_bullet_gray, (x, start_y))

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
                self.main_surface.blit(self.hud_bullet, (x, start_y + (height - visible_height)), clip_rect)

            else:
                # 3. This bullet is empty and waiting its turn - Draw fully gray
                self.main_surface.blit(self.hud_bullet_gray, (x, start_y))

    def update_difficulty(self):
        """Speeds up the game after killing a certain amount of enemies"""
        self.speed_multiplier = 1.0 + (self.level - 1) * self.difficulty_step
        if self.level % 5 == 0:
            self.max_bullet_stock += 1
        print(f"Current Level: {self.level}")

    def trigger_shake(self, intensity, duration=0.5):
        self.fx.trigger_shake(intensity)
        self.freeze_timer = duration

    def draw_menu(self):
        """Draws the main menu on the main surface."""
        # Dim background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(100)
        overlay.fill((0, 0, 0))
        self.main_surface.blit(overlay, (0, 0))

        # Title
        title_surf = self.over_font.render(TITLE, True, CYAN)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.3))
        self.main_surface.blit(title_surf, title_rect)

        # Options
        for i, option in enumerate(self.menu_options):
            color = GOLD if i == self.menu_index else WHITE
            txt_surf = self.font.render(option, True, color)
            txt_rect = txt_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.5 + i * 60))

            if i == self.menu_index:
                # Draw a little cursor >
                cursor = self.font.render(">", True, RED)
                self.main_surface.blit(cursor, (txt_rect.left - 40, txt_rect.top))

            self.main_surface.blit(txt_surf, txt_rect)

        # ---- NEW CODE: High Score Display ----
        # Draw a separator line
        pygame.draw.line(self.main_surface, WHITE,
                       (SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT * 0.75),
                        (SCREEN_WIDTH / 2 + 100, SCREEN_HEIGHT * 0.75), 2)

        # Draw the score
        hi_score_surf = self.font.render(f"BEST: {self.high_score}", True, GOLD)
        hi_score_rect = hi_score_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.82))
        self.main_surface.blit(hi_score_surf, hi_score_rect)

    def draw_pause_overlay(self):
        """Draws pause text over the frozen game."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.main_surface.blit(overlay, (0, 0))

        txt_surf = self.over_font.render("PAUSED", True, WHITE)
        txt_rect = txt_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
        self.main_surface.blit(txt_surf, txt_rect)

        sub_surf = self.font.render("Press Q to Quit to Main Menu", True, GRAY_HUD)
        sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 60))
        self.main_surface.blit(sub_surf, sub_rect)

    def draw_ui_to_main(self):
        score_txt = self.font.render(f"Score : {self.score}", True, WHITE)
        level_txt = self.font.render(f"Level : {self.level}", True, WHITE)
        hi_txt = self.font.render(f"Best  : {self.high_score}", True, GOLD)

        self.main_surface.blit(score_txt, (10, 10))
        self.main_surface.blit(level_txt, (10, 50))
        self.main_surface.blit(hi_txt, (10, 90))

    def draw(self):

        # 1. Background (Always draw this so we don't get trails)
        self.main_surface.blit(self.assets['bg'], (0, 0))

        # 2. Game Elements (Draw if Playing, Paused, or Game Over)
        if self.state != "MENU":
            self.main_surface.blit(self.player.image, self.player.rect)
            self.enemies.draw(self.main_surface)
            self.bullets.draw(self.main_surface)

        # 3. State-Specific Overlays (Drawn to main_surface to get FX)
        if self.state == "MENU":
            self.draw_menu()

        elif self.state == "PAUSED":
            self.draw_pause_overlay()

        elif self.state == "GAME_OVER":
            # Game Over Overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            self.main_surface.blit(overlay, (0, 0))

            msg_surface = self.over_font.render("EARTH HAS FALLEN", True, (200, 200, 200))
            text_rect = msg_surface.get_rect()
            text_rect.center = (int(SCREEN_WIDTH / 2), int(SCREEN_HEIGHT / 2))
            self.main_surface.blit(msg_surface, text_rect)

            restart_surface = self.font.render("Press R to Retry", True, (200, 200, 200))
            restart_rect = restart_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.main_surface.blit(restart_surface, restart_rect)

        # self.fx.render(self.main_surface, self.screen)


        # Draw UI (On top of affects)
        if self.state == "PLAYING" or self.state == "PAUSED" or self.state == "GAME_OVER":
            self.draw_ui_to_main()

            if self.state != "GAME_OVER":
                self.draw_bullet_hud()


        fps_val = int(self.clock.get_fps())
        fps_txt = self.font.render(f"FPS: {fps_val}", True, (0, 255, 0))  # Green text for performance

        self.fx.render(self.main_surface, self.screen)
        self.screen.blit(fps_txt, (SCREEN_WIDTH - 250, 10)) # FPS Counter
        pygame.display.flip()

    def update(self, dt, keys):
        # Always update FX (so shake decays even if game over, or static flickers in menu)
        # Assuming you might want menu background animation later.

        if self.state == "PLAYING":
            # Logic when Game is Active
            if self.freeze_timer > 0:
                self.freeze_timer -= dt
                if self.freeze_timer <= 0 and any(e.rect.y > COLLISION_DISTANCE for e in self.enemies):
                    self.state = "GAME_OVER"
            else:
                self.player.update(dt, keys)
                self.bullets.update(dt)
                for enemy in self.enemies: enemy.update(self.speed_multiplier, dt)
                self.check_collisions()

                if self.current_bullet_stock < self.max_bullet_stock:
                    self.recharge_timer += dt
                    if self.recharge_timer >= self.bullet_recharge_time:
                        self.current_bullet_stock += 1
                        self.recharge_timer = 0.0

        elif self.state == "MENU":
            # You could add background rotation or floaty enemies here
            pass

        elif self.state == "PAUSED":
            # Game logic is frozen
            pass

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            keys = pygame.key.get_pressed()

            if not self.handle_events():
                self.running = False

            self.update(dt, keys)
            self.draw()

        pygame.quit()

if __name__ == "__main__":
    game = GameManager()
    game.run()



