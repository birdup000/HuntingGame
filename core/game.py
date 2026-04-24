"""
Core game module for the 3D Hunting Simulator.
Handles the main game loop and initialization.
"""

import logging
from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionHandlerQueue
from player.player import Player
from environment.pbr_terrain import PBRTerrain, OptimizedTerrainRenderer
from environment.decor import DecorManager
from environment.simple_sky import SimpleSkyDome
from animals.animal import Deer, Rabbit, Bear, Wolf, Bird
from ui.menus import UIManager
from panda3d.core import Vec3, CardMaker, TransparencyAttrib
import random
import config

try:
    from audio.audio_manager import AudioManager
except ImportError:
    AudioManager = None

try:
    from utils.save_manager import SaveManager
except ImportError:
    SaveManager = None

from typing import Dict, Optional

# Import advanced graphics systems
try:
    from graphics.materials import TerrainPBR, EnvironmentMaterials
    from graphics.lighting import DynamicLighting
    from graphics.weather import WeatherSystem
    from graphics.foliage import FoliageRenderer, GrassField
except ImportError:
    # Handle cases where graphics modules are incomplete
    TerrainPBR = None
    EnvironmentMaterials = None
    DynamicLighting = None
    WeatherSystem = None
    FoliageRenderer = None
    GrassField = None

class Game:
    """Main game class that manages the game state and loop."""

    def __init__(self, app: ShowBase):
        """Initialize the game with the Panda3D application."""
        try:
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
            self.decor_manager = None
            self.animal_targets: Dict[str, int] = {}
            self._pending_objective_counts: Dict[str, int] = {}
            self._last_reported_objective_counts: Optional[Dict[str, int]] = None
            self._objective_initialized = False
            self.difficulty = 'normal'
            self._auto_save_timer = 0.0
            self._animal_respawn_timer = 0.0
            self._animal_respawn_interval = 45.0  # Respawn animals every 45 seconds
            
            # Initialize save manager
            try:
                if SaveManager is not None:
                    self.save_manager = SaveManager()
                else:
                    self.save_manager = None
            except Exception as e:
                logging.warning(f"Failed to initialize save manager: {e}")
                self.save_manager = None
            
            # Initialize audio manager
            try:
                if AudioManager is not None:
                    self.audio_manager = AudioManager(self.app)
                else:
                    self.audio_manager = None
            except Exception as e:
                logging.warning(f"Failed to initialize audio: {e}")
                self.audio_manager = None
            
            # Initialize advanced graphics systems with error handling
            self._initialize_graphics_systems()
            
            # Initialize error tracking
            self.error_count = 0
            self.max_errors_before_crash = 10
            self.last_error_time = 0.0
            
            logging.info("Game initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize game: {e}")
            raise

    def _initialize_graphics_systems(self):
        """Initialize advanced graphics systems with proper error handling."""
        try:
            if TerrainPBR is not None:
                try:
                    self.terrain_pbr = TerrainPBR()
                    logging.info("Terrain PBR system initialized")
                except Exception as e:
                    logging.warning(f"Failed to initialize TerrainPBR: {e}")
                    self.terrain_pbr = None
            else:
                self.terrain_pbr = None
                
            if EnvironmentMaterials is not None:
                try:
                    self.env_materials = EnvironmentMaterials()
                    logging.info("Environment materials system initialized")
                except Exception as e:
                    logging.warning(f"Failed to initialize EnvironmentMaterials: {e}")
                    self.env_materials = None
            else:
                self.env_materials = None
                
            if DynamicLighting is not None:
                try:
                    self.dynamic_lighting = DynamicLighting(self.app.render)
                    logging.info("Dynamic lighting system initialized")
                except Exception as e:
                    logging.warning(f"Failed to initialize DynamicLighting: {e}")
                    self.dynamic_lighting = None
            else:
                self.dynamic_lighting = None
                
            if WeatherSystem is not None:
                try:
                    self.weather_system = WeatherSystem(self.app.render)
                    logging.info("Weather system initialized")
                except Exception as e:
                    logging.warning(f"Failed to initialize WeatherSystem: {e}")
                    self.weather_system = None
            else:
                self.weather_system = None
                
            if FoliageRenderer is not None:
                try:
                    self.foliage_renderer = FoliageRenderer(self.app.render)
                    logging.info("Foliage renderer initialized")
                except Exception as e:
                    logging.warning(f"Failed to initialize FoliageRenderer: {e}")
                    self.foliage_renderer = None
            else:
                self.foliage_renderer = None
                
        except Exception as e:
            logging.error(f"Error during graphics system initialization: {e}")
            # Set all graphics systems to None if initialization fails
            self.terrain_pbr = None
            self.env_materials = None
            self.dynamic_lighting = None
            self.weather_system = None
            self.foliage_renderer = None

    def log_error(self, error_type: str, error_message: str, context: str = ""):
        """Log errors with context and track error frequency."""
        current_time = self.app.taskMgr.globalClock.getFrameTime() if hasattr(self.app, 'taskMgr') else 0.0
        time_since_last_error = current_time - self.last_error_time
        
        # Log the error
        error_log = f"[{error_type}] {error_message}"
        if context:
            error_log += f" - Context: {context}"
        logging.error(error_log)
        
        # Track error frequency
        self.error_count += 1
        self.last_error_time = current_time
        
        # Check for error flood (too many errors in short time)
        if self.error_count > 5 and time_since_last_error < 1.0:
            logging.critical("Error flood detected! Too many errors in short time period.")
            if self.error_count >= self.max_errors_before_crash:
                logging.critical("Too many errors, shutting down game to prevent instability.")
                self.app.userExit()

    def start(self):
        """Start the game loop with error handling."""
        try:
            self.is_running = True
            logging.info("Hunting Simulator Game Started")

            # Initialize game components
            self.initialize_components()

            # Set up the main game loop
            self.app.taskMgr.add(self.update, 'update')
            
        except Exception as e:
            logging.error(f"Failed to start game: {e}")
            self.is_running = False
            raise

    def initialize_components(self):
        """Initialize all game components with error handling."""
        try:
            # Initialize UI system first
            self.setup_ui()

            # Initialize player (but don't set up controls yet)
            try:
                self.player = Player(self.app, setup_controls=False)  # Pass flag to avoid control setup
                logging.info("Player initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize player: {e}")
                self.player = None

            # Set up basic environment (ground plane)
            try:
                self.setup_environment()
                logging.info("Environment setup completed")
            except Exception as e:
                logging.error(f"Failed to setup environment: {e}")
                # Continue with minimal environment

            # Set up lighting
            try:
                self.setup_lighting()
                logging.info("Lighting setup completed")
            except Exception as e:
                logging.error(f"Failed to setup lighting: {e}")

            # Adjust player position to terrain after environment is created
            if self.player:
                try:
                    self.player.adjust_to_terrain()
                    logging.info("Player position adjusted to terrain")
                except Exception as e:
                    logging.warning(f"Failed to adjust player to terrain: {e}")

            # Override player's projectile hit callback for visual feedback
            if self.player and self.player.collision_manager:
                try:
                    self.player.collision_manager.add_hit_callback(self.on_projectile_hit)
                    logging.info("Projectile hit callback registered")
                except Exception as e:
                    logging.warning(f"Failed to register hit callback: {e}")

            # Set up input handling for UI
            try:
                self.setup_ui_controls()
                logging.info("UI controls setup completed")
            except Exception as e:
                logging.error(f"Failed to setup UI controls: {e}")

        except Exception as e:
            logging.error(f"Critical error during component initialization: {e}")
            raise

    def setup_collision_detection(self):
        """Set up collision detection for animals and projectiles with error handling."""
        try:
            # Add all existing animals to collision detection
            for animal in self.animals:
                if self.player and hasattr(self.player, 'add_animal_to_collision'):
                    try:
                        self.player.add_animal_to_collision(animal)
                    except Exception as e:
                        logging.warning(f"Failed to add animal to collision detection: {e}")
                else:
                    logging.warning("Player not available for collision setup")
        except Exception as e:
            logging.error(f"Error during collision detection setup: {e}")

    def setup_environment(self):
        """Set up environment with procedural terrain and advanced graphics with error handling."""
        try:
            # Set up advanced lighting system
            if self.dynamic_lighting:
                try:
                    self.dynamic_lighting.setup_advanced_lighting()
                    logging.info("Advanced lighting setup completed")
                except Exception as e:
                    logging.warning(f"Failed to setup advanced lighting: {e}")
            else:
                logging.warning("Dynamic lighting not available")

            # Set up weather system
            if self.weather_system:
                try:
                    import random
                    weather_types = ['clear', 'partly_cloudy', 'overcast']  # Starting weather options
                    initial_weather = random.choice(weather_types)
                    self.weather_system.set_weather(initial_weather, random.uniform(0.1, 0.6))
                    logging.info(f"Weather set to {initial_weather}")
                except Exception as e:
                    logging.warning(f"Failed to setup weather: {e}")
            else:
                logging.warning("Weather system not available")
            
            # Create procedural terrain using config values with PBR
            try:
                terrain_cfg = config.TERRAIN_CONFIG
                self.terrain = PBRTerrain(
                    width=terrain_cfg['width'],
                    height=terrain_cfg['height'],
                    scale=terrain_cfg['scale'],
                    octaves=terrain_cfg['octaves']
                )
                self.terrain.render(self.app.render)
                logging.info("Terrain created and rendered")
            except Exception as e:
                logging.error(f"Failed to create terrain: {e}")
                # Create fallback terrain
                self._create_fallback_terrain()

            # Set up optimized terrain rendering
            try:
                self.terrain_renderer = OptimizedTerrainRenderer(self.app.render)
                self.terrain_renderer.add_terrain(self.terrain)
                logging.info("Optimized terrain rendering setup completed")
            except Exception as e:
                logging.warning(f"Failed to setup optimized terrain rendering: {e}")

            # Ensure terrain is properly positioned and visible
            if self.terrain and hasattr(self.terrain, 'terrain_node') and self.terrain.terrain_node:
                self.terrain.terrain_node.setPos(0, 0, 0)  # Center terrain

            # Set up advanced grass fields
            try:
                self._setup_grass_fields()
                logging.info("Grass fields setup completed")
            except Exception as e:
                logging.warning(f"Failed to setup grass fields: {e}")

            try:
                self._setup_tree_clusters()
                logging.info("Tree clusters setup completed")
            except Exception as e:
                logging.warning(f"Failed to setup tree clusters: {e}")

            try:
                self._spawn_rock_formations()
                logging.info("Rock formations setup completed")
            except Exception as e:
                logging.warning(f"Failed to spawn rock formations: {e}")

            # Set up decor manager
            try:
                if not self.decor_manager:
                    self.decor_manager = DecorManager(self.app, self.terrain)
                else:
                    self.decor_manager.cleanup()
                    self.decor_manager.terrain = self.terrain
                self.decor_manager.populate()
                logging.info("Decor manager populated")
            except Exception as e:
                logging.warning(f"Failed to populate decor manager: {e}")

            # Spawn animals using config values
            try:
                self.spawn_animals()
                logging.info("Animals spawned successfully")
            except Exception as e:
                logging.error(f"Failed to spawn animals: {e}")

            # Set up collision detection after animals are spawned
            try:
                self.setup_collision_detection()
                logging.info("Collision detection setup completed")
            except Exception as e:
                logging.warning(f"Failed to setup collision detection: {e}")

            # Create sky dome
            try:
                if not self.sky:
                    self.sky = SimpleSkyDome(self.app, radius=1000.0)
                    logging.info("Sky dome created")
            except Exception as e:
                logging.warning(f"Failed to create sky dome: {e}")

        except Exception as e:
            logging.error(f"Critical error during environment setup: {e}")
            self._create_minimal_environment()

    def _create_fallback_terrain(self):
        """Create a minimal fallback terrain if main terrain creation fails."""
        try:
            # Create a simple flat plane as fallback
            from panda3d.core import Geom, GeomNode, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles
            format = GeomVertexFormat.getV3n3c4()
            vdata = GeomVertexData('fallback_terrain', format, Geom.UHStatic)
            vertex = GeomVertexWriter(vdata, 'vertex')
            normal = GeomVertexWriter(vdata, 'normal')
            color = GeomVertexWriter(vdata, 'color')
            
            # Create a simple flat plane
            vertices = [
                (-50, -50, 0), (50, -50, 0), (50, 50, 0), (-50, 50, 0)
            ]
            
            for v in vertices:
                vertex.addData3f(*v)
                normal.addData3f(0, 0, 1)
                color.addData4f(0.5, 0.8, 0.3, 1)  # Green color
            
            prim = GeomTriangles(Geom.UHStatic)
            prim.addVertices(0, 1, 2)
            prim.addVertices(0, 2, 3)
            
            geom = Geom(vdata)
            geom.addPrimitive(prim)
            node = GeomNode('fallback_terrain')
            node.addGeom(geom)
            
            terrain_node = self.app.render.attachNewNode(node)
            terrain_node.setPos(0, 0, 0)
            
            self.terrain = type('FallbackTerrain', (), {'terrain_node': terrain_node, 'get_height': lambda x, y: 0.0})()
            logging.info("Fallback terrain created")
            
        except Exception as e:
            logging.error(f"Failed to create fallback terrain: {e}")

    def _create_minimal_environment(self):
        """Create minimal environment with just basic elements."""
        try:
            # Create a simple ground plane
            from panda3d.core import Geom, GeomNode, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles
            format = GeomVertexFormat.getV3n3c4()
            vdata = GeomVertexData('minimal_terrain', format, Geom.UHStatic)
            vertex = GeomVertexWriter(vdata, 'vertex')
            normal = GeomVertexWriter(vdata, 'normal')
            color = GeomVertexWriter(vdata, 'color')
            
            # Create a simple flat plane
            vertices = [
                (-100, -100, 0), (100, -100, 0), (100, 100, 0), (-100, 100, 0)
            ]
            
            for v in vertices:
                vertex.addData3f(*v)
                normal.addData3f(0, 0, 1)
                color.addData4f(0.4, 0.6, 0.2, 1)  # Simple green color
            
            prim = GeomTriangles(Geom.UHStatic)
            prim.addVertices(0, 1, 2)
            prim.addVertices(0, 2, 3)
            
            geom = Geom(vdata)
            geom.addPrimitive(prim)
            node = GeomNode('minimal_terrain')
            node.addGeom(geom)
            
            terrain_node = self.app.render.attachNewNode(node)
            terrain_node.setPos(0, 0, 0)
            
            self.terrain = type('MinimalTerrain', (), {'terrain_node': terrain_node, 'get_height': lambda x, y: 0.0})()
            logging.info("Minimal environment created")
            
        except Exception as e:
            logging.error(f"Failed to create minimal environment: {e}")


    def setup_ui(self):
        """Initialize the UI system with error handling."""
        try:
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
                'set_difficulty': self.set_difficulty,
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
                
            logging.info("UI system initialized")
            
        except Exception as e:
            logging.error(f"Failed to setup UI: {e}")
            self.ui_manager = None

    def setup_ui_controls(self):
        """Set up input controls for UI interactions."""
        # Escape key for pause menu
        self.app.accept('escape', self.handle_escape)
        # F5 key for toggling debug lights
        self.app.accept('f5', self.toggle_debug_lights)
        # F9 to save, F10 to load
        self.app.accept('f9', self.save_game)
        self.app.accept('f10', self.load_game)

        # Ensure mouse is visible for UI interaction
        if hasattr(self.app, 'enableMouse'):
            self.app.enableMouse()

    def save_game(self):
        """Save the current game state."""
        if self.game_state != 'playing':
            logging.debug("Cannot save outside of gameplay")
            return
        if self.save_manager:
            if self.save_manager.save_game(self, slot=1):
                if self.ui_manager:
                    self.ui_manager.show_message("Game Saved!", 2.0, (0.3, 1.0, 0.3, 1.0))
            else:
                if self.ui_manager:
                    self.ui_manager.show_message("Save Failed!", 2.0, (1.0, 0.3, 0.3, 1.0))

    def load_game(self):
        """Load the game state from save."""
        if self.game_state != 'playing':
            logging.debug("Cannot load outside of gameplay")
            return
        if self.save_manager and self.save_manager.has_save(1):
            if self.save_manager.load_game(self, slot=1):
                if self.ui_manager:
                    self.ui_manager.show_message("Game Loaded!", 2.0, (0.3, 1.0, 0.3, 1.0))
                self._sync_hud_objectives(force=True)
            else:
                if self.ui_manager:
                    self.ui_manager.show_message("Load Failed!", 2.0, (1.0, 0.3, 0.3, 1.0))
        else:
            if self.ui_manager:
                self.ui_manager.show_message("No Save Found!", 2.0, (1.0, 0.8, 0.3, 1.0))

    def handle_escape(self):
        """Handle escape key press for pause menu."""
        if self.game_state == 'playing':
            self.pause_game()
        elif self.game_state == 'paused':
            self.resume_game()

    def toggle_debug_lights(self):
        """Toggle debug light visualizations."""
        if self.dynamic_lighting:
            self.dynamic_lighting.toggle_debug_lights()
        else:
            logging.warning("Dynamic lighting not available, cannot toggle debug lights")

    def start_gameplay(self):
        """Start the actual gameplay with error handling."""
        try:
            self.game_state = 'playing'
            
            # Hide menus
            if self.ui_manager:
                self.ui_manager.hide_menus()

            # Hide mouse cursor for first-person controls
            try:
                if hasattr(self.app, 'openPointer'):
                    self.app.openPointer(0)  # Hide cursor
                elif hasattr(self.app, 'win') and hasattr(self.app.win, 'request_properties'):
                    props = self.app.win.get_properties()
                    props.set_cursor_hidden(True)
                    self.app.win.request_properties(props)
            except Exception as e:
                logging.warning(f"Failed to hide cursor: {e}")

            # Initialize mouse watcher if needed
            try:
                if not hasattr(self.app, 'mouseWatcherNode') or self.app.mouseWatcherNode is None:
                    if hasattr(self.app, 'defineVirtualMouse'):
                        self.app.defineVirtualMouse(True)
                elif hasattr(self.app, 'disableMouse'):
                    self.app.disableMouse()
            except Exception as e:
                logging.warning(f"Failed to setup mouse watcher: {e}")

            # Set up player controls
            if self.player and hasattr(self.player, 'setup_controls'):
                try:
                    self.player.setup_controls()
                    # Adjust to terrain when starting gameplay
                    self.player.adjust_to_terrain()
                    logging.info("Player controls initialized")
                except Exception as e:
                    logging.error(f"Failed to setup player controls: {e}")

            # Set up HUD for player
            if self.player and self.ui_manager:
                try:
                    self.ui_manager.setup_hud(self.player)
                    self.ui_manager.toggle_hud_visibility(True)
                    self._sync_hud_objectives(force=True)
                    logging.info("HUD setup completed")
                except Exception as e:
                    logging.warning(f"Failed to setup HUD: {e}")
                    self.ui_manager.toggle_hud_visibility(False)
        
            logging.info("Gameplay started successfully")
            
        except Exception as e:
            logging.error(f"Failed to start gameplay: {e}")
            self.game_state = 'main_menu'

    def pause_game(self):
        """Pause the game and show pause menu with error handling."""
        try:
            self.game_state = 'paused'
            self._pre_pause_game_time = self.game_time  # Freeze game time
            
            # Show mouse cursor for menu navigation
            try:
                if hasattr(self.app, 'openPointer'):
                    self.app.openPointer(1)  # Show cursor
                elif hasattr(self.app, 'win') and hasattr(self.app.win, 'request_properties'):
                    props = self.app.win.get_properties()
                    props.set_cursor_hidden(False)
                    self.app.win.request_properties(props)
            except Exception as e:
                logging.warning(f"Failed to show cursor: {e}")
        
            # Enable mouse for menu interaction
            try:
                if hasattr(self.app, 'enableMouse'):
                    self.app.enableMouse()
            except Exception as e:
                logging.warning(f"Failed to enable mouse: {e}")
        
            # Show pause menu
            if self.ui_manager:
                self.ui_manager.show_menu('pause')
                self.ui_manager.toggle_hud_visibility(False)
                logging.info("Game paused")
            else:
                logging.warning("UI manager not available for pause menu")
        except Exception as e:
            logging.error(f"Error during pause: {e}")

    def resume_game(self):
        """Resume the game from pause."""
        self.game_state = 'playing'
        
        # Restore game time from pre-pause snapshot
        if hasattr(self, '_pre_pause_game_time'):
            self.game_time = self._pre_pause_game_time
        
        # Hide mouse cursor for first-person controls
        if hasattr(self.app, 'openPointer'):
            try:
                self.app.openPointer(0)  # Hide cursor
            except Exception:
                pass
        elif hasattr(self.app, 'win') and hasattr(self.app.win, 'requestProperties'):
            try:
                props = self.app.win.get_properties()
                props.set_cursor_hidden(True)
                self.app.win.request_properties(props)
            except Exception:
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
        """Restart the game with error handling."""
        try:
            self.cleanup_game()
            self.initialize_components()
            self.start_gameplay()
            logging.info("Game restarted successfully")
        except Exception as e:
            logging.error(f"Failed to restart game: {e}")

    def show_main_menu(self):
        """Show the main menu with error handling."""
        try:
            self.game_state = 'main_menu'
            
            # Show mouse cursor for menu interaction
            try:
                if hasattr(self.app, 'openPointer'):
                    self.app.openPointer(1)  # Show cursor
                elif hasattr(self.app, 'win') and hasattr(self.app.win, 'request_properties'):
                    props = self.app.win.get_properties()
                    props.set_cursor_hidden(False)
                    self.app.win.request_properties(props)
            except Exception as e:
                logging.warning(f"Failed to show cursor: {e}")
        
            # Enable mouse for menu interaction
            try:
                if hasattr(self.app, 'enableMouse'):
                    self.app.enableMouse()
            except Exception as e:
                logging.warning(f"Failed to enable mouse: {e}")
        
            # Show main menu
            if self.ui_manager:
                self.ui_manager.show_menu('main')
                self.ui_manager.toggle_hud_visibility(False)
                logging.info("Main menu shown")
            else:
                logging.warning("UI manager not available for main menu")
        except Exception as e:
            logging.error(f"Error showing main menu: {e}")

    def show_settings(self):
        """Show the settings menu."""
        self.ui_manager.show_menu('settings')

    def quit_game(self):
        """Quit the game with error handling."""
        try:
            self.app.userExit()
            logging.info("Game quit successfully")
        except Exception as e:
            logging.error(f"Error during game quit: {e}")



    def spawn_animals(self):
        """Spawn initial animals in the game world using config values."""
        animal_cfg = config.ANIMAL_CONFIG
        spawn_radius = animal_cfg['spawn_radius']
        logging.info(f"Starting animal spawn with spawn_radius={spawn_radius}")

        def _spawn_positions(count, scenic):
            positions = list(scenic)
            attempts = 0
            max_attempts = min(10000, count * 1000)
            while len(positions) < count:
                attempts += 1
                if attempts > max_attempts:
                    break
                x = random.uniform(-spawn_radius, spawn_radius)
                y = random.uniform(-spawn_radius, spawn_radius)
                if x ** 2 + y ** 2 < (spawn_radius * 0.2) ** 2:
                    continue
                positions.append((x, y))
            return positions

        # Spawn deer
        for x, y in _spawn_positions(animal_cfg['deer_count'], [(22, 32), (-26, 20), (10, 38)]):
            z = self.terrain.get_height(x, y) if self.terrain else 0.0
            deer = Deer(Vec3(x, y, z))
            deer.render(self.app.render)
            self.animals.append(deer)
            if self.player:
                self.player.add_animal_to_collision(deer)

        # Spawn rabbits
        for x, y in _spawn_positions(animal_cfg['rabbit_count'], [(8, -6), (-12, -14), (6, 18)]):
            z = self.terrain.get_height(x, y) if self.terrain else 0.0
            rabbit = Rabbit(Vec3(x, y, z))
            rabbit.render(self.app.render)
            self.animals.append(rabbit)
            if self.player:
                self.player.add_animal_to_collision(rabbit)

        # Spawn bears
        for x, y in _spawn_positions(animal_cfg.get('bear_count', 3), [(-40, -40), (45, 30), (-30, 50)]):
            z = self.terrain.get_height(x, y) if self.terrain else 0.0
            bear = Bear(Vec3(x, y, z))
            bear.render(self.app.render)
            self.animals.append(bear)
            if self.player:
                self.player.add_animal_to_collision(bear)

        # Spawn wolves
        for x, y in _spawn_positions(animal_cfg.get('wolf_count', 5), [(35, -35), (-50, 10), (20, 55)]):
            z = self.terrain.get_height(x, y) if self.terrain else 0.0
            wolf = Wolf(Vec3(x, y, z))
            wolf.render(self.app.render)
            self.animals.append(wolf)
            if self.player:
                self.player.add_animal_to_collision(wolf)

        # Spawn birds (flying, so higher z)
        for x, y in _spawn_positions(animal_cfg.get('bird_count', 12), [(0, 0), (30, 30), (-30, -30), (40, -20)]):
            bird = Bird(Vec3(x, y, 0))
            # Birds set their own flight height in __init__, but position.z needs to be set after creation
            bird.position.z = bird.flight_height
            bird.render(self.app.render)
            self.animals.append(bird)

        self.animal_targets = self._current_animal_counts()
        self._sync_hud_objectives(force=True)
        logging.info(f"Animal spawning complete. Total animals: {len(self.animals)}")

    def _current_animal_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for animal in self.animals:
            species = getattr(animal, 'species', 'unknown')
            key = species.lower() if isinstance(species, str) else 'unknown'
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _sync_hud_objectives(self, force: bool = False):
        counts = self._current_animal_counts()
        self._pending_objective_counts = counts

        if self.ui_manager and self.ui_manager.hud:
            if self.animal_targets and (force or not self._objective_initialized):
                self.ui_manager.hud.set_objective_targets(self.animal_targets)
                self._objective_initialized = True
            if force or self._last_reported_objective_counts != counts:
                self.ui_manager.hud.update_objective_counts(counts)
                self._last_reported_objective_counts = counts.copy()
        else:
            self._objective_initialized = False
            self._last_reported_objective_counts = None

    def setup_lighting(self):
        """Set up realistic lighting for the scene."""
        # Lighting is now handled by DynamicLighting class
        # This method kept for backward compatibility
        pass


    def _setup_grass_fields(self):
        """Create and position grass fields for enhanced realism."""
        # Create multiple grass fields across the terrain
        field_configs = [
            {'width': 60, 'height': 40, 'density': 800},   # Larger fields
            {'width': 45, 'height': 30, 'density': 600},   # More dense
            {'width': 50, 'height': 30, 'density': 700}    # More coverage
        ]

        if GrassField is not None:
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
                    if self.foliage_renderer:
                        self.foliage_renderer.add_grass_field(field)
                        if getattr(field, 'grass_node', None):
                            field.grass_node.setPos(positions[i][0], positions[i][1], 0)
                    else:
                        logging.warning("Foliage renderer not available, skipping grass field addition")

            logging.info(f"Created {len(field_configs)} grass fields with {sum(c['density'] for c in field_configs)} grass blades")
        else:
            logging.warning("GrassField not available, skipping grass fields")

    def _setup_tree_clusters(self):
        if not self.foliage_renderer:
            logging.warning("Foliage renderer not available, skipping tree clusters")
            return
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
            logging.info("Loading rock model: models/misc/sphere")
            base_model = self.app.loader.loadModel('models/misc/sphere')
            logging.info("Rock model loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load rock model 'models/misc/sphere': {e}")
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
        """Update game state each frame with error handling."""
        try:
            if not self.is_running:
                return task.done

            # Calculate delta time with clamping to prevent physics explosions
            try:
                if hasattr(self.app.taskMgr, 'globalClock'):
                    current_time = self.app.taskMgr.globalClock.getFrameTime()
                else:
                    current_time = self.app.taskMgr.global_clock.getFrameTime()
                    
                if self.last_time == 0:
                    dt = 0.016  # Default 60 FPS
                else:
                    dt = current_time - self.last_time
                self.last_time = current_time
            except Exception as e:
                logging.error(f"Error calculating delta time: {e}")
                dt = 0.016
            
            # Clamp dt to prevent instability during lag spikes (max 100ms = 10 FPS minimum)
            dt = min(dt, 0.1)

            # Only update game components if actively playing
            if self.game_state == 'playing':
                # Update advanced graphics systems
                try:
                    self._update_graphics_systems(dt)
                except Exception as e:
                    logging.error(f"Error updating graphics systems: {e}")

                # Update foliage
                try:
                    if self.foliage_renderer:
                        self.foliage_renderer.update(dt, self.game_time)
                    else:
                        logging.debug("Foliage renderer not available, skipping update")
                except Exception as e:
                    logging.warning(f"Error updating foliage: {e}")

                # Update player
                try:
                    if self.player:
                        self.player.update(dt)
                        self.player._update_wind(dt)
                except Exception as e:
                    logging.error(f"Error updating player: {e}")

                # Tutorial hints for new players
                try:
                    self._update_tutorial(dt)
                except Exception:
                    pass

                # Apply settings sensitivity to player mouse
                if self.ui_manager and getattr(self.ui_manager, 'settings_menu', None) and self.player:
                    try:
                        sens = self.ui_manager.settings_menu.settings.get('sensitivity')
                        if sens is not None and abs(self.player.mouse_sensitivity - sens) > 0.001:
                            self.player.mouse_sensitivity = sens
                    except Exception:
                        pass

                # Update animals
                try:
                    player_pos = self.player.position if self.player else Vec3(0, 0, 0)
                    alive_animals = []
                    
                    for animal in self.animals:
                        try:
                            terrain_height = self.terrain.get_height(animal.position.x, animal.position.y) if self.terrain else 0.0
                            animal.update(dt, player_pos, terrain_height)

                            if not animal.is_dead():
                                alive_animals.append(animal)
                                # Predator damage to player
                                species = getattr(animal, 'species', '')
                                distance = (player_pos - animal.position).length()
                                if species in ('bear', 'wolf') and distance < getattr(animal, 'attack_range', 8.0) and hasattr(animal, 'damage'):
                                    # Damage cooldown — prevent instant death from frame-rate damage
                                    cooldown_attr = '_predator_damage_cooldown'
                                    current_cooldown = getattr(self.player, cooldown_attr, 0.0)
                                    if current_cooldown <= 0:
                                        # Check if predator is facing the player before dealing damage
                                        if animal.node:
                                            facing_dir = animal.node.getQuat().getForward()
                                            to_player = (player_pos - animal.position).normalized()
                                            dot = facing_dir.dot(to_player) if facing_dir.length() > 0 else 0
                                            if dot > -0.3:  # Predator must roughly face the player
                                                self.player.take_damage(animal.damage)
                                                setattr(self.player, cooldown_attr, 1.0)  # 1 second cooldown
                                    else:
                                        setattr(self.player, cooldown_attr, current_cooldown - dt)
                            else:
                                # Handle animal death - add score
                                self.handle_animal_killed(animal)
                                # Remove dead animal from collision detection
                                if self.player:
                                    self.player.remove_animal_from_collision(animal)
                                animal.cleanup()
                        except Exception as e:
                            logging.error(f"Error updating animal: {e}")
                            # Remove problematic animal
                            if hasattr(animal, 'cleanup'):
                                animal.cleanup()
                            continue

                    self.animals = alive_animals
                    self._sync_hud_objectives()

                    # Update minimap and time on HUD
                    if self.ui_manager and self.ui_manager.hud:
                        try:
                            self.ui_manager.hud.update_minimap(player_pos, alive_animals)
                        except Exception:
                            pass
                        try:
                            virtual_hour = (self.game_time * 0.016) % 24
                            self.ui_manager.hud.update_time(virtual_hour)
                        except Exception:
                            pass

                except Exception as e:
                    logging.error(f"Error updating animals: {e}")

                # Update audio manager
                try:
                    if self.audio_manager and self.player:
                        is_moving = any([
                            self.player.movement.get('forward', False),
                            self.player.movement.get('backward', False),
                            self.player.movement.get('left', False),
                            self.player.movement.get('right', False)
                        ])
                        weather_type = 'clear'
                        weather_strength = 0.0
                        if self.weather_system:
                            weather_type = getattr(self.weather_system, 'current_weather', 'clear')
                            weather_strength = getattr(self.weather_system, 'weather_strength', 0.0)
                        self.audio_manager.update(dt, self.player.position, is_moving, self.player.is_sprinting, weather_type, weather_strength)
                except Exception as e:
                    logging.debug(f"Audio update error: {e}")

                # Auto-save
                try:
                    if self.save_manager and config.SAVE_CONFIG.get('auto_save_interval', 300.0):
                        self._auto_save_timer += dt
                        if self._auto_save_timer >= config.SAVE_CONFIG['auto_save_interval']:
                            self._auto_save_timer = 0.0
                            self.save_manager.save_game(self, slot=1)
                except Exception as e:
                    logging.debug(f"Auto-save error: {e}")

                # Check for game over conditions (e.g., player health)
                try:
                    if self.player and hasattr(self.player, 'health') and self.player.health <= 0 and self.game_state == 'playing':
                        self._trigger_player_death()
                except Exception as e:
                    logging.error(f"Error checking game over conditions: {e}")

                # Animal respawn system - keep the world populated
                try:
                    self._animal_respawn_timer += dt
                    if self._animal_respawn_timer >= self._animal_respawn_interval:
                        self._animal_respawn_timer = 0.0
                        self._respawn_animals_if_needed()
                except Exception as e:
                    logging.debug(f"Animal respawn error: {e}")

            # Handle death state separately (freeze gameplay, show timer)
            if self.game_state == 'dead':
                try:
                    self._handle_death_state(dt)
                except Exception as e:
                    logging.error(f"Error in death state: {e}")
            
            # Update UI regardless of game state
            try:
                if self.ui_manager:
                    self.ui_manager.update_hud(dt)
            except Exception as e:
                logging.warning(f"Error updating UI: {e}")

            return task.cont
            
        except Exception as e:
            self.log_error("UPDATE_ERROR", f"Critical error in game update loop: {e}", "Main game loop failed")
            return task.done

    def _update_graphics_systems(self, dt):
        """Update advanced graphics systems for photorealistic rendering with error handling."""
        try:
            self.game_time += dt

            # Update dynamic lighting
            if self.dynamic_lighting:
                # Simulate time progression (1 minute = 1 real second)
                virtual_hour = (self.game_time * 0.016) % 24
                self.dynamic_lighting.update_time_of_day(virtual_hour)
            else:
                logging.debug("Dynamic lighting not available")

            # Update weather system
            if self.weather_system:
                self.weather_system.update_weather(dt)
            else:
                logging.debug("Weather system not available")

            # Adjust lighting for current weather
            if self.dynamic_lighting and self.weather_system:
                # Get weather intensities safely
                rain_intensity = getattr(self.weather_system, 'weather_strength', 0.0) if self.weather_system.current_weather in ('rain', 'storm') else 0.0
                fog_density = getattr(self.weather_system, 'weather_strength', 0.0) if self.weather_system.current_weather in ('fog', 'rain', 'snow') else 0.0
                
                # Apply weather effects to lighting
                if hasattr(self.dynamic_lighting, 'adjust_for_weather'):
                    self.dynamic_lighting.adjust_for_weather(rain_intensity, fog_density)
                
        except Exception as e:
            logging.error(f"Error updating graphics systems: {e}")

    def stop(self):
        """Stop the game loop."""
        self.is_running = False
        
        # Stop collision system properly
        if hasattr(self, 'collision_manager') and self.collision_manager:
            self.collision_manager.cleanup()

        # Clean up player
        if self.player:
            self.player.cleanup()
            self.player = None

        # Clean up animals and remove from collision detection
        for animal in self.animals:
            if self.player and hasattr(self.player, 'remove_animal_from_collision'):
                self.player.remove_animal_from_collision(animal)
            if hasattr(animal, 'cleanup'):
                animal.cleanup()
        self.animals.clear()

        # Clean up terrain
        if self.terrain:
            if hasattr(self.terrain, 'cleanup'):
                self.terrain.cleanup()
            self.terrain = None

        # Clean up sky and props
        if self.sky:
            if hasattr(self.sky, 'cleanup'):
                self.sky.cleanup()
            self.sky = None
        
        # Clean up rocks safely
        for rock in self.rocks:
            if hasattr(rock, 'removeNode'):
                try:
                    rock.removeNode()
                except:
                    pass  # Node already removed
        self.rocks = []

        # Clean up decor manager
        if self.decor_manager:
            if hasattr(self.decor_manager, 'cleanup'):
                self.decor_manager.cleanup()
            self.decor_manager = None

        # Clean up advanced graphics systems
        if self.dynamic_lighting:
            if hasattr(self.dynamic_lighting, 'cleanup'):
                self.dynamic_lighting.cleanup()
            self.dynamic_lighting = None
        if self.weather_system:
            if hasattr(self.weather_system, 'cleanup'):
                self.weather_system.cleanup()
            self.weather_system = None
        if self.foliage_renderer:
            if hasattr(self.foliage_renderer, 'cleanup'):
                self.foliage_renderer.cleanup()
            self.foliage_renderer = None

        # Clean up graphics manager
        if hasattr(self, 'graphics_manager') and self.graphics_manager:
            if hasattr(self.graphics_manager, 'cleanup'):
                self.graphics_manager.cleanup()

        # Clean up UI
        if self.ui_manager:
            if hasattr(self.ui_manager, 'cleanup'):
                self.ui_manager.cleanup()
            self.ui_manager = None

        logging.info("Hunting Simulator Game Stopped")

    def handle_animal_killed(self, animal):
        """Handle when an animal is killed - update score, statistics, and effects."""
        if self.ui_manager and self.ui_manager.hud and animal:
            # Award points based on animal type
            points = 10  # Base points
            xp_gain = 10  # Base XP
            species = getattr(animal, 'species', None)
            
            if species and isinstance(species, str):
                species_lower = species.lower()
                if species_lower == 'deer':
                    points = 50
                    xp_gain = 40
                elif species_lower == 'rabbit':
                    points = 25
                    xp_gain = 20
                elif species_lower == 'bear':
                    points = 150
                    xp_gain = 100
                elif species_lower == 'wolf':
                    points = 100
                    xp_gain = 60
                elif species_lower == 'bird':
                    points = 15
                    xp_gain = 10
            
            # Apply difficulty score multiplier
            diff_cfg = config.DIFFICULTY_CONFIG.get(self.difficulty, {})
            points = int(points * diff_cfg.get('score_multiplier', 1.0))
            
            self.ui_manager.add_score(points)
            self.ui_manager.record_shot(hit=True)
            self.ui_manager.record_kill()
            self.ui_manager.hud.register_animal_kill(species if isinstance(species, str) else '')
            
            # Grant XP to player
            if self.player:
                self.player.gain_experience(xp_gain)
            
            species_name = getattr(animal, 'species', 'Animal')
            if species_name and hasattr(animal, 'species'):
                self.ui_manager.show_message(f"{species_name} killed! +{points} pts  +{xp_gain} XP", 2.0)
            else:
                self.ui_manager.show_message(f"Animal killed! +{points} pts", 2.0)
            
            # Play death sound
            try:
                if self.audio_manager:
                    self.audio_manager.play_death(animal.position)
            except Exception:
                pass

    def _respawn_animals_if_needed(self):
        """Respawn animals if populations are low to keep the world alive."""
        if not self.terrain:
            return
        animal_cfg = config.ANIMAL_CONFIG
        spawn_radius = animal_cfg['spawn_radius']
        
        # Count current animals by species
        current_counts = {}
        for animal in self.animals:
            if not animal.is_dead():
                species = getattr(animal, 'species', 'unknown')
                current_counts[species] = current_counts.get(species, 0) + 1
        
        # Spawn missing animals
        species_map = {
            'deer': (Deer, animal_cfg['deer_count']),
            'rabbit': (Rabbit, animal_cfg['rabbit_count']),
            'bear': (Bear, animal_cfg.get('bear_count', 3)),
            'wolf': (Wolf, animal_cfg.get('wolf_count', 5)),
            'bird': (Bird, animal_cfg.get('bird_count', 12))
        }
        
        for species, (cls, target_count) in species_map.items():
            current = current_counts.get(species, 0)
            to_spawn = max(0, target_count - current)
            if to_spawn > 0:
                for _ in range(min(to_spawn, 3)):  # Spawn up to 3 at a time
                    x = random.uniform(-spawn_radius, spawn_radius)
                    y = random.uniform(-spawn_radius, spawn_radius)
                    if x ** 2 + y ** 2 < (spawn_radius * 0.2) ** 2:
                        continue
                    z = self.terrain.get_height(x, y) if self.terrain else 0.0
                    if species == 'bird':
                        z = 0  # Birds spawn at 0 then fly up
                    animal = cls(Vec3(x, y, z))
                    animal.render(self.app.render)
                    self.animals.append(animal)
                    if self.player:
                        self.player.add_animal_to_collision(animal)
                if to_spawn > 0:
                    logging.info(f"Respawned {min(to_spawn, 3)} {species}(s). Current: {current + min(to_spawn, 3)}/{target_count}")
        
        # Sync HUD
        self._sync_hud_objectives(force=True)

    def _update_tutorial(self, dt: float):
        """Show contextual tutorial hints for new players."""
        if not hasattr(self, '_tutorial_hints'):
            self._tutorial_hints = {
                'movement': {'shown': False, 'timer': 5.0, 'text': "WASD to move | SHIFT to sprint | SPACE to jump"},
                'shooting': {'shown': False, 'timer': 15.0, 'text': "MOUSE1 to shoot | R to reload | 1/2/3 to switch weapons"},
                'aiming': {'shown': False, 'timer': 30.0, 'text': "Right-click to zoom with rifle | Aim for headshots!"},
                'harvesting': {'shown': False, 'timer': 45.0, 'text': "Track wind direction — animals smell you downwind!"},
                'survival': {'shown': False, 'timer': 60.0, 'text': "Watch hunger & thirst | Use health potions with E"},
            }
        for key, hint in self._tutorial_hints.items():
            if not hint['shown']:
                hint['timer'] -= dt
                if hint['timer'] <= 0:
                    hint['shown'] = True
                    if self.ui_manager:
                        self.ui_manager.show_message(hint['text'], 5.0, (0.9, 0.9, 0.4, 1.0))
                    break  # Only show one hint at a time

    def on_projectile_hit(self, projectile, animal):
        """Callback when a projectile hits an animal — shows hit feedback even if not lethal."""
        if self.ui_manager and self.ui_manager.hud:
            self.ui_manager.hud.show_hit_marker()
            self.ui_manager.hud.show_damage_number(projectile.damage)
        # Also show a brief message for significant hits
        if self.ui_manager and projectile.damage >= 20:
            species = getattr(animal, 'species', 'Animal')
            self.ui_manager.show_message(f"Hit {species}! -{projectile.damage:.0f} HP", 1.0, (1.0, 0.5, 0.2, 1.0))

    def game_over(self):
        """Handle game over state with detailed statistics."""
        try:
            self.game_state = 'game_over'

            # Build detailed stats
            stats = {}
            if self.ui_manager and self.ui_manager.hud:
                hud = self.ui_manager.hud
                stats['score'] = hud.score
                stats['kills'] = hud.kills
                stats['shots_fired'] = hud.shots_fired
                stats['shots_hit'] = hud.shots_hit
                stats['accuracy'] = (hud.shots_hit / max(hud.shots_fired, 1)) * 100
            if self.player:
                stats['level'] = self.player.level
                stats['xp'] = self.player.experience
                stats['harvested_meats'] = self.player.harvested_meats
                stats['harvested_skins'] = self.player.harvested_skins
                stats['harvested_trophies'] = self.player.harvested_trophies
                stats['game_time'] = int(self.game_time)

            # Update game over screen
            if self.ui_manager:
                self.ui_manager.update_game_over_score(
                    stats.get('score', 0),
                    stats.get('kills', 0),
                    stats.get('accuracy', 0)
                )
                self.ui_manager.show_menu('game_over')
                self.ui_manager.toggle_hud_visibility(False)
                # Show detailed stats message
                detail = f"Level {stats.get('level', 1)}  |  {stats.get('harvested_meats', 0)} Meats  |  {stats.get('game_time', 0)}s"
                self.ui_manager.show_message(detail, 4.0, (0.8, 0.8, 0.8, 1.0))
                logging.info("Game over screen shown")
            else:
                logging.warning("UI manager not available for game over screen")
        except Exception as e:
            logging.error(f"Error during game over: {e}")

    def _trigger_player_death(self):
        """Handle player death with a short death screen before game over."""
        self.game_state = 'dead'
        self._death_timer = 3.0  # 3 second death screen
        
        if self.ui_manager:
            self.ui_manager.show_message("YOU DIED", 3.0, (1.0, 0.1, 0.1, 1.0))
        
        # Show cursor
        try:
            if hasattr(self.app, 'openPointer'):
                self.app.openPointer(1)
            elif hasattr(self.app, 'enableMouse'):
                self.app.enableMouse()
        except Exception:
            pass

    def _handle_death_state(self, dt):
        """Handle the death screen timer before transitioning to game over."""
        self._death_timer -= dt
        if self.ui_manager:
            self.ui_manager.show_message(
                f"Game Over in {max(1, int(self._death_timer))}...", 
                0.5, (1.0, 0.2, 0.2, 1.0)
            )
        if self._death_timer <= 0:
            self.game_over()

    def set_difficulty(self, difficulty: str):
        """Set game difficulty and apply config multipliers."""
        if difficulty in config.DIFFICULTY_CONFIG:
            self.difficulty = difficulty
            diff_cfg = config.DIFFICULTY_CONFIG[difficulty]
            # Apply difficulty settings to animals
            for animal in self.animals:
                if hasattr(animal, 'speed') and hasattr(animal, '_base_speed'):
                    animal.speed = animal._base_speed * diff_cfg.get('animal_speed_multiplier', 1.0)
                if hasattr(animal, 'health') and hasattr(animal, '_base_health'):
                    animal.health = animal._base_health * diff_cfg.get('animal_health_multiplier', 1.0)
            logging.info(f"Difficulty set to: {difficulty}")

    def cleanup_game(self):
        """Clean up current game session for restart."""
        # Reset game time
        self.game_time = 0.0
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

        # Clean up rocks
        for rock in self.rocks:
            if hasattr(rock, 'removeNode'):
                try:
                    rock.removeNode()
                except:
                    pass
        self.rocks.clear()

        self.animal_targets.clear()
        self._pending_objective_counts = {}
        self._last_reported_objective_counts = None
        self._objective_initialized = False
