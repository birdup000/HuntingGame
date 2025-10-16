from typing import Optional

from panda3d.core import (
    CardMaker,
    NodePath,
    TransparencyAttrib,
    CompassEffect,
    CullFaceAttrib,
    BoundingSphere,
    Point3,
)

from graphics.texture_factory import create_sky_texture


class SkyDome:
    def __init__(self, app, radius: float = 600.0):
        self.app = app
        self.radius = radius
        self.node: Optional[NodePath] = None
        self._root: Optional[NodePath] = None
        self._task = None
        self._setup_sky()

    def _setup_sky(self):
        texture = create_sky_texture()
        if hasattr(self.app, 'setBackgroundColor'):
            self.app.setBackgroundColor(0.45, 0.62, 0.88, 1)

        # Root node follows the camera to stay centered around the player
        parent = getattr(self.app, 'render', None) or getattr(self.app, 'camera', None)
        self._root = parent.attachNewNode('sky_dome_root')
        self._root.setBin('background', -10)  # Render before everything else
        self._root.setDepthWrite(False)
        self._root.setDepthTest(False)  # Sky should not be depth tested
        self._root.setLightOff(1)
        self._root.setFogOff()
        self._root.setShaderOff(1)
        self._root.setColor(1, 1, 1, 1)
        self._root.setTransparency(TransparencyAttrib.MNone)
        self._root.setScale(self.radius * 2)  # Make sky larger
        self._root.node().setBounds(BoundingSphere(Point3(0, 0, 0), self.radius * 1.2))
        self._root.node().setFinal(True)
        if hasattr(self.app, 'camera'):
            compass = CompassEffect.make(self.app.camera, CompassEffect.PRot)
            self._root.setEffect(compass)

        model = None
        if hasattr(self.app, 'loader') and getattr(self.app.loader, 'loadModel', None):
            try:
                model = self.app.loader.loadModel('models/misc/sphere')
            except Exception:
                model = None

        if model is None:
            cm = CardMaker('sky-backdrop')
            cm.setFrame(-2, 2, -2, 2)  # Make card larger
            model = self._root.attachNewNode(cm.generate())
            model.setScale(2.0)  # Double the scale
            model.setPos(0, 100, 0)  # Push it forward from the camera
            model.setBillboardPointEye()
            model.setTwoSided(True)
        else:
            model.reparentTo(self._root)
            model.setScale(1.0)
            model.setTwoSided(True)

        model.setTexture(texture, 1)
        model.setDepthWrite(False)
        model.setDepthTest(False)
        model.setLightOff(1)
        model.setFogOff()
        model.setShaderOff(1)
        model.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullNone))
        model.clearColorScale()
        model.setBin('background', -10)  # Ensure card also renders in background
        self.node = model

        if hasattr(self.app, 'taskMgr'):
            self._task = self.app.taskMgr.add(self._update_task, 'skyDomeFollow', sort=50)
        else:
            self._task = None

    def _update_task(self, task):
        if not self._root or not hasattr(self.app, 'camera'):
            return task.cont
        self._root.setPos(self.app.camera.getPos())
        return task.cont

    def cleanup(self):
        if self._task and hasattr(self.app, 'taskMgr'):
            self.app.taskMgr.remove(self._task)
            self._task = None
        if self._root:
            self._root.removeNode()
            self._root = None
        if self.node and not self.node.isEmpty():
            self.node.removeNode()
            self.node = None
