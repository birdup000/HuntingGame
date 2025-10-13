#!/usr/bin/env python3
"""
Main entry point for the 3D Hunting Simulator Game.
Initializes the game engine and starts the main game loop.
"""

import sys
from direct.showbase.ShowBase import ShowBase
from core.game import Game
from graphics.post_processing import PostProcessing, CinematicEffects
from graphics.settings_manager import GraphicsSettingsManager, create_optimized_graphics

class MainApp(ShowBase):
    """Main application class that initializes Panda3D and starts the game."""

    def __init__(self):
        """Initialize the Panda3D application and game."""
        # Set window properties for better branding
        from config import GAME_CONFIG
        ShowBase.__init__(self)
        
        # Ensure proper camera settings for visibility
        if hasattr(self, 'camLens'):
            self.camLens.setFar(2000)  # Increased far clip for better visibility
            self.camLens.setNear(0.1)  # Closer near clip
        
        # Initialize graphics systems
        self.graphics_manager = create_optimized_graphics(self)
        self.setup_post_processing()
        
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
        
        # Store reference for access by terrain system
        MainApp.app = self
        
    def setup_post_processing(self):
        """Set up post-processing effects for photorealistic rendering."""
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
            
        print("High-quality post-processing enabled")
    
    def setup_graphics_quality(self):
        """Enhance graphics quality with better rendering settings."""
        # Enable hardware anti-aliasing
        from panda3d.core import AntialiasAttrib
        if hasattr(self, 'props'):
            self.props.set_antialias(AntialiasAttrib.M_multisample)
        
        # Enable better texture filtering
        from panda3d.core import Texture, AntialiasAttrib
        Texture.set_textures_power_2(True)
        self.render.set_antialias(AntialiasAttrib.M_auto)
        
        # Improve overall rendering quality with better materials and lighting
        if hasattr(self, 'render'):
            # Use better material properties for scene
            from panda3d.core import Material, LightRampAttrib
            mat = Material()
            mat.setShininess(45)  # Higher shininess for more realistic materials
            mat.setSpecular((0.3, 0.3, 0.3, 1))  # Subtle specular highlights
            self.render.setMaterial(mat)
            
            # Enable better lighting model
            self.render.setAttrib(LightRampAttrib.makeDefault())
            
            # Enable fog for atmospheric depth
            from panda3d.core import Fog
            if self.render.has_fog():
                self.render.clear_fog()
            
        # Set better default render properties
        if hasattr(self, 'render'):
            self.render.setShaderAuto()
            
        print("Graphics quality enhanced")

def main():
    """Main function to run the application."""
    app = MainApp()
    app.run()

if __name__ == "__main__":
    main()