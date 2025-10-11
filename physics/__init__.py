"""
Physics module for the 3D Hunting Simulator.
Handles collision detection, ballistics, and physics simulations.
"""

from .collision import CollisionManager, Projectile

__all__ = ['CollisionManager', 'Projectile']