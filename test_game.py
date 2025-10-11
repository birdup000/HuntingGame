#!/usr/bin/env python3
"""
Test script for the 3D Hunting Simulator.
Tests basic functionality and identifies potential issues.
"""

import sys
import traceback

def test_imports():
    """Test all module imports."""
    print("Testing imports...")
    try:
        from core.game import Game
        from player.player import Player
        from animals.animal import Deer, Rabbit
        from environment.terrain import Terrain
        from physics.collision import CollisionManager
        from ui.hud import HUD
        import ui.menus
        import config
        print("[OK] All imports successful")
        return True
    except Exception as e:
        print(f"[ERROR] Import error: {e}")
        traceback.print_exc()
        return False

def test_config():
    """Test configuration loading."""
    print("Testing configuration...")
    try:
        import config
        print(f"[OK] Terrain config: {config.TERRAIN_CONFIG}")
        print(f"[OK] Animal config: {config.ANIMAL_CONFIG}")
        print(f"[OK] Game config: {config.GAME_CONFIG}")
        return True
    except Exception as e:
        print(f"[ERROR] Config error: {e}")
        traceback.print_exc()
        return False

def test_terrain_generation():
    """Test terrain generation."""
    print("Testing terrain generation...")
    try:
        from environment.terrain import Terrain
        terrain = Terrain(width=50, height=50, scale=1.0, octaves=2)
        height_map = terrain.generate_terrain()
        print(f"[OK] Terrain generated: {height_map.shape}")
        height = terrain.get_height(10, 10)
        print(f"[OK] Height at (10,10): {height}")
        return True
    except Exception as e:
        print(f"[ERROR] Terrain error: {e}")
        traceback.print_exc()
        return False

def test_animal_creation():
    """Test animal creation."""
    print("Testing animal creation...")
    try:
        from animals.animal import Deer, Rabbit
        from panda3d.core import Vec3

        deer = Deer(Vec3(0, 0, 0))
        rabbit = Rabbit(Vec3(10, 10, 0))

        print(f"[OK] Deer created: {deer.species}, health: {deer.health}")
        print(f"[OK] Rabbit created: {rabbit.species}, health: {rabbit.health}")
        return True
    except Exception as e:
        print(f"[ERROR] Animal creation error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=== 3D Hunting Simulator Test Suite ===\n")

    tests = [
        test_imports,
        test_config,
        test_terrain_generation,
        test_animal_creation
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"=== Test Results: {passed}/{total} tests passed ===")

    if passed == total:
        print("[SUCCESS] All tests passed! The game should run without major issues.")
        return 0
    else:
        print("[WARNING] Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())