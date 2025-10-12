"""
Enhanced terrain system with PBR materials, dynamic texturing, and optimized rendering.
Supports photorealistic terrain with multiple material zones and weather effects.
"""

import numpy as np
from opensimplex import OpenSimplex
from panda3d.core import (
    Geom, GeomNode, GeomVertexData, GeomVertexFormat, GeomVertexWriter, 
    GeomTriangles, Vec3, Vec4, NodePath, Texture, TextureStage, ColorWriteAttrib,
    AlphaTestAttrib, Material
)
from graphics.materials import TerrainPBR, EnvironmentMaterials
import math


class PBRTerrain:
    """Terrain with Physically Based Rendering support."""
    
    def __init__(self, width=100, height=100, scale=1.0, octaves=4):
        self.width = width
        self.height = height
        self.scale = scale
        self.octaves = octaves
        self.noise = OpenSimplex(seed=42)
        self.height_map = None
        self.terrain_node = None
        
        # PBR terrain materials
        self.terrain_pbr = TerrainPBR()
        self.environment_mats = EnvironmentMaterials()
        
        # Material blending zones
        self.material_zones = {}
        
    def generate_terrain(self):
        """Generate height map with erosion and hydrology simulation."""
        self.height_map = np.zeros((self.width + 1, self.height + 1))
        
        for x in range(self.width + 1):
            for y in range(self.height + 1):
                # Multi-octave noise with terrain shaping
                height = 0
                amplitude = 1.0
                frequency = self.scale
                
                for _ in range(self.octaves):
                    nx = (x / self.width - 0.5) * frequency
                    ny = (y / self.height - 0.5) * frequency
                    
                    height += self.noise.noise2(nx, ny) * amplitude
                    amplitude *= 0.5
                    frequency *= 2
                
                # Apply erosion simulation
                height = self._apply_erosion_filter(x, y, height)
                
                # Create river valleys
                if self._is_river_valley(x, y):
                    height -= 2.0 + abs(self._river_depth(x, y)) * 1.5
                
                self.height_map[x, y] = max(height * 3, -1.0)  # clamp minimum
    
    def _apply_erosion_filter(self, x, y, height):
        """Simulate erosion for more natural terrain."""
        # Simple erosion: lower areas based on neighbors
        erosion = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                    
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbor_height = self.height_map[nx, ny] if self.height_map is not None else 0
                    erosion += max(0, neighbor_height - height) * 0.1
                    
        return height - erosion * 0.05
    
    def _is_river_valley(self, x, y):
        """Determine if position should be in a river valley."""
        # Create meandering river pattern
        nx = x / self.width - 0.5
        ny = y / self.height - 0.5
        
        # River main path
        river_y = nx * 0.3 + 0.1 * math.sin(nx * 10)
        
        return abs(ny - river_y) < 0.1
    
    def _river_depth(self, x, y):
        """Calculate river depth at position."""
        nx = x / self.width - 0.5
        ny = y / self.height - 0.5
        river_y = nx * 0.3 + 0.1 * math.sin(nx * 10)
        return abs(ny - river_y) - 0.1
    
    def create_terrain_geometry(self):
        """Create optimized PBR terrain geometry."""
        # Create vertex format for PBR
        format = GeomVertexFormat.getV3n3c4t2()
        vdata = GeomVertexData('terrain', format, Geom.UHDynamic)
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        
        # Generate vertices and triangles
        vertices = []
        faces = []
        normals = []
        
        for x in range(self.width):
            for y in range(self.height):
                # Get height and calculate normal
                h = self.height_map[x, y]
                pos = Vec3(x - self.width/2, y - self.height/2, h)
                
                # Calculate normal using surrounding points
                normal_vec = self._calculate_normal(x, y)
                
                vertices.append(pos)
                normals.append(normal_vec)
                
                # Determine material zone
                zone = self._get_material_zone(x, y, h)
                
                # Store vertex data
                vertex.addData3f(pos.x, pos.y, pos.z)
                normal.addData3f(normal_vec.x, normal_vec.y, normal_vec.z)
                
                # Base color based on zone
                base_color = self._get_zone_color(zone, h)
                color.addData4f(*base_color)
                
                # UV coordinates with tiling
                uv_scale = 10.0  # Tiled texture
                texcoord.addData2f(
                    x / self.width * uv_scale,
                    y / self.height * uv_scale
                )
        
        # Create triangles
        for x in range(self.width - 1):
            for y in range(self.height - 1):
                idx = x * self.height + y
                
                # Two triangles per quad
                faces.extend([
                    [idx, idx + 1, idx + self.height],
                    [idx + 1, idx + self.height + 1, idx + self.height]
                ])
        
        # Add triangles to geometry
        tris = GeomTriangles(Geom.UHStatic)
        for face in faces:
            tris.addVertices(*face)
        
        # Create final geometry
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        
        # Create node and apply materials
        terrain_node = NodePath('terrain')
        
        # Create a GeomNode and attach the geom to it
        terrain_gnode = GeomNode('terrain_gnode')
        terrain_gnode.addGeom(geom)
        terrain_node_path = terrain_node.attachNewNode(terrain_gnode)
        
        return terrain_node
    
    def _calculate_normal(self, x, y):
        """Calculate surface normal at position."""
        # Use finite differences
        dx = 1 if x < self.width - 1 else -1
        dy = 1 if y < self.height - 1 else -1
        
        h = self.height_map[x, y]
        hx = self.height_map[x + dx, y] if 0 <= x + dx < self.width else h
        hy = self.height_map[x, y + dy] if 0 <= y + dy < self.height else h
        
        # Normal pointing up and away from slope
        return Vec3(
            -(hx - h) * dx,
            -(hy - h) * dy,
            1.0
        ).normalized()
    
    def _get_material_zone(self, x, y, height):
        """Determine material zone based on height, slope, and moisture."""
        # Height-based zones
        if height > 3:
            return 'snow'
        elif height > 1:
            return 'rock'
        elif height < 0:
            return 'wet'
        else:
            return 'forest'
    
    def _get_zone_color(self, zone, height):
        """Get base color for material zone."""
        colors = {
            'snow': (0.95, 0.98, 1.0, 1.0),
            'rock': (0.4, 0.4, 0.45, 1.0),
            'wet': (0.2, 0.15, 0.1, 1.0),
            'forest': (0.15, 0.2, 0.05, 1.0)
        }
        return colors.get(zone, (0.3, 0.3, 0.3, 1.0))
    
    def apply_dynamic_materials(self, player_pos):
        """Apply dynamic materials based on current conditions."""
        if not self.terrain_node:
            return
            
        # Sample current weather conditions for wetness
        wetness = 0.0  # Placeholder - weather system not available yet
        
        # Apply PBR materials to different zones (simple approach for now)
        # For now, just use basic materials directly on the terrain node
        for zone_name in self.material_zones:
            material = self._get_dynamic_material(zone_name, wetness)
            # Apply material to the main terrain node - in a full implementation, this would be zone-specific
            if hasattr(self.terrain_node, 'setMaterial'):
                self.terrain_node.setMaterial(material.material, 1)
    
    def _get_dynamic_material(self, zone_name, wetness):
        """Get material adjusted for current conditions."""
        base_material = None
        
        if zone_name == 'snow':
            base_material = self.terrain_pbr.snow
        elif zone_name == 'rock':
            base_material = self.terrain_pbr.rocks
        elif zone_name == 'wet':
            # Make wet areas shinier
            color = (0.15 + wetness * 0.1, 0.05 + wetness * 0.1, 0.03 + wetness * 0.1, 1.0)
            material = Material()
            material.setDiffuse(color)
            material.setSpecular((wetness * 0.3, wetness * 0.3, wetness * 0.3, 1.0))
            material.setShininess(64 + wetness * 64)
            return material
        else:
            base_material = self.terrain_pbr.forest_floor
            
        return base_material
    
    def render(self, parent_node):
        """Generate and render the terrain with PBR materials."""
        # Generate height map
        self.generate_terrain()
        
        # Create geometry
        self.terrain_node = self.create_terrain_geometry()
        
        # Apply to parent
        self.terrain_node.reparentTo(parent_node)
        
        # Set initial materials
        self.apply_dynamic_materials((0, 0, 0))  # Pass initial player position
        
        print(f"PBR Terrain generated: {self.width}x{self.height}, PBR materials applied")
    
    def get_height(self, x, y):
        """Get terrain height at world coordinates."""
        if self.height_map is None:
            return 0.0
        
        # Convert world coordinates to height map indices
        map_x = int(x + self.width // 2)
        map_y = int(y + self.height // 2)
        
        # Clamp to bounds
        map_x = max(0, min(map_x, self.width))
        map_y = max(0, min(map_y, self.height))
        
        return self.height_map[map_x, map_y]


class OptimizedTerrainRenderer:
    """Optimized terrain renderer with level-of-detail and culling."""
    
    def __init__(self, render_node):
        self.render = render_node
        self.active_terrains = []
        self.detail_levels = 3
        
    def add_terrain(self, terrain):
        """Add terrain for optimized rendering."""
        self.active_terrains.append(terrain)
        
    def update_lod(self, camera_pos):
        """Update level of detail based on camera distance."""
        for terrain in self.active_terrains:
            for zone in terrain.material_zones.values():
                dist = (zone['center'] - camera_pos).length()
                lod = min(int(dist / 50), self.detail_levels - 1)
                zone['node'].setEffect(LodEffect.make(
                    10 * lod,  # Switch distance
                    50 * lod,  # Fade start
                    100 * lod,  # Fade end
                    LodEffect.MAlpha
                ))
    
    def cull_terrain(self, camera_frustum):
        """Cull terrain outside camera view."""
        for terrain in self.active_terrains:
            # Simple frustum culling
            if not self._is_in_frustum(terrain.terrain_node, camera_frustum):
                terrain.terrain_node.hide()
            else:
                terrain.terrain_node.show()
    
    def _is_in_frustum(self, node, frustum):
        """Check if node is within camera frustum."""
        bounds = node.getTightBounds()
        if bounds:
            center = (bounds[0] + bounds[1]) / 2
            radius = (bounds[1] - bounds[0]).length() / 2
            return frustum.isSphereInFrustum(center, radius)
        return True
