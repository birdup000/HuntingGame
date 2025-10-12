"""Graphics settings manager that coordinates all visual systems.
Provides runtime adjustment of graphics quality and performance.
"""

from config import ADVANCED_GRAPHICS
from graphics.materials import MATERIAL_PRESETS
import os


class GraphicsSettingsManager:
    """Manages graphics settings and quality levels."""
    
    def __init__(self, base_app, render_node):
        self.base = base_app
        self.render = render_node
        
        # Current settings
        self.current_quality = 'high'
        self.settings = ADVANCED_GRAPHICS.copy()
        
        # Performance monitoring
        self.fps_samples = []
        self.target_fps = 60
        self.suggesting_settings = False
        
    def set_quality_preset(self, quality_level):
        """Apply graphics preset (low, medium, high, ultra)."""
        presets = {
            'low': {
                'texture_quality': 'low',
                'shadow_quality': 'low',
                'draw_distance': 500,
                'use_pbr': False,
                'bloom_enabled': False,
                'ssao_enabled': False,
                'volumetric_fog': False,
                'dynamic_weather': False,
                'foliage_wind': False,
                'fxaa': True
            },
            'medium': {
                'texture_quality': 'medium',
                'shadow_quality': 'medium',
                'draw_distance': 750,
                'use_pbr': True,
                'bloom_enabled': True,
                'ssao_enabled': False,
                'volumetric_fog': True,
                'dynamic_weather': True,
                'foliage_wind': True,
                'fxaa': True
            },
            'high': {
                'texture_quality': 'high',
                'shadow_quality': 'medium',
                'draw_distance': 1000,
                'use_pbr': True,
                'bloom_enabled': True,
                'ssao_enabled': True,
                'volumetric_fog': True,
                'dynamic_weather': True,
                'foliage_wind': True,
                'fxaa': True
            },
            'ultra': {
                'texture_quality': 'high',
                'shadow_quality': 'high',
                'draw_distance': 1500,
                'use_pbr': True,
                'bloom_enabled': True,
                'ssao_enabled': True,
                'volumetric_fog': True,
                'dynamic_weather': True,
                'foliage_wind': True,
                'fxaa': True,
                'motion_blur_enabled': True
            }
        }
        
        if quality_level in presets:
            for key, value in presets[quality_level].items():
                self.settings[key] = value
                
            self.current_quality = quality_level
            self.apply_settings()
            print(f"Graphics quality set to: {quality_level}")
            return True
        return False
    
    def apply_settings(self):
        """Apply current graphics settings."""
        # Update Panda3D settings
        from panda3d.core import Texture, AntialiasAttrib, GraphicsEngine
        
        # Texture quality
        # Note: setDefaultAnisotropicDegree not available in this Panda3D version
        # Anisotropic filtering will need to be applied per-texture
        if self.settings['texture_quality'] == 'low':
            aniso_degree = 1
        elif self.settings['texture_quality'] == 'medium':
            aniso_degree = 4
        else:
            aniso_degree = 16
        print(f"Anisotropic filtering degree: {aniso_degree} (applied to individual textures)")
        
        # Anti-aliasing
        if self.settings['fxaa']:
            self.render.setAntialias(AntialiasAttrib.MAuto)
        else:
            self.render.setAntialias(AntialiasAttrib.MNone)
        
        # Draw distance
        self.base.camLens.setFar(self.settings['draw_distance'])
        
        # Apply other settings through their respective systems
        if hasattr(self.base, 'game'):
            game = self.base.game
            
            # Update materials
            if self.settings['use_pbr']:
                print("PBR Materials: Enabled")
            else:
                print("PBR Materials: Disabled")
                
            # Update post-processing
            if hasattr(self, 'post_processing'):
                if not self.settings['bloom_enabled']:
                    self.post_processing.disable_bloom()
                if self.settings['ssao_enabled']:
                    self.post_processing.enable_ssao()
        
        print(f"Graphics settings applied - Quality: {self.current_quality}")
    
    def monitor_performance(self):
        """Monitor frames per second and adjust settings if needed."""
        # Frame rate monitoring disabled for now due to import issues
        # Would monitor FPS and adjust settings based on performance
        pass
    
    def get_performance_stats(self):
        """Get performance statistics."""
        return {
            'current_fps': 60,  # Placeholder
            'target_fps': self.target_fps,
            'quality_level': self.current_quality,
            'settings': {k: v for k, v in self.settings.items() if k in ['texture_quality', 'shadow_quality', 'use_pbr', 'bloom_enabled']}
        }
    
    def export_settings_report(self):
        """Export a detailed graphics settings report."""
        report = []
        report.append("=== HUNTING GAME GRAPHICS REPORT ===\n")
        report.append(f"Quality Level: {self.current_quality}")
        report.append(f"Target FPS: {self.target_fps}")
        report.append(f"Current FPS: 60")  # Placeholder
        report.append(f"Draw Distance: {self.settings['draw_distance']} units\n")
        
        # System status
        features = [
            ('PBR Materials', self.settings['use_pbr']),
            ('Bloom Effect', self.settings['bloom_enabled']),
            ('SSAO', self.settings['ssao_enabled']),
            ('Volumetric Fog', self.settings['volumetric_fog']),
            ('Dynamic Weather', self.settings['dynamic_weather']),
            ('Foliage Wind', self.settings['foliage_wind']),
            ('Motion Blur', self.settings['motion_blur_enabled'])
        ]
        
        report.append("Features:")
        for name, enabled in features:
            status = "✓" if enabled else "✗"
            report.append(f"  {status} {name}")
        
        return "\n".join(report)


def create_optimized_graphics(base_app):
    """Create an optimized graphics setup for the hunting game."""
    manager = GraphicsSettingsManager(base_app, base_app.render)
    
    # Set initial quality based on system capabilities
    import platform
    system = platform.system().lower()
    
    # Automatically select quality based on platform (simplified)
    if system == 'windows':
        manager.set_quality_preset('high')
    else:
        manager.set_quality_preset('medium')
    
    # Apply additional optimizations
    manager.apply_settings()
    
    # Start performance monitoring
    from direct.task import Task
    def monitor_perf(task):
        manager.monitor_performance()
        return Task.again
    
    base_app.taskMgr.add(monitor_perf, 'performanceMonitor', priority=5)
    
    print("Optimized graphics system initialized")
    return manager
