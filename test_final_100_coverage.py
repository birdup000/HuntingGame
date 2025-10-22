#!/usr/bin/env python3
"""
Final targeted tests for the remaining 100% coverage push.
Focused on completing coverage for critical lines.
"""

import sys
import unittest
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, '.')

class Final100CoverageTests(unittest.TestCase):
    """Final push for 100% coverage."""

    def test_animal_is_dead_method(self):
        """Test animal is_dead method with various health states."""
        try:
            from animals.animal import Deer, Rabbit
            from panda3d.core import Vec3
            
            # Test deer is_dead
            deer = Deer(Vec3(0, 0, 0))
            
            # Test above death threshold
            deer.health = 0.001
            self.assertFalse(deer.is_dead())
            
            # Test at death threshold
            deer.health = 0.0001
            self.assertTrue(deer.is_dead())
            
            # Test well below threshold
            deer.health = 0.0
            self.assertTrue(deer.is_dead())
            
            # Test rabbit is_dead
            rabbit = Rabbit(Vec3(10, 10, 0))
            rabbit.health = 0.001
            self.assertFalse(rabbit.is_dead())
            rabbit.health = 0.0001
            self.assertTrue(rabbit.is_dead())
            
        except Exception as e:
            self.fail(f"Animal is_dead method failed: {e}")

    def test_animal_killed_and_cleanup(self):
        """Test animal killed state and cleanup."""
        try:
            from animals.animal import Deer
            from panda3d.core import Vec3, NodePath
            
            deer = Deer(Vec3(0, 0, 0))
            
            # Mock the node cleanup
            deer.node = Mock()
            deer.node.removeNode = Mock()
            deer.node.isEmpty = Mock(return_value=False)
            
            # Test kill animal
            deer.take_damage(1000)  # Should kill
            
            # Test that is_dead returns True
            self.assertTrue(deer.is_dead())
            
            # Test cleanup
            deer.cleanup()
            deer.node.removeNode.assert_called()
            
        except Exception as e:
            self.fail(f"Animal killed and cleanup failed: {e}")

    def test_animal_movement_and_behavior(self):
        """Test animal movement and behavior patterns."""
        try:
            from animals.animal import Deer, Rabbit
            from panda3d.core import Vec3
            
            deer = Deer(Vec3(0, 0, 0))
            rabbit = Rabbit(Vec3(10, 10, 0))
            
            # Test initial state
            self.assertEqual(deer.state, 'idle')
            self.assertEqual(rabbit.state, 'idle')
            
            # Test position properties
            self.assertIsInstance(deer.position, Vec3)
            self.assertIsInstance(rabbit.position, Vec3)
            
            # Test health properties
            self.assertEqual(deer.health, 100.0)
            self.assertEqual(rabbit.health, 100.0)
            
        except Exception as e:
            self.fail(f"Animal movement and behavior failed: {e}")

    def test_pbr_terrain_render_method(self):
        """Test PBR terrain render method."""
        try:
            from environment.pbr_terrain import PBRTerrain
            
            # Create PBR terrain
            terrain = PBRTerrain(width=50, height=50, scale=1.0, octaves=2)
            
            # Mock render node
            mock_render = Mock()
            mock_node = Mock()
            mock_render.attachNewNode = Mock(return_value=mock_node)
            
            # Test render method
            terrain.render(mock_render)
            
            # Verify that attachNewNode was called
            mock_render.attachNewNode.assert_called()
            
        except Exception as e:
            self.fail(f"PBR terrain render method failed: {e}")

    def test_pbr_terrain_get_height_method(self):
        """Test PBR terrain get_height method."""
        try:
            from environment.pbr_terrain import PBRTerrain
            
            terrain = PBRTerrain(width=50, height=50, scale=1.0, octaves=2)
            
            # Test height before generation
            height = terrain.get_height(0, 0)
            self.assertIsInstance(height, float)
            
            # Test after generation
            terrain.generate_terrain()
            height = terrain.get_height(0, 0)
            self.assertIsInstance(height, float)
            
            # Test at edge coordinates
            height_edge = terrain.get_height(25, 25)  # Edge of 50x50 terrain
            self.assertIsInstance(height_edge, float)
            
        except Exception as e:
            self.fail(f"PBR terrain get_height method failed: {e}")

    def test_simple_sky_cleanup(self):
        """Test simple sky cleanup method."""
        try:
            from environment.simple_sky import SimpleSkyDome
            
            # Create mock app
            mock_app = Mock()
            mock_app.render = Mock()
            mock_app.taskMgr = Mock()
            mock_task = Mock()
            mock_app.taskMgr.add = Mock(return_value=mock_task)
            
            sky = SimpleSkyDome(mock_app, radius=100.0)
            
            # Test cleanup
            sky.cleanup()
            
        except Exception as e:
            self.fail(f"Simple sky cleanup failed: {e}")

    def test_decor_registration_methods(self):
        """Test decor manager registration methods."""
        try:
            from environment.decor import DecorManager
            
            mock_app = Mock()
            mock_app.render = Mock()
            mock_terrain = None
            
            decor_manager = DecorManager(mock_app, mock_terrain)
            
            # Test _register method
            mock_node = Mock()
            registered_node = decor_manager._register(mock_node)
            
            self.assertEqual(registered_node, mock_node)
            self.assertEqual(len(decor_manager.decor_nodes), 1)
            
            # Test _terrain_height method
            height = decor_manager._terrain_height(10.0, 10.0)
            self.assertIsInstance(height, float)
            
        except Exception as e:
            self.fail(f"Decor registration methods failed: {e}")

    def test_collision_cleanup_methods(self):
        """Test collision cleanup methods."""
        try:
            from physics.collision import CollisionManager, Projectile
            
            mock_app = Mock()
            mock_app.render = Mock()
            
            collision_manager = CollisionManager(mock_app)
            
            # Mock the traverser and handler
            collision_manager.traverser = Mock()
            collision_manager.handler = Mock()
            collision_manager.queues = []
            collision_manager.graphics_queues = []
            
            # Test cleanup
            collision_manager.cleanup()
            
        except Exception as e:
            self.fail(f"Collision cleanup methods failed: {e}")

    def test_collision_projectile_methods(self):
        """Test collision projectile methods."""
        try:
            from physics.collision import Projectile
            
            # Create a projectile
            pos = Mock()
            direction = Mock()
            pos.x = 0
            pos.y = 0  
            pos.z = 0
            direction.x = 1
            direction.y = 0
            direction.z = 0
            
            projectile = Projectile(pos, direction, speed=100.0, damage=25.0)
            
            # Test basic properties
            self.assertTrue(projectile.active)
            self.assertIsInstance(projectile.damage, float)
            self.assertIsInstance(projectile.distance_traveled, float)
            
        except Exception as e:
            self.fail(f"Collision projectile methods failed: {e}")

    def test_game_objective_methods(self):
        """Test game objective tracking methods."""
        try:
            from core.game import Game
            
            mock_app = Mock()
            mock_app.render = Mock()
            mock_app.taskMgr = Mock()
            mock_app.taskMgr.add = Mock()
            
            game = Game(mock_app)
            
            # Test _current_animal_counts
            counts = game._current_animal_counts()
            self.assertIsInstance(counts, dict)
            
            # Test _sync_hud_objectives
            game._sync_hud_objectives()
            
        except Exception as e:
            self.fail(f"Game objective methods failed: {e}")

if __name__ == '__main__':
    unittest.main(verbosity=2)
