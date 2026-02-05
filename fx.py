import pygame
import random
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

class PostProcessor:
    def __init__(self):

        self.crt_texture = self._create_crt_lines()
        self.vignette = self._create_vignette()

        # Shake state
        self.shake_intensity = 0
        self.shake_decay = 0.9

    def trigger_shake(self, intensity, duration=.5):
        """Public method to start a screen shake."""
        self.shake_intensity = intensity
        #self.freeze_timer = duration

    def apply_chromatic_aberration(self, surface, offset):
        # Move your existing RGB split logic here
        self.screen.blit(surface, (-2 + offset[0], 0 + offset[1]),
                         special_flags=pygame.BLEND_RGB_ADD)
        self.screen.blit(self.overlay, (2 + offset[0], 0 + offset[1]),
                         special_flags=pygame.BLEND_RGB_ADD)
        self.screen.blit(self.overlay, (0 + offset[0], 0 + offset[1]),
                         special_flags=pygame.BLEND_RGB_MULT)

        pass

    def _create_crt_lines(self):
        """Internal helper to build the scanline texture."""
        crt_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        line_color = (10, 10, 10, 80)

        for y in range(0, SCREEN_HEIGHT, 3):
            pygame.draw.line(crt_surface, line_color, (0, y), (SCREEN_WIDTH, y))

        return crt_surface

    def _create_vignette(self):
        """Internal helper to build the vignette shadow."""
        vignette_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        for i in range(0, 100, 10):
            alpha = 150 - (i * 1.5)
            pygame.draw.rect(vignette_surface, (0, 0, 0, alpha),
                             vignette_surface.get_rect().inflate(-i * 1.5, -i * 1.5), 25, border_radius=10)

        return vignette_surface

    def render(self, game_surface, final_screen):
        """
                Applies all effects to the game_surface and blits to final_screen.

                Args:
                    game_surface: The clean surface containing player/enemies/bg.
                    final_screen: The actual Pygame display surface.
                """
        # 1. Calculate Shake Offsets
        shake_x, shake_y = 0, 0
        if self.shake_intensity > 0.1:
            shake_x = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
            shake_y = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
            self.shake_intensity *= self.shake_decay

        # 2. Random Flicker (Atmospheric lighting)
        if random.randint(0, 100) > 90:
            flicker = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            flicker.set_alpha(random.randint(5, 12))
            flicker.fill((20, 30, 20))
            game_surface.blit(flicker, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # 3. Clear screen to black before drawing (prevents trails during shake)
        final_screen.fill((0, 0, 0))

        # 4. Chromatic Aberration (The "Glitch" RGB Split)
        # Red Channel (shifted left)
        final_screen.blit(game_surface, (-2 + shake_x, 0 + shake_y), special_flags=pygame.BLEND_RGB_ADD)
        # Green Channel (shifted right)
        final_screen.blit(game_surface, (2 + shake_x, 0 + shake_y), special_flags=pygame.BLEND_RGB_ADD)
        # Blue/Original Channel (centered)
        final_screen.blit(game_surface, (0 + shake_x, 0 + shake_y), special_flags=pygame.BLEND_RGB_MULT)

        # 5. Static Overlays (Vignette & CRT)
        final_screen.blit(self.crt_texture, (0, 0))
        final_screen.blit(self.vignette, (0, 0))
