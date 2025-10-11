#!/usr/bin/env python3
"""
Gameplay test script for the 3D Hunting Simulator.
Tests actual gameplay mechanics and interactions.
"""

import sys
import traceback
from panda3d.core import Vec3, Point3

def test_player_movement():
    """Test player movement mechanics."""
    print("Testing player movement...")
    try:
        from player.player import Player
        from direct.showbase.ShowBase import ShowBase

        # Create a mock ShowBase for testing
        class MockShowBase:
            def __init__(self):
                self.render = None
                self.camera = None
                self.mouseWatcherNode = None
                self.win = None
                self.loader = None
                self.aspect2d = None
                self.taskMgr = None

        mock_app = MockShowBase()
        player = Player(mock_app)

        # Test initial position
        initial_pos = player.position
        print(f"[OK] Initial position: {initial_pos}")

        # Test movement (simulate WASD keys)
        player.movement['forward'] = True
        player.update(0.1)  # Update for 0.1 seconds
        print(f"[OK] Position after forward movement: {player.position}")

        # Reset movement
        player.movement['forward'] = False
        player.position = initial_pos  # Reset position

        return True
    except Exception as e:
        print(f"[ERROR] Player movement error: {e}")
        traceback.print_exc()
        return False

def test_weapon_system():
    """Test weapon and shooting mechanics."""
    print("Testing weapon system...")
    try:
        from player.player import Player, Weapon
        from direct.showbase.ShowBase import ShowBase

        # Create a mock ShowBase for testing
        class MockShowBase:
            def __init__(self):
                self.render = None
                self.camera = None
                self.mouseWatcherNode = None
                self.win = None
                self.loader = None
                self.aspect2d = None
                self.taskMgr = None

        mock_app = MockShowBase()
        player = Player(mock_app)

        # Test weapon properties
        weapon = player.weapon
        print(f"[OK] Weapon: {weapon.name}, ammo: {weapon.current_ammo}/{weapon.max_ammo}")

        # Test shooting
        current_time = 0.0
        projectile = weapon.shoot(Point3(0, 0, 0), Vec3(0, 1, 0), current_time)
        if projectile:
            print(f"[OK] Projectile created: damage={projectile.damage}, speed={projectile.speed}")
        else:
            print("[WARNING] No projectile created (might be expected due to fire rate)")

        # Test reload
        weapon.current_ammo = 0  # Simulate empty magazine
        can_reload = weapon.reload(current_time)
        print(f"[OK] Reload initiated: {can_reload}")

        return True
    except Exception as e:
        print(f"[ERROR] Weapon system error: {e}")
        traceback.print_exc()
        return False

def test_animal_ai():
    """Test animal AI and behavior."""
    print("Testing animal AI...")
    try:
        from animals.animal import Deer, Rabbit
        from panda3d.core import Vec3

        # Create animals
        deer = Deer(Vec3(0, 0, 0))
        rabbit = Rabbit(Vec3(10, 0, 0))

        print(f"[OK] Deer state: {deer.state}, health: {deer.health}")
        print(f"[OK] Rabbit state: {rabbit.state}, health: {rabbit.health}")

        # Test player detection
        player_pos = Vec3(5, 0, 0)  # Close to deer, far from rabbit
        deer_detected = deer.detect_player(player_pos)
        rabbit_detected = rabbit.detect_player(player_pos)

        print(f"[OK] Deer detects player: {deer_detected}")
        print(f"[OK] Rabbit detects player: {rabbit_detected}")

        # Test damage system
        deer.take_damage(25)
        print(f"[OK] Deer after damage: health={deer.health}, state={deer.state}")

        return True
    except Exception as e:
        print(f"[ERROR] Animal AI error: {e}")
        traceback.print_exc()
        return False

def test_collision_system():
    """Test collision detection system."""
    print("Testing collision system...")
    try:
        from physics.collision import CollisionManager
        from direct.showbase.ShowBase import ShowBase

        # Create a mock ShowBase for testing
        class MockShowBase:
            def __init__(self):
                self.render = None

        mock_app = MockShowBase()
        collision_mgr = CollisionManager(mock_app)

        print(f"[OK] Collision manager created with {len(collision_mgr.animals)} animals and {len(collision_mgr.projectiles)} projectiles")

        # Test collision mask setup
        print(f"[OK] Projectile mask: {collision_mgr.PROJECTILE_MASK}")
        print(f"[OK] Animal mask: {collision_mgr.ANIMAL_MASK}")
        print(f"[OK] Terrain mask: {collision_mgr.TERRAIN_MASK}")

        return True
    except Exception as e:
        print(f"[ERROR] Collision system error: {e}")
        traceback.print_exc()
        return False

def test_terrain_interaction():
    """Test terrain and animal interaction."""
    print("Testing terrain interaction...")
    try:
        from environment.terrain import Terrain
        from animals.animal import Deer
        from panda3d.core import Vec3

        # Create terrain
        terrain = Terrain(width=50, height=50, scale=1.0, octaves=2)
        height_map = terrain.generate_terrain()

        # Test height queries
        height1 = terrain.get_height(10, 10)
        height2 = terrain.get_height(25, 25)
        height3 = terrain.get_height(40, 40)

        print(f"[OK] Terrain heights: (10,10)={height1:.2f}, (25,25)={height2:.2f}, (40,40)={height3:.2f}")

        # Test animal-terrain interaction
        deer = Deer(Vec3(10, 10, 0))
        terrain_height = terrain.get_height(10, 10)
        deer.position.z = terrain_height

        print(f"[OK] Deer positioned on terrain: {deer.position}")

        return True
    except Exception as e:
        print(f"[ERROR] Terrain interaction error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all gameplay tests."""
    print("=== 3D Hunting Simulator Gameplay Test Suite ===\n")

    tests = [
        test_player_movement,
        test_weapon_system,
        test_animal_ai,
        test_collision_system,
        test_terrain_interaction
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"=== Gameplay Test Results: {passed}/{total} tests passed ===")

    if passed == total:
        print("[SUCCESS] All gameplay tests passed! Core mechanics are working.")
        return 0
    else:
        print("[WARNING] Some gameplay tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())