"""
Dynamic foliage system with realistic wind physics and detailed rendering.
"""

import math
import random
from panda3d.core import (
    CardMaker, NodePath, TransformState, LVector3, Vec3, LVecBase3,
    GeomNode, GeomVertexFormat, GeomVertexData, Geom, GeomVertexWriter,
    GeomTriangles, GeomVertexReader, TransparencyAttrib
)
from direct.task import Task

from graphics.texture_factory import create_bark_texture, create_leaf_texture


class WindPhysics:
    """Advanced wind simulation for foliage and environment."""
    
    def __init__(self):
        self.wind_speed = 5.0
        self.wind_direction = Vec3(1, 0, 0)
        self.gustiness = 0.3
        self.turbulence = 0.2
        self._time_offset = random.uniform(0, 1000)
        
    def get_wind_at_point(self, position, time):
        """Calculate wind vector at a specific point in space."""
        # Base wind
        base_wind = self.wind_direction * self.wind_speed
        
        # Add turbulence using 3D noise
        turb_x = self._simplex_noise(position.x * 0.1, position.y * 0.1, time + self._time_offset)
        turb_y = self._simplex_noise(position.x * 0.1 + 500, position.y * 0.1, time + self._time_offset)
        
        # Add gusts
        gust_factor = self._simplex_noise(position.x * 0.01, position.y * 0.01, time * 0.1) * self.gustiness
        
        # Apply wind effects
        final_wind = base_wind + Vec3(
            turb_x * self.turbulence * self.wind_speed,
            turb_y * self.turbulence * self.wind_speed,
            0
        )
        
        return final_wind * (1 + gust_factor)
    
    def apply_to_foliage(self, foliage_node, position, dt, time):
        """Apply wind forces to foliage geometry."""
        wind_vector = self.get_wind_at_point(position, time)
        
        # Calculate bending based on wind strength
        wind_strength = wind_vector.length()
        bend_amount = min(wind_strength / 20.0, 1.0)  # Max 1.0 bend
        
        # Apply to branches and leaves
        self._animate_foliage(foliage_node, bend_amount, wind_vector, dt)
        
    def _animate_foliage(self, node, bend_amount, wind_vector, dt):
        """Animate individual foliage elements."""
        # Apply bending to main trunk
        swing = bend_amount * 5.0  # Degrees
        current_h = node.getH()
        target_h = current_h + (wind_vector.x * 0.1)
        target_p = node.getP() + (wind_vector.y * 0.1)
        
        # Smooth animation
        new_h = current_h + (target_h - current_h) * min(dt * 2.0, 1.0)
        new_p = node.getP() + (target_p - node.getP()) * min(dt * 2.0, 1.0)
        
        node.setH(new_h)
        node.setP(new_p)
        
    def _simplex_noise(self, x, y, z=0):
        """3D simplex noise function for natural turbulence."""
        # Simplified noise implementation
        # In a real implementation, this would use a proper noise library
        return (random.random() - 0.5) * 2


class GrassField:
    """Large-scale grass field with individual blade rendering."""
    
    def __init__(self, width=100, height=100, density=1000, render_node=None):
        self.width = width
        self.height = height
        self.density = density
        self.render = render_node
        self.grass_blades = []
        self.wind_system = WindPhysics()
        
    def generate_field(self, base_height=0):
        """Generate a field of individual grass blades."""
        if not self.render:
            return
            
        # Create grass geometry
        self._create_grass_mesh()
        
        # Add to scene
        self.grass_node = self.render.attachNewNode('grass_field')
        self._position_grass_blades()
        
    def _create_grass_mesh(self):
        """Create optimized grass blade geometry."""
        # Use instanced rendering for performance
        format = GeomVertexFormat.getV3n3cpt2()
        
        vdata = GeomVertexData('grass', format, Geom.UHDynamic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        texcoord = GeomVertexWriter(vdata, 'texcoord')
        
        # Create single grass blade template
        blade_verts = [
            (-0.02, 0, 0, 0, 0, 1, 0, 0, 1),   # Bottom left
            (0.02, 0, 0, 0, 0, 1, 1, 0, 1),    # Bottom right
            (0.01, 0, 0.3, 0, 0, 1, 1, 1, 0),  # Top right
            (-0.01, 0, 0.3, 0, 0, 1, 0, 1, 0)  # Top left
        ]
        
        # Add vertices
        for v in blade_verts:
            vertex.addData3f(v[0], v[1], v[2])
            normal.addData3f(v[3], v[4], v[5])
            color.addData3f(0.1, 0.4, 0.05)  # Green
            texcoord.addData2f(v[6], v[7])
            
        # Create triangles
        tris = GeomTriangles(Geom.UHStatic)
        tris.addVertices(0, 1, 2)
        tris.addVertices(0, 2, 3)
        
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        
        # Create node
        self.grass_template = NodePath('grass_blade')
        # Create GeomNode and add the geom to it
        grass_gnode = GeomNode('grass_geom_node')
        grass_gnode.addGeom(geom)
        self.grass_template = self.grass_template.attachNewNode(grass_gnode)
        
    def _position_grass_blades(self):
        """Position multiple instances of grass blades."""
        # Simple grass placement without instancing for now
        # Spread out blades
        for i in range(min(self.density, 1000)):  # Lower density for performance
            x = random.uniform(-self.width/2, self.width/2)
            y = random.uniform(-self.height/2, self.height/2)
            
            blade = self.grass_template.copyTo(self.grass_node)
            blade.setPos(x, y, 0)
            blade.setScale(random.uniform(0.8, 1.2))  # Random scale
            blade.setH(random.uniform(0, 360))  # Random heading rotation
            
            self.grass_blades.append(blade)
            
    def update(self, dt, time):
        """Update all grass blades with wind animations."""
        for blade in self.grass_blades:
            pos = blade.getPos()
            self.wind_system.apply_to_foliage(blade, pos, dt, time)
            
            # Age-based color variation
            if time % 3600 < 1800:  # Hourly cycle
                blade.setColorScale(0.1, 0.4 + abs(math.sin(time * 0.001)) * 0.1, 0.05, 1)


class TreeFactory:
    """Procedural tree generator with billboarding for foliage."""

    def __init__(self, render_node):
        self.render = render_node
        self.leaf_texture = create_leaf_texture()
        self.bark_texture = create_bark_texture()

    def create_tree(self, position: Vec3, scale: float = 1.0) -> NodePath:
        tree_root = self.render.attachNewNode('tree')
        trunk_height = 4.0 * scale
        trunk_radius = 0.22 * scale

        for heading in (0, 45, 90, 135):
            cm = CardMaker('branch_panel')
            cm.setFrame(-trunk_radius, trunk_radius, 0, trunk_height)
            trunk_panel = tree_root.attachNewNode(cm.generate())
            trunk_panel.setH(heading)
            trunk_panel.setTexture(self.bark_texture, 1)
            trunk_panel.setTwoSided(True)

        canopy = tree_root.attachNewNode('leaf_cluster')
        canopy.setZ(trunk_height * 0.85)
        leaf_radius = 2.2 * scale

        for heading in (0, 60, 120):
            cm = CardMaker('leaf_panel')
            cm.setFrame(-leaf_radius, leaf_radius, -leaf_radius, leaf_radius)
            leaf_card = canopy.attachNewNode(cm.generate())
            leaf_card.setH(heading)
            leaf_card.setTexture(self.leaf_texture, 1)
            leaf_card.setTransparency(TransparencyAttrib.MAlpha)
            leaf_card.setTwoSided(True)

        tree_root.setPos(position)
        tree_root.setShaderAuto()
        return tree_root


class TreeFoliage:
    """Individual tree with animated leaves and branches."""
    
    def __init__(self, tree_node):
        self.tree_node = tree_node
        self.leaf_nodes = []
        self.branch_nodes = []
        self.wind_system = WindPhysics()
        self._initialized = False
        
    def setup_foliage_animation(self):
        """Set up leaf and branch animation system."""
        if self._initialized:
            return
            
        # Find all leaf and branch geometry
        self._find_foliage_nodes()
        self._initialized = True
        
    def _find_foliage_nodes(self):
        """Identify nodes that should animate with wind."""
        self.leaf_nodes = []
        self.branch_nodes = []
        
        def traverse_node(node):
            if 'leaf' in node.getName().lower():
                self.leaf_nodes.append(node)
            elif 'branch' in node.getName().lower():
                self.branch_nodes.append(node)
                
            for child in node.getChildren():
                traverse_node(child)
                
        traverse_node(self.tree_node)
        
    def update(self, dt, time):
        """Update tree foliage with wind physics."""
        if not self._initialized:
            self.setup_foliage_animation()
            
        for branch in self.branch_nodes:
            pos = branch.getPos()
            self.wind_system.apply_to_foliage(branch, pos, dt, time * 0.1)  # Slower for branches
            
        for leaf in self.leaf_nodes:
            pos = leaf.getPos()
            self.wind_system.apply_to_foliage(leaf, pos, dt, time)  # Faster for leaves
            
            # Add leaf fluttering
            angle = math.sin(time * 5) * 10  # Fast flutter
            leaf.setR(leaf.getR() + angle * dt)


class InteractiveFoliage:
    """Foliage that responds to player and animal movement."""
    
    def __init__(self, render_node):
        self.render = render_node
        self.foliage_objects = []
        self.collision_events = []
        
    def add_foliage(self, node_path, trigger_distance=3.0):
        """Add a foliage object that responds to movement."""
        settings = {
            'trigger_distance': trigger_distance,
            'bend_amount': 0,
            'recovery_speed': 2.0
        }
        node_path.setPythonTag('foliage_settings', settings)
        node_path.setPythonTag('current_bend', 0.0)
        self.foliage_objects.append(node_path)
        
    def add_collision_event(self, position, intensity, duration=1.0):
        """Add a collision that moves foliage."""
        self.collision_events.append({
            'position': position,
            'intensity': intensity,
            'duration': duration,
            'elapsed': 0
        })
        
    def update(self, dt):
        """Update foliage interactions."""
        # Update active collision events
        remaining_events = []
        
        for event in self.collision_events:
            event['elapsed'] += dt
            
            if event['elapsed'] < event['duration']:
                # Apply push to nearby foliage
                self._apply_collision_to_foliage(event)
                remaining_events.append(event)
                
        self.collision_events = remaining_events
        
        # Update foliage recovery
        for foliage in self.foliage_objects:
            self._update_foliage_recovery(foliage, dt)
            
    def _apply_collision_to_foliage(self, event):
        """Apply collision force to nearby foliage."""
        for foliage in self.foliage_objects:
            foliage_pos = foliage.getPos()
            distance = (foliage_pos - event['position']).length()
            
            if distance < 10:  # Effect range
                # Calculate push strength
                strength = max(0, (10 - distance) / 10 * event['intensity'])
                
                # Apply animation
                current_bend = foliage.getPythonTag('current_bend') or 0.0
                new_bend = max(current_bend + strength, 0)
                foliage.setPythonTag('current_bend', min(new_bend, 1.0))
                
    def _update_foliage_recovery(self, foliage, dt):
        """Update foliage spring-back animation."""
        settings = foliage.getPythonTag('foliage_settings') or {'recovery_speed': 2.0}
        current_bend = foliage.getPythonTag('current_bend') or 0.0
        recovery = settings.get('recovery_speed', 2.0) * dt
        current_bend = max(0, current_bend - recovery)
        foliage.setPythonTag('current_bend', current_bend)
            
        # Apply visual effect
        if current_bend > 0:
            angle = current_bend * 15  # Max 15 degrees
            self._apply_bend_animation(foliage, angle)
                
    def _apply_bend_animation(self, foliage, angle):
        """Apply visual bending to foliage."""
        # Simple bending - in practice this would use more sophisticated techniques
        foliage.setH(foliage.getH() + angle * 0.1)
        foliage.setP(foliage.getP() - angle * 0.05)


class FoliageRenderer:
    """Optimized renderer for large-scale foliage."""
    
    def __init__(self, render_node):
        self.render = render_node
        self.grass_fields = []
        self.trees = []
        self.interactive_foliage = InteractiveFoliage(render_node)
        self.tree_factory = TreeFactory(render_node)
        
    def add_grass_field(self, field):
        """Add a grass field to the renderer."""
        self.grass_fields.append(field)
        field.generate_field()
        
    def add_tree(self, tree_node):
        """Add a tree with animated foliage."""
        tree_foliage = TreeFoliage(tree_node)
        self.trees.append(tree_foliage)

    def create_tree_cluster(self, center, count, radius, terrain=None):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(radius * 0.2, radius)
            x = center.x + math.cos(angle) * distance
            y = center.y + math.sin(angle) * distance
            z = center.z
            if terrain:
                z = terrain.get_height(x, y)
            tree = self.tree_factory.create_tree(Vec3(x, y, z), scale=random.uniform(0.85, 1.3))
            self.add_tree(tree)
            self.interactive_foliage.add_foliage(tree)
        
    def add_interactive_object(self, node_path):
        """Add an object that should respond to movement."""
        self.interactive_foliage.add_foliage(node_path)
        
    def player_moved(self, position, speed):
        """Notify vegetation that player moved nearby."""
        if speed > 1:  # Only trigger when moving
            self.interactive_foliage.add_collision_event(position, speed * 0.1)
            
    def animal_moved(self, position, animal_type):
        """Notify vegetation that animal moved nearby."""
        sizes = {'deer': 0.5, 'rabbit': 0.1, 'bear': 0.8}
        intensity = sizes.get(animal_type, 0.3)
        self.interactive_foliage.add_collision_event(position, intensity, 0.5)
        
    def update(self, dt, time):
        """Update all foliage systems."""
        # Update grass
        for field in self.grass_fields:
            field.update(dt, time)
            
        # Update tree foliage
        for tree in self.trees:
            tree.update(dt, time)
            
        # Update interactive elements
        self.interactive_foliage.update(dt)
