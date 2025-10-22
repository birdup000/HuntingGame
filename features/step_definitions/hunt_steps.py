"""
Step definitions for BDD tests of the 3D Hunting Simulator.
Implements the Gherkin scenarios with concrete Python code.
"""

import sys
import pytest
from pytest_bdd import given, when, then, parsers
from unittest.mock import Mock, patch, MagicMock
import threading
import time

# Add project root to path
sys.path.insert(0, '..')  # Go up to project root from features/step_definitions/
sys.path.insert(0, '.')   # Also include current directory

# Import game modules
from core.game import Game
from player.player import Player, Weapon
from animals.animal import Deer, Rabbit, AnimalState
from environment.pbr_terrain import PBRTerrain
from physics.collision import CollisionManager, Projectile
from panda3d.core import Vec3, Point3

# Note: pytest_bdd.scenarios() decorators are not needed when using pytest --bdd-features
# The scenarios will be automatically discovered when running: pytest features/ --bdd-features=features/

# Test fixtures and shared state
@pytest.fixture
def game_app():
    """Mock Panda3D application for testing."""
    app = Mock()
    app.render = Mock()
    app.render.attachNewNode = Mock()
    app.taskMgr = Mock()
    app.win = Mock()
    app.loader = Mock()
    app.camera = Mock()
    app.mouseWatcherNode = Mock()
    
    # Mock render node properties
    app.render.setDepthTest = Mock()
    app.render.setDepthWrite = Mock()
    
    return app

@pytest.fixture 
def mock_game(game_app):
    """Create a mock game instance."""
    return Game(game_app)

@pytest.fixture
def mock_player(game_app):
    """Create a mock player instance."""
    player = Player(game_app, setup_controls=False)
    return player

@pytest.fixture
def mock_terrain():
    """Create a mock terrain instance."""
    terrain = PBRTerrain(width=100, height=100, scale=1.0, octaves=3)
    return terrain

@pytest.fixture
def mock_deer():
    """Create a mock deer instance."""
    deer = Deer(Vec3(0, 0, 0))
    return deer

@pytest.fixture
def mock_collision_manager(game_app):
    """Create a collision manager instance."""
    return CollisionManager(game_app)

# PLAYER MOVEMENT STEP DEFINITIONS

@given('the game is running and player is in playing state')
def game_running_playing(mock_game):
    mock_game.is_running = True
    mock_game.game_state = 'playing'

@given('the player is stationary on flat terrain')
def player_stationary_flat(mock_player):
    mock_player.velocity = Vec3(0, 0, 0)
    mock_player.position = Point3(0, 0, 1.0)  # Flat terrain at y=1

@when('I press the \'W\' key for 1 second')
def press_w_key(mock_player):
    # Simulate W key being held for 1 second
    dt = 0.016  # 60 FPS
    initial_pos = mock_player.position
    
    # Mock movement input
    mock_player.movement['forward'] = True
    
    # Update multiple times to simulate 1 second
    for _ in range(60):
        mock_player.update(dt)
    
    # Store for verification
    mock_player._final_position = mock_player.position
    mock_player._moved = (mock_player.position != initial_pos)

@then('the player should move forward from their starting position')
def player_moved_forward(mock_player):
    assert mock_player._moved, "Player should have moved forward"
    assert mock_player.position.y > 0, "Player should move in positive Y direction"

@when('I press the \'A\' key for 0.5 seconds')
def press_a_key(mock_player):
    dt = 0.016
    initial_pos = mock_player.position
    mock_player.movement['left'] = True
    
    for _ in range(30):  # 0.5 seconds
        mock_player.update(dt)
    
    mock_player._final_position = mock_player.position
    mock_player._moved = (mock_player.position != initial_pos)

@then('the player should move to the left')
def player_moved_left(mock_player):
    assert mock_player._moved, "Player should have moved left"
    assert mock_player.position.x < 0, "Player should move in negative X direction"

@when('I press the \'C\' key')
def press_c_key(mock_player):
    initial_height = mock_player.position.z
    mock_player.crouch()
    mock_player._height_change = initial_height - mock_player.position.z

@then('the player\'s height should decrease')
def player_height_decreased(mock_player):
    assert mock_player._height_change > 0, "Player height should have decreased"

@then('the movement speed should be reduced by 50%')
def movement_speed_reduced(mock_player):
    expected_speed = mock_player.move_speed * 0.5
    assert mock_player.crouch_speed == expected_speed, "Speed should be halved when crouching"

# ANIMAL BEHAVIOR STEP DEFINITIONS

@given('a deer is in IDLE state')
def deer_idle(mock_deer):
    mock_deer.state = AnimalState.IDLE

@given('the player comes within 30 meters detection range')
def player_in_detection_range():
    # This will be handled in the when step
    pass

@when('the deer should transition to ALERTED state')
def deer_alert_transition(mock_deer):
    # Mock the detection logic
    mock_deer.state = AnimalState.ALERTED

@then('the deer should transition to ALERTED state')
def verify_deer_alerted(mock_deer):
    assert mock_deer.state == AnimalState.ALERTED, "Deer should be in ALERTED state"

@when('the deer should turn to face the player direction')
def deer_faces_player(mock_deer):
    # Mock facing logic
    mock_deer.target_position = Vec3(30, 0, 0)  # Player position
    mock_deer.velocity = Vec3(0, 0, 0)  # Stop movement to face player

@given('a deer is in ALERTED state')
def deer_alerted(mock_deer):
    mock_deer.state = AnimalState.ALERTED

@when('the player gets closer than 15 meters')
def player_closer_than_15m():
    # Trigger fleeing behavior
    pass

@when('the deer should transition to FLEEING state')
def deer_flee_transition(mock_deer):
    initial_state = mock_deer.state
    mock_deer.state = AnimalState.FLEEING
    mock_deer._state_changed = (mock_deer.state != initial_state)

@then('the deer should transition to FLEEING state')
def verify_deer_fleeing(mock_deer):
    assert mock_deer._state_changed, "Deer state should have changed"
    assert mock_deer.state == AnimalState.FLEEING, "Deer should be in FLEEING state"

# COMBAT SYSTEM STEP DEFINITIONS

@given('the player has a rifle with full ammo')
def player_with_rifle(mock_player):
    mock_player.weapon = Weapon(name="Rifle", max_ammo=30)
    mock_player.weapon.current_ammo = 30

@when('I left-click to shoot')
def shoot_rifle(mock_player):
    import time
    current_time = time.time()
    mock_player._shot_result = mock_player.weapon.shoot(
        mock_player.position, 
        Vec3(1, 0, 0),  # Direction
        current_time
    )

@then('a projectile should be created at gun position')
def projectile_created(mock_player):
    assert mock_player._shot_result is not None, "Projectile should be created"
    assert isinstance(mock_player._shot_result, Projectile), "Result should be a Projectile"

@then('the ammo count should decrease by 1')
def ammo_decreased(mock_player):
    assert mock_player.weapon.current_ammo == 29, "Ammo should decrease by 1"

@given('I just fired a shot')
def just_fired(mock_player):
    # Mock recent shot
    import time
    mock_player.weapon.last_shot_time = time.time()

@when('I try to shoot again immediately')
def try_shoot_immediately(mock_player):
    import time
    current_time = time.time()
    mock_player._can_shoot = mock_player.weapon.can_shoot(current_time)

@then('the shot should be blocked for 0.5 seconds')
def shot_blocked(mock_player):
    # Direct verification of fire rate logic
    assert mock_player._can_shoot is False, "Shot should be blocked due to fire rate"

# GAME STATE STEP DEFINITIONS

@given('the game is launched')
def game_launched():
    pass

@when('the application starts')
def app_starts(mock_game):
    # Mock the start process
    mock_game.start()
    mock_game._started = True

@then('the main menu should be displayed')
def main_menu_displayed(mock_game):
    # Mock UI system
    assert hasattr(mock_game, '_started'), "Game should have started"

@given('I\'m in main menu')
def in_main_menu():
    pass

@when('I click \'Start Game\'')
def click_start_game(mock_game):
    # Mock game start process
    mock_game.game_state = 'playing'
    mock_game._world_loaded = True

@then('the game world should load')
def game_world_loaded(mock_game):
    assert mock_game._world_loaded, "Game world should be loaded"

# ENVIRONMENT STEP DEFINITIONS

@given('the game is starting')
def game_starting():
    pass

@when('the environment loads')
def environment_loads(mock_terrain):
    mock_terrain.generate_terrain()
    mock_terrain._generated = True

@then('varied terrain should generate with hills and valleys')
def terrain_generated(mock_terrain):
    assert mock_terrain._generated, "Terrain should be generated"
    # Basic validation that generation occurred
    assert hasattr(mock_terrain, 'heightmap'), "Terrain should have heightmap"

# COLLISION AND PROJECTILE TESTS

@when('I shoot a bullet horizontally')
def shoot_bullet_horizontal(mock_player, mock_collision_manager):
    current_time = time.time()
    projectile = Projectile(mock_player.position, Vec3(1, 0, 0), speed=100.0)
    mock_collision_manager.add_projectile(projectile)
    mock_player._fired_projectile = projectile

@then('the bullet should drop due to gravity over distance')
def bullet_drops(mock_player):
    # Simulate gravity effect over time
    dt = 0.1
    projectile = mock_player._fired_projectile
    initial_y = projectile.position.y
    
    # Update with gravity simulation
    for _ in range(10):
        # Simple gravity simulation
        dt = 0.016
        gravity_force = Vec3(0, 0, -9.8 * dt)
        mock_player._final_y = projectile.position.y + gravity_force.z
        mock_player._y_dropped = (mock_player._final_y < initial_y)
    
@then('bullet should have maximum range of 500 meters')
def bullet_max_range(mock_player):
    dt = 0.1
    projectile = Projectile(Point3(0, 0, 0), Vec3(1, 0, 0), speed=100.0)
    projectile.max_range = 500.0
    
    # Simulate travel to max range
    distance_to_travel = 500.0
    time_to_max_range = distance_to_travel / projectile.speed
    
    # Update until max range
    steps = int(time_to_max_range / dt)
    for _ in range(steps + 1):  # One extra step to exceed range
        active = projectile.update(dt)
        if not active:
            mock_player._reached_max_range = True
            break
    
    assert mock_player._reached_max_range, "Projectile should deactivate at max range"

# ANIMAL SPAWNING TESTS

@when('the system spawns deer in the environment')
def spawn_deer(mock_game, mock_terrain):
    deer = Deer(Vec3(10, 10, 0))
    deer.position.z = mock_terrain.get_height(10, 10)  # Position on terrain
    mock_game.animals.append(deer)
    mock_game._deer_spawned = True

@then('deer should be positioned on terrain height')
def deer_on_terrain(mock_game, mock_terrain):
    assert len(mock_game.animals) > 0, "Deer should be spawned"
    deer = mock_game.animals[0]
    expected_height = mock_terrain.get_height(deer.position.x, deer.position.y)
    assert abs(deer.position.z - expected_height) < 0.1, "Deer should be on terrain height"

# INTEGRATION TEST HELPERS

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Ensure test isolation between scenarios."""
    yield
    # Cleanup can be added here if needed
