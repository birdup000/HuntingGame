#!/usr/bin/env python3
"""
More targeted tests for specific missing coverage lines in player and other modules.
"""

import sys
import unittest
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, '.')

class VeryTargetedTests(unittest.TestCase):
    """Very targeted tests for specific missing lines."""

    def test_weapon_cannot_shoot_cases(self):
        """Test weapon cases where cannot_shoot returns False."""
        try:
            from player.player import Weapon
            
            # Test cannot shoot when reloading
            weapon = Weapon("Test")
            weapon.reloading = True
            can_shoot = weapon.can_shoot(1.0)
            self.assertFalse(can_shoot)
            
            # Test cannot shoot when out of ammo
            weapon.reloading = False
            weapon.current_ammo = 0
            can_shoot = weapon.can_shoot(1.0)
            self.assertFalse(can_shoot)
            
            # Test cannot shoot when fire rate not met
            weapon.current_ammo = 10
            weapon.last_shot_time = 0.0
            weapon.fire_rate = 1.0
            can_shoot = weapon.can_shoot(0.5)  # Should not be able to shoot yet
            self.assertFalse(can_shoot)
            
        except Exception as e:
            self.fail(f"Weapon cannot shoot cases failed: {e}")

    def test_weapon_reload_cases(self):
        """Test weapon reload edge cases."""
        try:
            from player.player import Weapon
            
            # Test cannot reload when already reloading
            weapon = Weapon("Test")
            weapon.reloading = True
            result = weapon.reload(0.0)
            self.assertFalse(result)
            
            # Test cannot reload when already at max ammo
            weapon.reloading = False
            weapon.current_ammo = weapon.max_ammo
            result = weapon.reload(0.0)
            self.assertFalse(result)
            
            # Test cannot reload when max_ammo is 0
            weapon.current_ammo = 0
            weapon.max_ammo = 0
            result = weapon.reload(0.0)
            self.assertFalse(result)
            
        except Exception as e:
            self.fail(f"Weapon reload cases failed: {e}")

    def test_weapon_update_reload_cases(self):
        """Test weapon update_reload edge cases."""
        try:
            from player.player import Weapon
            
            # Test update_reload when not reloading
            weapon = Weapon("Test")
            weapon.reloading = False
            result = weapon.update_reload(1.0)
            self.assertFalse(result)
            
            # Test update_reload when reload not complete
            weapon.reloading = True
            weapon.reload_start_time = 0.0
            weapon.reload_time = 2.0
            result = weapon.update_reload(1.0)  # Half way through
            self.assertFalse(result)
            self.assertTrue(weapon.reloading)  # Still reloading
            
        except Exception as e:
            self.fail(f"Weapon update_reload cases failed: {e}")

    def test_player_health_edge_cases(self):
        """Test player health edge cases."""
        try:
            from player.player import Player
            
            # Create minimal mock for player
            class MinimalMockApp:
                def __init__(self):
                    self.render = None
                    self.loader = None
                    self.taskMgr = None
                    
            mock_app = MinimalMockApp()
            player = Player(mock_app, setup_controls=False)
            
            # Test heal above max health
            player.health = 95
            player.heal(10)  # Should cap at 100
            self.assertEqual(player.health, 100)
            
            # Test take damage when already dead
            player.take_damage(200)  # Should stay at 0
            self.assertEqual(player.health, 0)
            self.assertTrue(player.health <= 0)
            
        except Exception as e:
            self.fail(f"Player health edge cases failed: {e}")

    def test_player_movement_additional(self):
        """Test additional player movement paths."""
        try:
            from player.player import Player
            
            class MinimalMockApp:
                def __init__(self):
                    self.render = None
                    self.loader = None
                    self.taskMgr = None
                    self.mouseWatcherNode = None
                    
            mock_app = MinimalMockApp()
            player = Player(mock_app, setup_controls=False)
            
            # Test set_move functionality
            self.assertEqual(player.movement['forward'], False)
            player.set_move('forward', True)
            self.assertEqual(player.movement['forward'], True)
            player.set_move('forward', False)
            self.assertEqual(player.movement['forward'], False)
            
        except Exception as e:
            self.fail(f"Player movement additional failed: {e}")

    def test_collision_additional_methods(self):
        """Test additional collision methods."""
        try:
            from physics.collision import CollisionManager, Projectile
            
            class MinimalMockApp:
                def __init__(self):
                    self.render = None
                    
            mock_app = MinimalMockApp()
            collision_manager = CollisionManager(mock_app)
            
            # Test update method
            collision_manager.update()  # Should not crash
            
        except Exception as e:
            self.fail(f"Collision additional methods failed: {e}")

    def test_decor_manager_additional(self):
        """Test additional decor manager methods."""
        try:
            from environment.decor import DecorManager
            
            class MinimalMockApp:
                def __init__(self):
                    self.render = None
                    self.loader = None
                    
            mock_app = MinimalMockApp()
            mock_terrain = None
            
            decor_manager = DecorManager(mock_app, mock_terrain)
            
            # Test populate method with None render
            decor_manager.render = None
            decor_manager.populate()  # Should not crash
            
            # Test cleanup of empty list
            decor_manager.decor_nodes = []
            decor_manager.cleanup()  # Should not crash
            
        except Exception as e:
            self.fail(f"Decor manager additional failed: {e}")

    def test_terrain_additional_methods(self):
        """Test additional terrain methods."""
        try:
            from environment.terrain import Terrain
            
            terrain = Terrain(width=50, height=50, scale=1.0, octaves=2)
            
            # Test generate_terrain method
            height_map = terrain.generate_terrain()
            self.assertIsNotNone(height_map)
            
            # Test get_height method
            height = terrain.get_height(10, 10)
            self.assertIsInstance(height, float)
            
        except Exception as e:
            self.fail(f"Terrain additional methods failed: {e}")

if __name__ == '__main__':
    unittest.main(verbosity=2)
