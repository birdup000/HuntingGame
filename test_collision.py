#!/usr/bin/env python3
"""
Test script for the collision detection system.
"""

import unittest
from unittest.mock import Mock, MagicMock
from panda3d.core import Vec3, Point3, NodePath, CollisionNode, PandaNode
from physics.collision import CollisionManager, Projectile
from animals.animal import Animal

class MockApp:
    def __init__(self):
        self.render = NodePath("render")

class MockAnimal(Animal):
    def __init__(self, position=Vec3(0, 0, 0), species="mock_animal"):
        super().__init__(position, species)
        self.node = NodePath("animal_node")
        self.damage_taken = 0

    def create_model(self):
        return NodePath("mock_animal_model")

    def take_damage(self, damage: float):
        self.damage_taken += damage

    def is_dead(self):
        return False

class TestCollisionSystem(unittest.TestCase):
    """Test suite for the collision detection system."""

    def setUp(self):
        """Set up the test environment."""
        self.app = MockApp()
        self.collision_manager = CollisionManager(self.app)
        self.collision_manager.traverser = MagicMock()

    def test_add_animal(self):
        """Test that an animal is correctly added to the collision manager."""
        animal = MockAnimal()
        self.collision_manager.add_animal(animal)
        self.assertTrue(hasattr(animal, 'collision_np'))
        self.assertIsNotNone(animal.collision_np.getPythonTag('animal'))

    def test_add_projectile(self):
        """Test that a projectile is correctly added to the collision manager."""
        projectile = Projectile(Point3(0, 0, 0), Vec3(1, 0, 0))
        self.collision_manager.add_projectile(projectile)
        self.assertTrue(hasattr(projectile, 'collision_np'))
        self.assertIsNotNone(projectile.collision_np.getPythonTag('projectile'))

    def test_collision_processing(self):
        """Test that a collision between a projectile and an animal is processed correctly."""
        # Mock the collision handler to simulate a collision
        self.collision_manager.handler = MagicMock()
        mock_entry = MagicMock()
        from_node_path = NodePath('projectile_collision_node')
        into_node_path = NodePath('animal_collision_node')

        projectile = Projectile(Point3(0, 0, 0), Vec3(1, 0, 0), damage=25)
        animal = MockAnimal(position=Vec3(10, 0, 0))

        from_node_path.setPythonTag('projectile', projectile)
        into_node_path.setPythonTag('animal', animal)

        mock_entry.getFromNodePath.return_value = from_node_path
        mock_entry.getIntoNodePath.return_value = into_node_path

        self.collision_manager.handler.getNumEntries.return_value = 1
        self.collision_manager.handler.getEntry.return_value = mock_entry

        # Run the update
        self.collision_manager.update()

        # Assert that the animal took damage
        self.assertEqual(animal.damage_taken, 25)
        self.assertFalse(projectile.active)

if __name__ == "__main__":
    unittest.main()
