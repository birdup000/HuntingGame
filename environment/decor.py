from __future__ import annotations

import random
from typing import List

from panda3d.core import CardMaker, NodePath, TransparencyAttrib, Vec3, getModelPath

from graphics.texture_factory import (
    create_bark_texture,
    create_leaf_texture,
    create_water_texture,
    create_flower_patch_texture,
)


class DecorManager:
    """Places natural props such as ponds, logs, and shrubs to add variety."""

    def __init__(self, app, terrain):
        self.app = app
        self.render = app.render
        self.terrain = terrain
        self.decor_nodes: List[NodePath] = []

    def populate(self):
        self._add_water_features()
        self._add_fallen_logs()
        self._add_shrubs()
        self._add_flower_meadows()

    def cleanup(self):
        for node in self.decor_nodes:
            if node:
                node.removeNode()
        self.decor_nodes.clear()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _register(self, node: NodePath) -> NodePath:
        self.decor_nodes.append(node)
        return node

    def _terrain_height(self, x: float, y: float) -> float:
        if self.terrain:
            return float(self.terrain.get_height(x, y))
        return 0.0

    def _add_water_features(self):
        if not self.render:
            return

        water_texture = create_water_texture()
        cm = CardMaker('pond')
        cm.setFrame(-1, 1, -1, 1)

        pond_positions = [Vec3(18, 28, 0), Vec3(-24, -18, 0)]
        for pos in pond_positions:
            node = self.render.attachNewNode(cm.generate())
            node.setTransparency(TransparencyAttrib.MAlpha)
            node.setTexture(water_texture, 1)
            node.setScale(6.5)
            node.setP(-90)  # Lay flat on the ground
            node.setPos(pos.x, pos.y, self._terrain_height(pos.x, pos.y) + 0.02)
            node.setColorScale(1, 1, 1, 0.8)
            node.setShaderAuto()
            self._register(node)

    def _add_fallen_logs(self):
        if not self.render:
            return

        bark_tex = create_bark_texture()
        base_model = None
        if getModelPath().findFile('models/misc/cylinder.egg'):
            try:
                base_model = self.app.loader.loadModel('models/misc/cylinder')
            except Exception:
                base_model = None

        log_positions = [
            (Vec3(12, -8, 0), 4.5, 25),
            (Vec3(-15, 22, 0), 3.2, -18)
        ]

        for pos, length, heading in log_positions:
            z = self._terrain_height(pos.x, pos.y)
            if base_model:
                log = base_model.copyTo(self.render)
            else:
                cm = CardMaker('log')
                cm.setFrame(-0.5, 0.5, -0.5, 0.5)
                log = self.render.attachNewNode(cm.generate())
                log.setP(-90)
            log.setPos(pos.x, pos.y, z + 0.1)
            log.setH(heading)
            log.setScale(0.4, length, 0.4)
            log.setTexture(bark_tex, 1)
            log.setColorScale(0.8, 0.72, 0.6, 1.0)
            log.setShaderAuto()
            log.setTransparency(TransparencyAttrib.MNone)
            self._register(log)

    def _add_shrubs(self):
        if not self.render:
            return

        leaf_tex = create_leaf_texture(96)
        cm = CardMaker('shrub')
        cm.setFrame(-0.8, 0.8, -0.8, 0.8)

        random.seed(42)
        for _ in range(16):
            offset_x = random.uniform(-35, 35)
            offset_y = random.uniform(-35, 35)
            z = self._terrain_height(offset_x, offset_y)
            shrub = self.render.attachNewNode('shrub')
            for heading in (0, 60, 120):
                card = shrub.attachNewNode(cm.generate())
                card.setTexture(leaf_tex, 1)
                card.setTransparency(TransparencyAttrib.MAlpha)
                card.setH(heading)
                card.setBillboardPointEye()
            shrub.setPos(offset_x, offset_y, z + 0.1)
            shrub.setScale(random.uniform(1.0, 1.6))
            shrub.setColorScale(0.85 + random.uniform(-0.1, 0.1), 1.0, 0.85, 1.0)
            shrub.setShaderAuto()
            self._register(shrub)

    def _add_flower_meadows(self):
        if not self.render:
            return

        flower_texture = create_flower_patch_texture(160)
        cm = CardMaker('flower_patch')
        cm.setFrame(-1, 1, -1, 1)

        patch_centers = [
            Vec3(14, 18, 0),
            Vec3(-20, -12, 0),
            Vec3(6, 32, 0),
        ]

        for center in patch_centers:
            z = self._terrain_height(center.x, center.y) + 0.02
            patch = self.render.attachNewNode(cm.generate())
            patch.setTransparency(TransparencyAttrib.MAlpha)
            patch.setTexture(flower_texture, 1)
            patch.setPos(center.x, center.y, z)
            patch.setP(-90)
            patch.setScale(3.0 + random.uniform(-0.5, 0.7))
            patch.setColorScale(0.94 + random.uniform(-0.04, 0.06), 1.0, 0.94, 0.92)
            patch.setShaderAuto()
            self._register(patch)
