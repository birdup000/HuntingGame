"""
Collision detection module for the 3D Hunting Simulator.
Handles collision detection between projectiles and game objects.
"""

from typing import List, Dict, Callable, TYPE_CHECKING
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
        # CollisionNode doesn't need explicit cleanup - it's removed when the NodePath is removed
        # Only clear references
        if hasattr(self, 'collision_node'):
            self.collision_node = None
        if hasattr(self, 'collision_np'):
            self.collision_np = None
        if hasattr(self, 'collision_id'):
            self.collision_id = None


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
        if animal is not None and hasattr(animal, 'node') and animal.node and hasattr(animal, 'is_dead') and not animal.is_dead():
            # Create collision node for animal
            collision_node = CollisionNode(f'animal_collision_{id(animal)}')
            collision_node.addSolid(CollisionSphere(0, 0, 0, 1.0))  # Simple sphere collision
            collision_node.setFromCollideMask(self.PROJECTILE_MASK)
            collision_node.setIntoCollideMask(BitMask32.allOff())

            # Attach to animal node and set Python tag
            collision_np = animal.node.attachNewNode(collision_node)
            collision_np.setPythonTag('animal', animal)
            self.traverser.addCollider(collision_np, self.handler)

            # Store reference
            animal.collision_np = collision_np

    def remove_animal(self, animal: 'Animal'):
        """Remove an animal from collision detection."""
        if animal is not None and hasattr(animal, 'collision_np') and animal.collision_np:
            try:
                # Try to remove from traverser safely
                if hasattr(self.traverser, 'getColliderQueue'):
                    if animal.collision_np in self.traverser.getColliderQueue():
                        self.traverser.removeCollider(animal.collision_np)
                else:
                    # Fallback for different Panda3D versions
                    try:
                        self.traverser.removeCollider(animal.collision_np)
                    except:
                        pass
                        
                # Remove the node safely
                if hasattr(animal.collision_np, 'isSingleton') and animal.collision_np.isSingleton():
                    animal.collision_np.removeNode()
                    
                # Clean up the attribute
                if hasattr(animal, 'collision_np'):
                    delattr(animal, 'collision_np')
            except Exception:
                # Silent failure for safety - don't crash on cleanup issues
                pass

    def add_projectile(self, projectile: 'Projectile'):
        """Add a projectile to collision detection."""
        if projectile is None:
            return
            
        # Set up collision node and Python tag
        projectile.collision_node.setFromCollideMask(self.ANIMAL_MASK)
        projectile.collision_node.setIntoCollideMask(self.PROJECTILE_MASK)

        # Attach to render and set Python tag
        projectile.collision_np = self.app.render.attachNewNode(projectile.collision_node)
        projectile.collision_np.setPythonTag('projectile', projectile)
        self.traverser.addCollider(projectile.collision_np, self.handler)

    def remove_projectile(self, projectile: 'Projectile'):
        """Remove a projectile from collision detection."""
        if projectile is not None and hasattr(projectile, 'collision_np') and projectile.collision_np:
            try:
                # Try to remove from traverser safely
                if hasattr(projectile.collision_np, 'parent') and projectile.collision_np.parent:
                    self.traverser.removeCollider(projectile.collision_np)
                    
                # Remove the node safely
                if hasattr(projectile.collision_np, 'isSingleton') and projectile.collision_np.isSingleton():
                    projectile.collision_np.removeNode()
                    
                # Clean up the attribute
                if hasattr(projectile, 'collision_np'):
                    delattr(projectile, 'collision_np')
            except Exception:
                # Silent failure for safety - don't crash on cleanup issues
                pass

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
            # Check if render is a valid NodePath (has the expected method for traverse)
            try:
                from panda3d.core import NodePath
                if isinstance(self.app.render, NodePath):
                    self.traverser.traverse(self.app.render)
                else:
                    # Skip traversal if render is not a proper NodePath (test mode)
                    return
            except ImportError:
                # Skip if NodePath import fails (fallback for testing)
                return
        else:
            return  # Cannot perform collision detection without render

        # Process collisions
        for i in range(self.handler.getNumEntries()):
            entry = self.handler.getEntry(i)

            # Get the colliding nodes
            from_node_path = entry.getFromNodePath()
            into_node_path = entry.getIntoNodePath()

            # Retrieve the Python objects from the tags
            projectile = from_node_path.getPythonTag('projectile')
            animal = into_node_path.getPythonTag('animal')

            # Handle cases where from/into might be swapped
            if not projectile or not animal:
                projectile = into_node_path.getPythonTag('projectile')
                animal = from_node_path.getPythonTag('animal')

            # Check if it's a projectile hitting an animal
            if projectile and animal:
                if projectile.active and not animal.is_dead():
                    # Process the hit
                    self._process_hit(projectile, animal)

                    # Mark projectile as inactive
                    projectile.active = False

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