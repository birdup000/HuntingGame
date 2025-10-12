from typing import Optional

from panda3d.core import CardMaker, NodePath, TransparencyAttrib

from graphics.texture_factory import create_sky_texture


class SkyDome:
    def __init__(self, app, radius: float = 600.0):
        self.app = app
        self.radius = radius
        self.node: Optional[NodePath] = None
        self._task = None
        self._setup_sky()

    def _setup_sky(self):
        texture = create_sky_texture()
        model = None
        if hasattr(self.app, 'loader') and getattr(self.app.loader, 'loadModel', None):
            try:
                model = self.app.loader.loadModel('models/misc/sphere')
            except Exception:
                model = None
        if model is None:
            cm = CardMaker('sky-backdrop')
            cm.setFrame(-1, 1, -1, 1)
            model = self.app.render.attachNewNode(cm.generate())
            model.setScale(self.radius)
            model.setBillboardPointEye()
        else:
            model.reparentTo(self.app.render)
            model.setScale(self.radius)
            model.setTwoSided(True)
        model.setTexture(texture, 1)
        model.setBin('background', 0)
        model.setDepthWrite(False)
        model.setDepthTest(False)
        model.setLightOff(1)
        model.setShaderOff(1)
        model.setColor(1, 1, 1, 1)
        model.setTransparency(TransparencyAttrib.MNone)
        self.node = model
        if hasattr(self.app, 'taskMgr'):
            self._task = self.app.taskMgr.add(self._update_task, 'skyDomeFollow', sort=50)

    def _update_task(self, task):
        if not self.node or not hasattr(self.app, 'camera'):
            return task.cont
        self.node.setPos(self.app.camera.getPos())
        return task.cont

    def cleanup(self):
        if self._task and hasattr(self.app, 'taskMgr'):
            self.app.taskMgr.remove(self._task)
            self._task = None
        if self.node:
            self.node.removeNode()
            self.node = None
