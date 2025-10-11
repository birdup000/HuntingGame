"""
Collision detection module for the 3D Hunting Simulator.
Handles collision detection between projectiles and game objects.
"""

from typing import List, Dict, Callable, Any, Optional, TYPE_CHECKING
from panda3d.core import CollisionTraverser, CollisionHandlerQueue, CollisionNode, CollisionSphere, BitMask32, Point3, Vec3

if TYPE_CHECKING:
    from animals.animal import Animal


class Projectile:
    """Represents a projectile (bullet) in the game."""

    def __init__(self, position: Point3, direction: Vec3, speed: float = 100.0, damage: float = 25.0):
        self.position = position
        self.direction = direction.normalized()
        self.speed = speed
        self.damage = damage
        self.distance_traveled = 0.0
        self.max_range = 500.0
        self.active = True

        # Create collision ray for hit detection
        self.collision_ray = CollisionNode('projectile')
        self.collision_ray.addSolid(CollisionSphere(0, 0, 0, 0.1))  # Small sphere for projectile
        self.collision_ray.setFromCollideMask(BitMask32.bit(1))  # Hit animals
        self.collision_ray.setIntoCollideMask(BitMask32.allOff())

        self.collision_node = self.collision_ray

    def update(self, dt: float) -> bool:
        """Update projectile position. Returns False if projectile should be removed."""
        if not self.active:
            return False

        move_distance = self.speed * dt
        self.position += self.direction * move_distance
        self.distance_traveled += move_distance

        # Check if projectile exceeded max range
        if self.distance_traveled >= self.max_range:
            self.active = False
            return False

        return True

    def cleanup(self):
        """Clean up projectile resources."""
        if hasattr(self, 'collision_node'):
            self.collision_node.removeNode()


class CollisionManager:
    """Manages collision detection for the hunting simulator."""

    def __init__(self, app):
        """Initialize collision manager with Panda3D application."""
        self.app = app
        self.traverser = CollisionTraverser('collision_manager')
        self.handler = CollisionHandlerQueue()

        # Collision masks
        self.PROJECTILE_MASK = BitMask32.bit(1)
        self.ANIMAL_MASK = BitMask32.bit(2)
        self.TERRAIN_MASK = BitMask32.bit(3)

        # Object mappings for collision detection
        self.animals: Dict[str, 'Animal'] = {}
        self.projectiles: Dict[str, 'Projectile'] = {}

        # Hit callbacks
        self.hit_callbacks: List[Callable[['Projectile', 'Animal'], None]] = []

    def add_animal(self, animal: 'Animal'):
        """Add an animal to collision detection."""
        if animal.node and not animal.is_dead():
            # Create collision node for animal
            collision_node = CollisionNode(f'animal_collision_{id(animal)}')
            collision_node.addSolid(CollisionSphere(0, 0, 0, 1.0))  # Simple sphere collision
            collision_node.setFromCollideMask(self.PROJECTILE_MASK)
            collision_node.setIntoCollideMask(BitMask32.allOff())

            # Attach to animal node
            collision_np = animal.node.attachNewNode(collision_node)
            self.traverser.addCollider(collision_np, self.handler)

            # Store reference
            animal_id = f"animal_{id(animal)}"
            self.animals[animal_id] = animal
            animal.collision_np = collision_np
            animal.collision_id = animal_id

    def remove_animal(self, animal: 'Animal'):
        """Remove an animal from collision detection."""
        if hasattr(animal, 'collision_id'):
            animal_id = animal.collision_id
            if animal_id in self.animals:
                del self.animals[animal_id]

        if hasattr(animal, 'collision_np'):
            self.traverser.removeCollider(animal.collision_np)
            animal.collision_np.removeNode()
            delattr(animal, 'collision_np')
            if hasattr(animal, 'collision_id'):
                delattr(animal, 'collision_id')

    def add_projectile(self, projectile: 'Projectile'):
        """Add a projectile to collision detection."""
        projectile_id = f"projectile_{id(projectile)}"
        self.projectiles[projectile_id] = projectile

        # Set up collision node
        projectile.collision_node.setFromCollideMask(BitMask32.allOff())
        projectile.collision_node.setIntoCollideMask(self.PROJECTILE_MASK)

        # Attach to render
        projectile.collision_np = self.app.render.attachNewNode(projectile.collision_node)
        projectile.collision_id = projectile_id

        self.traverser.addCollider(projectile.collision_np, self.handler)

    def remove_projectile(self, projectile: 'Projectile'):
        """Remove a projectile from collision detection."""
        if hasattr(projectile, 'collision_id'):
            projectile_id = projectile.collision_id
            if projectile_id in self.projectiles:
                del self.projectiles[projectile_id]

        if hasattr(projectile, 'collision_np'):
            self.traverser.removeCollider(projectile.collision_np)
            projectile.collision_np.removeNode()
            delattr(projectile, 'collision_np')
            if hasattr(projectile, 'collision_id'):
                delattr(projectile, 'collision_id')

    def add_hit_callback(self, callback: Callable[['Projectile', 'Animal'], None]):
        """Add a callback for when projectile hits are detected."""
        self.hit_callbacks.append(callback)

    def remove_hit_callback(self, callback: Callable[['Projectile', 'Animal'], None]):
        """Remove a hit callback."""
        if callback in self.hit_callbacks:
            self.hit_callbacks.remove(callback)

    def update(self):
        """Update collision detection and process hits."""
        # Perform collision detection
        if hasattr(self.app, 'render') and self.app.render is not None:
            self.traverser.traverse(self.app.render)
        else:
            return  # Cannot perform collision detection without render

        # Process collisions
        for i in range(self.handler.getNumEntries()):
            entry = self.handler.getEntry(i)

            # Get the colliding nodes
            from_node = entry.getFromNodePath()
            into_node = entry.getIntoNodePath()

            # Check if it's a projectile hitting an animal
            projectile = self._get_projectile_from_node(from_node)
            animal = self._get_animal_from_node(into_node)

            if projectile and animal and projectile.active and not animal.is_dead():
                # Process the hit
                self._process_hit(projectile, animal)

                # Mark projectile as inactive
                projectile.active = False

    def _get_projectile_from_node(self, node_path) -> Optional['Projectile']:
        """Get projectile from collision node path."""
        for projectile_id, projectile in self.projectiles.items():
            if hasattr(projectile, 'collision_id') and projectile_id in node_path.getName():
                return projectile
        return None

    def _get_animal_from_node(self, node_path) -> Optional['Animal']:
        """Get animal from collision node path."""
        for animal_id, animal in self.animals.items():
            if hasattr(animal, 'collision_id') and animal_id in node_path.getName():
                return animal
        return None

    def _process_hit(self, projectile: 'Projectile', animal: 'Animal'):
        """Process a projectile hitting an animal."""
        # Apply damage to the animal
        animal.take_damage(projectile.damage)

        # Notify callbacks
        for callback in self.hit_callbacks:
            callback(projectile, animal)

    def cleanup(self):
        """Clean up collision manager resources."""
        self.hit_callbacks.clear()
        self.animals.clear()
        self.projectiles.clear()
        self.traverser.clearColliders()