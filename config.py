"""
Configuration file for the 3D Hunting Simulator.
Contains game settings that can be easily modified.
"""

# Terrain settings
TERRAIN_CONFIG = {
    'width': 100,          # Terrain width in units
    'height': 100,         # Terrain height in units
    'scale': 1.0,          # Scale factor for terrain
    'octaves': 4,          # Number of noise octaves
    'seed': 42             # Random seed for reproducible terrain
}

# Animal settings
ANIMAL_CONFIG = {
    'deer_count': 5,       # Number of deer to spawn
    'rabbit_count': 8,     # Number of rabbits to spawn
    'spawn_radius': 40,    # Radius for animal spawning
    'deer': {
        'speed': 6.0,
        'detection_range': 60.0,
        'flee_range': 40.0,
        'size': 1.5
    },
    'rabbit': {
        'speed': 4.0,
        'detection_range': 30.0,
        'flee_range': 20.0,
        'size': 0.8
    }
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
    'lod_distance': 500.0
}