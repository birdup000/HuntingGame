#!/usr/bin/env python3
"""Test script to verify sky rendering in isolation."""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from environment.sky import SkyDome


class SkyTestApp(ShowBase):
    """Simple app to test sky rendering."""
    
    def __init__(self):
        ShowBase.__init__(self)
        
        # Set background color to red to make it obvious if sky isn't rendering
        self.setBackgroundColor(1, 0, 0, 1)  # Red background
        
        # Set up camera
        self.camera.setPos(0, -50, 10)
        self.camera.lookAt(0, 0, 10)
        
        # Set camera clip planes
        if hasattr(self, 'camLens'):
            self.camLens.setFar(2000)
            self.camLens.setNear(0.1)
        
        # Create sky
        print("Creating sky...")
        self.sky = SkyDome(self, radius=1000.0)
        print(f"Sky created. Root node: {self.sky._root}")
        print(f"Sky node: {self.sky.node}")
        
        # Print sky node details
        if self.sky._root:
            print(f"Sky root position: {self.sky._root.getPos()}")
            print(f"Sky root scale: {self.sky._root.getScale()}")
            print(f"Sky root hidden: {self.sky._root.isHidden()}")
            print(f"Sky root bin: {self.sky._root.getBinName()}")
            
        if self.sky.node:
            print(f"Sky model position: {self.sky.node.getPos()}")
            print(f"Sky model scale: {self.sky.node.getScale()}")
            print(f"Sky model hidden: {self.sky.node.isHidden()}")
        
        # Add simple camera controls
        self.accept('w', lambda: self.camera.setPos(self.camera.getPos() + (0, 10, 0)))
        self.accept('s', lambda: self.camera.setPos(self.camera.getPos() - (0, 10, 0)))
        self.accept('a', lambda: self.camera.setPos(self.camera.getPos() - (10, 0, 0)))
        self.accept('d', lambda: self.camera.setPos(self.camera.getPos() + (10, 0, 0)))
        self.accept('q', lambda: self.camera.setPos(self.camera.getPos() + (0, 0, 10)))
        self.accept('e', lambda: self.camera.setPos(self.camera.getPos() - (0, 0, 10)))
        self.accept('escape', self.userExit)
        
        print("\nControls:")
        print("WASD - Move horizontally")
        print("Q/E - Move up/down")
        print("ESC - Exit")


if __name__ == "__main__":
    print("Starting sky test...")
    app = SkyTestApp()
    app.run()
