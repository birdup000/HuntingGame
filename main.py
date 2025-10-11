#!/usr/bin/env python3
"""
Main entry point for the 3D Hunting Simulator Game.
Initializes the game engine and starts the main game loop.
"""

import sys
from direct.showbase.ShowBase import ShowBase
from core.game import Game

class MainApp(ShowBase):
    """Main application class that initializes Panda3D and starts the game."""

    def __init__(self):
        """Initialize the Panda3D application and game."""
        # Set window properties for better branding
        from config import GAME_CONFIG
        ShowBase.__init__(self)
        
        # Note: Window title can be set via Config.prc configuration file if needed
        
        # ENSURE clean 2D rendering to prevent UI distortion
        self.setFrameRateMeter(False)  # Hide FPS in final build
        self.render2d.setDepthTest(False)  # Prevent 3D interaction with 2D
        self.render2d.setDepthWrite(False)  # Ensure 2D elements don't write to depth buffer
        
        # Set up proper render-to-2D separation
        if hasattr(self, 'render'):
            self.render.setDepthTest(True)  # Enable depth test for 3D
            self.render.setDepthWrite(True)  # Enable depth writing for 3D
            
        # Additional cleanup - ensure no stray debug visualization
        self.disableAllAudio()  # Prevent debug sounds
        
        # Initialize game after engine setup
        self.game = Game(self)
        self.game.start()

def main():
    """Main function to run the application."""
    app = MainApp()
    app.run()

if __name__ == "__main__":
    main()