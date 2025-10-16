#!/usr/bin/env python3
"""Debug script to test sky rendering with detailed output."""

from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, DirectionalLight, AmbientLight, Vec4
from environment.simple_sky import SimpleSkyDome
from panda3d.core import CardMaker, TransparencyAttrib


class SkyDebugApp(ShowBase):
    """Debug app to test sky rendering."""
    
    def __init__(self):
        ShowBase.__init__(self)
        
        # Set background color to red to make it obvious if sky isn't rendering
        self.setBackgroundColor(1, 0, 0, 1)  # Red background
        
        # Set up camera
        self.camera.setPos(0, -100, 20)
        self.camera.lookAt(0, 0, 20)
        
        # Set camera clip planes
        if hasattr(self, 'camLens'):
            self.camLens.setFar(3000)
            self.camLens.setNear(0.1)
            print(f"Camera far plane: {self.camLens.getFar()}")
            print(f"Camera near plane: {self.camLens.getNear()}")
        
        # Add basic lighting so we can see things
        dlight = DirectionalLight('sun')
        dlight.setColor(Vec4(1, 1, 0.9, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(-45, -45, 0)
        self.render.setLight(dlnp)
        
        alight = AmbientLight('ambient')
        alight.setColor(Vec4(0.3, 0.3, 0.3, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)
        
        # Create ground reference plane
        cm = CardMaker('ground')
        cm.setFrame(-200, 200, -200, 200)
        ground = self.render.attachNewNode(cm.generate())
        ground.setPos(0, 0, 0)
        ground.setHpr(0, -90, 0)  # Make it horizontal
        ground.setColor(0, 0.5, 0, 1)  # Green
        print("Ground plane created at z=0")
        
        # Create sky
        print("\n--- Creating SimpleSkyDome ---")
        self.sky = SimpleSkyDome(self, radius=500.0)
        
        # Debug output
        if self.sky._root:
            print(f"\nSky root node details:")
            print(f"  Position: {self.sky._root.getPos()}")
            print(f"  Scale: {self.sky._root.getScale()}")
            print(f"  Hidden: {self.sky._root.isHidden()}")
            print(f"  Bin: {self.sky._root.getBinName()}")
            print(f"  Depth write: {self.sky._root.getDepthWrite()}")
            print(f"  Depth test: {self.sky._root.getDepthTest()}")
            
            # Check if it has children
            children = self.sky._root.getChildren()
            print(f"  Number of children: {len(children)}")
            for child in children:
                print(f"    Child: {child.getName()}")
                
        if self.sky.node:
            print(f"\nSky hemisphere node details:")
            print(f"  Position: {self.sky.node.getPos()}")
            print(f"  Scale: {self.sky.node.getScale()}")
            print(f"  Hidden: {self.sky.node.isHidden()}")
            
            # Check texture
            if self.sky.node.hasTexture():
                tex = self.sky.node.getTexture()
                print(f"  Has texture: {tex.getName() if tex else 'unnamed'}")
            else:
                print(f"  No texture!")
        
        # List all nodes in render
        print("\n--- All nodes in render ---")
        def print_tree(node, indent=0):
            print("  " * indent + node.getName())
            for child in node.getChildren():
                print_tree(child, indent + 1)
        print_tree(self.render, 0)
        
        # Add camera controls
        self.accept('w', lambda: self.camera.setY(self.camera.getY() + 10))
        self.accept('s', lambda: self.camera.setY(self.camera.getY() - 10))
        self.accept('a', lambda: self.camera.setX(self.camera.getX() - 10))
        self.accept('d', lambda: self.camera.setX(self.camera.getX() + 10))
        self.accept('q', lambda: self.camera.setZ(self.camera.getZ() + 10))
        self.accept('e', lambda: self.camera.setZ(self.camera.getZ() - 10))
        self.accept('r', lambda: self.camera.setPos(0, -100, 20))  # Reset
        self.accept('escape', self.userExit)
        
        # Toggle sky visibility
        self.accept('h', self.toggle_sky)
        
        print("\n=== Controls ===")
        print("WASD - Move horizontally")
        print("Q/E - Move up/down")
        print("R - Reset camera position")
        print("H - Toggle sky visibility")
        print("ESC - Exit")
        print("\nIf you see a RED background, the sky is NOT rendering.")
        print("If you see a BLUE gradient with clouds, the sky IS rendering.")
        print("Green ground plane is at z=0 for reference.")
    
    def toggle_sky(self):
        """Toggle sky visibility for debugging."""
        if self.sky._root:
            if self.sky._root.isHidden():
                self.sky._root.show()
                print("Sky shown")
            else:
                self.sky._root.hide()
                print("Sky hidden")


if __name__ == "__main__":
    print("Starting sky debug test...")
    app = SkyDebugApp()
    app.run()
