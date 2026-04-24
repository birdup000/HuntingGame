"""
Player module for the 3D Hunting Simulator.
Handles player character, controls, and inventory.
"""

from .player import Player, Weapon
from physics.collision import Projectile

__all__ = ['Player', 'Weapon', 'Projectile']