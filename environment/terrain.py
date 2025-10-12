"""
Terrain module for procedural terrain generation in the 3D Hunting Simulator.
Uses OpenSimplex noise for realistic landscape generation.
"""

import numpy as np
from opensimplex import OpenSimplex
from panda3d.core import Geom, GeomNode, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles, Vec3, Vec4, NodePath
from typing import Tuple, Optional


class Terrain:
    """Handles procedural terrain generation and rendering."""

    def __init__(self, width: int = 200, height: int = 200, scale: float = 0.5, octaves: int = 4):
        """
        Initialize terrain generator.

        Args:
            width: Width of the terrain in units
            height: Height of the terrain in units
            scale: Scale factor for noise (lower = smoother terrain)
            octaves: Number of noise octaves for detail
        """
        self.width = width
        self.height = height
        self.scale = scale
        self.octaves = octaves
        self.noise = OpenSimplex(seed=42)  # Fixed seed for reproducible terrain
        self.terrain_node: Optional[NodePath] = None
        self.height_map: Optional[np.ndarray] = None

    def generate_terrain(self) -> np.ndarray:
        """
        Generate height map using multi-octave noise with improved realism.

        Returns:
            2D numpy array representing height values
        """
        self.height_map = np.zeros((self.width + 1, self.height + 1))

        for x in range(self.width + 1):
            for y in range(self.height + 1):
                # Normalize coordinates
                nx = x / self.width - 0.5
                ny = y / self.height - 0.5

                # Distance from center for terrain shaping
                distance = np.sqrt(nx * nx + ny * ny)
                center_weight = max(0, 1 - distance * 1.3)  # Hills near center, flatter edges

                # Multi-octave noise with terrain shaping
                amplitude = 1.0
                frequency = 1.0
                value = 0.0

                for _ in range(self.octaves):
                    value += self.noise.noise2(nx * frequency, ny * frequency) * amplitude
                    amplitude *= 0.5
                    frequency *= 2.0

                # Apply erosion-like effect and scale
                value = value * center_weight  # Mountains in center, valleys at edges
                self.height_map[x, y] = value * 15.0 + distance * 3.0  # More dramatic terrain

        return self.height_map

    def get_height(self, x: float, y: float) -> float:
        """
        Get interpolated height at given coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Height value at the given position
        """
        if self.height_map is None:
            return 0.0

        # Convert world coordinates to height map indices
        map_x = int((x + self.width / 2) / self.scale)
        map_y = int((y + self.height / 2) / self.scale)

        # Clamp to bounds
        map_x = max(0, min(self.width, map_x))
        map_y = max(0, min(self.height, map_y))

        return float(self.height_map[map_x, map_y])

    def create_terrain_mesh(self) -> GeomNode:
        """
        Create 3D mesh from height map.

        Returns:
            Panda3D GeomNode containing the terrain mesh
        """
        if self.height_map is None:
            self.generate_terrain()

        # Create vertex format
        format = GeomVertexFormat.getV3n3c4t2()
        vdata = GeomVertexData('terrain', format, Geom.UHStatic)

        # Create writers
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        texcoord = GeomVertexWriter(vdata, 'texcoord')

        # Generate vertices
        for x in range(self.width + 1):
            for y in range(self.height + 1):
                # Position
                world_x = (x - self.width / 2) * self.scale
                world_y = (y - self.height / 2) * self.scale
                world_z = self.height_map[x, y]

                vertex.addData3f(world_x, world_y, world_z)

                # Calculate normal (simplified)
                normal_x = 0.0
                normal_y = 0.0
                normal_z = 1.0

                # Simple normal calculation using neighboring heights
                if x > 0 and x < self.width and y > 0 and y < self.height:
                    h_left = self.height_map[x - 1, y]
                    h_right = self.height_map[x + 1, y]
                    h_down = self.height_map[x, y - 1]
                    h_up = self.height_map[x, y + 1]

                    normal_x = (h_left - h_right) / (2 * self.scale)
                    normal_y = (h_down - h_up) / (2 * self.scale)
                    normal_z = 1.0

                    # Normalize
                    length = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
                    if length > 0:
                        normal_x /= length
                        normal_y /= length
                        normal_z /= length

                normal.addData3f(normal_x, normal_y, normal_z)

                # Color based on height (realistic biome coloring)
                if world_z < 2.0:
                    color.addData4f(0.2, 0.4, 0.8, 1.0)  # Deep water
                elif world_z < 4.0:
                    color.addData4f(0.1, 0.5, 0.1, 1.0)  # Grass (natural green)
                elif world_z < 6.0:
                    color.addData4f(0.4, 0.28, 0.15, 1.0)  # Dirt (earth tone)
                elif world_z < 8.0:
                    color.addData4f(0.25, 0.2, 0.1, 1.0)  # Forest (darker green-brown)
                elif world_z < 10.0:
                    color.addData4f(0.2, 0.15, 0.1, 1.0)  # Mountain (dark brown)
                else:
                    color.addData4f(0.95, 0.95, 0.95, 1.0)  # Snow (pure white)

                # Texture coordinates
                texcoord.addData2f(x / self.width, y / self.height)

        # Create triangles
        geom = Geom(vdata)
        prim = GeomTriangles(Geom.UHStatic)

        for x in range(self.width):
            for y in range(self.height):
                # First triangle
                prim.addVertex(x * (self.height + 1) + y)
                prim.addVertex((x + 1) * (self.height + 1) + y)
                prim.addVertex(x * (self.height + 1) + (y + 1))

                # Second triangle
                prim.addVertex((x + 1) * (self.height + 1) + y)
                prim.addVertex((x + 1) * (self.height + 1) + (y + 1))
                prim.addVertex(x * (self.height + 1) + (y + 1))

        geom.addPrimitive(prim)

        # Create node
        node = GeomNode('terrain')
        node.addGeom(geom)

        return node

    def render(self, parent_node: NodePath) -> NodePath:
        """
        Render the terrain and attach to parent node.

        Args:
            parent_node: Parent node to attach terrain to

        Returns:
            NodePath containing the rendered terrain
        """
        terrain_geom = self.create_terrain_mesh()
        self.terrain_node = parent_node.attachNewNode(terrain_geom)

        return self.terrain_node

    def cleanup(self):
        """Clean up terrain resources."""
        if self.terrain_node:
            self.terrain_node.removeNode()
            self.terrain_node = None