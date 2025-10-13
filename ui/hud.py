"""
HUD module for the 3D Hunting Simulator.
Handles heads-up display elements like health, ammo, crosshair, and score.
"""

import os
import pygame
from typing import Optional, Tuple, Dict

from panda3d.core import Vec4, TextNode, TransparencyAttrib, Filename
from direct.gui.DirectGui import DirectFrame, DirectWaitBar
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.task import Task

from graphics.texture_factory import create_crosshair_texture, create_icon_texture, get_ui_panel_texture


class HUD:
    """Heads-Up Display class for game information and crosshair."""

    def __init__(self, app, player):
        """Initialize the HUD with the Panda3D application and player reference."""
        self.app = app
        self.player = player

        # HUD state
        self.score = 0
        self.kills = 0
        self.shots_fired = 0
        self.shots_hit = 0

        self.theme = {
            'primary_text': (0.93, 0.96, 0.98, 1.0),
            'secondary_text': (0.78, 0.83, 0.9, 1.0),
            'accent': (0.94, 0.75, 0.32, 1.0),
            'panel_tint': (1.0, 1.0, 1.0, 1.0),
            'warning': (1.0, 0.42, 0.32, 1.0)
        }
        self._last_state: Dict[str, Optional[float]] = {
            'health': None,
            'ammo': None,
            'weapon_status': None,
            'score': None,
            'accuracy': None,
            'kills': None,
            'objective': None
        }
        self._idle_time = 0.0
        self.fade_delay = 2.6
        self.fade_duration = 0.6
        self.fade_target_opacity = 0.38
        self._current_opacity = 1.0
        self._objective_state: Dict[str, Dict[str, int]] = {
            'totals': {},
            'alive': {}
        }
        self._objective_dirty = False

        # Initialize Pygame for 2D rendering
        self.pygame_initialized = False
        self.screen = None
        self.font = None
        self.setup_pygame()

        # Create HUD elements
        self.hud_elements = []
        self.hud_panels = []
        self.setup_hud_elements()

        # Crosshair settings
        self.crosshair_image: Optional[OnscreenImage] = None
        self.crosshair_color_ready = Vec4(0.95, 0.95, 0.95, 1.0)
        self.crosshair_color_empty = Vec4(1.0, 0.65, 0.2, 1.0)
        self.crosshair_color_reload = Vec4(1.0, 0.25, 0.25, 1.0)

    def setup_pygame(self):
        """Initialize Pygame for 2D UI rendering."""
        try:
            pygame.init()
            self.pygame_initialized = True

            # Get window size from config
            from config import GAME_CONFIG
            window_size = GAME_CONFIG['window_size']

            # Create a surface for 2D rendering
            self.screen = pygame.Surface(window_size, pygame.SRCALPHA)
            self.font = pygame.font.SysFont('Arial', 24)

            # Test font creation to ensure it works
            test_text = self.font.render("Test", True, (255, 255, 255))
            
            print("Pygame initialized for HUD rendering")
        except Exception as e:
            print(f"Failed to initialize Pygame: {e}")
            self.pygame_initialized = False

    def _register_panel(self, panel: DirectFrame) -> DirectFrame:
        self.hud_panels.append(panel)
        return panel

    def _register_element(self, element):
        self.hud_elements.append(element)
        return element

    def _create_text(self, text: str, parent, pos, scale, fg, align=TextNode.ALeft):
        element = OnscreenText(
            text=text,
            pos=pos,
            scale=scale,
            fg=fg,
            align=align,
            parent=parent,
            mayChange=True,
            shadow=(0, 0, 0, 0.85),
            shadowOffset=(0.012, 0.012)
        )
        if getattr(self, 'ui_font', None):
            element.setFont(self.ui_font)
        return self._register_element(element)

    def setup_hud_elements(self):
        """Set up HUD display elements using Panda3D's GUI system."""

        # Create font with error handling
        def load_default_font():
            """Load a bundled font if available, else fall back to Panda3D default."""
            from panda3d.core import TextNode

            font_dir = os.path.join(os.path.dirname(__file__), '..', 'fonts')
            candidate = os.path.join(font_dir, 'ui_font.ttf')
            if hasattr(self.app, 'loader') and hasattr(self.app.loader, 'loadFont') and os.path.isfile(candidate):
                try:
                    filename = Filename.fromOsSpecific(candidate)
                    return self.app.loader.loadFont(filename)
                except Exception:
                    pass
            return TextNode.getDefaultFont()

        loaded_font = load_default_font()
        self.ui_font = loaded_font

        hud_parent = getattr(self.app, 'aspect2d', getattr(self.app, 'render2d', None))
        if hud_parent is None:
            raise RuntimeError("HUD requires a Panda3D application with aspect2d or render2d")

        # Reset collections before building
        self.hud_elements = []
        self.hud_panels = []

        panel_texture = get_ui_panel_texture()

        # Left status panel
        self.left_panel = self._register_panel(DirectFrame(
            parent=hud_parent,
            frameColor=self.theme['panel_tint'],
            frameSize=(-0.36, 0.36, -0.18, 0.18),
            pos=(-1.08, 0, 0.86)
        ))
        self.left_panel.setTransparency(TransparencyAttrib.MAlpha)
        self.left_panel.setTexture(panel_texture)

        self._create_text("Vitals", self.left_panel, (-0.32, 0.12), 0.045, self.theme['accent'])

        self.health_bar = DirectWaitBar(
            parent=self.left_panel,
            range=100,
            value=100,
            frameSize=(-0.54, 0.54, -0.065, 0.065),
            pos=(0.0, 0, 0.0),
            barColor=(0.82, 0.29, 0.26, 0.95),
            frameColor=(0.08, 0.1, 0.15, 0.9)
        )
        self.health_bar.setScale(0.25)
        self._register_element(self.health_bar)

        self.health_icon = self._register_element(OnscreenImage(
            image=create_icon_texture('health'),
            parent=self.left_panel,
            pos=(-0.32, 0, 0.02)
        ))
        self.health_icon.setScale(0.05)
        self.health_icon.setTransparency(TransparencyAttrib.MAlpha)

        self.health_text = self._create_text("100 HP", self.left_panel, (0.3, 0.02), 0.055, self.theme['primary_text'], TextNode.ARight)

        self.score_text = self._create_text("Score: 0", self.left_panel, (-0.32, -0.08), 0.05, self.theme['accent'], TextNode.ALeft)
        self.kills_text = self._create_text("Harvested: 0", self.left_panel, (-0.32, -0.14), 0.045, self.theme['secondary_text'], TextNode.ALeft)

        # Right combat panel
        self.right_panel = self._register_panel(DirectFrame(
            parent=hud_parent,
            frameColor=self.theme['panel_tint'],
            frameSize=(-0.36, 0.36, -0.18, 0.18),
            pos=(1.08, 0, 0.86)
        ))
        self.right_panel.setTransparency(TransparencyAttrib.MAlpha)
        self.right_panel.setTexture(panel_texture)

        self._create_text("Ballistics", self.right_panel, (-0.32, 0.12), 0.045, self.theme['accent'])

        self.ammo_text = self._create_text("Ammo 10 / 10", self.right_panel, (-0.32, 0.04), 0.05, self.theme['primary_text'])

        self.ammo_bar = DirectWaitBar(
            parent=self.right_panel,
            range=1.0,
            value=1.0,
            frameSize=(-0.54, 0.54, -0.06, 0.06),
            pos=(0.0, 0, -0.02),
            barColor=(0.88, 0.74, 0.32, 0.95),
            frameColor=(0.08, 0.1, 0.15, 0.88)
        )
        self.ammo_bar.setScale(0.24)
        self._register_element(self.ammo_bar)

        self.ammo_icon = self._register_element(OnscreenImage(
            image=create_icon_texture('ammo'),
            parent=self.right_panel,
            pos=(-0.32, 0, -0.02)
        ))
        self.ammo_icon.setScale(0.045)
        self.ammo_icon.setTransparency(TransparencyAttrib.MAlpha)

        self.accuracy_text = self._create_text("Accuracy: 0%", self.right_panel, (-0.32, -0.1), 0.045, self.theme['secondary_text'])

        # Objective panel
        self.objective_panel = self._register_panel(DirectFrame(
            parent=hud_parent,
            frameColor=self.theme['panel_tint'],
            frameSize=(-0.52, 0.52, -0.14, 0.14),
            pos=(0, 0, 0.92)
        ))
        self.objective_panel.setTransparency(TransparencyAttrib.MAlpha)
        self.objective_panel.setTexture(panel_texture)

        self.objective_title = self._create_text("Active Objective", self.objective_panel, (0, 0.06), 0.05, self.theme['accent'], TextNode.ACenter)
        self.objective_text = self._create_text("Explore the reserve", self.objective_panel, (0, -0.02), 0.045, self.theme['primary_text'], TextNode.ACenter)

        # Weapon panel bottom
        self.weapon_panel = self._register_panel(DirectFrame(
            parent=hud_parent,
            frameColor=self.theme['panel_tint'],
            frameSize=(-0.45, 0.45, -0.12, 0.12),
            pos=(0, 0, -0.9)
        ))
        self.weapon_panel.setTransparency(TransparencyAttrib.MAlpha)
        self.weapon_panel.setTexture(panel_texture)

        self.weapon_icon = self._register_element(OnscreenImage(
            image=create_icon_texture('accuracy'),
            parent=self.weapon_panel,
            pos=(-0.36, 0, 0.0)
        ))
        self.weapon_icon.setScale(0.05)
        self.weapon_icon.setTransparency(TransparencyAttrib.MAlpha)

        self.weapon_label = self._create_text("Equipped", self.weapon_panel, (-0.28, 0.05), 0.045, self.theme['secondary_text'])
        self.weapon_text = self._create_text("Hunting Rifle", self.weapon_panel, (0.08, 0.05), 0.055, self.theme['primary_text'], TextNode.ALeft)
        self.weapon_status_text = self._create_text("Ready", self.weapon_panel, (0.0, -0.04), 0.045, self.theme['secondary_text'], TextNode.ACenter)

        self.create_crosshair()

    def create_crosshair(self):
        """Create a crosshair using Panda3D's CardMaker."""
        try:
            texture = create_crosshair_texture()
            parent = getattr(self.app, 'render2d', None)
            if parent is None:
                return
            self.crosshair_image = OnscreenImage(
                image=texture,
                pos=(0, 0, 0),
                scale=0.045,
                parent=parent
            )
            self.crosshair_image.setTransparency(TransparencyAttrib.MAlpha)
            self.crosshair_image.setColorScale(1, 1, 1, 1)
        except Exception as e:
            self.crosshair_image = None
            print(f"Crosshair creation failed: {e}")

    def update(self, dt: float):
        """Update HUD elements with current game state."""
        if not self.player:
            return

        changed = False
        self._idle_time += dt

        # Update health display
        health = getattr(self.player, 'health', 100)
        if hasattr(self, 'health_bar'):
            try:
                max_value = float(self.health_bar['range'])
            except Exception:
                max_value = 100.0
            self.health_bar['value'] = max(0.0, min(max_value, float(health)))
        self.health_text.setText(f"{health:.0f} HP")
        if self._last_state['health'] != health:
            self._last_state['health'] = health
            changed = True

        # Update ammo display
        if hasattr(self.player, 'weapon'):
            current_ammo = self.player.weapon.current_ammo
            max_ammo = self.player.weapon.max_ammo
            self.ammo_text.setText(f"Ammo {current_ammo} / {max_ammo}")
            ratio = 0.0 if max_ammo <= 0 else current_ammo / float(max_ammo)
            self.ammo_bar['value'] = max(0.0, min(1.0, ratio))
            if self._last_state['ammo'] != ratio:
                self._last_state['ammo'] = ratio
                changed = True

            # Update weapon name
            self.weapon_text.setText(self.player.weapon.name)
            if self.player.weapon.reloading:
                self.weapon_status_text.setText("Reloading")
            elif current_ammo == 0:
                self.weapon_status_text.setText("Empty")
            else:
                self.weapon_status_text.setText("Ready")
        else:
            self.weapon_status_text.setText("Unarmed")

        weapon_state = self.weapon_status_text.getText()
        if self._last_state['weapon_status'] != weapon_state:
            self._last_state['weapon_status'] = weapon_state
            changed = True

        # Update score display
        self.score_text.setText(f"Score: {self.score}")
        if self._last_state['score'] != self.score:
            self._last_state['score'] = self.score
            changed = True

        if self._last_state['kills'] != self.kills:
            self._last_state['kills'] = self.kills
            self.kills_text.setText(f"Harvested: {self.kills}")
            changed = True
        else:
            self.kills_text.setText(f"Harvested: {self.kills}")

        # Update accuracy
        if self.shots_fired > 0:
            accuracy = (self.shots_hit / self.shots_fired) * 100
            self.accuracy_text.setText(f"Accuracy: {accuracy:.1f}%")
        else:
            self.accuracy_text.setText("Accuracy: 0%")
            accuracy = 0.0
        if self._last_state['accuracy'] != accuracy:
            self._last_state['accuracy'] = accuracy
            changed = True

        # Update crosshair color based on weapon state
        if self.crosshair_image:
            if hasattr(self.player, 'weapon') and self.player.weapon.reloading:
                self.crosshair_image.setColorScale(self.crosshair_color_reload)
            elif hasattr(self.player, 'weapon') and self.player.weapon.current_ammo == 0:
                self.crosshair_image.setColorScale(self.crosshair_color_empty)
            else:
                self.crosshair_image.setColorScale(self.crosshair_color_ready)

        if self._objective_dirty:
            changed = True
            self._objective_dirty = False
            self._refresh_objective_text()

        self._update_fade(dt, changed)

        # Render Pygame overlay if available
        if self.pygame_initialized:
            self.render_pygame_overlay()

    def render_pygame_overlay(self):
        """Render additional 2D elements using Pygame."""
        if not self.screen:
            return

        # Clear the surface
        self.screen.fill((0, 0, 0, 0))

        # Draw additional HUD elements if needed
        # This can be extended for more complex 2D UI elements

        # Convert Pygame surface to Panda3D texture if needed
        # This is optional and can be used for more complex 2D rendering

    def _set_opacity(self, opacity: float):
        if abs(opacity - self._current_opacity) <= 0.01:
            return
        self._current_opacity = opacity
        for panel in getattr(self, 'hud_panels', []):
            if panel:
                panel.setColorScale(1, 1, 1, opacity)
        for element in getattr(self, 'hud_elements', []):
            if hasattr(element, 'setColorScale'):
                element.setColorScale(1, 1, 1, opacity)

    def _update_fade(self, dt: float, changed: bool):
        if changed:
            self._idle_time = 0.0

        target_opacity = 1.0 if self._idle_time < self.fade_delay else self.fade_target_opacity

        if target_opacity < self._current_opacity:
            fade_speed = self.fade_duration if self.fade_duration > 0 else 0.6
            delta = (self._current_opacity - target_opacity)
            if fade_speed <= 0:
                new_opacity = target_opacity
            else:
                new_opacity = max(target_opacity, self._current_opacity - (dt / fade_speed) * delta)
        else:
            new_opacity = min(1.0, target_opacity * 0.5 + self._current_opacity * 0.5)

        self._set_opacity(max(0.1, min(1.0, new_opacity)))

    def _refresh_objective_text(self):
        totals = self._objective_state.get('totals', {})
        alive = self._objective_state.get('alive', {})
        if not totals:
            self.objective_text.setText("Explore the reserve")
            self.objective_text.setFg(self.theme['primary_text'])
            self._last_state['objective'] = None
            return

        alive_total = sum(max(0, count) for count in alive.values())
        grand_total = sum(max(0, count) for count in totals.values())
        harvested_total = max(0, grand_total - alive_total)

        segments = []
        for species, total in totals.items():
            remaining = max(0, alive.get(species, 0))
            harvested = max(0, total - remaining)
            segments.append(f"{species.title()}: {harvested}/{total}")

        detail = "   ".join(segments)
        header_line = f"Harvest wildlife ({harvested_total}/{grand_total})" if grand_total else "Survey the reserve"
        self.objective_text.setText(f"{header_line}\n{detail}")

        remaining_ratio = 0 if grand_total == 0 else alive_total / grand_total
        if remaining_ratio <= 0.2:
            self.objective_text.setFg(self.theme['warning'])
        else:
            self.objective_text.setFg(self.theme['primary_text'])

        new_state_value = (harvested_total, grand_total)
        if self._last_state['objective'] != new_state_value:
            self._last_state['objective'] = new_state_value

    def set_objective_targets(self, species_totals: Dict[str, int]):
        cleaned_totals = {k: max(0, int(v)) for k, v in species_totals.items() if v}
        self._objective_state['totals'] = cleaned_totals
        self._objective_state['alive'] = cleaned_totals.copy()
        self._objective_dirty = True
        self._idle_time = 0.0
        self._refresh_objective_text()

    def update_objective_counts(self, alive_by_species: Dict[str, int]):
        if not isinstance(alive_by_species, dict):
            return
        self._objective_state['alive'] = {k: max(0, int(v)) for k, v in alive_by_species.items()}
        self._objective_dirty = True
        self._refresh_objective_text()

    def register_animal_kill(self, species: str):
        species_key = species.lower() if species else ''
        alive = self._objective_state.get('alive', {})
        if species_key in alive:
            alive[species_key] = max(0, alive[species_key] - 1)
            self._objective_dirty = True
            self._refresh_objective_text()
        self._idle_time = 0.0

    def add_score(self, points: int):
        """Add points to the player's score."""
        self.score += points
        print(f"Score updated: +{points}, Total: {self.score}")
        self._idle_time = 0.0

    def record_shot(self, hit: bool = False):
        """Record a shot fired and whether it hit a target."""
        self.shots_fired += 1
        if hit:
            self.shots_hit += 1
            self.kills += 1
        self._idle_time = 0.0

    def show_message(self, message: str, duration: float = 3.0, color: Tuple[float, float, float, float] = (1, 1, 1, 1)):
        """Display a temporary message on screen."""
        # Create temporary text node with proper parenting
        temp_text = OnscreenText(
            text=message,
            pos=(0, 0.4),
            scale=0.08,
            fg=color,
            align=TextNode.ACenter,
            parent=self.app.render2d,  # Use render2d for proper depth
            mayChange=True
        )
        
        # Set font if available
        weapon_font = self.weapon_text.getFont() if hasattr(self.weapon_text, 'getFont') else None
        if weapon_font:
            temp_text.setFont(weapon_font)
        
        # Schedule removal
        def remove_message():
            temp_text.destroy()

        self.app.taskMgr.doMethodLater(duration, lambda task: remove_message(), 'remove_message')

    def toggle_visibility(self, visible: bool = True):
        """Toggle HUD visibility."""
        if hasattr(self, 'hud_panels'):
            for panel in self.hud_panels:
                if visible:
                    panel.show()
                else:
                    panel.hide()

        for element in getattr(self, 'hud_elements', []):
            if visible:
                element.show()
            else:
                element.hide()

        if self.crosshair_image:
            if visible:
                self.crosshair_image.show()
            else:
                self.crosshair_image.hide()

    def cleanup(self):
        """Clean up HUD resources."""
        for element in getattr(self, 'hud_elements', []):
            if hasattr(element, 'destroy'):
                element.destroy()
        self.hud_elements = []

        if hasattr(self, 'hud_panels'):
            for panel in self.hud_panels:
                if panel:
                    panel.destroy()
            self.hud_panels = []

        if hasattr(self, 'crosshair_image') and self.crosshair_image:
            self.crosshair_image.destroy()
            self.crosshair_image = None

        # Clean up Pygame
        if self.pygame_initialized:
            pygame.quit()
            self.pygame_initialized = False

        print("HUD cleanup completed")