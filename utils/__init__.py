"""Utilities package for the 3D Hunting Simulator."""

try:
    from utils.save_manager import SaveManager
    __all__ = ['SaveManager']
except ImportError:
    __all__ = []
