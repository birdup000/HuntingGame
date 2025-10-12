"""
Core game module for the 3D Hunting Simulator.
Handles the main game loop and initialization.
"""

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from player.player import Player
from environment.pbr_terrain import PBRTerrain, OptimizedTerrainRenderer
from environment.decor import DecorManager
from environment.sky import SkyDome
from animals.animal import Deer, Rabbit
from ui.menus import UIManager, SettingsMenu
from panda3d.core import Vec3, CardMaker, TransparencyAttrib
import random
import config

# Import advanced graphics systems
from graphics.materials import TerrainPBR, EnvironmentMaterials
from graphics.lighting import DynamicLighting
from graphics.weather import WeatherSystem
from graphics.foliage import FoliageRenderer, GrassField

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
        self.game_time = 0.0
        self.sky = None
        self.rocks = []
        
        # Initialize advanced graphics systems
        self.terrain_pbr = TerrainPBR()
        self.env_materials = EnvironmentMaterials()
        self.dynamic_lighting = DynamicLighting(self.app.render)
        self.weather_system = WeatherSystem(self.app.render)
        self.foliage_renderer = FoliageRenderer(self.app.render)
        self.decor_manager = None

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
        """Set up environment with procedural terrain and advanced graphics."""
        # Set up advanced lighting system
        self.dynamic_lighting.setup_advanced_lighting()
        
        # Set up weather system
        import random
        weather_types = ['clear', 'partly_cloudy', 'overcast']  # Starting weather options
        initial_weather = random.choice(weather_types)
        self.weather_system.set_weather(initial_weather, random.uniform(0.1, 0.6))
        
        # Create procedural terrain using config values with PBR
        terrain_cfg = config.TERRAIN_CONFIG
        self.terrain = PBRTerrain(
            width=terrain_cfg['width'],
            height=terrain_cfg['height'],
            scale=terrain_cfg['scale'],
            octaves=terrain_cfg['octaves']
        )
        self.terrain.render(self.app.render)

        # Set up optimized terrain rendering
        self.terrain_renderer = OptimizedTerrainRenderer(self.app.render)
        self.terrain_renderer.add_terrain(self.terrain)

        # Ensure terrain is properly positioned and visible
        if self.terrain.terrain_node:
            self.terrain.terrain_node.setPos(0, 0, 0)  # Center terrain

        # Set up advanced grass fields
        self._setup_grass_fields()
        self._setup_tree_clusters()
        self._spawn_rock_formations()

        if not self.decor_manager:
            self.decor_manager = DecorManager(self.app, self.terrain)
        else:
            self.decor_manager.cleanup()
            self.decor_manager.terrain = self.terrain
        self.decor_manager.populate()
        
        # Spawn animals using config values
        self.spawn_animals()

        # Set up collision detection after animals are created
        self.setup_collision_detection()

        if not self.sky:
            self.sky = SkyDome(self.app)

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
        
        # Ensure mouse is visible for UI interaction
        if hasattr(self.app, 'enableMouse'):
            self.app.enableMouse()

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

        # Hide mouse cursor for first-person controls
        if hasattr(self.app, 'openPointer'):
            # Use Panda3D's proper method to hide cursor
            try:
                self.app.openPointer(0)  # Hide cursor
            except:
                pass
        elif hasattr(self.app, 'win') and hasattr(self.app.win, 'requestProperties'):
            # Alternative method to hide cursor
            try:
                props = self.app.win.get_properties()
                props.set_cursor_hidden(True)
                self.app.win.request_properties(props)
            except:
                pass
        
        # Initialize mouse watcher if needed
        if not hasattr(self.app, 'mouseWatcherNode') or self.app.mouseWatcherNode is None:
            if hasattr(self.app, 'defineVirtualMouse'):
                self.app.defineVirtualMouse(True)
        elif hasattr(self.app, 'disableMouse'):
            self.app.disableMouse()

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
        
        # Show mouse cursor for menu navigation
        if hasattr(self.app, 'openPointer'):
            try:
                self.app.openPointer(1)  # Show cursor
            except:
                pass
        elif hasattr(self.app, 'win') and hasattr(self.app.win, 'requestProperties'):
            try:
                props = self.app.win.get_properties()
                props.set_cursor_hidden(False)
                self.app.win.request_properties(props)
            except:
                pass
        
        # Enable mouse for menu interaction
        if hasattr(self.app, 'enableMouse'):
            self.app.enableMouse()
        
        self.ui_manager.show_menu('pause')
        self.ui_manager.toggle_hud_visibility(False)

    def resume_game(self):
        """Resume the game from pause."""
        self.game_state = 'playing'
        
        # Hide mouse cursor for first-person controls
        if hasattr(self.app, 'openPointer'):
            try:
                self.app.openPointer(0)  # Hide cursor
            except:
                pass
        elif hasattr(self.app, 'win') and hasattr(self.app.win, 'requestProperties'):
            try:
                props = self.app.win.get_properties()
                props.set_cursor_hidden(True)
                self.app.win.request_properties(props)
            except:
                pass
        
        # Enable mouse look
        if not hasattr(self.app, 'mouseWatcherNode') or self.app.mouseWatcherNode is None:
            if hasattr(self.app, 'defineVirtualMouse'):
                self.app.defineVirtualMouse(True)
        elif hasattr(self.app, 'disableMouse'):
            self.app.disableMouse()
        
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
        
        # Show mouse cursor for menu interaction
        if hasattr(self.app, 'openPointer'):
            try:
                self.app.openPointer(1)  # Show cursor
            except:
                pass
        elif hasattr(self.app, 'win') and hasattr(self.app.win, 'requestProperties'):
            try:
                props = self.app.win.get_properties()
                props.set_cursor_hidden(False)
                self.app.win.request_properties(props)
            except:
                pass
        
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
            # Ensure deer don't spawn too close to player spawn
            x, y = 0, 0
            attempts = 0
            while attempts < 20 and (x**2 + y**2 < 40):  # Keep distance from center (>6.3 units)
                x = random.uniform(-spawn_radius, spawn_radius)
                y = random.uniform(-spawn_radius, spawn_radius)
                attempts += 1
            z = self.terrain.get_height(x, y) if self.terrain else 0.0
            deer = Deer(Vec3(x, y, z))
            deer.render(self.app.render)
            self.animals.append(deer)
            # Add to collision detection
            if self.player:
                self.player.add_animal_to_collision(deer)

        # Spawn rabbits using config values
        for _ in range(animal_cfg['rabbit_count']):
            x, y = 0, 0
            attempts = 0
            while attempts < 10 and (x**2 + y**2 < 10):  # Keep some distance but closer than deer
                x = random.uniform(-spawn_radius, spawn_radius)
                y = random.uniform(-spawn_radius, spawn_radius)
                attempts += 1
            z = self.terrain.get_height(x, y) if self.terrain else 0.0
            rabbit = Rabbit(Vec3(x, y, z))
            rabbit.render(self.app.render)
            self.animals.append(rabbit)
            # Add to collision detection
            if self.player:
                self.player.add_animal_to_collision(rabbit)

    def setup_lighting(self):
        """Set up realistic lighting for the scene."""
        # Lighting is now handled by DynamicLighting class
        # This method kept for backward compatibility
        pass

    def _apply_terrain_materials(self):
        """Apply PBR materials to terrain based on height and conditions."""
        if not self.terrain or not self.terrain.terrain_node:
            return
            
        # Sample terrain heights to determine material zones
        terrain_size = config.TERRAIN_CONFIG['width']
        
        # Apply different materials to terrain patches based on height
        for x in range(-terrain_size//4, terrain_size//4, 10):
            for y in range(-terrain_size//4, terrain_size//4, 10):
                height = self.terrain.get_height(x, y)
                material = self.terrain_pbr.get_material_for_height(height)
                
                # Create material region
                region_node = self.terrain.terrain_node.find(f"**/terrain_patch_{x}_{y}")
                if not region_node.isEmpty():
                    material.apply_to(region_node)
                else:
                    # Apply to all terrain children
                    material.apply_to(self.terrain.terrain_node)
        
        print("PBR materials applied to terrain")

    def _setup_grass_fields(self):
        """Create and position grass fields for enhanced realism."""
        terrain_cfg = config.TERRAIN_CONFIG
        
        # Create multiple grass fields across the terrain
        field_configs = [
            {'width': 40, 'height': 30, 'density': 500},
            {'width': 30, 'height': 25, 'density': 300},
            {'width': 35, 'height': 20, 'density': 400}
        ]
        
        for i, cfg in enumerate(field_configs):
            field = GrassField(
                width=cfg['width'],
                height=cfg['height'], 
                density=cfg['density'],
                render_node=self.app.render
            )
            
            # Position fields around the map
            positions = [(30, 30), (-30, 20), (0, -25)]
            if i < len(positions):
                self.foliage_renderer.add_grass_field(field)
                if getattr(field, 'grass_node', None):
                    field.grass_node.setPos(positions[i][0], positions[i][1], 0)
        
        print(f"Created {len(field_configs)} grass fields with {sum(c['density'] for c in field_configs)} grass blades")

    def _setup_tree_clusters(self):
        positions = [
            (Vec3(25, 32, 0), 8, 12),
            (Vec3(-28, 18, 0), 6, 10),
            (Vec3(-10, -35, 0), 10, 15)
        ]
        for center, count, radius in positions:
            if self.terrain:
                z = self.terrain.get_height(center.x, center.y)
                center.setZ(z)
            self.foliage_renderer.create_tree_cluster(center, count, radius, self.terrain)

    def _spawn_rock_formations(self):
        if not hasattr(self.app, 'loader'):
            return
        rock_positions = [
            Vec3(12, 18, 0),
            Vec3(-22, -15, 0),
            Vec3(18, -28, 0)
        ]
        # Cleanup existing rocks before creating new ones
        for rock in self.rocks:
            rock.removeNode()
        self.rocks = []

        if self.decor_manager:
            self.decor_manager.cleanup()
            self.decor_manager = None

        try:
            base_model = self.app.loader.loadModel('models/misc/sphere')
        except Exception:
            base_model = None

        for pos in rock_positions:
            z = self.terrain.get_height(pos.x, pos.y) if self.terrain else 0
            if base_model:
                rock = base_model.copyTo(self.app.render)
            else:
                cm = CardMaker('rock-card')
                cm.setFrame(-0.6, 0.6, -0.6, 0.6)
                rock = self.app.render.attachNewNode('rock')
                quad = rock.attachNewNode(cm.generate())
                quad.setBillboardPointEye()
                quad.setTransparency(TransparencyAttrib.MAlpha)
            rock.setPos(pos.x, pos.y, z)
            rock.setScale(2.5 + random.uniform(-0.8, 1.2))
            rock.setColor(0.38 + random.uniform(-0.05, 0.05), 0.37, 0.35, 1.0)
            rock.setShaderAuto()
            self.rocks.append(rock)

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
            # Update advanced graphics systems
            self._update_graphics_systems(dt)
            self.foliage_renderer.update(dt, self.game_time)
            
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
        
    def _update_graphics_systems(self, dt):
        """Update advanced graphics systems for photorealistic rendering."""
        if not hasattr(self, 'game_time'):
            self.game_time = 0.0
            
        self.game_time += dt
        
        # Update dynamic lighting
        # Simulate time progression (1 minute = 1 real second)
        virtual_hour = (self.game_time * 0.016) % 24
        self.dynamic_lighting.update_time_of_day(virtual_hour)
        
        # Update weather system
        self.weather_system.update_weather(dt)
        
        # Adjust lighting for current weather
        # Get weather intensities safely
        precipitation = getattr(self.weather_system, 'precipitation', None)
        rain_intensity = precipitation.intensity if precipitation else 0
        
        fog_effect = getattr(self.weather_system, 'fog_effect', None)
        fog_density = fog_effect.density if fog_effect else 0
        # Already handled above
        self.dynamic_lighting.adjust_for_weather(rain_intensity, fog_density)

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

        # Clean up sky and props
        if self.sky:
            self.sky.cleanup()
            self.sky = None
        for rock in self.rocks:
            rock.removeNode()
        self.rocks = []

        if self.decor_manager:
            self.decor_manager.cleanup()
            self.decor_manager = None

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

        if self.decor_manager:
            self.decor_manager.cleanup()

        # Reset UI but keep the manager
        if self.ui_manager:
            self.ui_manager.hide_menus()
            if hasattr(self.ui_manager, 'hud') and self.ui_manager.hud:
                self.ui_manager.hud.cleanup()
                self.ui_manager.hud = None