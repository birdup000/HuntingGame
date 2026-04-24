"""
Graphics package for the 3D Hunting Simulator.
Handles textures, materials, lighting, weather, foliage, and post-processing.
"""

from graphics.texture_factory import (
    TextureFactory,
    create_crosshair_texture,
    create_icon_texture,
    get_ui_panel_texture,
    create_terrain_texture,
    create_track_texture,
)

from graphics.materials import TerrainPBR, EnvironmentMaterials
from graphics.lighting import DynamicLighting
from graphics.weather import WeatherSystem
from graphics.foliage import FoliageRenderer, GrassField
from graphics.post_processing import PostProcessing, CinematicEffects
from graphics.settings_manager import GraphicsSettingsManager, create_optimized_graphics

__all__ = [
    'TextureFactory',
    'create_crosshair_texture',
    'create_icon_texture',
    'get_ui_panel_texture',
    'create_terrain_texture',
    'create_track_texture',
    'TerrainPBR',
    'EnvironmentMaterials',
    'DynamicLighting',
    'WeatherSystem',
    'FoliageRenderer',
    'GrassField',
    'PostProcessing',
    'CinematicEffects',
    'GraphicsSettingsManager',
    'create_optimized_graphics',
]
