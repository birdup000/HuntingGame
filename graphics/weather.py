"""
Dynamic weather system with precipitation, wind, and atmospheric effects.
"""

import random
from panda3d.core import (
    Vec3, PointLight, NodePath,
    PTAFloat, VBase4, TransformState, LVector3, Fog, AmbientLight
)


class WeatherSystem:
    """Manages dynamic weather conditions and effects."""
    
    def __init__(self, render_node):
        self.render = render_node
        self.current_weather = 'clear'
        self.weather_strength = 0.0
        self.wind_speed = 5.0
        self.wind_direction = Vec3(1, 0, 0)
        self.precipitation = None
        self.fog_effect = None
        self.lightning_active = False
        self.thunder_active = False
        self.season = 'summer'

        # Initialize fog and lighting
        self.fog = Fog('weather_fog')
        self.fog.setColor(1, 1, 1)
        self.fog.setMode(Fog.MExponential)
        self.render.setFog(self.fog)

        self.ambient_light = AmbientLight('weather_ambient')
        self.ambient_light.setColor(VBase4(1, 1, 1, 1))
        self.light_np = self.render.attachNewNode(self.ambient_light)
        self.render.setLight(self.light_np)

        # Weather transition parameters
        self.transition_time = 0
        self.target_weather = 'clear'
        self.target_strength = 0.0
        
    def update_weather(self, dt):
        """Update weather conditions and visual effects."""
        # Gradual weather transitions
        if self.transition_time > 0:
            self.transition_time -= dt
            progress = 1.0 - (self.transition_time / 10.0)  # 10 second transitions
            
            if self.transition_time <= 0:
                self.current_weather = self.target_weather
                self.weather_strength = self.target_strength
                self.transition_time = 0
            else:
                # Blend between weather states
                self.weather_strength = self.weather_strength * (1 - progress) + self.target_strength * progress
        
        # Update particle effects
        if self.precipitation:
            self.update_precipitation(dt)
        if self.fog_effect:
            self.update_fog_effect(dt)
        
        # Random weather events
        self._check_weather_events()

        # Update visual effects
        self.update(dt)
        
    def set_weather(self, weather_type, strength=0.0, transition_time=10.0):
        """Change weather with smooth transition."""
        self.target_weather = weather_type
        self.target_strength = strength
        self.transition_time = transition_time
        
        # Start/stop precipitation
        if weather_type == 'rain' and strength > 0.3:
            self._start_rain()
        elif weather_type == 'snow' and strength > 0.3:
            self._start_snow()
        else:
            self._stop_precipitation()
            
        # Adjust fog
        if weather_type in ['fog', 'rain', 'snow'] and strength > 0.5:
            self._start_fog()
        else:
            self._stop_fog()
    
    def _start_rain(self):
        """Create rain particle effect."""
        self.fog.setExpDensity(0.01)
        self.fog.setColor(0.7, 0.8, 0.9)
        self.ambient_light.setColor(VBase4(0.5, 0.5, 0.5, 1))
        
    def _start_snow(self):
        """Create snow particle effect."""
        self.fog.setExpDensity(0.005)
        self.fog.setColor(0.9, 0.9, 0.95)
        self.ambient_light.setColor(VBase4(0.7, 0.7, 0.7, 1))
    
    def update_precipitation(self, dt):
        """Update precipitation particles and wetness."""
        if self.precipitation:
            if self.current_weather == 'rain':
                density = 0.01 * self.weather_strength
                self.fog.setExpDensity(density)
            elif self.current_weather == 'snow':
                density = 0.005 * self.weather_strength
                self.fog.setExpDensity(density)
            
    def _stop_precipitation(self):
        """Remove precipitation effects."""
        self.fog.setExpDensity(0.0)
        self.fog.setColor(1, 1, 1)
        self.ambient_light.setColor(VBase4(1, 1, 1, 1))
    
    def _start_fog(self):
        """Add fog layer for weather effects."""
        self.fog.setExpDensity(0.02)
        self.fog.setColor(0.8, 0.8, 0.8)
        self.ambient_light.setColor(VBase4(0.6, 0.6, 0.6, 1))
        
    def _stop_fog(self):
        """Remove fog effects."""
        self.fog.setExpDensity(0.0)
        self.fog.setColor(1, 1, 1)
        self.ambient_light.setColor(VBase4(1, 1, 1, 1))
    
    def update_fog_effect(self, dt):
        """Update moving fog effects."""
        if self.fog_effect:
            if self.current_weather == 'fog':
                density = 0.02 * self.weather_strength
                self.fog.setExpDensity(density)
    
    def _check_weather_events(self):
        """Random weather events like thunder/lightning."""
        # Lightning events during storms
        if self.current_weather == 'storm' and random.random() < 0.002:
            self._trigger_lightning()
        
    def _trigger_lightning(self):
        """Create lightning flash effect."""
        # Flash ambient light bright white briefly
        if hasattr(self, 'ambient_light'):
            original = self.ambient_light.getColor()
            self.ambient_light.setColor(VBase4(2.0, 2.0, 2.5, 1.0))
            # Restore after brief flash
            from direct.task import Task
            def restore_light(task):
                self.ambient_light.setColor(original)
                return task.done
            # Use doMethodLater via taskMgr if available on render
            try:
                from direct.task import TaskManager
                import builtins
                base = builtins.get('base', None)
                if base and hasattr(base, 'taskMgr'):
                    base.taskMgr.doMethodLater(0.08, restore_light, 'restore_lightning')
            except Exception:
                pass
        
    def get_wetness_factor(self):
        """Return wetness for material dampening."""
        if self.current_weather == 'rain':
            return self.weather_strength * 0.8
        elif self.current_weather == 'fog':
            return self.weather_strength * 0.3
        return 0.0
        
    def get_wind_vector(self):
        """Get current wind direction and speed."""
        return self.wind_direction * self.wind_speed
    
    def get_puddles(self):
        """Calculate potential for puddle formation."""
        if self.current_weather == 'rain':
            return self.weather_strength * 0.7
        return 0.0

    def update(self, dt):
        """Update weather effects based on current state."""
        if self.current_weather == 'rain':
            density = 0.01 * self.weather_strength
            color = VBase4(1 - 0.3 * self.weather_strength, 1 - 0.2 * self.weather_strength, 1 - 0.1 * self.weather_strength, 1)
            light_factor = 1.0 - 0.5 * self.weather_strength
        elif self.current_weather == 'snow':
            density = 0.005 * self.weather_strength
            color = VBase4(1 - 0.1 * self.weather_strength, 1 - 0.1 * self.weather_strength, 1 - 0.05 * self.weather_strength, 1)
            light_factor = 1.0 - 0.3 * self.weather_strength
        else:
            density = 0.0
            color = VBase4(1, 1, 1, 1)
            light_factor = 1.0

        self.fog.setExpDensity(density)
        self.fog.setColor(color)
        self.ambient_light.setColor(VBase4(light_factor, light_factor, light_factor, 1))

    def start_rain(self):
        """Start rain weather effect."""
        self.current_weather = 'rain'
        self.weather_strength = 1.0
        self.update(0)

    def stop_rain(self):
        """Stop rain weather effect."""
        self.current_weather = 'clear'
        self.weather_strength = 0.0
        self.update(0)

    def start_snow(self):
        """Start snow weather effect."""
        self.current_weather = 'snow'
        self.weather_strength = 1.0
        self.update(0)

    def stop_snow(self):
        """Stop snow weather effect."""
        self.current_weather = 'clear'
        self.weather_strength = 0.0
        self.update(0)


# Weather presets
WEATHER_PRESETS = {
    'clear': {'visibility': 1000, 'temperature': 25, 'precipitation': 0},
    'partly_cloudy': {'visibility': 800, 'temperature': 22, 'precipitation': 0.1},
    'overcast': {'visibility': 500, 'temperature': 18, 'precipitation': 0.2},
    'fog': {'visibility': 200, 'temperature': 15, 'precipitation': 0.3},
    'rain': {'visibility': 300, 'temperature': 14, 'precipitation': 0.8},
    'snow': {'visibility': 250, 'temperature': 5, 'precipitation': 0.7},
    'storm': {'visibility': 150, 'temperature': 12, 'precipitation': 0.9}
}

# Ensure WeatherPresets is defined
WeatherPresets = WEATHER_PRESETS

# Backwards-compatible alias for tests and external modules
PRESETS = WEATHER_PRESETS
