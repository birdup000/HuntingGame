"""
Animal module for the 3D Hunting Simulator.
Handles animal AI, behavior, and basic 3D models.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Union
from panda3d.core import (
    CardMaker,
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    NodePath,
    TransparencyAttrib,
    Vec3,
    Vec4,
)
import math
import random

from graphics.texture_factory import create_track_texture


class AnimalState(Enum):
    """States for animal behavior."""
    IDLE = "idle"
    FORAGING = "foraging"
    FLEEING = "fleeing"
    ALERTED = "alerted"
    DEAD = "dead"


class Animal(ABC):
    """Base class for all animals in the hunting simulator."""

    def __init__(self, position: Vec3 = Vec3(0, 0, 0), species: str = "unknown"):
        """
        Initialize animal.

        Args:
            position: Initial position in 3D space
            species: Species name
        """
        self.position = position
        self.species = species
        self.state = AnimalState.IDLE
        self.health = 100.0
        self.speed = 5.0
        self.detection_range = 50.0
        self.flee_range = 30.0
        self.node: Optional[NodePath] = None
        self.velocity = Vec3(0, 0, 0)
        self.target_position: Optional[Vec3] = None
        self.state_timer = 0.0
        self.state_duration = 3.0  # How long to stay in current state
        # Height offset to keep animals above terrain
        self.height_offset = 0.0
        self.render_node: Optional[NodePath] = None
        self.tracks: list[NodePath] = []
        self.track_spacing = 1.6
        self._distance_since_track = 0.0

    @abstractmethod
    def create_model(self) -> Union[GeomNode, NodePath]:
        """Create the 3D model for this animal. Must be implemented by subclasses."""
        pass

    def create_basic_shape(self, size: float, color: Vec4) -> GeomNode:
        """
        Create a more detailed animal shape with better visibility and realism.

        Args:
            size: Size of the shape
            color: Color of the shape

        Returns:
            GeomNode containing the basic shape
        """
        # Create a more detailed animal-like shape
        format = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData('animal', format, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color_writer = GeomVertexWriter(vdata, 'color')

        # Create elongated body with head and legs
        body_length = size * 2.0
        body_width = size * 0.8
        body_height = size * 0.6
        
        vertices = [
            # Body vertices (8 corners)
            (-body_length/2, -body_width/2, -body_height/2),  # 0
            (body_length/2, -body_width/2, -body_height/2),   # 1
            (body_length/2, body_width/2, -body_height/2),    # 2
            (-body_length/2, body_width/2, -body_height/2),   # 3
            (-body_length/2, -body_width/2, body_height/2),   # 4
            (body_length/2, -body_width/2, body_height/2),    # 5
            (body_length/2, body_width/2, body_height/2),     # 6
            (-body_length/2, body_width/2, body_height/2),    # 7
        ]


        # Add vertices with realistic colors
        for i, v in enumerate(vertices):
            vertex.addData3f(*v)
            # Use consistent direction normals for cleaner look
            normal.addData3f(0, 0, 1)
            # Simply use base color for cleaner appearance
            color_writer.addData4f(color.x, color.y, color.z, color.w)

        # Create body triangles
        geom = Geom(vdata)
        prim = GeomTriangles(Geom.UHStatic)

        # Each face as 2 triangles
        faces = [
            [0, 1, 2, 3], [4, 7, 6, 5],  # top, bottom
            [0, 4, 5, 1], [2, 6, 7, 3],  # front, back  
            [0, 3, 7, 4], [1, 5, 6, 2]  # left, right
        ]
        
        for vertices_indices in faces:
            prim.addVertex(vertices_indices[0])
            prim.addVertex(vertices_indices[1])
            prim.addVertex(vertices_indices[2])
            prim.addVertex(vertices_indices[0])
            prim.addVertex(vertices_indices[2])
            prim.addVertex(vertices_indices[3])

        geom.addPrimitive(prim)

        node = GeomNode(f'animal_{self.species}')
        node.addGeom(geom)

        return node

    def _create_box_geom(self, length: float, width: float, height: float, color: Vec4, name: str = 'box') -> GeomNode:
        """Create a simple box geometry for modular animal construction."""
        half_l = length / 2.0
        half_w = width / 2.0
        half_h = height / 2.0

        format = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData(f'{name}_vdata', format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color_writer = GeomVertexWriter(vdata, 'color')

        vertices = [
            (-half_w, -half_l, -half_h),
            (half_w, -half_l, -half_h),
            (half_w, half_l, -half_h),
            (-half_w, half_l, -half_h),
            (-half_w, -half_l, half_h),
            (half_w, -half_l, half_h),
            (half_w, half_l, half_h),
            (-half_w, half_l, half_h),
        ]

        normals = [
            (0, 0, -1),
            (0, 0, 1),
            (0, -1, 0),
            (0, 1, 0),
            (-1, 0, 0),
            (1, 0, 0),
        ]

        faces = [
            (0, 1, 2, 3, 0),  # bottom
            (4, 5, 6, 7, 1),  # top
            (0, 1, 5, 4, 2),  # back
            (2, 3, 7, 6, 3),  # front
            (0, 3, 7, 4, 4),  # left
            (1, 2, 6, 5, 5),  # right
        ]

        for v in vertices:
            vertex.addData3f(*v)
        for _ in vertices:
            normal.addData3f(0, 0, 1)  # placeholder, will overwrite
        for _ in vertices:
            color_writer.addData4f(color.x, color.y, color.z, color.w)

        # Update normals per face
        normal_writer = GeomVertexWriter(vdata, 'normal')
        normals_per_vertex = [Vec3(0, 0, 0) for _ in vertices]
        counts = [0] * len(vertices)
        for a, b, c, d, normal_index in faces:
            nx, ny, nz = normals[normal_index]
            for idx in (a, b, c, d):
                normals_per_vertex[idx] += Vec3(nx, ny, nz)
                counts[idx] += 1
        for idx, accum in enumerate(normals_per_vertex):
            if counts[idx] > 0:
                accum /= counts[idx]
            accum.normalize()
            normal_writer.setData3f(accum.x, accum.y, accum.z)

        prim = GeomTriangles(Geom.UHStatic)
        for a, b, c, d, _ in faces:
            prim.addVertices(a, b, c)
            prim.addVertices(a, c, d)

        geom = Geom(vdata)
        geom.addPrimitive(prim)
        geom_node = GeomNode(name)
        geom_node.addGeom(geom)
        return geom_node

    def render(self, parent_node: NodePath) -> NodePath:
        """
        Render the animal and attach to parent node.

        Args:
            parent_node: Parent node to attach animal to

        Returns:
            NodePath containing the rendered animal
        """
        animal_geom = self.create_model()
        if isinstance(animal_geom, NodePath):
            self.node = animal_geom
            self.node.reparentTo(parent_node)
        elif isinstance(animal_geom, GeomNode):
            self.node = parent_node.attachNewNode(animal_geom)
        else:
            raise TypeError("create_model must return a GeomNode or NodePath")
        self.render_node = parent_node
        # Apply height offset to position animals above terrain
        self.node.setPos(self.position.x, self.position.y, self.position.z + self.height_offset)

        return self.node

    def detect_player(self, player_position: Vec3) -> bool:
        """
        Check if animal can detect the player.

        Args:
            player_position: Current player position

        Returns:
            True if player is detected
        """
        distance = (player_position - self.position).length()

        if distance <= self.flee_range:
            return True

        return False

    def update(self, dt: float, player_position: Vec3, terrain_height: float = 0.0):
        """
        Update animal state and behavior.

        Args:
            dt: Time delta since last update
            player_position: Current player position
            terrain_height: Height of terrain at current position
        """
        # Dead animals don't update
        if self.state == AnimalState.DEAD:
            return

        self.state_timer += dt

        # Store player position for fleeing behavior
        self._last_player_position = player_position
        self._last_terrain_height = terrain_height

        # Check for player detection
        if self.detect_player(player_position):
            self.state = AnimalState.FLEEING
            self.state_timer = 0.0
        elif self.state_timer >= self.state_duration:
            # Change state randomly
            self._change_state()

        # Update position based on current state
        self._update_movement(dt)

        # Update node position if rendered
        if self.node:
            # Always ensure animal is properly positioned above terrain
            self.position.setZ(terrain_height + self.height_offset)
                
            self.node.setPos(self.position)
            self._distance_since_track += self.velocity.length() * dt
            if self._distance_since_track >= self.track_spacing:
                self._distance_since_track = 0.0
                self._leave_track(terrain_height)

    def _change_state(self):
        """Randomly change to a new state."""
        # Don't change state if dead
        if self.state == AnimalState.DEAD:
            return

        self.state = random.choice([AnimalState.IDLE, AnimalState.FORAGING])
        self.state_timer = 0.0
        self.state_duration = random.uniform(2.0, 5.0)

        # Set new target for foraging
        if self.state == AnimalState.FORAGING:
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(5.0, 20.0)
            # Keep target at same z-level for terrain following
            self.target_position = Vec3(
                self.position.x + math.cos(angle) * distance,
                self.position.y + math.sin(angle) * distance,
                self.position.z
            )

    def is_dead(self) -> bool:
        """Check if the animal is dead."""
        return self.state == AnimalState.DEAD

    def _update_movement(self, dt: float):
        """Update animal movement based on current state."""
        if self.state == AnimalState.DEAD:
            # Dead animals don't move
            self.velocity = Vec3(0, 0, 0)
            return

        elif self.state == AnimalState.FLEEING:
            # Move away from player with more realistic fleeing behavior
            self.speed = 10.0  # Faster when fleeing

            # Calculate flee direction (away from player)
            if hasattr(self, '_last_player_position'):
                flee_direction = self.position - self._last_player_position
                if flee_direction.length() > 0:
                    flee_direction.normalize()
                    # Add some randomness to make fleeing less predictable
                    random_offset = Vec3(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), 0)
                    flee_direction += random_offset
                    flee_direction.normalize()
                    self.velocity = flee_direction * self.speed
                else:
                    # Fallback random direction
                    self.velocity = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), 0).normalized() * self.speed
            else:
                # No player position known, use random direction
                self.velocity = Vec3(random.uniform(-1, 1), random.uniform(-1, 1), 0).normalized() * self.speed

        elif self.state == AnimalState.FORAGING:
            if self.target_position:
                direction = self.target_position - self.position
                if direction.length() < 1.0:
                    # Reached target, stop moving
                    self.velocity = Vec3(0, 0, 0)
                    self.target_position = None
                else:
                    self.velocity = direction.normalized() * self.speed
            else:
                self.velocity = Vec3(0, 0, 0)

        elif self.state == AnimalState.IDLE:
            self.velocity = Vec3(0, 0, 0)
            self.speed = 5.0  # Normal speed

        # Update position
        self.position += self.velocity * dt
        
        # Apply gravity/terrain alignment - ensure animals stay on terrain
        if hasattr(self, '_last_ground_height'):
            # Smooth terrain following
            current_ground = self._last_ground_height
        else:
            current_ground = 0  # Fallback
            
        # Store position for terrain queries
        self._last_position = Vec3(self.position.x, self.position.y, 0)
        self._last_ground_height = current_ground

    def _leave_track(self, terrain_height: float):
        """Leave a subtle track on the terrain to reinforce presence."""
        if not self.render_node or self.velocity.lengthSquared() < 1e-4:
            return

        texture = create_track_texture()
        cm = CardMaker(f"track_{self.species}")
        cm.setFrame(-0.25, 0.25, -0.45, 0.45)
        track_node = self.render_node.attachNewNode(cm.generate())
        track_node.setTransparency(TransparencyAttrib.MAlpha)
        track_node.setTexture(texture, 1)
        track_node.setPos(self.position.x, self.position.y, terrain_height + 0.02)
        track_node.setP(-90)
        track_node.setScale(1.0)
        if self.velocity.lengthSquared() > 1e-6:
            direction = self.position + self.velocity.normalized()
            track_node.lookAt(direction.x, direction.y, terrain_height + 0.02)
        track_node.setColorScale(1, 1, 1, 0.75)
        self.tracks.append(track_node)
        if len(self.tracks) > 14:
            oldest = self.tracks.pop(0)
            oldest.removeNode()

    def take_damage(self, damage: float):
        """Apply damage to the animal."""
        if self.state == AnimalState.DEAD:
            return  # Can't damage a dead animal

        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.state = AnimalState.DEAD
            self.velocity = Vec3(0, 0, 0)  # Stop moving when dead
            # Visual feedback for death (if node exists)
            if self.node:
                # Simple death animation - fall over
                self.node.setH(self.node.getH() + 90)  # Rotate to fall over
                self.node.setZ(self.node.getZ() - 0.5)  # Lower to ground
        else:
            # Injured but not dead - increase flee behavior
            if self.state != AnimalState.FLEEING:
                self.state = AnimalState.FLEEING
                self.state_timer = 0.0

    def cleanup(self):
        """Clean up animal resources."""
        if self.node:
            self.node.removeNode()
            self.node = None
        for track in self.tracks:
            track.removeNode()
        self.tracks.clear()
        self.render_node = None


class Deer(Animal):
    """Deer animal class."""

    def __init__(self, position: Vec3 = Vec3(0, 0, 0)):
        super().__init__(position, "deer")
        self.speed = 6.0
        self.detection_range = 60.0
        self.flee_range = 40.0

    def create_model(self) -> Union[GeomNode, NodePath]:
        """Create a layered deer mesh with body, legs, head, and antlers."""
        body_color = Vec4(0.58, 0.38, 0.2, 1.0)
        underbelly_color = Vec4(0.82, 0.74, 0.62, 1.0)
        leg_color = Vec4(0.42, 0.26, 0.14, 1.0)

        root = NodePath('deer_model')

        body = root.attachNewNode(self._create_box_geom(3.2, 1.1, 1.2, body_color, 'deer_body'))
        body.setZ(1.1)
        chest = root.attachNewNode(self._create_box_geom(1.1, 0.9, 1.0, underbelly_color, 'deer_chest'))
        chest.setPos(0.9, 0, 1.2)

        neck = root.attachNewNode(self._create_box_geom(1.0, 0.5, 0.9, body_color, 'deer_neck'))
        neck.setPos(1.9, 0, 1.6)
        neck.setP(-20)

        head = root.attachNewNode(self._create_box_geom(0.9, 0.6, 0.6, Vec4(0.54, 0.32, 0.16, 1.0), 'deer_head'))
        head.setPos(2.5, 0, 1.9)
        head.setP(10)

        ear_geom = self._create_box_geom(0.4, 0.18, 0.5, Vec4(0.78, 0.6, 0.4, 1.0), 'deer_ear')
        left_ear = root.attachNewNode(ear_geom)
        left_ear.setPos(2.7, 0.22, 2.3)
        left_ear.setH(10)
        right_ear = root.attachNewNode(ear_geom)
        right_ear.setPos(2.7, -0.22, 2.3)
        right_ear.setH(-10)

        antler_geom = self._create_box_geom(0.6, 0.12, 0.6, Vec4(0.9, 0.88, 0.82, 1.0), 'deer_antler')
        for offset in ((2.8, 0.18, 2.45), (2.8, -0.18, 2.45)):
            antler = root.attachNewNode(antler_geom)
            antler.setPos(*offset)
            antler.setH(20 if offset[1] > 0 else -20)
            antler.setP(35)

        leg_geom = self._create_box_geom(0.35, 0.35, 1.1, leg_color, 'deer_leg')
        leg_positions = [
            (-1.0, 0.4, 0.55),
            (-1.0, -0.4, 0.55),
            (1.0, 0.45, 0.55),
            (1.0, -0.45, 0.55)
        ]
        for pos in leg_positions:
            leg = root.attachNewNode(leg_geom)
            leg.setPos(*pos)

        tail = root.attachNewNode(self._create_box_geom(0.4, 0.4, 0.4, underbelly_color, 'deer_tail'))
        tail.setPos(-1.7, 0, 1.6)
        tail.setP(35)

        root.setScale(0.75)
        root.flattenLight()
        return root


class Rabbit(Animal):
    """Rabbit animal class."""

    def __init__(self, position: Vec3 = Vec3(0, 0, 0)):
        super().__init__(position, "rabbit")
        self.speed = 4.0
        self.detection_range = 30.0
        self.flee_range = 20.0

    def create_model(self) -> Union[GeomNode, NodePath]:
        """Create a stylized rabbit with rounded body and tall ears."""
        body_color = Vec4(0.74, 0.66, 0.58, 1.0)
        accent_color = Vec4(0.9, 0.86, 0.82, 1.0)

        root = NodePath('rabbit_model')

        body = root.attachNewNode(self._create_box_geom(1.6, 1.1, 0.9, body_color, 'rabbit_body'))
        body.setZ(0.65)
        head = root.attachNewNode(self._create_box_geom(0.8, 0.7, 0.7, body_color, 'rabbit_head'))
        head.setPos(0.9, 0, 1.0)

        ear_geom = self._create_box_geom(0.2, 0.25, 0.9, accent_color, 'rabbit_ear')
        left_ear = root.attachNewNode(ear_geom)
        left_ear.setPos(1.1, 0.18, 1.6)
        left_ear.setH(6)
        right_ear = root.attachNewNode(ear_geom)
        right_ear.setPos(1.1, -0.18, 1.6)
        right_ear.setH(-6)

        foot_color = Vec4(body_color.x * 0.9, body_color.y * 0.9, body_color.z * 0.9, 1.0)
        foot_geom = self._create_box_geom(0.35, 0.3, 0.55, foot_color, 'rabbit_foot')
        paw_positions = [
            (-0.6, 0.35, 0.3),
            (-0.6, -0.35, 0.3),
            (0.6, 0.35, 0.3),
            (0.6, -0.35, 0.3)
        ]
        for pos in paw_positions:
            paw = root.attachNewNode(foot_geom)
            paw.setPos(*pos)

        tail = root.attachNewNode(self._create_box_geom(0.4, 0.4, 0.4, accent_color, 'rabbit_tail'))
        tail.setPos(-0.9, 0, 1.0)

        root.setScale(0.9)
        root.flattenLight()
        return root