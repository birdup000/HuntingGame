"""
HUD module for the 3D Hunting Simulator.
Handles heads-up display elements like health, ammo, crosshair, and score.
"""

import pygame
from typing import Optional, Tuple
from panda3d.core import Vec4, Vec3, Point3, TextNode, CardMaker, TextureStage, TransparencyAttrib
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.task import Task


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
        self.setup_hud_elements()

        # Crosshair settings
        self.crosshair_size = 20
        self.crosshair_color = (255, 255, 255, 200)
        self.crosshair_thickness = 2

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

            print("Pygame initialized for HUD rendering")
        except Exception as e:
            print(f"Failed to initialize Pygame: {e}")
            self.pygame_initialized = False

    def setup_hud_elements(self):
        """Set up HUD display elements using Panda3D's GUI system."""

        # Health display
        self.health_text = OnscreenText(
            text="Health: 100",
            pos=(-1.3, 0.9),
            scale=0.07,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            font=self.app.loader.loadFont("cmss12")
        )

        # Ammo display
        self.ammo_text = OnscreenText(
            text="Ammo: 10/10",
            pos=(1.0, 0.9),
            scale=0.07,
            fg=(1, 1, 1, 1),
            align=TextNode.ARight,
            font=self.app.loader.loadFont("cmss12")
        )

        # Score display
        self.score_text = OnscreenText(
            text="Score: 0",
            pos=(-1.3, 0.8),
            scale=0.06,
            fg=(1, 0.8, 0, 1),
            align=TextNode.ALeft,
            font=self.app.loader.loadFont("cmss12")
        )

        # Accuracy display
        self.accuracy_text = OnscreenText(
            text="Accuracy: 0%",
            pos=(1.0, 0.8),
            scale=0.06,
            fg=(0.8, 0.8, 0.8, 1),
            align=TextNode.ARight,
            font=self.app.loader.loadFont("cmss12")
        )

        # Weapon info display
        self.weapon_text = OnscreenText(
            text="Hunting Rifle",
            pos=(0, -0.9),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            font=self.app.loader.loadFont("cmss12")
        )

        # Create crosshair using CardMaker
        self.create_crosshair()

    def create_crosshair(self):
        """Create a crosshair using Panda3D's CardMaker."""
        cm = CardMaker('crosshair')

        # Horizontal line
        cm.setFrame(-0.02, 0.02, -0.002, 0.002)
        self.crosshair_h = self.app.aspect2d.attachNewNode(cm.generate())
        self.crosshair_h.setColor(1, 1, 1, 0.8)
        self.crosshair_h.setTransparency(TransparencyAttrib.MAlpha)

        # Vertical line
        cm.setFrame(-0.002, 0.002, -0.02, 0.02)
        self.crosshair_v = self.app.aspect2d.attachNewNode(cm.generate())
        self.crosshair_v.setColor(1, 1, 1, 0.8)
        self.crosshair_v.setTransparency(TransparencyAttrib.MAlpha)

    def update(self, dt: float):
        """Update HUD elements with current game state."""
        if not self.player:
            return

        # Update health display
        health = getattr(self.player, 'health', 100)
        self.health_text.setText(f"Health: {health}")

        # Update ammo display
        if hasattr(self.player, 'weapon'):
            current_ammo = self.player.weapon.current_ammo
            max_ammo = self.player.weapon.max_ammo
            self.ammo_text.setText(f"Ammo: {current_ammo}/{max_ammo}")

            # Update weapon name
            self.weapon_text.setText(self.player.weapon.name)

        # Update score display
        self.score_text.setText(f"Score: {self.score}")

        # Update accuracy
        if self.shots_fired > 0:
            accuracy = (self.shots_hit / self.shots_fired) * 100
            self.accuracy_text.setText(f"Accuracy: {accuracy:.1f}%")
        else:
            self.accuracy_text.setText("Accuracy: 0%")

        # Update crosshair color based on weapon state
        if hasattr(self.player, 'weapon'):
            if self.player.weapon.reloading:
                self.crosshair_h.setColor(1, 0, 0, 0.8)  # Red when reloading
                self.crosshair_v.setColor(1, 0, 0, 0.8)
            elif self.player.weapon.current_ammo == 0:
                self.crosshair_h.setColor(1, 0.5, 0, 0.8)  # Orange when out of ammo
                self.crosshair_v.setColor(1, 0.5, 0, 0.8)
            else:
                self.crosshair_h.setColor(1, 1, 1, 0.8)  # White when ready
                self.crosshair_v.setColor(1, 1, 1, 0.8)

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
        # Create temporary text node
        temp_text = OnscreenText(
            text=message,
            pos=(0, 0.7),
            scale=0.08,
            fg=color,
            align=TextNode.ACenter,
            font=self.app.loader.loadFont("cmss12")
        )

        # Schedule removal
        def remove_message():
            temp_text.destroy()

        self.app.taskMgr.doMethodLater(duration, lambda task: remove_message(), 'remove_message')

    def toggle_visibility(self, visible: bool = True):
        """Toggle HUD visibility."""
        if visible:
            self.health_text.show()
            self.ammo_text.show()
            self.score_text.show()
            self.accuracy_text.show()
            self.weapon_text.show()
            self.crosshair_h.show()
            self.crosshair_v.show()
        else:
            self.health_text.hide()
            self.ammo_text.hide()
            self.score_text.hide()
            self.accuracy_text.hide()
            self.weapon_text.hide()
            self.crosshair_h.hide()
            self.crosshair_v.hide()

    def cleanup(self):
        """Clean up HUD resources."""
        # Remove all HUD elements
        if hasattr(self, 'health_text'):
            self.health_text.destroy()
        if hasattr(self, 'ammo_text'):
            self.ammo_text.destroy()
        if hasattr(self, 'score_text'):
            self.score_text.destroy()
        if hasattr(self, 'accuracy_text'):
            self.accuracy_text.destroy()
        if hasattr(self, 'weapon_text'):
            self.weapon_text.destroy()
        if hasattr(self, 'crosshair_h'):
            self.crosshair_h.removeNode()
        if hasattr(self, 'crosshair_v'):
            self.crosshair_v.removeNode()

        # Clean up Pygame
        if self.pygame_initialized:
            pygame.quit()
            self.pygame_initialized = False

        print("HUD cleanup completed")