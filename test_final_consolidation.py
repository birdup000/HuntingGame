#!/usr/bin/env python3
"""
Final consolidation tests to target specific missing coverage areas.
Based on actual analysis of what needs to be tested.
"""

import sys
import unittest
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, '.')

class FinalCoverageConsolidation(unittest.TestCase):
    """Final tests to consolidate coverage improvements."""

    def test_animal_additional_edges(self):
        """Test animal functionality not yet covered."""
        try:
            from animals.animal import AnimalState, Animal, Deer, Rabbit
            from panda3d.core import Vec3
            
            # Test state transitions
            deer = Deer(Vec3(0, 0, 0))
            self.assertEqual(deer.state, AnimalState.IDLE)
            
            # Test that state can be changed
            deer.state = AnimalState.MOVING
            self.assertEqual(deer.state, AnimalState.MOVING)
            
            # Test health functionality
            initial_health = deer.health
            deer.health = initial_health - 10
            self.assertEqual(deer.health, initial_health - 10)
            
            # Test is_dead method when health is low
            deer.health = 0.001  # Just above the threshold
            self.assertFalse(deer.is_dead())
            
            deer.health = 0.0001  # Below threshold
            self.assertTrue(deer.is_dead())
            
        except Exception as e:
            self.fail(f"Animal additional edges test failed: {e}")

    def test_player_additional_methods(self):
        """Test additional player methods."""
        try:
            from player.player import Player
            
            # Create minimal mock for player that doesn't need full app
            class MinimalMockApp:
                def __init__(self):
                    self.render = None
                    self.loader = None
                    self.taskMgr = None
                    
            mock_app = MinimalMockApp()
            
            # Test player with minimal setup
            player = Player(mock_app, setup_controls=False)
            
            # Test health methods
            initial_health = player.health
            player.take_damage(10.0)
            self.assertEqual(player.health, initial_health - 10.0)
            
            player.heal(5.0)
            self.assertEqual(player.health, initial_health - 5.0)
            
            # Test that health doesn't go below 0
            player.take_damage(200.0)
            self.assertEqual(player.health, 0.0)
            
            # Test that health doesn't go above max
            player.heal(1000.0)
            self.assertEqual(player.health, player.max_health)
            
        except Exception as e:
            self.fail(f"Player additional methods test failed: {e}")

    def test_environment_additional_areas(self):
        """Test additional environment areas."""
        try:
            from environment.terrain import Terrain
            from environment.pbr_terrain import PBRTerrain
            
            # Test terrain height queries at edge cases
            terrain = Terrain(width=50, height=50, scale=1.0, octaves=2)
            pbr_terrain = PBRTerrain(width=50, height=50, scale=1.0, octaves=2)
            
            # Generate terrain for height testing
            height_map = terrain.generate_terrain()
            
            # Test height queries (should not crash)
            height_at_origin = terrain.get_height(0, 0)
            height_at_edge = terrain.get_height(25, 25)
            
            # Should be floats
            self.assertIsInstance(height_at_origin, float)
            self.assertIsInstance(height_at_edge, float)
            
        except Exception as e:
            self.fail(f"Environment additional areas test failed: {e}")

    def test_collision_additional_areas(self):
        """Test additional collision functionality."""
        try:
            from physics.collision import CollisionManager, Projectile
            
            # Create minimal mock for collision manager
            class MinimalMockApp:
                def __init__(self):
                    self.render = None
                    
            mock_app = MinimalMockApp()
            
            # Test collision manager with minimal setup
            collision_manager = CollisionManager(mock_app)
            
            # Test that we can call update without crashing
            collision_manager.update()  # Should not crash
            
        except Exception as e:
            self.fail(f"Collision additional areas test failed: {e}")

    def test_core_game_misc_methods(self):
        """Test miscellaneous core game methods."""
        try:
            from core.game import Game
            
            # Create minimal mock for game
            class MinimalMockApp:
                def __init__(self):
                    self.render = None
                    self.taskMgr = None
                    self.loader = None
                    
            mock_app = MinimalMockApp()
            
            # Test game initialization
            game = Game(mock_app)
            
            # Test basic properties
            self.assertEqual(game.game_state, 'main_menu')
            self.assertFalse(game.is_running)
            self.assertEqual(game.game_time, 0.0)
            self.assertEqual(game.last_time, 0)
            
        except Exception as e:
            self.fail(f"Core game misc methods test failed: {e}")

    def test_config_compatibility(self):
        """Test configuration compatibility and access."""
        try:
            import config
            
            # Test that all config types work together
            terrain_config = config.TERRAIN_CONFIG.copy()
            animal_config = config.ANIMAL_CONFIG.copy()
            game_config = config.GAME_CONFIG.copy()
            
            # Test numerical values are compatible
            width = terrain_config['width']
            height = terrain_config['height']
            spawn_radius = animal_config['spawn_radius']
            title = game_config['title']
            
            # Verify they are the expected types
            self.assertIsInstance(width, int)
            self.assertIsInstance(height, int)
            self.assertIsInstance(spawn_radius, int)
            self.assertIsInstance(title, str)
            
        except Exception as e:
            self.fail(f"Config compatibility test failed: {e}")

def run_final_tests():
    """Run all final consolidation tests."""
    test = FinalCoverageConsolidation()
    
    # Run all tests
    test.test_animal_additional_edges()
    test.test_player_additional_methods() 
    test.test_environment_additional_areas()
    test.test_collision_additional_areas()
    test.test_core_game_misc_methods()
    test.test_config_compatibility()
    
    print("All final consolidation tests passed!")

if __name__ == '__main__':
    unittest.main(verbosity=2)
