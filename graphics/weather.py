"""
Dynamic weather system with precipitation particles, wind, and atmospheric effects.
"""

import random
import math
from panda3d.core import (
    Vec3, PointLight, NodePath, CardMaker,
    PTAFloat, VBase4, TransformState, LVector3, Fog, AmbientLight,
    TransparencyAttrib, GeomNode, Geom, GeomVertexFormat, GeomVertexData,
    GeomVertexWriter, GeomTriangles
)


class PrecipitationParticles:
    """Manages visible rain/snow particle billboards."""

    def __init__(self, render_node, weather_type='rain'):
        self.render = render_node
        self.weather_type = weather_type
        self.particle_node = None
        self.particles = []
        self._particle_count = 0
        self._spawn_radius = 40.0
        self._height_ceiling = 25.0
        self._fall_speed = 18.0 if weather_type == 'rain' else 3.5
        self._active = False

    def start(self, strength=1.0):
        if self._active:
            return
        self._active = True
        self._particle_count = int(800 * strength) if self.weather_type == 'rain' else int(300 * strength)
        self.particle_node = self.render.attachNewNode(f'precipitation_{self.weather_type}')
        self._spawn_particles()

    def _spawn_particles(self):
        cm = CardMaker('precip_card')
        if self.weather_type == 'rain':
            cm.setFrame(-0.03, 0.03, -0.4, 0.4)
        else:
            cm.setFrame(-0.15, 0.15, -0.15, 0.15)
        for _ in range(self._particle_count):
            card = self.particle_node.attachNewNode(cm.generate())
            card.setTransparency(TransparencyAttrib.MAlpha)
            card.setBillboardPointEye()
            card.setPos(
                random.uniform(-self._spawn_radius, self._spawn_radius),
                random.uniform(-self._spawn_radius, self._spawn_radius),
                random.uniform(0, self._height_ceiling)
            )
            if self.weather_type == 'rain':
                card.setColorScale(0.65, 0.72, 0.85, 0.55)
            else:
                card.setColorScale(0.95, 0.97, 1.0, 0.8)
                card.setScale(random.uniform(0.5, 1.8))
            card.setShaderAuto()
            self.particles.append(card)

    def update(self, dt, strength=1.0):
        if not self._active or not self.particle_node:
            return
        for p in self.particles:
            z = p.getZ() - self._fall_speed * strength * dt
            if z < -1.0:
                z = self._height_ceiling
                p.setX(random.uniform(-self._spawn_radius, self._spawn_radius))
                p.setY(random.uniform(-self._spawn_radius, self._spawn_radius))
            p.setZ(z)

    def stop(self):
        if self.particle_node:
            self.particle_node.removeNode()
            self.particle_node = None
        self.particles.clear()
        self._active = False


class WeatherSystem:
    """Manages dynamic weather conditions and effects."""

    def __init__(self, render_node):
        self.render = render_node
        self.current_weather = 'clear'
        self.weather_strength = 0.0
        self.wind_speed = 5.0
        self.wind_direction = Vec3(1, 0, 0)
        self.precipitation = None
        self._precip_particles = None
        self.fog_effect = None
        self.lightning_active = False
        self.thunder_active = False
        self.season = 'summer'
        self._owns_fog = False
        self._owns_ambient = False

        # Fog — only create if not already set by dynamic lighting
        self.fog = Fog('weather_fog')
        self.fog.setColor(1, 1, 1)
        self.fog.setMode(Fog.MExponential)

        # Ambient light — use a lower-priority approach that doesn't clear existing lights
        self.ambient_light = AmbientLight('weather_ambient')
        self.ambient_light.setColor(VBase4(1, 1, 1, 1))

        # Weather transition parameters
        self.transition_time = 0
        self.target_weather = 'clear'
        self.target_strength = 0.0

    def _ensure_weather_fog_and_light(self):
        """Lazily attach fog and ambient light so they don't conflict with DynamicLighting init."""
        if not self._owns_fog:
            try:
                self.render.setFog(self.fog)
                self._owns_fog = True
            except Exception:
                pass
        if not self._owns_ambient:
            try:
                self.light_np = self.render.attachNewNode(self.ambient_light)
                self.render.setLight(self.light_np)
                self._owns_ambient = True
            except Exception:
                pass

    def update_weather(self, dt):
        """Update weather conditions and visual effects."""
        self._ensure_weather_fog_and_light()

        # Gradual weather transitions
        if self.transition_time > 0:
            self.transition_time -= dt
            progress = 1.0 - (self.transition_time / 10.0)

            if self.transition_time <= 0:
                self.current_weather = self.target_weather
                self.weather_strength = self.target_strength
                self.transition_time = 0
            else:
                self.weather_strength = self.weather_strength * (1 - progress) + self.target_strength * progress

        # Update particle effects
        if self._precip_particles:
            self._precip_particles.update(dt, self.weather_strength)
        elif self.current_weather in ('rain', 'snow'):
            self.update_precipitation(dt)

        # Update fog effects for foggy weather
        if self.current_weather == 'fog':
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

        # Start/stop precipitation particles
        if weather_type in ('rain', 'storm') and strength > 0.3:
            if self._precip_particles is None or self._precip_particles.weather_type != 'rain':
                if self._precip_particles:
                    self._precip_particles.stop()
                self._precip_particles = PrecipitationParticles(self.render, 'rain')
                self._precip_particles.start(strength)
        elif weather_type == 'snow' and strength > 0.3:
            if self._precip_particles is None or self._precip_particles.weather_type != 'snow':
                if self._precip_particles:
                    self._precip_particles.stop()
                self._precip_particles = PrecipitationParticles(self.render, 'snow')
                self._precip_particles.start(strength)
        else:
            self._stop_precipitation()

        # Adjust fog
        if weather_type in ['fog', 'rain', 'snow'] and strength > 0.5:
            self._start_fog()
        else:
            self._stop_fog()

    def _start_rain(self):
        """Create rain particle effect."""
        strength = max(self.weather_strength, self.target_strength)
        self.fog.setExpDensity(0.01 * strength)
        self.fog.setColor(0.7, 0.8, 0.9)
        self.ambient_light.setColor(VBase4(0.5, 0.5, 0.5, 1))

    def _start_snow(self):
        """Create snow particle effect."""
        strength = max(self.weather_strength, self.target_strength)
        self.fog.setExpDensity(0.005 * strength)
        self.fog.setColor(0.9, 0.9, 0.95)
        self.ambient_light.setColor(VBase4(0.7, 0.7, 0.7, 1))

    def _stop_precipitation(self):
        """Remove precipitation effects."""
        if self._precip_particles:
            self._precip_particles.stop()
            self._precip_particles = None
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
            # Schedule delayed restoration via the render node's task chain
            try:
                from direct.task import Task
                if hasattr(self.render, 'getPythonTag'):
                    base_ref = self.render.getPythonTag('base_app')
                else:
                    base_ref = None
                if base_ref is None:
                    import __main__
                    base_ref = getattr(__main__, 'app', None)
                if base_ref and hasattr(base_ref, 'taskMgr'):
                    base_ref.taskMgr.doMethodLater(0.08, restore_light, 'restore_lightning')
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
        self.set_weather('rain', 1.0, 0.5)
        self.update(0)

    def stop_rain(self):
        """Stop rain weather effect."""
        self.set_weather('clear', 0.0, 0.5)
        self.update(0)

    def start_snow(self):
        """Start snow weather effect."""
        self.current_weather = 'snow'
        self.weather_strength = 1.0
        self.set_weather('snow', 1.0, 0.5)
        self.update(0)

    def stop_snow(self):
        """Stop snow weather effect."""
        self.set_weather('clear', 0.0, 0.5)
        self.update(0)

    def cleanup(self):
        """Clean up weather system resources."""
        if self._precip_particles:
            self._precip_particles.stop()
            self._precip_particles = None
        if self._owns_ambient and hasattr(self, 'light_np'):
            try:
                self.render.clearLight(self.light_np)
                self.light_np.removeNode()
            except Exception:
                pass
            self._owns_ambient = False
        self._owns_fog = False


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
