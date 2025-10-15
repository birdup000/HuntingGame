#!/usr/bin/env python3
"""
Main entry point for the 3D Hunting Simulator Game.
Initializes the game engine and starts the main game loop.
"""

import logging
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from core.game import Game
try:
    from graphics.post_processing import PostProcessing, CinematicEffects
    from graphics.settings_manager import create_optimized_graphics
except ImportError:
    # Handle cases where graphics modules are incomplete
    PostProcessing = None
    CinematicEffects = None
    create_optimized_graphics = None

class MainApp(ShowBase):
    """Main application class that initializes Panda3D and starts the game."""

    def __init__(self):
        """Initialize the Panda3D application and game."""
        # Set window properties for better branding
        ShowBase.__init__(self)

        # Set window to foreground
        props = WindowProperties()
        props.setForeground(True)
        self.win.requestProperties(props)

        # Ensure proper camera settings for visibility
        if hasattr(self, 'camLens'):
            self.camLens.setFar(2000)  # Increased far clip for better visibility
            self.camLens.setNear(0.1)  # Closer near clip
        
        # Initialize graphics systems
        if create_optimized_graphics is not None:
            self.graphics_manager = create_optimized_graphics(self)
        else:
            self.graphics_manager = None
        self.setup_post_processing()
        
        # PROPER render-to-2D separation to prevent UI artifacts
        self.setFrameRateMeter(False)  # Hide FPS in final build
        self.render2d.setDepthTest(False)  # Prevent 3D interaction with 2D
        self.render2d.setDepthWrite(False)  # Ensure 2D elements don't write to depth buffer
        
        # Set up proper render-to-2D separation with explicit sorting
        # Create a proper render bin for 3D scene first
        if hasattr(self, 'render'):
            self.render.setDepthTest(True)  # Enable depth test for 3D
            self.render.setDepthWrite(True)  # Enable depth writing for 3D
            
        # Set up render2d with proper bin sorting for UI
        self.render2d.setBin('fixed', 60)  # UI renders last
        self.aspect2d.setBin('fixed', 60)  # Aspect2d for overlays
            
        # Additional cleanup - ensure no stray debug visualization
        self.disableAllAudio()  # Prevent debug sounds
        
        # Initialize game after engine setup
        self.game = Game(self)
        self.game.start()
        
        # Store reference for access by terrain system
        MainApp.app = self
        
    def setup_post_processing(self):
        """Set up post-processing effects for photorealistic rendering."""
        if PostProcessing is None or CinematicEffects is None:
            logging.warning("Post-processing modules not available")
            return

        from config import GRAPHICS_CONFIG, ADVANCED_GRAPHICS

        self.post_processing = PostProcessing(self)
        self.cinematic = CinematicEffects(self)

        # Apply graphics settings
        if GRAPHICS_CONFIG['use_bloom']:
            self.post_processing.enable_bloom(ADVANCED_GRAPHICS['bloom_intensity'])

        if GRAPHICS_CONFIG['fxaa']:
            self.post_processing.enable_fxaa()

        if GRAPHICS_CONFIG['use_ssao']:
            self.post_processing.enable_ssao(ADVANCED_GRAPHICS['ssao_radius'])

        logging.info("High-quality post-processing enabled")

def main():
    """Main function to run the application."""
    app = MainApp()
    app.run()

if __name__ == "__main__":
    main()