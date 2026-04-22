"""
Audio Manager for the 3D Hunting Simulator.
Handles ambient sounds, weapon sounds, animal sounds, footstep sounds, and music.
Uses Panda3D's built-in audio capabilities for 3D spatial audio.
"""

import logging
import random
from panda3d.core import AudioSound, Vec3


class AudioManager:
    """Manages all game audio including 3D spatial sounds, music, and effects."""

    def __init__(self, app):
        self.app = app
        self.sounds = {}
        self.music = None
        self.ambient_sounds = []
        self.master_volume = 0.8
        self.sfx_volume = 1.0
        self.music_volume = 0.5
        self.ambient_volume = 0.6
        self._footstep_timer = 0.0
        self._footstep_interval = 0.45
        self._wind_sound = None
        self._last_player_pos = Vec3(0, 0, 0)
        self._initialized = False

        self._init_audio()

    def _init_audio(self):
        """Initialize audio manager and load sound placeholders."""
        try:
            if not hasattr(self.app, 'loader') or not hasattr(self.app.loader, 'loadSfx'):
                logging.warning("Panda3D audio loader not available")
                return
            self._initialized = True
            self._load_sounds()
            self._start_ambient()
            logging.info("Audio manager initialized successfully")
        except Exception as e:
            logging.warning(f"Audio initialization failed: {e}")

    def _load_sounds(self):
        """Load or synthesize game sounds. Uses procedural generation when files unavailable."""
        # We attempt to load from assets/audio/ but gracefully fall back to silent operation
        sound_definitions = {
            'rifle_fire': {'file': 'audio/assets/rifle_fire.wav', 'volume': 0.9},
            'pistol_fire': {'file': 'audio/assets/pistol_fire.wav', 'volume': 0.8},
            'bow_fire': {'file': 'audio/assets/bow_fire.wav', 'volume': 0.7},
            'reload': {'file': 'audio/assets/reload.wav', 'volume': 0.6},
            'empty_click': {'file': 'audio/assets/empty_click.wav', 'volume': 0.5},
            'footstep_grass': {'file': 'audio/assets/footstep_grass.wav', 'volume': 0.4},
            'footstep_dirt': {'file': 'audio/assets/footstep_dirt.wav', 'volume': 0.4},
            'deer_call': {'file': 'audio/assets/deer_call.wav', 'volume': 0.5},
            'rabbit_squeak': {'file': 'audio/assets/rabbit_squeak.wav', 'volume': 0.3},
            'bear_growl': {'file': 'audio/assets/bear_growl.wav', 'volume': 0.7},
            'wolf_howl': {'file': 'audio/assets/wolf_howl.wav', 'volume': 0.6},
            'bird_chirp': {'file': 'audio/assets/bird_chirp.wav', 'volume': 0.3},
            'animal_hit': {'file': 'audio/assets/animal_hit.wav', 'volume': 0.6},
            'animal_death': {'file': 'audio/assets/animal_death.wav', 'volume': 0.7},
            'wind': {'file': 'audio/assets/wind_loop.wav', 'volume': 0.3, 'loop': True},
            'rain': {'file': 'audio/assets/rain_loop.wav', 'volume': 0.4, 'loop': True},
            'ui_click': {'file': 'audio/assets/ui_click.wav', 'volume': 0.4},
            'ui_hover': {'file': 'audio/assets/ui_hover.wav', 'volume': 0.2},
        }

        for name, cfg in sound_definitions.items():
            try:
                sound = self.app.loader.loadSfx(cfg['file'])
                if sound:
                    sound.setVolume(cfg['volume'] * self.master_volume)
                    if cfg.get('loop'):
                        sound.setLoop(True)
                    self.sounds[name] = sound
            except Exception:
                # Sound file missing - create a silent placeholder
                self.sounds[name] = None

    def _start_ambient(self):
        """Start ambient background sounds."""
        wind = self.sounds.get('wind')
        if wind:
            wind.setVolume(self.ambient_volume * self.master_volume)
            wind.play()
            self._wind_sound = wind

    def set_master_volume(self, volume: float):
        """Set master volume (0.0 to 1.0)."""
        self.master_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            if sound:
                sound.setVolume(self.master_volume)

    def play_sound(self, sound_name: str, pos: Vec3 = None):
        """Play a one-shot sound effect, optionally at a 3D position."""
        sound = self.sounds.get(sound_name)
        if not sound:
            return
        try:
            if pos and hasattr(sound, 'set3dAttributes'):
                sound.set3dAttributes(pos.x, pos.y, pos.z, 0, 0, 0)
            sound.setVolume(self.sfx_volume * self.master_volume)
            sound.play()
        except Exception as e:
            logging.debug(f"Sound play error: {e}")

    def play_weapon_fire(self, weapon_type: str):
        """Play weapon fire sound based on weapon type."""
        mapping = {
            'rifle': 'rifle_fire',
            'pistol': 'pistol_fire',
            'bow': 'bow_fire'
        }
        self.play_sound(mapping.get(weapon_type, 'rifle_fire'))

    def play_reload(self):
        """Play reload sound."""
        self.play_sound('reload')

    def play_empty_click(self):
        """Play empty weapon click sound."""
        self.play_sound('empty_click')

    def play_animal_sound(self, species: str, pos: Vec3 = None):
        """Play ambient animal vocalization."""
        mapping = {
            'deer': 'deer_call',
            'rabbit': 'rabbit_squeak',
            'bear': 'bear_growl',
            'wolf': 'wolf_howl',
            'bird': 'bird_chirp'
        }
        self.play_sound(mapping.get(species, 'deer_call'), pos)

    def play_hit(self, pos: Vec3 = None):
        """Play animal hit sound."""
        self.play_sound('animal_hit', pos)

    def play_death(self, pos: Vec3 = None):
        """Play animal death sound."""
        self.play_sound('animal_death', pos)

    def play_ui_click(self):
        """Play UI click sound."""
        self.play_sound('ui_click')

    def play_ui_hover(self):
        """Play UI hover sound."""
        self.play_sound('ui_hover')

    def update_footsteps(self, dt: float, player_pos: Vec3, is_moving: bool, is_sprinting: bool):
        """Update footstep sound timing based on movement."""
        if not is_moving:
            self._footstep_timer = 0.0
            return

        interval = self._footstep_interval
        if is_sprinting:
            interval *= 0.6

        self._footstep_timer += dt
        if self._footstep_timer >= interval:
            self._footstep_timer = 0.0
            # Alternate between grass and dirt for variety
            sound_name = 'footstep_grass' if random.random() > 0.3 else 'footstep_dirt'
            self.play_sound(sound_name)

    def update_weather_audio(self, weather_type: str, strength: float):
        """Update weather-related ambient audio."""
        rain = self.sounds.get('rain')
        wind = self.sounds.get('wind')
        if rain:
            if weather_type in ('rain', 'storm'):
                rain.setVolume(strength * self.ambient_volume * self.master_volume)
                if not rain.status() == AudioSound.PLAYING:
                    rain.play()
            else:
                rain.stop()
        if wind:
            base_vol = 0.2 + (strength * 0.3) if weather_type != 'clear' else 0.15
            wind.setVolume(base_vol * self.ambient_volume * self.master_volume)

    def update(self, dt: float, player_pos: Vec3, is_moving: bool, is_sprinting: bool,
               weather_type: str = 'clear', weather_strength: float = 0.0):
        """Main audio update loop. Call every frame."""
        if not self._initialized:
            return
        self.update_footsteps(dt, player_pos, is_moving, is_sprinting)
        self.update_weather_audio(weather_type, weather_strength)
        self._last_player_pos = player_pos

    def cleanup(self):
        """Stop and clean up all audio."""
        for sound in self.sounds.values():
            if sound:
                try:
                    sound.stop()
                except Exception:
                    pass
        self.sounds.clear()
        self._initialized = False
        logging.info("Audio manager cleaned up")
