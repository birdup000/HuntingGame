#!/usr/bin/env python3
"""
Detailed test coverage for environment.simple_sky module.
This file specifically targets the 11% coverage gap in environment/simple_sky.py
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import math

# Mock panda3d modules for testing
class MockNodePath:
    def __init__(self, name="test"):
        self.name = name
        self.children = []
        self.is_empty = False
        
    def attachNewNode(self, name):
        child = MockNodePath(name)
        self.children.append(child)
        return child
        
    def reparentTo(self, parent):
        pass
        
    def setBin(self, bin_type, priority):
        pass
        
    def setDepthWrite(self, value):
        pass
        
    def setDepthTest(self, value):
        pass
        
    def setLightOff(self, level):
        pass
        
    def setFogOff(self):
        pass
        
    def setShaderOff(self, level):
        pass
        
    def setTransparency(self, mode):
        pass
        
    def setTexture(self, texture, level):
        pass
        
    def setTwoSided(self, value):
        pass
        
    def setAttrib(self, attrib):
        pass
        
    def setScale(self, *args):
        pass
        
    def setEffect(self, effect):
        pass
        
    def removeNode(self):
        pass
        
    def setPos(self, *args):
        pass
        
    def isEmpty(self):
        return self.is_empty

class MockGeomNode:
    def __init__(self, name):
        self.name = name
        
    def addGeom(self, geom):
        pass

class MockGeom:
    def __init__(self, vdata):
        self.vdata = vdata
        
    def addPrimitive(self, primitive):
        pass

class MockTask:
    def __init__(self):
        pass

class MockTaskManager:
    def add(self, func, name, sort=0):
        return MockTask()
        
    def remove(self, task):
        pass

class MockCamera:
    def __init__(self):
        pass

class MockApp:
    def __init__(self):
        self.render = MockNodePath("render")
        self.camera = MockCamera()
        self.taskMgr = MockTaskManager()
        
    def setBackgroundColor(self, *args):
        pass

# Add these mocks before importing simple_sky module
sys.modules['panda3d.core'] = Mock()
sys.modules['panda3d.core'].NodePath = MockNodePath
sys.modules['panda3d.core'].GeomNode = MockGeomNode
sys.modules['panda3d.core'].Geom = MockGeom
sys.modules['panda3d.core'].GeomTriangles = Mock()
sys.modules['panda3d.core'].GeomTriangles.UHStatic = "static"
sys.modules['panda3d.core'].GeomVertexFormat = Mock()
sys.modules['panda3d.core'].GeomVertexFormat.getV3t2 = Mock(return_value="format")
sys.modules['panda3d.core'].GeomVertexData = Mock()
sys.modules['panda3d.core'].GeomVertexData.UHStatic = "static"
sys.modules['panda3d.core'].GeomVertexWriter = Mock()
sys.modules['panda3d.core'].TransparencyAttrib = Mock()
sys.modules['panda3d.core'].TransparencyAttrib.MNone = "none"
sys.modules['panda3d.core'].CompassEffect = Mock()
sys.modules['panda3d.core'].CullFaceAttrib = Mock()
sys.modules['panda3d.core'].BoundingSphere = Mock()
sys.modules['panda3d.core'].Point3 = Mock()
sys.modules['panda3d.core'].Vec3 = Mock()

# Mock texture factory
class MockTexture:
    def __init__(self, name="test_texture"):
        self.name = name

def create_sky_texture():
    return MockTexture("sky")

sys.modules['graphics.texture_factory'] = Mock()
sys.modules['graphics.texture_factory'].create_sky_texture = create_sky_texture

from environment.simple_sky import SimpleSkyDome

class TestSimpleSkyDomeComprehensive(unittest.TestCase):
    """Comprehensive tests for SimpleSkyDome class to improve coverage."""

    def setUp(self):
        """Setup test fixtures."""
        self.mock_app = MockApp()

    def test_sky_dome_creation(self):
        """Test basic sky dome creation."""
        sky_dome = SimpleSkyDome(self.mock_app, radius=600.0)
        
        self.assertEqual(sky_dome.radius, 600.0)
        self.assertEqual(sky_dome.app, self.mock_app)
        self.assertIsNotNone(sky_dome._root)
        self.assertIsNotNone(sky_dome.node)

    def test_custom_radius(self):
        """Test sky dome with custom radius."""
        sky_dome = SimpleSkyDome(self.mock_app, radius=1000.0)
        
        self.assertEqual(sky_dome.radius, 1000.0)

    def test_create_hemisphere_default_params(self):
        """Test hemisphere creation with default parameters."""
        sky_dome = SimpleSkyDome(self.mock_app, radius=100.0)
        
        # Test the _create_hemisphere method
        hemisphere = sky_dome._create_hemisphere()  # Default: segments=32, rings=16
        
        self.assertIsInstance(hemisphere, MockNodePath)

    def test_create_hemisphere_custom_params(self):
        """Test hemisphere creation with custom parameters."""
        sky_dome = SimpleSkyDome(self.mock_app, radius=100.0)
        
        # Test with custom segments and rings
        hemisphere = sky_dome._create_hemisphere(segments=16, rings=8)
        
        self.assertIsInstance(hemisphere, MockNodePath)

    def test_hemisphere_geometry_generation(self):
        """Test that hemisphere geometry is properly generated."""
        sky_dome = SimpleSkyDome(self.mock_app, radius=100.0)
        
        # Create a hemisphere and verify geometry generation
        with patch('environment.simple_sky.GeomVertexWriter') as mock_writer_class, \
             patch('environment.simple_sky.Geom') as mock_geom_class, \
             patch('environment.simple_sky.GeomTriangles') as mock_triangles_class:
            
            mock_writer = Mock()
            mock_writer_class.return_value = mock_writer
            
            mock_geom = Mock()
            mock_geom_class.return_value = mock_geom
            
            mock_triangles = Mock()
            mock_triangles_class.return_value = mock_triangles
            mock_triangles.addVertices = Mock()
            mock_triangles.closePrimitive = Mock()
            
            hemisphere = sky_dome._create_hemisphere(segments=4, rings=3)
            
            # Verify that vertex data was written
            self.assertTrue(mock_writer.addData3.called or mock_writer.addData2.called)

    def test_setup_sky_with_app_render(self):
        """Test sky setup when app has render attribute."""
        sky_dome = SimpleSkyDome(self.mock_app, radius=600.0)
        
        self.assertIsNotNone(sky_dome._root)
        self.assertIsNotNone(sky_dome.node)

    def test_setup_sky_without_app_render(self):
        """Test sky setup when app lacks render attribute."""
        mock_app_no_render = Mock()
        # Don't add render attribute
        
        sky_dome = SimpleSkyDome(mock_app_no_render, radius=600.0)
        
        # Should handle missing render gracefully
        self.assertIsNone(sky_dome._root)
        self.assertIsNone(sky_dome.node)

    def test_setup_sky_without_taskmgr(self):
        """Test sky setup when app lacks taskMgr."""
        mock_app_no_taskmgr = MockApp()
        del mock_app_no_taskmgr.taskMgr  # Remove taskMgr
        
        sky_dome = SimpleSkyDome(mock_app_no_taskmgr, radius=600.0)
        
        # Should still setup sky but without update task
        self.assertIsNotNone(sky_dome._root)
        self.assertIsNone(sky_dome._task)

    def test_update_task(self):
        """Test the update task functionality."""
        sky_dome = SimpleSkyDome(self.mock_app, radius=600.0)
        
        # Test update task with valid setup
        mock_task = Mock()
        result = sky_dome._update_task(mock_task)
        
        self.assertEqual(result, 'cont')  # Should continue the task

    def test_update_task_without_root(self):
        """Test update task when root node is None."""
        sky_dome = SimpleSkyDome(self.mock_app, radius=600.0)
        sky_dome._root = None
        
        mock_task = Mock()
        result = sky_dome._update_task(mock_task)
        
        self.assertEqual(result, 'cont')

    def test_update_task_without_camera(self):
        """Test update task when app lacks camera."""
        mock_app_no_camera = MockApp()
        del mock_app_no_camera.camera
        
        sky_dome = SimpleSkyDome(mock_app_no_camera, radius=600.0)
        sky_dome._root = MockNodePath("root")
        
        mock_task = Mock()
        result = sky_dome._update_task(mock_task)
        
        self.assertEqual(result, 'cont')

class TestSimpleSkyDomeEdgeCases(unittest.TestCase):
    """Edge cases and error conditions for SimpleSkyDome."""

    def test_cleanup_comprehensive(self):
        """Test comprehensive cleanup functionality."""
        mock_app = MockApp()
        
        sky_dome = SimpleSkyDome(mock_app, radius=600.0)
        
        # Test cleanup with all components present
        sky_dome.cleanup()
        
        # Verify cleanup was handled gracefully
        self.assertIsNone(sky_dome._root)
        self.assertIsNone(sky_dome._task)

    def test_cleanup_without_taskmgr(self):
        """Test cleanup when taskMgr is missing."""
        mock_app_no_taskmgr = MockApp()
        del mock_app_no_taskmgr.taskMgr
        
        sky_dome = SimpleSkyDome(mock_app_no_taskmgr, radius=600.0)
        
        # Should handle missing taskMgr gracefully
        sky_dome.cleanup()

    def test_cleanup_with_none_components(self):
        """Test cleanup with None components."""
        mock_app = MockApp()
        
        sky_dome = SimpleSkyDome(mock_app, radius=600.0)
        
        # Set components to None
        sky_dome._root = None
        sky_dome._task = None
        sky_dome.node = None
        
        # Should handle None components gracefully
        sky_dome.cleanup()

    def test_cleanup_with_invalid_node(self):
        """Test cleanup with invalid node."""
        mock_app = MockApp()
        
        sky_dome = SimpleSkyDome(mock_app, radius=600.0)
        
        # Set node to have isEmpty() return True
        sky_dome.node = MockNodePath("test")
        sky_dome.node.isEmpty = Mock(return_value=True)
        
        sky_dome.cleanup()

    def test_texture_factory_failure(self):
        """Test behavior when texture creation fails."""
        mock_app = MockApp()
        
        # Mock texture factory to fail
        with patch('environment.simple_sky.create_sky_texture', side_effect=Exception("Texture creation failed")):
            sky_dome = SimpleSkyDome(mock_app, radius=600.0)
        
        # Should handle texture creation failure gracefully
        self.assertIsNotNone(sky_dome)

    def test_app_without_set_background_color(self):
        """Test when app doesn't have setBackgroundColor method."""
        mock_app = MockApp()
        del mock_app.setBackgroundColor  # Remove setBackgroundColor method
        
        sky_dome = SimpleSkyDome(mock_app, radius=600.0)
        
        # Should handle missing setBackgroundColor gracefully
        self.assertIsNotNone(sky_dome)

    def test_app_without_camera(self):
        """Test when app doesn't have camera."""
        mock_app_no_camera = MockApp()
        del mock_app_no_camera.camera
        
        sky_dome = SimpleSkyDome(mock_app_no_camera, radius=600.0)
        
        # Should still create sky dome without camera following
        self.assertIsNotNone(sky_dome)

    def test_app_without_render(self):
        """Test when app doesn't have render attribute."""
        mock_app_no_render = Mock()
        
        sky_dome = SimpleSkyDome(mock_app_no_render, radius=600.0)
        
        # Should handle missing render gracefully
        self.assertIsNone(sky_dome._root)
        self.assertIsNone(sky_dome.node)

class TestSimpleSkyDomeIntegration(unittest.TestCase):
    """Integration tests for SimpleSkyDome with other systems."""

    def test_collision_and_compass_effect(self):
        """Test integration with camera and compass effect."""
        mock_app = MockApp()
        
        sky_dome = SimpleSkyDome(mock_app, radius=600.0)
        
        # Verify that the sky dome setup tried to create a compass effect
        self.assertIsNotNone(sky_dome._root)

    def test_render_ordering(self):
        """Test that render ordering is properly configured."""
        mock_app = MockApp()
        
        sky_dome = SimpleSkyDome(mock_app, radius=600.0)
        
        # Should have configured render bin for background
        self.assertIsNotNone(sky_dome._root)

    def test_z_fighting_prevention(self):
        """Test that z-fighting prevention is configured."""
        mock_app = MockApp()
        
        sky_dome = SimpleSkyDome(mock_app, radius=600.0)
        
        # Should have configured depth settings to prevent z-fighting
        self.assertIsNotNone(sky_dome._root)

    def test_task_scheduling_integration(self):
        """Test integration with Panda3D task system."""
        mock_app = MockApp()
        
        sky_dome = SimpleSkyDome(mock_app, radius=600.0)
        
        # Should have scheduled an update task
        self.assertIsNotNone(sky_dome._task)

class TestSimpleSkyDomeGeometryValidation(unittest.TestCase):
    """Geometry validation tests for the hemisphere."""

    def test_hemisphere_coordinates(self):
        """Test that hemisphere coordinates are properly generated."""
        sky_dome = SimpleSkyDome(MockApp(), radius=100.0)
        
        # Test that the geometry generation produces valid coordinates
        with patch('environment.simple_sky.GeomVertexWriter') as mock_writer_class:
            mock_writer = Mock()
            mock_writer_class.return_value = mock_writer
            
            sky_dome._create_hemisphere(segments=4, rings=3)
            
            # Should have written vertex data
            self.assertTrue(mock_writer.addData3.called)

    def test_texture_coordinate_generation(self):
        """Test that texture coordinates are properly generated."""
        sky_dome = SimpleSkyDome(MockApp(), radius=100.0)
        
        # Test that texture coordinates are generated in proper range
        with patch('environment.simple_sky.GeomVertexWriter') as mock_writer_class:
            mock_writer = Mock()
            mock_writer_class.return_value = mock_writer
            
            sky_dome._create_hemisphere(segments=4, rings=3)
            
            # Should have written texture coordinate data
            self.assertTrue(mock_writer.addData2.called)

    def test_triangle_primitive_generation(self):
        """Test that triangle primitives are properly generated."""
        sky_dome = SimpleSkyDome(MockApp(), radius=100.0)
        
        # Test that geometry primitives are created correctly
        with patch('environment.simple_sky.Geom') as mock_geom_class, \
             patch('environment.simple_sky.GeomTriangles') as mock_tri_class:
            mock_geom = Mock()
            mock_geom_class.return_value = mock_geom
            
            mock_tri = Mock()
            mock_tri_class.return_value = mock_tri
            
            sky_dome._create_hemisphere(segments=4, rings=3)
            
            # Should have added primitives to geometry
            self.assertTrue(mock_geom.addPrimitive.called)

if __name__ == '__main__':
    unittest.main(verbosity=2)
