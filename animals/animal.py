"""
Animal module for the 3D Hunting Simulator.
Handles animal AI, behavior, and basic 3D models.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, Optional
from panda3d.core import NodePath, Vec3, LVecBase3f, GeomNode, Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles, Vec4
import math
import random


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

    @abstractmethod
    def create_model(self) -> GeomNode:
        """Create the 3D model for this animal. Must be implemented by subclasses."""
        pass

    def create_basic_shape(self, size: float, color: Vec4) -> GeomNode:
        """
        Create a basic geometric shape for the animal model.

        Args:
            size: Size of the shape
            color: Color of the shape

        Returns:
            GeomNode containing the basic shape
        """
        # Create a simple cube as placeholder
        format = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData('animal', format, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color_writer = GeomVertexWriter(vdata, 'color')

        # Cube vertices
        vertices = [
            (-size, -size, -size), (-size, -size, size), (-size, size, -size), (-size, size, size),
            (size, -size, -size), (size, -size, size), (size, size, -size), (size, size, size)
        ]

        # Add vertices, normals, and colors
        for v in vertices:
            vertex.addData3f(*v)
            normal.addData3f(0, 0, 1)  # Simple normal
            color_writer.addData4f(*color)

        # Create triangles
        geom = Geom(vdata)
        prim = GeomTriangles(Geom.UHStatic)

        # Cube faces
        faces = [
            (0, 1, 3), (0, 3, 2),  # left
            (4, 6, 7), (4, 7, 5),  # right
            (0, 4, 5), (0, 5, 1),  # bottom
            (2, 3, 7), (2, 7, 6),  # top
            (0, 2, 6), (0, 6, 4),  # front
            (1, 5, 7), (1, 7, 3)   # back
        ]

        for face in faces:
            for vertex_index in face:
                prim.addVertex(vertex_index)

        geom.addPrimitive(prim)

        node = GeomNode(f'animal_{self.species}')
        node.addGeom(geom)

        return node

    def render(self, parent_node: NodePath) -> NodePath:
        """
        Render the animal and attach to parent node.

        Args:
            parent_node: Parent node to attach animal to

        Returns:
            NodePath containing the rendered animal
        """
        animal_geom = self.create_model()
        self.node = parent_node.attachNewNode(animal_geom)
        self.node.setPos(self.position)

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
            self.node.setPos(self.position)

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
            self.target_position = self.position + Vec3(
                math.cos(angle) * distance,
                math.sin(angle) * distance,
                0
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


class Deer(Animal):
    """Deer animal class."""

    def __init__(self, position: Vec3 = Vec3(0, 0, 0)):
        super().__init__(position, "deer")
        self.speed = 6.0
        self.detection_range = 60.0
        self.flee_range = 40.0

    def create_model(self) -> GeomNode:
        """Create deer model (simplified as colored cube)."""
        return self.create_basic_shape(1.5, Vec4(0.6, 0.4, 0.2, 1.0))  # Brown color


class Rabbit(Animal):
    """Rabbit animal class."""

    def __init__(self, position: Vec3 = Vec3(0, 0, 0)):
        super().__init__(position, "rabbit")
        self.speed = 4.0
        self.detection_range = 30.0
        self.flee_range = 20.0

    def create_model(self) -> GeomNode:
        """Create rabbit model (simplified as colored cube)."""
        return self.create_basic_shape(0.8, Vec4(0.8, 0.8, 0.8, 1.0))  # Gray color