"""
Dynamic weather system with precipitation, wind, and atmospheric effects.
"""

import random
from panda3d.core import (
    Vec3, PointLight, NodePath,
    PTAFloat, VBase4, TransformState, LVector3
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
        if self.precipitation:
            self._stop_precipitation()
            
        rain = ParticleSystem('rain', technique='sheet')
        rain.set_texture('assets/textures/rain.png')
        rain.set_lifespan(1.5)
        rain.set_rate(500 * self.weather_strength)
        rain.set_velocity(Vec3(0, 0, -20))  # Fast downward
        rain.set_size(0.1)
        rain.set_color(VBase4(0.8, 0.8, 1.0, 0.6))
        rain.create(self.render)
        self.precipitation = rain
        
    def _start_snow(self):
        """Create snow particle effect."""
        if self.precipitation:
            self._stop_precipitation()
            
        snow = ParticleSystem('snow', technique='point')
        snow.set_texture('assets/textures/snowflake.png')
        snow.set_lifespan(5.0)
        snow.set_rate(100 * self.weather_strength)
        snow.set_velocity(Vec3(
            self.wind_speed * 2, 
            self.wind_speed * random.uniform(-1, 1), 
            -5
        ))
        snow.set_size(0.3)
        snow.set_color(VBase4(0.9, 0.9, 1.0, 0.8))
        snow.create(self.render)
        self.precipitation = snow
    
    def update_precipitation(self, dt):
        """Update precipitation particles and wetness."""
        if self.precipitation:
            self.precipitation.update(dt)
            self.precipitation.set_rate(500 * self.weather_strength)
            
    def _stop_precipitation(self):
        """Remove precipitation effects."""
        if self.precipitation:
            self.precipitation.cleanup()
            self.precipitation = None
    
    def _start_fog(self):
        """Add fog layer for weather effects."""
        if not self.fog_effect:
            self.fog_effect = FogEmitter(self.render)
        
        self.fog_effect.set_density(0.002 + self.weather_strength * 0.003)
        self.fog_effect.start()
        
    def _stop_fog(self):
        """Remove fog effects."""
        if self.fog_effect:
            self.fog_effect.stop()
    
    def update_fog_effect(self, dt):
        """Update moving fog effects."""
        if self.fog_effect:
            self.fog_effect.update(dt, self.wind_direction, self.weather_strength)
    
    def _check_weather_events(self):
        """Random weather events like thunder/lightning."""
        if (self.current_weather == 'rain' and 
            self.weather_strength > 0.7 and 
            random.random() < 0.001):  # 0.1% chance per second
            self._trigger_lightning()
        
    def _trigger_lightning(self):
        """Create lightning flash effect."""
        # Quick bright light flash
        flash = PointLight('lightning')
        flash.setColor(VBase4(0.8, 0.9, 1.0, 1.0))
        
        flash_np = self.render.attachNewNode(flash)
        flash_np.setPos(Vec3(
            random.uniform(-100, 100),
            random.uniform(-100, 100), 
            50
        ))
        
        # Brief intense flash
        def light_callback(elapsed):
            if elapsed > 0.1:  # 100ms flash
                self.render.clearLight(flash_np)
                flash_np.removeNode()
                return False
            return True
            
        taskMgr.doMethodLater(0.1, lambda: None, 'lightning_flash')
        self.render.setLight(flash_np)
        
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


class ParticleSystem:
    """Placeholder for particle effects (Panda3D requires specific particle system setup)."""
    
    def __init__(self, name, technique='point'):
        self.name = name
        self.technique = technique
        self.node = None
        self.rate = 100
        self.lifespan = 1.0
        self.velocity = Vec3(0, 0, -10)
        self.size = 0.1
        self.color = VBase4(1, 1, 1, 1)
        
    def create(self, parent):
        """Initialize the particle system."""
        # Note: Simplified - full particle effects require proper Panda3D setup
        self.node = NodePath('particles-' + self.name)
        self.node.reparentTo(parent)
        print(f"Particle system {self.name} created (simplified)")
        
    def _configure_rain(self, effect):
        """Configure rain particle settings."""
        p0 = effect.getPartSystem().getPool().makePart()
        p0.factory.setLifespanBase(self.lifespan)
        p0.factory.setLifespanSpread(0.5)
        p0.renderer.setInitialXScale(self.size)
        p0.renderer.setFinalXScale(self.size)
        p0.emitter.setEmissionType(BaseParticleEmitter.ETRadiate)
        p0.emitter.setAmplitude(5.0)
        p0.emitter.setAmplitudeSpread(2.0)
        p0.emitter.setOffsetForce(Vec3(0, 0, -20))  # Fast down
        p0.renderer.setColor(self.color)
        p0.renderer.setAlphaDisable(False)
        
    def _configure_snow(self, effect):
        """Configure snow particle settings."""
        p0 = effect.getPartSystem().getPool().makePart()
        p0.factory.setLifespanBase(self.lifespan)
        p0.factory.setLifespanSpread(1.0)
        p0.renderer.setInitialXScale(self.size)
        p0.renderer.setFinalXScale(self.size * 1.5)
        p0.emitter.setEmissionType(BaseParticleEmitter.ETExplicit)
        p0.emitter.setAmplitude(self.wind_speed)
        p0.emitter.setAmplitudeSpread(1.0)
        p0.emitter.setExplicitLaunchVector(self.velocity)
        p0.emitter.setExplicitFinalVector(Vec3(0, 0, -2))
        p0.renderer.setColor(self.color)
        
    def update(self, dt):
        """Update particle position and physics."""
        self._emission_time += dt
        if self._emission_time >= 1.0 / self.rate:
            self._emit_particles()
            self._emission_time = 0
            
        # Apply wind
        if self.node and hasattr(self, 'effect'):
            wind_offset = self.wind_speed * dt
            self.node.setPos(Vec3(wind_offset, 0, 0))
            
    def _emit_particles(self):
        """Emit a burst of particles."""
        pass  # Handled by Panda3D system internally
        
    def cleanup(self):
        """Clean up particle system."""
        if self.node:
            self.node.removeNode()
            self.node = None


class FogEmitter:
    """Dynamic fog with movement and density variation."""
    
    def __init__(self, render_node):
        self.render = render_node
        self.density = 0.002
        self.base_color = (0.5, 0.55, 0.7)
        self.active = False
        self.fog_node = None
        
    def set_density(self, density):
        """Set fog density."""
        self.density = density
        
    def start(self):
        """Start fog effect."""
        if not self.active:
            fog = Fog('dynamic_fog')
            fog.setColor(*self.base_color)
            fog.setExpDensity(self.density)
            
            self.fog_node = self.render.attachNewNode('fog_node')
            self.fog_node.setFog(fog)
            self.active = True
            
    def stop(self):
        """Stop fog effect."""
        if self.fog_node:
            self.render.clearFog(self.fog_node)
            self.fog_node.removeNode()
            self.active = False
            
    def update(self, wind_vector, weather_strength):
        """Update fog movement and density."""
        if not self.active:
            return
            
        # Move fog with wind
        wind_speed = wind_vector.length()
        move_amount = wind_speed * 0.01
        current_pos = self.fog_node.getPos()
        self.fog_node.setPos(current_pos + wind_vector * move_amount)
        
        # Vary density
        variation = (random.random() - 0.5) * 0.1 * weather_strength
        current_fog = self.fog_node.getFog()
        current_fog.setExpDensity(self.density + variation)


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
