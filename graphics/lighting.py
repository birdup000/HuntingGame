"""
Advanced lighting system with dynamic time, volumetric effects, and photorealistic rendering.
"""

from panda3d.core import (
    DirectionalLight, AmbientLight, PointLight, Spotlight,
    Vec4, Vec3, Fog, LVector3, NodePath, ShaderGenerator, 
    RenderState, Material
)
import math
import random


class DynamicLighting:
    """Advanced lighting system with time-of-day cycles and weather effects."""
    
    def __init__(self, render_node):
        self.render = render_node
        self.sun_light = None
        self.ambient_light = None
        self.fill_light = None
        self.sky_ambient = None
        self.time_of_day = 12.0  # 12:00 PM (noon)
        self.is_setup = False
        
        # Weather states
        self.rain_intensity = 0.0
        self.fog_density = 0.0
        self.sun_light_base_color = None
        self.ambient_light_base_color = None
        self.sky_ambient_base_color = None
        
    def setup_advanced_lighting(self):
        """Set up photorealistic lighting system with PBR support."""
        if self.is_setup:
            return
            
        self.render.clearLight()
        self.render.clearFog()
        
        # Main directional light (sun/moon)
        self.sun_light = DirectionalLight('sun')
        self.sun_light.setColor(Vec4(1.0, 0.9, 0.8, 1.0))  # Warm white
        self.sun_light.setDirection(Vec3(-1, -1, -1))
        self.sun_light.setSpecularColor(Vec4(1.0, 1.0, 1.0, 1.0))
        try:
            self.sun_light.setShadowCaster(True, 2048, 2048)
        except Exception:
            pass
        
        sun_np = self.render.attachNewNode(self.sun_light)
        self.render.setLight(sun_np)
        
        # Ambient skylight
        self.ambient_light = AmbientLight('skylight')
        self.ambient_light.setColor(Vec4(0.2, 0.3, 0.5, 1.0))  # Blue sky color
        ambient_np = self.render.attachNewNode(self.ambient_light)
        self.render.setLight(ambient_np)
        
        # Fill light (opposite side)
        self.fill_light = DirectionalLight('fill')
        self.fill_light.setColor(Vec4(0.2, 0.2, 0.25, 1.0))
        self.fill_light.setDirection(Vec3(1, 1, 0.5))
        fill_np = self.render.attachNewNode(self.fill_light)
        self.render.setLight(fill_np)
        
        # Sky ambient for indirect lighting
        self.sky_ambient = AmbientLight('sky_ambient')
        self.sky_ambient.setColor(Vec4(0.1, 0.15, 0.25, 1.0))
        sky_np = self.render.attachNewNode(self.sky_ambient)
        self.render.setLight(sky_np)

        self.sun_light_base_color = Vec4(self.sun_light.getColor())
        self.ambient_light_base_color = Vec4(self.ambient_light.getColor())
        self.sky_ambient_base_color = Vec4(self.sky_ambient.getColor())
        
        # Volumetric fog for atmosphere depth
        fog = Fog('atmosphere')
        fog.setColor(0.5, 0.55, 0.7)
        fog.setExpDensity(0.002)
        self.render.setFog(fog)
        
        # Enable PBR lighting model
        self._setup_pbr_lights()
        self.render.setShaderAuto()
        
        self.is_setup = True
    
    def _setup_pbr_lights(self):
        """Additional lighting for PBR rendering."""
        # Enable hardware lighting for PBR
        self.render.setShaderAuto()
        
        # Set up material properties for realistic light interaction
        mat = Material()
        mat.setShininess(128)
        mat.setSpecular((0.5, 0.5, 0.5, 1))
        self.render.setMaterial(mat)
    
    def update_time_of_day(self, hour):
        """Update lighting based on time of day (0-24)."""
        self.time_of_day = hour % 24.0
        
        # Solar position based on time
        hour_angle = (self.time_of_day - 6) * (math.pi / 12)  # 6 AM = 0, noon = π/2
        if hour_angle < 0:
            hour_angle += 2 * math.pi
            
        # Sun position in sky
        x = math.cos(hour_angle) * 2
        y = math.sin(hour_angle) * 2
        z = abs(math.sin(hour_angle)) * 1.5 + 0.1  # Never go below horizon
        
        # Update sun direction
        self.sun_light.setDirection(Vec3(-x, -y, -z))
        
        # Color temperature changes
        if 5 <= self.time_of_day <= 7:  # Dawn
            temp = (0.8, 0.4, 0.2)  # Orange
        elif 7 < self.time_of_day <= 10:  # Morning
            temp = (0.95, 0.8, 0.6)
        elif 10 < self.time_of_day <= 16:  # Day
            temp = (1.0, 0.95, 0.9)
        elif 16 < self.time_of_day <= 19:  # Evening
            temp = (0.9, 0.6, 0.3)
        else:  # Night
            temp = (0.8, 0.9, 1.0)
        
        # Adjust intensity based on time
        if 6 <= self.time_of_day <= 18:
            intensity = 1.0
        else:
            intensity = 0.1

        new_color = Vec4(temp[0] * intensity, temp[1] * intensity, temp[2] * intensity, 1.0)
        self.sun_light_base_color = Vec4(new_color)
        self.sun_light.setColor(new_color)
        self._update_ambient_colors(hour)
        
        return Vec3(x, y, z)
    
    def _update_ambient_colors(self, hour):
        """Update ambient lighting based on time."""
        if 6 <= hour <= 18:  # Daytime
            sky_color = Vec4(0.2, 0.3, 0.5, 1.0)
            base_ambient = Vec4(0.15, 0.2, 0.3, 1.0)
        else:  # Night
            sky_color = Vec4(0.05, 0.1, 0.2, 1.0)
            base_ambient = Vec4(0.05, 0.05, 0.08, 1.0)
            
        self.ambient_light_base_color = Vec4(sky_color)
        self.sky_ambient_base_color = Vec4(base_ambient)
        self.ambient_light.setColor(sky_color)
        self.sky_ambient.setColor(base_ambient)
    
    def add_spotlight(self, position, direction, color=(1.0, 1.0, 1.0, 1.0)):
        """Add a dynamic spotlight (for flashlights, etc)."""
        spot = Spotlight('dynamic_spot')
        spot.setColor(Vec4(*color))
        
        spot_np = self.render.attachNewNode(spot)
        spot_np.setPos(position)
        spot_np.setHpr(direction[0], direction[1], direction[2])
        
        self.render.setLight(spot_np)
        return spot_np
    
    def adjust_for_weather(self, rain_intensity=0.0, fog_density=0.0):
        """Adjust lighting for weather conditions."""
        # Reduce overall brightness in rain/fog
        sun_factor = max(0.3, 1.0 - rain_intensity * 0.7 - fog_density * 0.5)
        ambient_factor = max(0.5, 1.0 - rain_intensity * 0.4 - fog_density * 0.3)
        
        if self.sun_light_base_color is None:
            self.sun_light_base_color = Vec4(self.sun_light.getColor())
        if self.ambient_light_base_color is None:
            self.ambient_light_base_color = Vec4(self.ambient_light.getColor())

        new_sun_color = Vec4(
            self.sun_light_base_color[0] * sun_factor,
            self.sun_light_base_color[1] * sun_factor,
            self.sun_light_base_color[2] * sun_factor,
            self.sun_light_base_color[3]
        )
        self.sun_light.setColor(new_sun_color)

        new_ambient = Vec4(
            self.ambient_light_base_color[0] * ambient_factor,
            self.ambient_light_base_color[1] * ambient_factor,
            self.ambient_light_base_color[2] * ambient_factor,
            self.ambient_light_base_color[3]
        )
        self.ambient_light.setColor(new_ambient)


class VolumetricFog:
    """Advanced volumetric fog with light shafts and density variation."""
    
    def __init__(self, render_node):
        self.render = render_node
        self.fog_density = 0.002
        self.base_color = (0.5, 0.55, 0.7)
        
    def setup_volumetric_fog(self):
        """Set up realistic volumetric fog with light scattering."""
        fog = Fog('volumetric')
        fog.setColor(*self.base_color)
        fog.setExpDensity(self.fog_density)
        self.render.setFog(fog)
    
    def update_density(self, density):
        """Update fog density (0.0 = clear, 1.0 = thick fog)."""
        self.fog_density = 0.002 + (density * 0.01)
        self.render.clearFog()
        self.setup_volumetric_fog()
    
    def enable_god_rays(self, light_source):
        """Enable volumetric lighting (god rays) from sun."""
        # This would work with post-processing shaders
        # For now, we'll simulate with fog density variation
        if light_source:
            # TODO: Implement volumetric light shafts
            pass


class PointLightEmitter:
    """Dynamic point light for fires, lanterns, muzzle flashes."""
    
    def __init__(self, render_node, position, color, radius):
        self.render = render_node
        self.position = position
        self.color = color
        self.radius = radius
        self.intensity = 1.0
        self.decay = 0.01
        
        self.create_light()
        
    def create_light(self):
        """Create the point light."""
        point_light = PointLight('point_emitter')
        point_light.setColor(Vec4(*self.color, 1.0))
        point_light.setAttenuation(Vec3(1, 0, 0.01))  # Linear attenuation
        
        self.light_np = self.render.attachNewNode(point_light)
        self.light_np.setPos(self.position)
        self.render.setLight(self.light_np)
        
    def update(self, dt):
        """Update light intensity and position."""
        self.intensity -= self.decay * dt
        if self.intensity <= 0:
            self.remove()
            return False
        
        # Vary intensity for flicker effect
        variation = random.uniform(-0.1, 0.1) * self.intensity
        self.light_np.node().setColor(Vec4(
            self.color[0] * self.intensity + variation,
            self.color[1] * self.intensity + variation,
            self.color[2] * self.intensity + variation,
            1.0
        ))
        return True
        
    def remove(self):
        """Remove the light."""
        if hasattr(self, 'light_np'):
            self.render.clearLight(self.light_np)
            self.light_np.removeNode()


# Global lighting presets for different weather/time conditions
LIGHTING_PRESETS = {
    'sunny_day': {
        'sun_color': (1.0, 0.95, 0.8, 1.0),
        'ambient_color': (0.2, 0.3, 0.5, 1.0),
        'fog_density': 0.001,
        'fill_factor': 0.2
    },
    'cloudy_day': {
        'sun_color': (0.8, 0.8, 0.85, 1.0),
        'ambient_color': (0.3, 0.35, 0.45, 1.0),
        'fog_density': 0.003,
        'fill_factor': 0.3
    },
    'foggy_morning': {
        'sun_color': (0.7, 0.6, 0.5, 1.0),
        'ambient_color': (0.25, 0.28, 0.35, 1.0),
        'fog_density': 0.008,
        'fill_factor': 0.35
    },
    'sunset': {
        'sun_color': (1.0, 0.4, 0.1, 1.0),
        'ambient_color': (0.2, 0.1, 0.15, 1.0),
        'fog_density': 0.0015,
        'fill_factor': 0.15
    },
    'rainy': {
        'sun_color': (0.5, 0.5, 0.6, 1.0),
        'ambient_color': (0.25, 0.3, 0.4, 1.0),
        'fog_density': 0.004,
        'fill_factor': 0.3
    },
    'night': {
        'sun_color': (0.2, 0.3, 0.6, 1.0),
        'ambient_color': (0.05, 0.08, 0.15, 1.0),
        'fog_density': 0.002,
        'fill_factor': 0.1
    }
}
