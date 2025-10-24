#!/usr/bin/env python3
"""
Detailed test coverage for environment.decor module.
This file specifically targets the 13% coverage gap in environment/decor.py
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# Mock panda3d modules for testing
class MockVec3:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
        
    def length(self):
        return (self.x**2 + self.y**2 + self.z**2)**0.5
    
    def normalize(self):
        length = self.length()
        if length > 0:
            self.x /= length
            self.y /= length
            self.z /= length
        return self
    
    def __add__(self, other):
        return MockVec3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return MockVec3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        return MockVec3(self.x * scalar, self.y * scalar, self.z * scalar)

class MockCardMaker:
    def __init__(self, name):
        self.name = name
        
    def setFrame(self, *args):
        pass
    
    def generate(self):
        return Mock()

class MockNodePath:
    def __init__(self, name="test"):
        self.name = name
        self.children = []
        
    def attachNewNode(self, name):
        child = MockNodePath(name)
        self.children.append(child)
        return child
        
    def removeNode(self):
        pass
        
    def setTransparency(self, mode):
        pass
        
    def setTexture(self, texture, level):
        pass
        
    def setScale(self, *args):
        pass
        
    def setP(self, angle):
        pass
        
    def setPos(self, x, y, z):
        pass
        
    def setColorScale(self, *args):
        pass
        
    def setShaderAuto(self):
        pass

class MockTexture:
    def __init__(self, name="test_texture"):
        self.name = name

# Add these mocks before importing decor module
sys.modules['panda3d.core'] = Mock()
sys.modules['panda3d.core'].CardMaker = MockCardMaker
sys.modules['panda3d.core'].NodePath = MockNodePath
sys.modules['panda3d.core'].TransparencyAttrib = Mock()
sys.modules['panda3d.core'].TransparencyAttrib.MAlpha = "alpha"
sys.modules['panda3d.core'].TransparencyAttrib.MNone = "none"
sys.modules['panda3d.core'].Vec3 = MockVec3
sys.modules['panda3d.core'].getModelPath = Mock()

# Add texture factory mocks
class MockTextureFactory:
    @staticmethod
    def create_bark_texture():
        return MockTexture("bark")
    
    @staticmethod
    def create_leaf_texture(size):
        return MockTexture("leaf")
    
    @staticmethod
    def create_water_texture():
        return MockTexture("water")
    
    @staticmethod
    def create_flower_patch_texture(size):
        return MockTexture("flower")

sys.modules['graphics.texture_factory'] = Mock()
sys.modules['graphics.texture_factory'].create_bark_texture = MockTextureFactory.create_bark_texture
sys.modules['graphics.texture_factory'].create_leaf_texture = MockTextureFactory.create_leaf_texture
sys.modules['graphics.texture_factory'].create_water_texture = MockTextureFactory.create_water_texture
sys.modules['graphics.texture_factory'].create_flower_patch_texture = MockTextureFactory.create_flower_patch_texture

from environment.decor import DecorManager

class TestDecorManagerComprehensive(unittest.TestCase):
    """Comprehensive tests for DecorManager class to improve coverage."""

    def setUp(self):
        """Setup test fixtures."""
        self.mock_app = Mock()
        self.mock_app.render = Mock()
        self.mock_app.loader = Mock()
        
        # Mock the render to support attachNewNode
        def mock_attach_new_node(name):
            node = MockNodePath(name)
            return node
        
        self.mock_app.render.attachNewNode = mock_attach_new_node
        
        # Mock loader to return None for cylinder model
        self.mock_app.loader.loadModel = Mock(return_value=None)
        self.mock_app.loader._path_findFile = Mock(return_value=None)

    def test_decor_manager_initialization(self):
        """Test DecorManager initialization."""
        mock_terrain = Mock()
        decor_manager = DecorManager(self.mock_app, mock_terrain)
        
        self.assertEqual(decor_manager.app, self.mock_app)
        self.assertEqual(decor_manager.render, self.mock_app.render)
        self.assertEqual(decor_manager.terrain, mock_terrain)
        self.assertEqual(len(decor_manager.decor_nodes), 0)

    def test_terrain_height_queries(self):
        """Test terrain height querying methods."""
        mock_terrain = Mock()
        mock_terrain.get_height = Mock(return_value=5.0)
        
        decor_manager = DecorManager(self.mock_app, mock_terrain)
        
        # Test _terrain_height method
        height = decor_manager._terrain_height(10.0, 10.0)
        self.assertEqual(height, 5.0)
        
        # Test with None terrain
        decor_manager_none = DecorManager(self.mock_app, None)
        height_none = decor_manager_none._terrain_height(10.0, 10.0)
        self.assertEqual(height_none, 0.0)

    def test_node_registration(self):
        """Test node registration system."""
        mock_terrain = Mock()
        decor_manager = DecorManager(self.mock_app, mock_terrain)
        
        # Test _register method
        mock_node = MockNodePath("test_node")
        registered_node = decor_manager._register(mock_node)
        
        self.assertEqual(registered_node, mock_node)
        self.assertEqual(len(decor_manager.decor_nodes), 1)
        self.assertEqual(decor_manager.decor_nodes[0], mock_node)

    def test_cleanup_functionality(self):
        """Test cleanup functionality."""
        mock_terrain = Mock()
        decor_manager = DecorManager(self.mock_app, mock_terrain)
        
        # Add some mock nodes
        mock_node1 = MockNodePath("node1")
        mock_node2 = MockNodePath("node2")
        
        decor_manager.decor_nodes = [mock_node1, mock_node2]
        
        # Mock removeNode method
        mock_node1.removeNode = Mock()
        mock_node2.removeNode = Mock()
        
        # Test cleanup
        decor_manager.cleanup()
        
        # Verify nodes were cleaned up
        mock_node1.removeNode.assert_called()
        mock_node2.removeNode.assert_called()
        self.assertEqual(len(decor_manager.decor_nodes), 0)

    def test_cleanup_with_none_nodes(self):
        """Test cleanup with None nodes."""
        mock_terrain = Mock()
        decor_manager = DecorManager(self.mock_app, mock_terrain)
        
        # Add None nodes
        decor_manager.decor_nodes = [None, MockNodePath("valid")]
        valid_node = decor_manager.decor_nodes[1]
        valid_node.removeNode = Mock()
        
        # Test cleanup should handle None gracefully
        decor_manager.cleanup()
        
        # Verify only valid node was cleaned up
        valid_node.removeNode.assert_called()
        self.assertEqual(len(decor_manager.decor_nodes), 0)

    def test_add_water_features(self):
        """Test water feature addition."""
        mock_terrain = Mock()
        mock_terrain.get_height = Mock(return_value=2.0)
        
        decor_manager = DecorManager(self.mock_app, mock_terrain)
        
        # Mock texture creation
        with patch('environment.decor.create_water_texture', return_value=MockTexture("water")):
            decor_manager._add_water_features()
        
        # Should have added pond nodes
        self.assertGreater(len(decor_manager.decor_nodes), 0)

    def test_add_fallen_logs(self):
        """Test fallen log addition."""
        mock_terrain = Mock()
        mock_terrain.get_height = Mock(return_value=1.5)
        
        decor_manager = DecorManager(self.mock_app, mock_terrain)
        
        # Mock model loading to return None (fallback to CardMaker)
        with patch.object(self.mock_app.loader, 'loadModel', return_value=None):
            with patch.object(self.mock_app.loader, '_path_findFile', return_value=None):
                with patch('environment.decor.create_bark_texture', return_value=MockTexture("bark")):
                    decor_manager._add_fallen_logs()
        
        # Should have added log nodes
        self.assertGreater(len(decor_manager.decor_nodes), 0)

    def test_add_shrubs(self):
        """Test shrub addition."""
        mock_terrain = Mock()
        mock_terrain.get_height = Mock(return_value=0.5)
        
        decor_manager = DecorManager(self.mock_app, mock_terrain)
        
        # Mock texture creation and random
        with patch('environment.decor.create_leaf_texture', return_value=MockTexture("leaf")):
            with patch('environment.decor.random.uniform', side_effect=[5.0, 5.0, 1.2, 0.9]):  # Provide deterministic values
                decor_manager._add_shrubs()
        
        # Should have added shrub nodes
        self.assertGreater(len(decor_manager.decor_nodes), 0)

    def test_add_flower_meadows(self):
        """Test flower meadow addition."""
        mock_terrain = Mock()
        mock_terrain.get_height = Mock(return_value=0.2)
        
        decor_manager = DecorManager(self.mock_app, mock_terrain)
        
        # Mock texture creation and random
        with patch('environment.decor.create_flower_patch_texture', return_value=MockTexture("flower")):
            with patch('environment.decor.random.uniform', side_effect=[-0.2, 0.3]):  # Provide deterministic values
                decor_manager._add_flower_meadows()
        
        # Should have added flower patch nodes
        self.assertGreater(len(decor_manager.decor_nodes), 0)

class TestDecorManagerEdgeCases(unittest.TestCase):
    """Edge cases and error conditions for DecorManager."""

    def test_missing_render(self):
        """Test behavior when render is None."""
        mock_terrain = Mock()
        
        # Create DecorManager with None render
        decor_manager = DecorManager(Mock(), mock_terrain)
        decor_manager.render = None
        
        # All add methods should handle None render gracefully
        decor_manager._add_water_features()
        decor_manager._add_fallen_logs()
        decor_manager._add_shrubs()
        decor_manager._add_flower_meadows()
        
        # Should not have any nodes
        self.assertEqual(len(decor_manager.decor_nodes), 0)

    def test_missing_terrain(self):
        """Test behavior when terrain is None."""
        mock_app = Mock()
        mock_app.render = Mock()
        
        # Create DecorManager with None terrain
        decor_manager = DecorManager(mock_app, None)
        
        # Should use default height (0.0) when terrain is None
        height = decor_manager._terrain_height(10.0, 10.0)
        self.assertEqual(height, 0.0)

    def test_missing_loader(self):
        """Test behavior when loader is missing."""
        mock_app = Mock()
        mock_app.render = Mock()
        del mock_app.loader  # Remove loader attribute
        
        mock_terrain = Mock()
        
        decor_manager = DecorManager(mock_app, mock_terrain)
        
        # Should handle missing loader gracefully in add_fallen_logs
        try:
            decor_manager._add_fallen_logs()
        except AttributeError:
            self.fail("add_fallen_logs should handle missing loader")

    def test_fallback_model_creation(self):
        """Test fallback to CardMaker when model loading fails."""
        mock_app = Mock()
        mock_app.render = Mock()
        mock_app.loader = Mock()
        mock_app.loader.loadModel = Mock(side_effect=Exception("Model not found"))
        
        def mock_attach_new_node(name):
            return MockNodePath(name)
        mock_app.render.attachNewNode = mock_attach_new_node
        
        mock_terrain = Mock()
        mock_terrain.get_height = Mock(return_value=1.0)
        
        decor_manager = DecorManager(mock_app, mock_terrain)
        
        # Should fallback to CardMaker when model loading fails
        with patch('environment.decor.create_bark_texture', return_value=MockTexture("bark")):
            decor_manager._add_fallen_logs()
        
        # Should still create log nodes via CardMaker
        self.assertGreater(len(decor_manager.decor_nodes), 0)

    def test_texture_factory_failures(self):
        """Test behavior when texture factory functions fail."""
        mock_app = Mock()
        mock_app.render = Mock()
        mock_app.loader = Mock()
        
        def mock_attach_new_node(name):
            return MockNodePath(name)
        mock_app.render.attachNewNode = mock_attach_new_node
        
        mock_terrain = Mock()
        mock_terrain.get_height = Mock(return_value=1.0)
        
        decor_manager = DecorManager(mock_app, mock_terrain)
        
        # Test water features with failed texture creation
        with patch('environment.decor.create_water_texture', side_effect=Exception("Texture failed")):
            try:
                decor_manager._add_water_features()
            except Exception:
                self.fail("add_water_features should handle texture creation failure")

    def test_random_seed_consistency(self):
        """Test that random seed produces consistent results."""
        mock_app = Mock()
        mock_app.render = Mock()
        
        def mock_attach_new_node(name):
            return MockNodePath(name)
        mock_app.render.attachNewNode = mock_attach_new_node
        
        mock_terrain = Mock()
        mock_terrain.get_height = Mock(return_value=0.0)
        
        # Test that repeat calls with same seed produce same results
        decor_manager1 = DecorManager(mock_app, mock_terrain)
        decor_manager1._add_shrubs()
        count1 = len(decor_manager1.decor_nodes)
        
        # Reset for second call
        decor_manager2 = DecorManager(mock_app, mock_terrain)
        decor_manager2._add_shrubs()
        count2 = len(decor_manager2.decor_nodes)
        
        # Should create same number of shrubs
        self.assertEqual(count1, count2)

class TestDecorManagerIntegration(unittest.TestCase):
    """Integration tests for DecorManager with other systems."""

    def test_populate_method(self):
        """Test the main populate method."""
        mock_app = Mock()
        mock_app.render = Mock()
        
        def mock_attach_new_node(name):
            return MockNodePath(name)
        mock_app.render.attachNewNode = mock_attach_new_node
        
        mock_terrain = Mock()
        mock_terrain.get_height = Mock(return_value=0.0)
        
        decor_manager = DecorManager(mock_app, mock_terrain)
        
        # Mock all texture creation functions
        with patch('environment.decor.create_water_texture', return_value=MockTexture("water")), \
             patch('environment.decor.create_bark_texture', return_value=MockTexture("bark")), \
             patch('environment.decor.create_leaf_texture', return_value=MockTexture("leaf")), \
             patch('environment.decor.create_flower_patch_texture', return_value=MockTexture("flower")):
            
            # Mock random for deterministic results
            with patch('environment.decor.random.uniform', side_effect=[1.0, 1.0] * 100):
                decor_manager.populate()
        
        # Should have created nodes for all decor types
        self.assertGreater(len(decor_manager.decor_nodes), 0)

    def test_full_lifecycle(self):
        """Test full lifecycle: populate -> cleanup."""
        mock_app = Mock()
        mock_app.render = Mock()
        
        def mock_attach_new_node(name):
            return MockNodePath(name)
        mock_app.render.attachNewNode = mock_attach_new_node
        
        mock_terrain = Mock()
        mock_terrain.get_height = Mock(return_value=0.0)
        
        decor_manager = DecorManager(mock_app, mock_terrain)
        
        # Mock all texture creation functions
        with patch('environment.decor.create_water_texture', return_value=MockTexture("water")), \
             patch('environment.decor.create_bark_texture', return_value=MockTexture("bark")), \
             patch('environment.decor.create_leaf_texture', return_value=MockTexture("leaf")), \
             patch('environment.decor.create_flower_patch_texture', return_value=MockTexture("flower")):
            
            # Mock random for deterministic results
            with patch('environment.decor.random.uniform', side_effect=[1.0, 1.0] * 100):
                decor_manager.populate()
        
        # Should have created nodes
        initial_count = len(decor_manager.decor_nodes)
        self.assertGreater(initial_count, 0)
        
        # Clean up
        decor_manager.cleanup()
        
        # Should be empty after cleanup
        self.assertEqual(len(decor_manager.decor_nodes), 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
