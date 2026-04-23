"""
Environment module for the 3D Hunting Simulator.
Handles terrain generation, weather, and environmental effects.
"""

from .pbr_terrain import PBRTerrain as Terrain

__all__ = ['Terrain']