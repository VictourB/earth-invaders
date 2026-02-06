from settings import *
import pygame

class AudioManager:
    def __init__(self, assets):
        # --- Background
        self.music_tracks = {
            'menu': get_path("assets/audio/menu_music.mp3"),
            'playing': get_path("assets/audio/bg_1.mp3"),
            'game_over': get_path("assets/audio/game_over.mp3")
        }

        # 2. Sound Effects (Pre-loaded into RAM)
        self.sfx = {
            "shoot": pygame.mixer.Sound(get_path("assets/audio/firing_sound.wav")),
            "explosion": pygame.mixer.Sound(get_path("assets/audio/explosion.wav")),
            "ufo": pygame.mixer.Sound(get_path("assets/audio/ufo_sound.mp3"))
        }

        self.current_track = None

        self.master_volume = 0.5
        self.set_volume(self.master_volume)

    def play_music(self, key, loops=-1, fade_ms=2000):
        if self.current_track == key:
            return
        if key in self.music_tracks:
            try:
                pygame.mixer.music.load(self.music_tracks[key])
                pygame.mixer.music.play(loops, fade_ms=fade_ms)

                self.current_track = key
            except pygame.error as e:
                print(f"couldn't load music {key}: {e}")

    def play_sfx(self, key, loops=0):
        if key in self.sfx:
            # .play() returns a Channel object, allowing multiple instances
            self.sfx[key].play(loops=loops)
        return None

    def stop_sfx(self, key):
        if key in self.sfx:
            self.sfx[key].stop()

    def set_volume(self, volume):
        self.master_volume = volume
        pygame.mixer.music.set_volume(volume)
        for sound in self.sfx.values():
            sound.set_volume(volume)

    def pause_all(self):
        pygame.mixer.music.pause()
        pygame.mixer.pause()  # Pauses all SFX channels

    def unpause_all(self):
        pygame.mixer.music.unpause()
        pygame.mixer.unpause()