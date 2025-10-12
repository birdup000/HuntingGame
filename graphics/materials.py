"""
PBR Materials System for realistic terrain, objects, and environment rendering.
Implements Physically Based Rendering for photorealistic graphics.
"""

from panda3d.core import Material, TextureStage, NodePath, LVector3, LVector4
import math


class PBRMaterial:
    """Physically Based Rendering material with metallic, roughness, and normal maps."""
    
    def __init__(self, base_color=(1, 1, 1, 1), metallic=0.0, roughness=1.0, normal_scale=1.0):
        self.material = Material()
        self.base_color = base_color
        self.metallic = metallic
        self.roughness = roughness
        self.normal_scale = normal_scale
        self._setup_material()
    
    def _setup_material(self):
        """Set up the PBR material properties."""
        # Base color (albedo)
        self.material.setDiffuse(self.base_color)
        self.material.setAmbient(self.base_color)
        
        # Handle metallic/roughness workflow
        # Convert roughness to glossiness for Panda3D
        gloss = max(0.001, 1.0 - self.roughness)
        self.material.setShininess(128 * gloss)
        
        # Calculate specular based on metallic workflow
        if self.metallic > 0.5:
            # Metallic materials have colored specular
            spec_color = LVector3(*self.base_color[:3]) * self.metallic
            self.material.setSpecular(LVector4(spec_color[0], spec_color[1], spec_color[2], 1.0))
        else:
            # Non-metallic materials use standard specular
            spec_strength = 0.04 * (1.0 - self.metallic) + self.metallic
            self.material.setSpecular(LVector4(spec_strength, spec_strength, spec_strength, 1.0))
    
    def apply_to(self, node_path):
        """Apply this PBR material to a NodePath."""
        node_path.setMaterial(self.material, 1)  # 1 = override parent materials


class TerrainPBR:
    """PBR terrain material with layered texturing."""
    
    def __init__(self):
        self.setup_terrain_materials()
    
    def setup_terrain_materials(self):
        """Create realistic terrain materials using PBR principles."""
        # Forest floor material
        self.forest_floor = PBRMaterial(
            base_color=(0.1, 0.05, 0.03, 1.0),  # Dark brown
            metallic=0.0,
            roughness=0.9,  # Very rough
            normal_scale=1.0
        )
        
        # Rocky terrain material  
        self.rocks = PBRMaterial(
            base_color=(0.3, 0.3, 0.35, 1.0),  # Gray rock
            metallic=0.1,
            roughness=0.7,  # Moderately rough
            normal_scale=1.2
        )
        
        # Wet mud material
        self.wet_mud = PBRMaterial(
            base_color=(0.15, 0.08, 0.05, 1.0),  # Dark muddy brown
            metallic=0.0,
            roughness=0.5,  # Smoother when wet
            normal_scale=0.8
        )
        
        # Snow material
        self.snow = PBRMaterial(
            base_color=(0.95, 0.98, 1.0, 1.0),  # Pure white
            metallic=0.0,
            roughness=0.3,  # Smooth but not glossy
            normal_scale=0.5
        )
    
    def get_material_for_height(self, height, moisture=0.0):
        """Return appropriate material based on terrain height and moisture."""
        if height > 2.0:
            return self.snow
        elif height > 0.5:
            return self.rocks
        elif moisture > 0.7:
            return self.wet_mud
        else:
            return self.forest_floor


class EnvironmentMaterials:
    """Collection of PBR materials for natural elements."""
    
    def __init__(self):
        self.setup_natural_materials()
    
    def setup_natural_materials(self):
        """Set up materials for trees, water, and other natural elements."""
        # Tree bark material
        self.tree_bark = PBRMaterial(
            base_color=(0.15, 0.08, 0.04, 1.0),  # Dark brown
            metallic=0.0,
            roughness=0.95,  # Very rough
            normal_scale=1.5
        )
        
        # Leaves material
        self.leaves = PBRMaterial(
            base_color=(0.1, 0.3, 0.05, 1.0),  # Green leaves
            metallic=0.0,
            roughness=0.6,  # Moderately rough
            normal_scale=0.8
        )
        
        # Water material (dynamic)
        self.water_static = PBRMaterial(
            base_color=(0.2, 0.3, 0.5, 1.0),  # Blue water
            metallic=0.5,
            roughness=0.2,  # Smooth
            normal_scale=0.3
        )
        
        # Grass material
        self.grass = PBRMaterial(
            base_color=(0.1, 0.4, 0.05, 1.0),  # Green grass
            metallic=0.0,
            roughness=0.8,  # Rough
            normal_scale=0.6
        )
        
    def get_dynamic_water_material(self, wave_intensity):
        """Get water material that changes with wave conditions."""
        roughness = 0.2 + (wave_intensity * 0.3)  # Waves increase roughness
        return PBRMaterial(
            base_color=(0.2, 0.3, 0.5, 1.0),
            metallic=0.4,
            roughness=roughness,
            normal_scale=0.2 + wave_intensity
        )


class FoliageMaterial:
    """Specialized material for animated foliage."""
    
    def __init__(self):
        self.leaf_material = PBRMaterial(
            base_color=(0.1, 0.3, 0.05, 1.0),
            metallic=0.0,
            roughness=0.7,
            normal_scale=0.5
        )
        self.grass_material = PBRMaterial(
            base_color=(0.1, 0.4, 0.05, 1.0),
            metallic=0.0,
            roughness=0.8,
            normal_scale=0.3
        )
    
    def apply_with_wind(self, node_path, wind_strength=0.0):
        """Apply material with wind animation considerations."""
        # Adjust roughness based on wind (wet leaves are shinier when windblown)
        roughness = 0.7 + (wind_strength * 0.1)
        self.leaf_material.roughness = roughness
        self.leaf_material._setup_material()
        self.leaf_material.apply_to(node_path)


# Import fixes for circular references
def import_main_app():
    """Safely import main app reference."""
    try:
        from main import main_app
        return main_app
    except ImportError:
        # Fallback - would be set by MainApp at runtime
        return getattr(MainApp, 'app', None)


# Predefined material presets for common elements
MATERIAL_PRESETS = {
    'dirt': PBRMaterial((0.3, 0.2, 0.1, 1.0), 0.0, 0.9),
    'rock': PBRMaterial((0.4, 0.4, 0.45, 1.0), 0.1, 0.7),
    'grass': PBRMaterial((0.1, 0.4, 0.05, 1.0), 0.0, 0.8),
    'tree_bark': PBRMaterial((0.15, 0.08, 0.04, 1.0), 0.0, 0.95),
    'leaves': PBRMaterial((0.1, 0.3, 0.05, 1.0), 0.0, 0.6),
    'water': PBRMaterial((0.2, 0.3, 0.5, 1.0), 0.5, 0.2),
    'snow': PBRMaterial((0.95, 0.98, 1.0, 1.0), 0.0, 0.3),
    'metal_gun': PBRMaterial((0.2, 0.22, 0.25, 1.0), 0.8, 0.4),
    'wood_gun': PBRMaterial((0.4, 0.25, 0.1, 1.0), 0.0, 0.6),
}
