"""Simple sky dome implementation using procedural geometry."""

from typing import Optional
from panda3d.core import (
    NodePath,
    GeomNode,
    Geom,
    GeomTriangles,
    GeomVertexFormat,
    GeomVertexData,
    GeomVertexWriter,
    TransparencyAttrib,
    CompassEffect,
    CullFaceAttrib,
    BoundingSphere,
    Point3,
    Vec3,
)
import math
from graphics.texture_factory import create_sky_texture


class SimpleSkyDome:
    """Simple procedural sky dome using a hemisphere."""
    
    def __init__(self, app, radius: float = 600.0):
        self.app = app
        self.radius = radius
        self.node: Optional[NodePath] = None
        self._root: Optional[NodePath] = None
        self._task = None
        self._setup_sky()

    def _create_hemisphere(self, segments: int = 32, rings: int = 16):
        """Create a hemisphere mesh procedurally."""
        # Create vertex format and data
        format = GeomVertexFormat.getV3t2()
        vdata = GeomVertexData('hemisphere', format, Geom.UHStatic)
        vdata.setNumRows((rings + 1) * (segments + 1))
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        
        # Generate vertices
        for ring in range(rings + 1):
            phi = (math.pi / 2.0) * (ring / rings)  # 0 to pi/2 (hemisphere)
            for seg in range(segments + 1):
                theta = (2 * math.pi) * (seg / segments)
                
                # Spherical coordinates to Cartesian
                x = self.radius * math.cos(phi) * math.sin(theta)
                y = self.radius * math.cos(phi) * math.cos(theta)
                z = self.radius * math.sin(phi)
                
                vertex.addData3(x, y, z)
                
                # Texture coordinates
                u = seg / segments
                v = 1.0 - (ring / rings)  # Invert V for correct orientation
                texcoord.addData2(u, v)
        
        # Create geometry
        geom = Geom(vdata)
        
        # Generate triangles
        for ring in range(rings):
            for seg in range(segments):
                # Calculate vertex indices
                v0 = ring * (segments + 1) + seg
                v1 = v0 + 1
                v2 = v0 + segments + 1
                v3 = v2 + 1
                
                # Create two triangles for each quad
                tri1 = GeomTriangles(Geom.UHStatic)
                tri1.addVertices(v0, v2, v1)
                tri1.closePrimitive()
                geom.addPrimitive(tri1)
                
                tri2 = GeomTriangles(Geom.UHStatic)
                tri2.addVertices(v1, v2, v3)
                tri2.closePrimitive()
                geom.addPrimitive(tri2)
        
        # Create node
        geom_node = GeomNode('hemisphere')
        geom_node.addGeom(geom)
        
        return NodePath(geom_node)

    def _setup_sky(self):
        """Set up the sky dome."""
        # Get sky texture
        texture = create_sky_texture()
        
        # Set background color
        if hasattr(self.app, 'setBackgroundColor'):
            self.app.setBackgroundColor(0.45, 0.62, 0.88, 1)

        # Create root node
        parent = getattr(self.app, 'render', None)
        if parent is None:
            return
            
        self._root = parent.attachNewNode('sky_dome_root')
        
        # Configure root node for background rendering
        self._root.setBin('background', -100)  # Render first
        self._root.setDepthWrite(False)
        self._root.setDepthTest(False)
        self._root.setLightOff(1)
        self._root.setFogOff()
        self._root.setShaderOff(1)
        self._root.setTransparency(TransparencyAttrib.MNone)
        
        # Create hemisphere geometry
        hemisphere = self._create_hemisphere()
        hemisphere.reparentTo(self._root)
        
        # Configure hemisphere
        hemisphere.setTexture(texture, 1)
        hemisphere.setTwoSided(False)  # Only render inside
        hemisphere.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullClockwise))  # Cull outside faces
        hemisphere.setScale(1, 1, 1)
        
        self.node = hemisphere
        
        # Make sky follow camera
        if hasattr(self.app, 'camera'):
            compass = CompassEffect.make(self.app.camera, CompassEffect.PPos)
            self._root.setEffect(compass)
        
        # Add update task
        if hasattr(self.app, 'taskMgr'):
            self._task = self.app.taskMgr.add(self._update_task, 'simpleSkyDomeFollow', sort=50)

    def _update_task(self, task):
        """Update sky position to follow camera."""
        if not self._root or not hasattr(self.app, 'camera'):
            return task.cont
        # The CompassEffect should handle this, but we can add extra positioning if needed
        return task.cont

    def cleanup(self):
        """Clean up resources."""
        if self._task and hasattr(self.app, 'taskMgr'):
            self.app.taskMgr.remove(self._task)
            self._task = None
        if self._root:
            self._root.removeNode()
            self._root = None
        if self.node and not self.node.isEmpty():
            self.node.removeNode()
            self.node = None
