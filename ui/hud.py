"""
HUD module for the 3D Hunting Simulator.
Handles heads-up display elements like health, ammo, crosshair, and score.
"""

import os
import pygame
from typing import Optional, Tuple

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

        hud_parent = getattr(self.app, 'aspect2d', getattr(self.app, 'render2d', None))
        if hud_parent is None:
            raise RuntimeError("HUD requires a Panda3D application with aspect2d or render2d")

        panel_texture = get_ui_panel_texture()
        accent_color = (1.0, 0.8, 0.35, 1.0)

        self.left_panel = DirectFrame(
            parent=hud_parent,
            frameColor=(1, 1, 1, 1),
            frameSize=(-0.55, 0.45, -0.22, 0.2),
            pos=(-0.95, 0, 0.84)
        )
        self.left_panel.setTransparency(TransparencyAttrib.MAlpha)
        self.left_panel.setTexture(panel_texture)

        self.right_panel = DirectFrame(
            parent=hud_parent,
            frameColor=(1, 1, 1, 1),
            frameSize=(-0.55, 0.45, -0.22, 0.2),
            pos=(0.95, 0, 0.84)
        )
        self.right_panel.setTransparency(TransparencyAttrib.MAlpha)
        self.right_panel.setTexture(panel_texture)

        self.weapon_panel = DirectFrame(
            parent=hud_parent,
            frameColor=(1, 1, 1, 1),
            frameSize=(-0.45, 0.45, -0.14, 0.14),
            pos=(0, 0, -0.88)
        )
        self.weapon_panel.setTransparency(TransparencyAttrib.MAlpha)
        self.weapon_panel.setTexture(panel_texture)
        self.hud_panels = [self.left_panel, self.right_panel, self.weapon_panel]

        self.weapon_icon = OnscreenImage(
            image=create_icon_texture('accuracy'),
            parent=self.weapon_panel,
            pos=(-0.36, 0, 0.03)
        )
        self.weapon_icon.setScale(0.06)
        self.weapon_icon.setTransparency(TransparencyAttrib.MAlpha)
        self.hud_elements.append(self.weapon_icon)

        self.health_icon = OnscreenImage(
            image=create_icon_texture('health'),
            parent=self.left_panel,
            pos=(-0.48, 0, 0.08)
        )
        self.health_icon.setScale(0.08)
        self.health_icon.setTransparency(TransparencyAttrib.MAlpha)
        self.hud_elements.append(self.health_icon)

        self.health_bar = DirectWaitBar(
            parent=self.left_panel,
            range=100,
            value=100,
            frameSize=(-0.52, 0.52, -0.08, 0.08),
            pos=(-0.05, 0, 0.08),
            barColor=(0.86, 0.32, 0.28, 0.95),
            frameColor=(0.12, 0.16, 0.2, 0.85)
        )
        self.health_bar.setScale(0.27)
        self.hud_elements.append(self.health_bar)

        self.health_text = OnscreenText(
            text="100 HP",
            pos=(0.32, 0.07),
            scale=0.055,
            fg=(0.92, 0.95, 0.98, 1),
            align=TextNode.ARight,
            parent=self.left_panel,
            mayChange=True
        )
        if loaded_font:
            self.health_text.setFont(loaded_font)
        self.hud_elements.append(self.health_text)

        self.score_icon = OnscreenImage(
            image=create_icon_texture('score'),
            parent=self.left_panel,
            pos=(-0.48, 0, -0.06)
        )
        self.score_icon.setScale(0.07)
        self.score_icon.setTransparency(TransparencyAttrib.MAlpha)
        self.hud_elements.append(self.score_icon)

        self.score_text = OnscreenText(
            text="Score: 0",
            pos=(-0.32, -0.06),
            scale=0.055,
            fg=(accent_color[0], accent_color[1], accent_color[2], 1.0),
            align=TextNode.ALeft,
            parent=self.left_panel,
            mayChange=True
        )
        if loaded_font:
            self.score_text.setFont(loaded_font)
        self.hud_elements.append(self.score_text)

        self.ammo_icon = OnscreenImage(
            image=create_icon_texture('ammo'),
            parent=self.right_panel,
            pos=(-0.44, 0, 0.08)
        )
        self.ammo_icon.setScale(0.075)
        self.ammo_icon.setTransparency(TransparencyAttrib.MAlpha)
        self.hud_elements.append(self.ammo_icon)

        self.ammo_text = OnscreenText(
            text="10 / 10",
            pos=(-0.18, 0.07),
            scale=0.055,
            fg=(1, 1, 1, 1),
            align=TextNode.ARight,
            parent=self.right_panel,
            mayChange=True
        )
        if loaded_font:
            self.ammo_text.setFont(loaded_font)
        self.hud_elements.append(self.ammo_text)

        self.accuracy_icon = OnscreenImage(
            image=create_icon_texture('accuracy'),
            parent=self.right_panel,
            pos=(-0.44, 0, -0.06)
        )
        self.accuracy_icon.setScale(0.075)
        self.accuracy_icon.setTransparency(TransparencyAttrib.MAlpha)
        self.hud_elements.append(self.accuracy_icon)

        self.accuracy_text = OnscreenText(
            text="Accuracy: 0%",
            pos=(-0.14, -0.06),
            scale=0.055,
            fg=(0.82, 0.84, 0.88, 1),
            align=TextNode.ARight,
            parent=self.right_panel,
            mayChange=True
        )
        if loaded_font:
            self.accuracy_text.setFont(loaded_font)
        self.hud_elements.append(self.accuracy_text)

        self.weapon_text = OnscreenText(
            text="Hunting Rifle",
            pos=(0, 0.03),
            scale=0.06,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            parent=self.weapon_panel,
            mayChange=True
        )
        if loaded_font:
            self.weapon_text.setFont(loaded_font)
        self.hud_elements.append(self.weapon_text)

        self.weapon_status_text = OnscreenText(
            text="Ready",
            pos=(0, -0.06),
            scale=0.045,
            fg=(0.75, 0.78, 0.84, 1),
            align=TextNode.ACenter,
            parent=self.weapon_panel,
            mayChange=True
        )
        if loaded_font:
            self.weapon_status_text.setFont(loaded_font)
        self.hud_elements.append(self.weapon_status_text)

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
                scale=0.055,
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

        # Update health display
        health = getattr(self.player, 'health', 100)
        if hasattr(self, 'health_bar'):
            try:
                max_value = float(self.health_bar['range'])
            except Exception:
                max_value = 100.0
            self.health_bar['value'] = max(0.0, min(max_value, float(health)))
        self.health_text.setText(f"{health:.0f} HP")

        # Update ammo display
        if hasattr(self.player, 'weapon'):
            current_ammo = self.player.weapon.current_ammo
            max_ammo = self.player.weapon.max_ammo
            self.ammo_text.setText(f"{current_ammo} / {max_ammo}")

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

        # Update score display
        self.score_text.setText(f"Score: {self.score}")

        # Update accuracy
        if self.shots_fired > 0:
            accuracy = (self.shots_hit / self.shots_fired) * 100
            self.accuracy_text.setText(f"Accuracy: {accuracy:.1f}%")
        else:
            self.accuracy_text.setText("Accuracy: 0%")

        # Update crosshair color based on weapon state
        if self.crosshair_image:
            if hasattr(self.player, 'weapon') and self.player.weapon.reloading:
                self.crosshair_image.setColorScale(self.crosshair_color_reload)
            elif hasattr(self.player, 'weapon') and self.player.weapon.current_ammo == 0:
                self.crosshair_image.setColorScale(self.crosshair_color_empty)
            else:
                self.crosshair_image.setColorScale(self.crosshair_color_ready)

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

    def add_score(self, points: int):
        """Add points to the player's score."""
        self.score += points
        print(f"Score updated: +{points}, Total: {self.score}")

    def record_shot(self, hit: bool = False):
        """Record a shot fired and whether it hit a target."""
        self.shots_fired += 1
        if hit:
            self.shots_hit += 1
            self.kills += 1

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