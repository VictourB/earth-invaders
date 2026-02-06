import pygame
import random
import math
from pygame import mixer
from settings import *
from entities import Player, Bullet, Enemy, ShooterEnemy, Particle, UFO
from fx import PostProcessor
from audio import AudioManager

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
            "enemy_shooter": pygame.image.load(get_path("assets/invadership_shooter.png")).convert_alpha(),
            "bullet": pygame.image.load(get_path("assets/spaceMissile.png",)).convert_alpha(),
            "ufo": pygame.image.load(get_path("assets/ufo.png")).convert_alpha(),
            "bg": pygame.image.load(get_path("assets/earth_background_transparent.png")).convert_alpha()
        }

        # ---- Music and Audio ----
        self.audio = AudioManager(self.assets)
        self.audio.play_music("menu")

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

        # ---- Parallax Setup ----
        self.star_layers = []
        # Create 3 layers of stars with different densities and speeds
        for i in range(3):
            layer_stars = []
            num_stars = 50 // (i + 1)
            for _ in range(num_stars):
                # Random (x, y)
                star_x = random.randint(0, SCREEN_WIDTH)
                star_y = random.randint(0, SCREEN_HEIGHT)
                layer_stars.append([star_x, star_y])

            # Speed: further stars (index 2) move slower
            speed = 20.0 * (i + 1)
            self.star_layers.append(
                {"stars": layer_stars, "speed": speed, "color": (150, 150, 150) if i == 0 else WHITE})

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
        self.enemy_bullets = pygame.sprite.Group()
        self.player = Player(self.assets["player"])
        self.enemies = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()

        self.ufo_group = pygame.sprite.GroupSingle()  # Use GroupSingle because there's usually only one UFO
        self.ufo_spawn_timer = random.uniform(10.0, 20.0)  # Seconds until next UFO

        if self.state == "PLAYING":
            self.spawn_enemies()
            pass

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

    def create_explosion(self, x, y, color, count=20):
        for _ in range(count):
            self.particles.add(Particle(x, y, color))

    def spawn_enemies(self):
        self.enemies.empty()
        self.enemy_bullets.empty()
        self.update_difficulty()

        for _ in range(5 + self.level):
            x = random.randint(50, SCREEN_WIDTH - 100)
            y = random.randint(ENEMY_SPAWN_Y_MIN, ENEMY_SPAWN_Y_MAX)

            if self.level >= 5 and random.random() < 0.3:
                self.enemies.add(ShooterEnemy(self.assets["enemy_shooter"], x, y, self.assets["bullet"]))
            else:
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
                    if event.key == pygame.K_EQUALS:
                        self.level += 1
                        self.spawn_enemies()
                        print(f"DEBUG: Advanced to Level {self.level}")



                    elif event.key == pygame.K_SPACE and self.current_bullet_stock > 0:
                        self.bullets.add(Bullet(self.assets["bullet"], self.player.rect.centerx, self.player.rect.top))
                        self.audio.play_sfx("shoot")
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

        # Player's Bullets -> Enemies
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True, pygame.sprite.collide_mask)
        for hit in hits:
            self.score += hit.points
            self.audio.play_sfx("explosion")
            self.create_explosion(hit.rect.centerx, hit.rect.centery, GOLD, count=15)
            if not self.enemies:
                self.level += 1
                self.spawn_enemies()

        # Enemy Bullets -> Player
        if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True, pygame.sprite.collide_mask):
            self.player_death_sequence()

        for enemy in self.enemies:
            if enemy.rect.bottom >= COLLISION_DISTANCE:
                if self.state == "PLAYING" and self.freeze_timer <= 0:
                    self.player_death_sequence()
                break

        # Player Bullets vs UFO
        ufo_hit = pygame.sprite.groupcollide(self.ufo_group, self.bullets, True, True,
                                                     pygame.sprite.collide_mask)
        for hit in ufo_hit:
            self.audio.stop_sfx("ufo")
            self.score += hit.points
            self.audio.play_sfx("explosion")
            self.create_explosion(hit.rect.centerx, hit.rect.centery, GOLD, count=30)
            # Maybe trigger a unique screen shake for the UFO?
            self.fx.trigger_shake(15, 0.3)

    def player_death_sequence(self):
        self.audio.set_volume(0.2)  # Lower background music
        self.audio.play_sfx("explosion")
        # After a delay, switch to game over music
        self.create_explosion(self.player.rect.centerx, self.player.rect.centery, RED, count=50)
        self.trigger_shake(50, 2.0)  # Big shake
        self.state = "GAME_OVER"
        self.save_high_score()

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

    def update_background(self, dt):
        for layer in self.star_layers:
            for star in layer["stars"]:
                # Move star downward
                star[1] += layer["speed"] * dt

                # Wrap around if it leaves the bottom
                if star[1] > SCREEN_HEIGHT:
                    star[1] = 0
                    star[0] = random.randint(0, SCREEN_WIDTH)

    def update_difficulty(self):
        """Speeds up the game after killing a certain amount of enemies"""
        self.speed_multiplier += 0.2
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

    def draw_parallax(self):
        # 1. Draw static earth background first
        self.main_surface.blit(self.assets["bg"], (0, 0))

        # 2. Draw moving star layers
        for i, layer in enumerate(self.star_layers):
            # i=0 is furthest, i=2 is closest
            size = i + 1
            for star in layer["stars"]:
                pygame.draw.rect(self.main_surface, layer["color"], (star[0], star[1], size, size))

        # 3. Draw the Earth background OVER the stars
        # Because the PNG has transparency, the stars will only show through the "holes"
        self.main_surface.blit(self.assets["bg"], (0, 0))

    def draw_danger_zone(self):
        # Create a flicker effect using the current time
        # This oscillates between 50 and 150 alpha for a pulsing "warning" look

        # Pulse speed increases if enemies are very close
        proximity_warning = any(e.rect.bottom > COLLISION_DISTANCE - 125 for e in self.enemies)
        pulse_speed = 0.02 if proximity_warning else 0.01

        flicker = int(100 + math.sin(pygame.time.get_ticks() * 0.01) * 50)

        # 2. The Warning Zone (Transparent red floor)
        warning_floor = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - COLLISION_DISTANCE))
        warning_floor.set_alpha(flicker // 4)  # Very faint
        warning_floor.fill((200, 0, 0))
        self.main_surface.blit(warning_floor, (0, COLLISION_DISTANCE))

        # 3. Text Alert
        if proximity_warning:
            msg = "CAUTION: BREACH IMMINENT" if any(
                e.rect.bottom > COLLISION_DISTANCE - 50 for e in self.enemies) else "!!! ENEMY PROXIMITY !!!"
            warn_txt = self.font.render(msg, True, (255, flicker, flicker))
            self.main_surface.blit(warn_txt, (SCREEN_WIDTH // 2 - warn_txt.get_width() // 2, SCREEN_HEIGHT - 34))


        # Create a temporary surface for transparency
        danger_surf = pygame.Surface((SCREEN_WIDTH, 2))
        danger_surf.set_alpha(flicker)
        danger_surf.fill(DANGER_COLOR)

        # Draw the line
        self.main_surface.blit(danger_surf, (0, COLLISION_DISTANCE))

    def draw(self):

        self.main_surface.fill(SPACE_COLOR)
        # 1. Background (Always draw this so we don't get trails)
        #self.main_surface.blit(self.assets['bg'], (0, 0))

        self.draw_parallax()

        # 2. Game Elements (Draw if Playing, Paused, or Game Over)
        if self.state != "MENU":
            self.particles.draw(self.main_surface)
            self.main_surface.blit(self.player.image, self.player.rect)
            self.enemies.draw(self.main_surface)
            self.bullets.draw(self.main_surface)
            self.enemy_bullets.draw(self.main_surface)
            self.ufo_group.draw(self.main_surface)

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
            self.draw_danger_zone()
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
        self.update_background(dt)

        if self.state == "PLAYING":
            # Logic when Game is Active
            self.audio.play_music("playing")
            if self.freeze_timer > 0:
                self.freeze_timer -= dt
                if self.freeze_timer <= 0 and any(e.rect.y > COLLISION_DISTANCE for e in self.enemies):
                    self.state = "GAME_OVER"
            else:
                self.player.update(dt, keys)
                self.bullets.update(dt)
                self.enemy_bullets.update(dt)

                for enemy in self.enemies:
                    if hasattr(enemy, "fire"):
                        enemy.update(self.speed_multiplier, dt, self.enemy_bullets)
                    else:
                        enemy.update(self.speed_multiplier, dt)

                self.check_collisions()

                if self.current_bullet_stock < self.max_bullet_stock:
                    self.recharge_timer += dt
                    if self.recharge_timer >= self.bullet_recharge_time:
                        self.current_bullet_stock += 1
                        self.recharge_timer = 0.0

            self.particles.update(dt)

            # ENGINE EXHAUST LOGIC
            # Spawn small blue/white particles at the back of the player
            if random.random() > 0.5:  # Don't spawn every frame to save performance
                exhaust_x = self.player.rect.centerx + random.randint(-5, 5)
                exhaust_y = self.player.rect.bottom - 10
                # Give exhaust a downward velocity
                self.particles.add(Particle(
                    exhaust_x, exhaust_y, CYAN,
                    velocity=(random.uniform(-20, 20), random.uniform(100, 200)),
                    lifetime=0.3, size=3
                ))

            # ---- Spawn UFO
            if not self.ufo_group:  # Only spawn if one isn't already there
                self.ufo_spawn_timer -= dt
                if self.ufo_spawn_timer <= 0:
                    self.audio.play_sfx("ufo", loops=-1)
                    side = random.choice(["left", "right"])
                    self.ufo_group.add(UFO(self.assets["ufo"], side))
                    self.ufo_spawn_timer = random.uniform(15.0, 30.0)
            else:
                self.ufo_group.update(dt)
                if not self.ufo_group:
                    self.audio.stop_sfx("ufo")


        elif self.state == "MENU":
            # You could add background rotation or floaty enemies here
            self.audio.play_music("menu")
            pass

        elif self.state == "PAUSED":
            # Game logic is frozen
            self.audio.play_music("menu")
            pass

        elif self.state == "GAME_OVER":
            self.audio.play_music("game_over")
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



