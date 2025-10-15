import math
from typing import Callable, Dict, Sequence

import numpy as np
from panda3d.core import PNMImage, Texture


_TEXTURE_CACHE: Dict[str, Texture] = {}


def _cache_texture(key: str, builder: Callable[[], Texture]) -> Texture:
    texture = _TEXTURE_CACHE.get(key)
    if texture is None:
        texture = builder()
        _TEXTURE_CACHE[key] = texture
    return texture


def _lerp(a: Sequence[float], b: Sequence[float], t: float) -> tuple:
    return tuple(a[i] * (1.0 - t) + b[i] * t for i in range(3))


def _hash_noise(x: int, y: int) -> float:
    return math.fmod(math.sin(x * 12.9898 + y * 78.233) * 43758.5453, 1.0)


def _perlin_like_noise(x: float, y: float, frequency: float = 1.0) -> float:
    """Generate smoother Perlin-like noise for natural variation."""
    x *= frequency
    y *= frequency
    x0 = int(math.floor(x))
    x1 = x0 + 1
    y0 = int(math.floor(y))
    y1 = y0 + 1
    
    # Interpolation weights
    sx = x - x0
    sy = y - y0
    
    # Smoothstep for better interpolation
    sx = sx * sx * (3.0 - 2.0 * sx)
    sy = sy * sy * (3.0 - 2.0 * sy)
    
    # Hash corners
    n0 = _hash_noise(x0, y0)
    n1 = _hash_noise(x1, y0)
    n2 = _hash_noise(x0, y1)
    n3 = _hash_noise(x1, y1)
    
    # Bilinear interpolation
    nx0 = n0 * (1 - sx) + n1 * sx
    nx1 = n2 * (1 - sx) + n3 * sx
    
    return nx0 * (1 - sy) + nx1 * sy


def create_vertical_gradient_texture(size: int, top_color: Sequence[float], bottom_color: Sequence[float]) -> Texture:
    cache_key = f"vertical-gradient-{size}-{top_color}-{bottom_color}"

    def builder() -> Texture:
        image = PNMImage(size, size, 4)
        for y in range(size):
            t = y / float(size - 1)
            r, g, b = _lerp(top_color, bottom_color, t)
            for x in range(size):
                image.setXel(x, y, r, g, b)
                image.setAlpha(x, y, 1.0)
        texture = Texture("vertical-gradient")
        texture.load(image)
        texture.setWrapU(Texture.WMClamp)
        texture.setWrapV(Texture.WMClamp)
        texture.setMagfilter(Texture.FTLinear)
        texture.setMinfilter(Texture.FTLinear)
        return texture

    return _cache_texture(cache_key, builder)


def create_terrain_texture(height_map: np.ndarray) -> Texture:
    if height_map is None:
        raise ValueError("height_map must be provided")

    h, w = height_map.shape

    image = PNMImage(h, w, 4)

    # Normalize height map
    min_h = np.min(height_map)
    max_h = np.max(height_map)
    if max_h == min_h:
        normalized_height = np.full_like(height_map, 0.5)
    else:
        normalized_height = (height_map - min_h) / (max_h - min_h)

    for x in range(h):
        for y in range(w):
            height = normalized_height[x, y]

            # Define terrain colors based on height
            if height < 0.3:
                # Low areas: greens
                base_color = (0.2, 0.4, 0.1)
            elif height < 0.7:
                # Mid areas: browns
                base_color = (0.4, 0.3, 0.2)
            else:
                # High areas: grays
                base_color = (0.5, 0.5, 0.5)

            # Add Perlin noise for variation
            noise_val = _perlin_like_noise(x / 32.0, y / 32.0, 1.0) * 0.1

            # Apply the noise to the base color
            color = tuple(max(0.0, min(1.0, c + noise_val)) for c in base_color)

            image.setXel(x, y, *color)
            image.setAlpha(x, y, 1.0)

    texture = Texture("terrain-texture")
    texture.load(image)
    texture.setWrapU(Texture.WMRepeat)
    texture.setWrapV(Texture.WMRepeat)
    texture.setMagfilter(Texture.FTLinear)
    texture.setMinfilter(Texture.FTLinearMipmapLinear)
    return texture


def create_leaf_texture(size: int = 128) -> Texture:
    cache_key = f"leaf-{size}"

    def builder() -> Texture:
        image = PNMImage(size, size, 4)
        center = size / 2.0
        radius = size * 0.45
        for x in range(size):
            for y in range(size):
                dx = x - center
                dy = y - center
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > radius:
                    image.setAlpha(x, y, 0.0)
                    continue
                t = dist / radius
                base = (0.08, 0.32, 0.05)
                edge = (0.12, 0.38, 0.08)
                color = _lerp(base, edge, t)
                noise = _hash_noise(x, y) - 0.5
                color = tuple(max(0.0, min(1.0, c + noise * 0.06)) for c in color)
                image.setXel(x, y, *color)
                image.setAlpha(x, y, 1.0)

        texture = Texture("leaf-texture")
        texture.load(image)
        texture.setWrapU(Texture.WMMirror)
        texture.setWrapV(Texture.WMMirror)
        texture.setMagfilter(Texture.FTLinear)
        texture.setMinfilter(Texture.FTLinearMipmapLinear)
        return texture

    return _cache_texture(cache_key, builder)


def create_flower_patch_texture(size: int = 128) -> Texture:
    cache_key = f"flower-patch-{size}"

    def builder() -> Texture:
        image = PNMImage(size, size, 4)
        center = size / 2.0
        radius = size * 0.48

        petal_palette = [
            (0.94, 0.82, 0.28),
            (0.93, 0.68, 0.74),
            (0.88, 0.9, 0.95),
            (0.78, 0.86, 0.4),
        ]

        for x in range(size):
            for y in range(size):
                dx = x - center
                dy = y - center
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > radius:
                    image.setAlpha(x, y, 0.0)
                    continue

                falloff = 1.0 - (dist / radius)
                base = 0.18 + falloff * 0.22
                noise = (_hash_noise(x, y) - 0.5) * 0.05
                r = max(0.0, min(1.0, base * 0.6 + noise))
                g = max(0.0, min(1.0, 0.3 + base * 0.8 + noise * 1.2))
                b = max(0.0, min(1.0, base * 0.45 + noise * 0.6))
                image.setXel(x, y, r, g, b)
                alpha = 0.75 + falloff * 0.2
                image.setAlpha(x, y, max(0.0, min(1.0, alpha)))

        for x in range(size):
            for y in range(size):
                dx = x - center
                dy = y - center
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > radius * 0.96:
                    continue
                highlight = _hash_noise(x + size, y - size)
                if highlight > 0.87:
                    petals = petal_palette[int(highlight * len(petal_palette)) % len(petal_palette)]
                    image.setXel(x, y, *petals)
                    image.setAlpha(x, y, 0.98)

        texture = Texture("flower-patch")
        texture.load(image)
        texture.setWrapU(Texture.WMClamp)
        texture.setWrapV(Texture.WMClamp)
        texture.setMagfilter(Texture.FTLinear)
        texture.setMinfilter(Texture.FTLinearMipmapLinear)
        return texture

    return _cache_texture(cache_key, builder)


def create_bark_texture(size: int = 64) -> Texture:
    cache_key = f"bark-{size}"

    def builder() -> Texture:
        image = PNMImage(size, size, 4)
        for x in range(size):
            stripe = 0.5 + 0.5 * math.sin(x * 0.35)
            for y in range(size):
                grain = (math.sin((y + x) * 0.18) + 1.0) * 0.5
                base = (0.24, 0.17, 0.1)
                highlight = (0.34, 0.25, 0.16)
                t = min(1.0, max(0.0, stripe * 0.6 + grain * 0.4))
                color = _lerp(base, highlight, t)
                image.setXel(x, y, *color)
                image.setAlpha(x, y, 1.0)

        texture = Texture("bark-texture")
        texture.load(image)
        texture.setWrapU(Texture.WMRepeat)
        texture.setWrapV(Texture.WMRepeat)
        texture.setMagfilter(Texture.FTLinear)
        texture.setMinfilter(Texture.FTLinearMipmapLinear)
        return texture

    return _cache_texture(cache_key, builder)


def create_grass_texture(size: int = 128) -> Texture:
    cache_key = f"grass-{size}"

    def builder() -> Texture:
        image = PNMImage(size, size, 4)
        center = size / 2.0
        radius = size * 0.45
        for x in range(size):
            for y in range(size):
                dx = x - center
                dy = y - center
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > radius:
                    image.setAlpha(x, y, 0.0)
                    continue
                t = dist / radius
                base = (0.08, 0.32, 0.05)
                edge = (0.12, 0.38, 0.08)
                color = _lerp(base, edge, t)
                noise = _hash_noise(x, y) - 0.5
                color = tuple(max(0.0, min(1.0, c + noise * 0.06)) for c in color)
                image.setXel(x, y, *color)
                alpha = 0.7 + (1.0 - t) * 0.3  # Fade edges
                image.setAlpha(x, y, alpha)

        texture = Texture("grass-texture")
        texture.load(image)
        texture.setWrapU(Texture.WMMirror)
        texture.setWrapV(Texture.WMMirror)
        texture.setMagfilter(Texture.FTLinear)
        texture.setMinfilter(Texture.FTLinearMipmapLinear)
        return texture

    return _cache_texture(cache_key, builder)


def create_crosshair_texture(size: int = 192) -> Texture:
    cache_key = f"crosshair-{size}"

    def builder() -> Texture:
        image = PNMImage(size, size, 4)
        center = size / 2.0
        ring_radius = size * 0.32
        ring_thickness = size * 0.02
        gap = size * 0.06
        line_thickness = max(1.0, size * 0.01)

        for x in range(size):
            for y in range(size):
                dx = x - center
                dy = y - center
                dist = math.hypot(dx, dy)
                alpha = 0.0
                if abs(dist - ring_radius) <= ring_thickness:
                    alpha = 1.0
                elif abs(dx) <= line_thickness and gap < abs(dy) <= ring_radius:
                    alpha = 1.0
                elif abs(dy) <= line_thickness and gap < abs(dx) <= ring_radius:
                    alpha = 1.0
                elif dist <= line_thickness * 1.5:
                    alpha = 1.0

                if alpha > 0.0:
                    image.setXel(x, y, 0.95, 0.95, 0.95)
                    image.setAlpha(x, y, alpha)
                else:
                    image.setAlpha(x, y, 0.0)

        texture = Texture("modern-crosshair")
        texture.load(image)
        texture.setWrapU(Texture.WMClamp)
        texture.setWrapV(Texture.WMClamp)
        texture.setMagfilter(Texture.FTLinear)
        texture.setMinfilter(Texture.FTLinear)
        return texture

    return _cache_texture(cache_key, builder)


def create_sky_texture(size: int = 512) -> Texture:
    cache_key = f"sky-{size}"

    def builder() -> Texture:
        # Define sky colors
        top_color = (0.35, 0.55, 0.85)  # Sky blue
        horizon_color = (0.65, 0.75, 0.85)  # Lighter horizon

        image = PNMImage(size, size, 4)

        # Create sky gradient
        for y in range(size):
            vertical_t = y / float(size - 1)
            base_color = _lerp(top_color, horizon_color, vertical_t)
            for x in range(size):
                image.setXel(x, y, *base_color)
                image.setAlpha(x, y, 1.0)

        # Add clouds using Perlin noise
        cloud_color = (1.0, 1.0, 1.0)
        cloud_coverage = 0.45  # 45% coverage

        for y in range(size):
            for x in range(size):
                # Multi-layered Perlin noise for realistic clouds
                noise1 = _perlin_like_noise(x / (size / 4), y / (size / 4), 0.5)
                noise2 = _perlin_like_noise(x / (size / 8), y / (size / 8), 1.0) * 0.5
                noise3 = _perlin_like_noise(x / (size / 16), y / (size / 16), 2.0) * 0.25

                noise_val = (noise1 + noise2 + noise3) / 1.75

                # Apply cloud coverage
                if noise_val > (1.0 - cloud_coverage):
                    # Feather the cloud edges
                    cloud_intensity = (noise_val - (1.0 - cloud_coverage)) / cloud_coverage
                    cloud_intensity = min(1.0, cloud_intensity * 1.5) # Sharpen the edges a bit

                    # Get current pixel color
                    current_color = image.getXel(x, y)

                    # Blend sky color with cloud color
                    final_color = _lerp(current_color, cloud_color, cloud_intensity)

                    image.setXel(x, y, *final_color)

        texture = Texture("sky-with-clouds")
        texture.load(image)
        texture.setWrapU(Texture.WMClamp)
        texture.setWrapV(Texture.WMClamp)
        texture.setMagfilter(Texture.FTLinear)
        texture.setMinfilter(Texture.FTLinear)
        return texture

    return _cache_texture(cache_key, builder)


def get_ui_panel_texture(size: int = 256) -> Texture:
    cache_key = f"ui-panel-{size}"

    def builder() -> Texture:
        image = PNMImage(size, size, 4)
        for y in range(size):
            vertical = y / float(size - 1)
            base = _lerp((0.06, 0.08, 0.12), (0.02, 0.03, 0.05), vertical)
            for x in range(size):
                horizon = x / float(size - 1)
                highlight = _lerp((0.18, 0.26, 0.33), base, horizon * 0.6)
                noise = (_hash_noise(x, y) - 0.5) * 0.05
                color = tuple(max(0.0, min(1.0, c + noise)) for c in highlight)
                image.setXel(x, y, *color)
                alpha = 0.92 if 0.1 < vertical < 0.9 else 0.78
                image.setAlpha(x, y, alpha)
        texture = Texture("ui-panel")
        texture.load(image)
        texture.setWrapU(Texture.WMClamp)
        texture.setWrapV(Texture.WMClamp)
        texture.setMagfilter(Texture.FTLinear)
        texture.setMinfilter(Texture.FTLinear)
        return texture

    return _cache_texture(cache_key, builder)


def create_icon_texture(kind: str, size: int = 128) -> Texture:
    kind = kind.lower()
    cache_key = f"icon-{kind}-{size}"

    def builder() -> Texture:
        image = PNMImage(size, size, 4)
        for x in range(size):
            for y in range(size):
                image.setXel(x, y, 0, 0, 0)
                image.setAlpha(x, y, 0.0)
        center = size / 2.0
        thickness = max(1, int(size * 0.06))

        def draw_dot(cx, cy, radius, color):
            for x in range(size):
                for y in range(size):
                    dx = x - cx
                    dy = y - cy
                    if dx * dx + dy * dy <= radius * radius:
                        image.setXel(x, y, *color)
                        image.setAlpha(x, y, 1.0)

        def draw_line(x0, y0, x1, y1, color):
            steps = int(max(abs(x1 - x0), abs(y1 - y0)))
            for i in range(steps + 1):
                t = i / float(max(steps, 1))
                x = int(round(x0 + (x1 - x0) * t))
                y = int(round(y0 + (y1 - y0) * t))
                for dx in range(-thickness, thickness + 1):
                    for dy in range(-thickness, thickness + 1):
                        px = x + dx
                        py = y + dy
                        if 0 <= px < size and 0 <= py < size:
                            image.setXel(px, py, *color)
                            image.setAlpha(px, py, 1.0)

        accent = (0.94, 0.82, 0.42)
        base = (0.78, 0.88, 0.95)

        if kind == 'health':
            draw_line(center - size * 0.28, center, center + size * 0.28, center, accent)
            draw_line(center, center - size * 0.28, center, center + size * 0.28, accent)
        elif kind == 'ammo':
            for i in range(4):
                x = int(center - size * 0.25 + i * size * 0.16)
                draw_line(x, center - size * 0.22, x, center + size * 0.22, base)
        elif kind == 'accuracy':
            radius_outer = size * 0.32
            radius_inner = size * 0.06
            for x in range(size):
                for y in range(size):
                    dx = x - center
                    dy = y - center
                    dist = math.sqrt(dx * dx + dy * dy)
                    if abs(dist - radius_outer) <= thickness * 0.7 or dist <= radius_inner:
                        image.setXel(x, y, *base)
                        image.setAlpha(x, y, 1.0)
        else:  # score or default icon
            draw_dot(center, center, size * 0.18, accent)
            draw_dot(center, center, size * 0.1, base)

        texture = Texture(f"icon-{kind}")
        texture.load(image)
        texture.setWrapU(Texture.WMClamp)
        texture.setWrapV(Texture.WMClamp)
        texture.setMagfilter(Texture.FTLinear)
        texture.setMinfilter(Texture.FTLinear)
        return texture

    return _cache_texture(cache_key, builder)


def create_track_texture(size: int = 64) -> Texture:
    cache_key = f"track-{size}"

    def builder() -> Texture:
        image = PNMImage(size, size, 4)
        center = size / 2.0
        for x in range(size):
            for y in range(size):
                dx = (x - center) / center
                dy = (y - center) / center
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 1.0:
                    image.setAlpha(x, y, 0.0)
                    continue
                depth = (1.0 - dist) ** 2
                color = 0.25 + depth * 0.45
                image.setXel(x, y, color, color * 0.75, 0.28)
                image.setAlpha(x, y, min(1.0, depth * 2.5))

        texture = Texture("wildlife-track")
        texture.load(image)
        texture.setWrapU(Texture.WMClamp)
        texture.setWrapV(Texture.WMClamp)
        texture.setMagfilter(Texture.FTLinear)
        texture.setMinfilter(Texture.FTLinear)
        return texture

    return _cache_texture(cache_key, builder)


def create_water_texture(size: int = 256) -> Texture:
    cache_key = f"water-{size}"

    def builder() -> Texture:
        image = PNMImage(size, size, 4)
        center = size / 2.0
        for x in range(size):
            for y in range(size):
                dx = (x - center) / center
                dy = (y - center) / center
                r = math.sqrt(dx * dx + dy * dy)
                if r > 1.0:
                    image.setAlpha(x, y, 0.0)
                    continue
                base = _lerp((0.08, 0.21, 0.32), (0.12, 0.35, 0.48), r)
                ripple = math.sin(r * 14.0) * 0.03 + (_hash_noise(x, y) - 0.5) * 0.02
                color = tuple(max(0.0, min(1.0, c + ripple)) for c in base)
                image.setXel(x, y, *color)
                alpha = max(0.25, 1.0 - r * 0.7)
                image.setAlpha(x, y, alpha)

        texture = Texture("water-surface")
        texture.load(image)
        texture.setWrapU(Texture.WMClamp)
        texture.setWrapV(Texture.WMClamp)
        texture.setMagfilter(Texture.FTLinear)
        texture.setMinfilter(Texture.FTLinearMipmapLinear)
        return texture

    return _cache_texture(cache_key, builder)
