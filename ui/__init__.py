"""
UI module for the 3D Hunting Simulator.
Handles user interface elements and menus.
"""

from .hud import HUD
from .menus import UIManager, MainMenu, PauseMenu, GameOverMenu, SettingsMenu

__all__ = ['HUD', 'UIManager', 'MainMenu', 'PauseMenu', 'GameOverMenu', 'SettingsMenu']