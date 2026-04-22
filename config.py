"""
Configuration file for the 3D Hunting Simulator.
Contains game settings that can be easily modified.
"""

# Terrain settings
TERRAIN_CONFIG = {
    'width': 300,          # Terrain width in units
    'height': 300,         # Terrain height in units
    'scale': 1.0,          # Scale factor for terrain
    'octaves': 5,          # Number of noise octaves
    'seed': 42             # Random seed for reproducible terrain
}

# Animal settings
ANIMAL_CONFIG = {
    'deer_count': 15,
    'rabbit_count': 20,
    'bear_count': 3,
    'wolf_count': 5,
    'bird_count': 12,
    'spawn_radius': 120,   # Larger spawn area for more exploration
    'deer': {
        'speed': 6.0,
        'detection_range': 60.0,
        'flee_range': 40.0,
        'size': 2.5
    },
    'rabbit': {
        'speed': 4.0,
        'detection_range': 30.0,
        'flee_range': 20.0,
        'size': 1.8
    },
    'bear': {
        'speed': 5.5,
        'detection_range': 70.0,
        'flee_range': 15.0,
        'size': 4.0
    },
    'wolf': {
        'speed': 8.0,
        'detection_range': 80.0,
        'flee_range': 25.0,
        'size': 2.2
    },
    'bird': {
        'speed': 12.0,
        'detection_range': 40.0,
        'flee_range': 20.0,
        'size': 0.8
    }
}

# Difficulty settings
DIFFICULTY_CONFIG = {
    'easy': {
        'animal_health_multiplier': 0.7,
        'animal_speed_multiplier': 0.7,
        'player_damage_multiplier': 1.5,
        'ammo_scarcity': 0.5,
        'predator_aggression': 0.3,
        'hunger_thirst_rate': 0.5,
        'score_multiplier': 0.8
    },
    'normal': {
        'animal_health_multiplier': 1.0,
        'animal_speed_multiplier': 1.0,
        'player_damage_multiplier': 1.0,
        'ammo_scarcity': 1.0,
        'predator_aggression': 0.6,
        'hunger_thirst_rate': 1.0,
        'score_multiplier': 1.0
    },
    'hard': {
        'animal_health_multiplier': 1.4,
        'animal_speed_multiplier': 1.2,
        'player_damage_multiplier': 0.7,
        'ammo_scarcity': 1.5,
        'predator_aggression': 1.0,
        'hunger_thirst_rate': 1.5,
        'score_multiplier': 1.5
    },
    'extreme': {
        'animal_health_multiplier': 2.0,
        'animal_speed_multiplier': 1.5,
        'player_damage_multiplier': 0.5,
        'ammo_scarcity': 2.0,
        'predator_aggression': 1.5,
        'hunger_thirst_rate': 2.0,
        'score_multiplier': 2.5
    }
}

# Save game settings
SAVE_CONFIG = {
    'save_file': 'savegame.json',
    'auto_save_interval': 300.0,  # Auto-save every 5 minutes
    'max_save_slots': 3
}

# Game settings
GAME_CONFIG = {
    'title': '3D Hunting Simulator',
    'window_size': (1200, 800),
    'fullscreen': False,
    'vsync': True,
    'antialiasing': True
}

# Graphics settings
GRAPHICS_CONFIG = {
    'texture_quality': 'high',
    'shadow_quality': 'medium',
    'draw_distance': 1000.0,
    'lod_distance': 500.0,
    'use_pbr': True,
    'use_bloom': True,
    'use_ssao': True,
    'use_motion_blur': False,
    'volumetric_fog': True,
    'dynamic_lighting': True,
    'dynamic_weather': True,
    'foliage_wind': True,
    'hdr_rendering': True,
    'fxaa': True,
    'texture_filtering': 'anisotropic',
    'debug_lights': False
}

# Advanced Graphics Settings for PBR, Lighting, and Effects
ADVANCED_GRAPHICS = {
    # PBR Material Settings
    'pbr_metallic_scale': 0.3,
    'pbr_roughness_scale': 0.4,
    'pbr_normal_scale': 1.0,
    
    # Atmospheric Settings
    'fog_density': 0.002,
    'fog_color': (0.5, 0.55, 0.7),
    'bloom_threshold': 1.0,
    'bloom_intensity': 1.2,
    
    # Time of Day Settings
    'time_cycle_enabled': True,
    'dawn_time': 6.0,     # 6 AM
    'dusk_time': 18.0,     # 6 PM
    'noon_time': 12.0,     # 12 PM
    
    # Weather Settings
    'rain_enabled': True,
    'snow_enabled': True,
    'fog_enabled': True,
    'wind_speed': 5.0,
    'wind_gustiness': 0.3,
    
    # Post Processing
    'ssao_enabled': True,
    'ssao_radius': 1.0,
    'ssao_intensity': 1.5,
    'motion_blur_enabled': False,
    'chromatic_aberration': 0.01,
    
    # Performance Settings
    'target_fps': 60,
    'lod_bias': 1.0,
    'texture_streaming': True,
    'occlusion_culling': True
}