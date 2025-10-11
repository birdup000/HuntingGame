"""
Core game module for the 3D Hunting Simulator.
Handles the main game loop and initialization.
"""

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from player.player import Player
from environment.terrain import Terrain
from animals.animal import Deer, Rabbit
from ui.menus import UIManager, SettingsMenu
from panda3d.core import Vec3
import random
import config

class Game:
    """Main game class that manages the game state and loop."""

    def __init__(self, app: ShowBase):
        """Initialize the game with the Panda3D application."""
        self.app = app
        self.is_running = False
        self.player = None
        self.terrain = None
        self.animals = []
        self.last_time = 0
        self.ui_manager = None
        self.game_state = 'main_menu'  # main_menu, playing, paused, game_over

    def start(self):
        """Start the game loop."""
        self.is_running = True
        print("Hunting Simulator Game Started")

        # Initialize game components
        self.initialize_components()

        # Set up the main game loop
        self.app.taskMgr.add(self.update, 'update')

    def initialize_components(self):
        """Initialize all game components."""
        # Initialize UI system first
        self.setup_ui()

        # Initialize player (but don't set up controls yet)
        self.player = Player(self.app, setup_controls=False)  # Pass flag to avoid control setup

        # Set up basic environment (ground plane)
        self.setup_environment()

        # Set up lighting
        self.setup_lighting()

        # Set up input handling for UI
        self.setup_ui_controls()

    def setup_collision_detection(self):
        """Set up collision detection for animals and projectiles."""
        # Add all existing animals to collision detection
        for animal in self.animals:
            if self.player:
                self.player.add_animal_to_collision(animal)

    def setup_environment(self):
        """Set up environment with procedural terrain."""
        # Create procedural terrain using config values
        terrain_cfg = config.TERRAIN_CONFIG
        self.terrain = Terrain(
            width=terrain_cfg['width'],
            height=terrain_cfg['height'],
            scale=terrain_cfg['scale'],
            octaves=terrain_cfg['octaves']
        )
        self.terrain.render(self.app.render)

        # Spawn animals using config values
        self.spawn_animals()

        # Set up collision detection
        self.setup_collision_detection()

    def setup_ui(self):
        """Initialize the UI system."""
        self.ui_manager = UIManager(self.app)

        # Set up UI callbacks
        callbacks = {
            'start_game': self.start_gameplay,
            'settings': self.show_settings,
            'quit': self.quit_game,
            'resume': self.resume_game,
            'restart': self.restart_game,
            'main_menu': self.show_main_menu,
            'back_to_main': self.show_main_menu,
            'settings_data': {  # Default settings data
                'volume': 0.8,
                'sensitivity': 0.2,
                'fullscreen': False,
                'vsync': True
            }
        }

        self.ui_manager.setup_menus(callbacks)

        # Show main menu initially
        self.ui_manager.show_menu('main')
        
        # Enable mouse for menu interaction
        if hasattr(self.app, 'enableMouse'):
            self.app.enableMouse()

    def setup_ui_controls(self):
        """Set up input controls for UI interactions."""
        # Escape key for pause menu
        self.app.accept('escape', self.handle_escape)

    def handle_escape(self):
        """Handle escape key press for pause menu."""
        if self.game_state == 'playing':
            self.pause_game()
        elif self.game_state == 'paused':
            self.resume_game()

    def start_gameplay(self):
        """Start the actual gameplay."""
        self.game_state = 'playing'
        self.ui_manager.hide_menus()

        # Enable mouse for mouse look
        if hasattr(self.app, 'disableMouse') and hasattr(self.app, 'mouseWatcherNode'):
            self.app.enableMouse()
            if not hasattr(self.app, 'mouseWatcherNode') or self.app.mouseWatcherNode is None:
                # Initialize mouse watcher if needed
                self.app.defineVirtualMouse(True)

        # Set up player controls
        if self.player and hasattr(self.player, 'setup_controls'):
            self.player.setup_controls()

        # Set up HUD for player
        if self.player:
            self.ui_manager.setup_hud(self.player)
            self.ui_manager.toggle_hud_visibility(True)

        print("Gameplay started")

    def pause_game(self):
        """Pause the game and show pause menu."""
        self.game_state = 'paused'
        
        # Enable mouse for menu navigation
        if hasattr(self.app, 'enableMouse'):
            self.app.enableMouse()
        
        self.ui_manager.show_menu('pause')
        self.ui_manager.toggle_hud_visibility(False)

    def resume_game(self):
        """Resume the game from pause."""
        self.game_state = 'playing'
        
        # Re-enable mouse look
        if hasattr(self.app, 'disableMouse') and hasattr(self.app, 'mouseWatcherNode'):
            self.app.enableMouse()
            if not hasattr(self.app, 'mouseWatcherNode') or self.app.mouseWatcherNode is None:
                self.app.defineVirtualMouse(True)
        
        self.ui_manager.hide_menus()
        self.ui_manager.toggle_hud_visibility(True)

    def restart_game(self):
        """Restart the game."""
        self.cleanup_game()
        self.initialize_components()
        self.start_gameplay()

    def show_main_menu(self):
        """Show the main menu."""
        self.game_state = 'main_menu'
        
        # Enable mouse for menu interaction
        if hasattr(self.app, 'enableMouse'):
            self.app.enableMouse()
        
        self.ui_manager.show_menu('main')
        self.ui_manager.toggle_hud_visibility(False)

    def show_settings(self):
        """Show the settings menu."""
        self.ui_manager.show_menu('settings')

    def quit_game(self):
        """Quit the game."""
        self.app.userExit()

    def game_over(self):
        """Handle game over state."""
        self.game_state = 'game_over'

        # Update game over screen with final score
        if self.ui_manager and self.ui_manager.hud:
            hud = self.ui_manager.hud
            self.ui_manager.update_game_over_score(hud.score, hud.kills, hud.accuracy)

        self.ui_manager.show_menu('game_over')
        self.ui_manager.toggle_hud_visibility(False)

    def spawn_animals(self):
        """Spawn initial animals in the game world using config values."""
        animal_cfg = config.ANIMAL_CONFIG
        spawn_radius = animal_cfg['spawn_radius']

        # Spawn deer using config values
        for _ in range(animal_cfg['deer_count']):
            x = random.uniform(-spawn_radius, spawn_radius)
            y = random.uniform(-spawn_radius, spawn_radius)
            z = self.terrain.get_height(x, y) if self.terrain else 0.0
            deer = Deer(Vec3(x, y, z))
            deer.render(self.app.render)
            self.animals.append(deer)
            # Add to collision detection
            if self.player:
                self.player.add_animal_to_collision(deer)

        # Spawn rabbits using config values
        for _ in range(animal_cfg['rabbit_count']):
            x = random.uniform(-spawn_radius, spawn_radius)
            y = random.uniform(-spawn_radius, spawn_radius)
            z = self.terrain.get_height(x, y) if self.terrain else 0.0
            rabbit = Rabbit(Vec3(x, y, z))
            rabbit.render(self.app.render)
            self.animals.append(rabbit)
            # Add to collision detection
            if self.player:
                self.player.add_animal_to_collision(rabbit)

    def setup_lighting(self):
        """Set up basic lighting for the scene."""
        from panda3d.core import DirectionalLight, Vec4, Vec3

        # Create directional light (sun)
        dlight = DirectionalLight('sun')
        dlight.setColor(Vec4(0.8, 0.8, 0.8, 1))
        dlight.setDirection(Vec3(-1, -1, -1))

        # Attach light to render
        dlnp = self.app.render.attachNewNode(dlight)
        self.app.render.setLight(dlnp)

        # Set ambient light
        from panda3d.core import AmbientLight
        alight = AmbientLight('ambient')
        alight.setColor(Vec4(0.3, 0.3, 0.3, 1))
        alnp = self.app.render.attachNewNode(alight)
        self.app.render.setLight(alnp)

    def update(self, task):
        """Update game state each frame."""
        if not self.is_running:
            return task.done

        # Calculate delta time
        current_time = self.app.taskMgr.globalClock.getFrameTime()
        if self.last_time == 0:
            dt = 0.016  # Default 60 FPS
        else:
            dt = current_time - self.last_time
        self.last_time = current_time

        # Only update game components if actively playing
        if self.game_state == 'playing':
            # Update game components
            if self.player:
                self.player.update(dt)

            # Update animals
            player_pos = self.player.position if self.player else Vec3(0, 0, 0)
            alive_animals = []

            for animal in self.animals:
                terrain_height = self.terrain.get_height(animal.position.x, animal.position.y) if self.terrain else 0.0
                animal.update(dt, player_pos, terrain_height)

                if not animal.is_dead():
                    alive_animals.append(animal)
                else:
                    # Handle animal death - add score
                    self.handle_animal_killed(animal)
                    # Remove dead animal from collision detection
                    if self.player:
                        self.player.remove_animal_from_collision(animal)
                    animal.cleanup()

            self.animals = alive_animals

            # Check for game over conditions (e.g., player health)
            if self.player and hasattr(self.player, 'health') and self.player.health <= 0:
                self.game_over()

        # Update UI regardless of game state
        if self.ui_manager:
            self.ui_manager.update_hud(dt)

        # Render the scene (Panda3D handles this automatically)
        # Additional rendering setup can be done here if needed

        return task.cont

    def stop(self):
        """Stop the game loop."""
        self.is_running = False
        if self.player:
            self.player.cleanup()

        # Clean up animals
        for animal in self.animals:
            animal.cleanup()
        self.animals.clear()

        # Clean up terrain
        if self.terrain:
            self.terrain.cleanup()

        # Clean up UI
        if self.ui_manager:
            self.ui_manager.cleanup()

        print("Hunting Simulator Game Stopped")

    def handle_animal_killed(self, animal):
        """Handle when an animal is killed - update score and statistics."""
        if self.ui_manager and self.ui_manager.hud:
            # Award points based on animal type
            points = 10  # Base points
            if hasattr(animal, 'species'):
                if animal.species.lower() == 'deer':
                    points = 50
                elif animal.species.lower() == 'rabbit':
                    points = 25

            self.ui_manager.add_score(points)
            self.ui_manager.record_shot(hit=True)
            self.ui_manager.show_message(f"{animal.species} killed! +{points} points", 2.0)

    def cleanup_game(self):
        """Clean up current game session for restart."""
        # Clean up animals
        for animal in self.animals:
            if self.player:
                self.player.remove_animal_from_collision(animal)
            animal.cleanup()
        self.animals.clear()

        # Clean up player
        if self.player:
            self.player.cleanup()
            self.player = None

        # Clean up terrain
        if self.terrain:
            self.terrain.cleanup()
            self.terrain = None

        # Reset UI but keep the manager
        if self.ui_manager:
            self.ui_manager.hide_menus()
            if hasattr(self.ui_manager, 'hud') and self.ui_manager.hud:
                self.ui_manager.hud.cleanup()
                self.ui_manager.hud = None