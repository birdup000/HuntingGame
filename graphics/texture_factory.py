import math
from typing import Sequence

import numpy as np
from panda3d.core import PNMImage, Texture


def _lerp(a: Sequence[float], b: Sequence[float], t: float) -> tuple:
    return tuple(a[i] * (1.0 - t) + b[i] * t for i in range(3))


def _hash_noise(x: int, y: int) -> float:
    return math.fmod(math.sin(x * 12.9898 + y * 78.233) * 43758.5453, 1.0)


def create_vertical_gradient_texture(size: int, top_color: Sequence[float], bottom_color: Sequence[float]) -> Texture:
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


def create_terrain_texture(height_map: np.ndarray) -> Texture:
    if height_map is None:
        raise ValueError("height_map must be provided")
    heights = np.array(height_map, copy=False)
    h, w = heights.shape
    minimum = float(np.min(heights))
    maximum = float(np.max(heights))
    scale = max(maximum - minimum, 1e-5)

    palette = [
        (0.25, (0.18, 0.28, 0.12), (0.22, 0.34, 0.15)),
        (0.45, (0.28, 0.2, 0.12), (0.34, 0.24, 0.15)),
        (0.7, (0.32, 0.32, 0.35), (0.45, 0.45, 0.48)),
        (1.01, (0.88, 0.9, 0.92), (0.97, 0.98, 1.0)),
    ]

    image = PNMImage(h, w, 4)
    for x in range(h):
        for y in range(w):
            normalized = (heights[x, y] - minimum) / scale
            prev_threshold = 0.0
            base_low = (0.12, 0.2, 0.08)
            base_high = (0.14, 0.24, 0.09)
            for threshold, low_color, high_color in palette:
                if normalized <= threshold:
                    span = threshold - prev_threshold
                    t = 0.0 if span <= 1e-5 else (normalized - prev_threshold) / span
                    base_low, base_high = low_color, high_color
                    color = _lerp(base_low, base_high, t)
                    break
                prev_threshold = threshold
            else:
                color = base_high

            detail = _hash_noise(x, y)
            color = tuple(max(0.0, min(1.0, c + (detail - 0.5) * 0.08)) for c in color)
            image.setXel(x, y, *color)
            image.setAlpha(x, y, 1.0)

    texture = Texture("terrain-detail")
    texture.load(image)
    texture.setWrapU(Texture.WMRepeat)
    texture.setWrapV(Texture.WMRepeat)
    texture.setMagfilter(Texture.FTLinear)
    texture.setMinfilter(Texture.FTLinearMipmapLinear)
    return texture


def create_leaf_texture(size: int = 128) -> Texture:
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


def create_bark_texture(size: int = 64) -> Texture:
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


def create_crosshair_texture(size: int = 192) -> Texture:
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


def create_sky_texture(size: int = 512) -> Texture:
    top = (0.15, 0.28, 0.52)
    horizon = (0.6, 0.65, 0.72)
    image = PNMImage(size, size, 4)
    sun_center = (size * 0.5, size * 0.3)
    sun_radius = size * 0.12

    for y in range(size):
        vertical = y / float(size - 1)
        base_color = _lerp(top, horizon, vertical)
        for x in range(size):
            dx = x - sun_center[0]
            dy = y - sun_center[1]
            dist = math.hypot(dx, dy)
            glow = max(0.0, 1.0 - dist / sun_radius)
            glow = glow ** 2.5
            color = tuple(min(1.0, c + glow * 0.35) for c in base_color)
            image.setXel(x, y, *color)
            image.setAlpha(x, y, 1.0)

    texture = Texture("sky-gradient")
    texture.load(image)
    texture.setWrapU(Texture.WMClamp)
    texture.setWrapV(Texture.WMClamp)
    texture.setMagfilter(Texture.FTLinear)
    texture.setMinfilter(Texture.FTLinear)
    return texture
