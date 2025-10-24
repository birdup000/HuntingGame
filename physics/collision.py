#!/usr/bin/env python3
"""
Collision detection module for the collision system.
Handles collision detection between projectiles and game objects.
"""

import logging
from typing import List, Dict, Callable, TYPE_CHECKING
from panda3d.core import CollisionTraverser, CollisionHandlerQueue, CollisionNode, CollisionSphere, BitMask32, Point3, Vec3

if TYPE_CHECKING:
    from animals.animal import Animal


class Projectile:
    """Represents a projectile (bullet) in the collision system."""

    def __init__(self, position: Point3, direction: Vec3, speed: float = 100.0, damage: float = 25.0):
        self.position = position
        self.direction = direction.normalized()
        self.speed = speed
        self.damage = damage
        self.distance_traversed = 0.0
        self.max_range = 500.0
        self.active = True
        self.collision_np = None
        self.collision_node = None
        self.collision_id = None

    def update(self, dt: float) -> bool:
        """Update projectile position. Returns False if projectile should be removed."""
        if not self.active:
            return False

        # Use epsilon for floating-point precision
        EPSILON = 0.001
        
        move_distance = self.speed * dt
        self.position += self.direction * self.speed * dt
        self.distance_traversed += move_distance

        # Check if projectile exceeded max range with epsilon for precision
        if self.distance_traversed >= self.max_range - EPSILON:
            self.active = False
            return False

        return True

    def cleanup(self):
        """Clean up projectile resources."""
        # Clean up collision node if it exists
        if hasattr(self, 'collision_np') and self.collision_np:
            try:
                if hasattr(self.collision_np, 'removeNode'):
                    self.collision_np.removeNode()
                self.collision_np = None
            except Exception as e:
                logging.debug(f"Collision cleanup error: {e}")
                
        # Clear all references
        for attr in ['collision_node', 'collision_id']:
            if hasattr(self, attr):
                setattr(self, attr, None)

    def __del__(self):
        """Destructor to ensure cleanup on garbage collection."""
        self.cleanup()


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
        
        # Reference to game for context
        self.game = None
        
        # Performance tracking
        self.collision_checks = 0
        self.collision_hits = 0

    def add_animal(self, animal: 'Animal'):
        """Add an animal to collision detection."""
        if not animal:
            return
            
        try:
            # Check if animal already has collision node
            if hasattr(animal, 'collision_np') and animal.collision_np:
                self.remove_animal(animal)
                
            # Create collision node for animal
            collision_node = CollisionNode(f"animal_collision_{id(animal)}")
            collision_node.addSolid(CollisionSphere(0, 0, 0, 1.0))  # Simple sphere collision
            collision_node.setFromCollideMask(self.PROJECTILE_MASK)
            collision_node.setIntoCollideMask(BitMask32.allOff())

            # Attach to animal node and set Python tag
            if hasattr(animal, 'node') and animal.node:
                collision_np = animal.node.attachNewNode(collision_node)
                collision_np.setPythonTag('animal', animal)
                self.traverser.addCollider(collision_np, self.handler)
                
                # Store reference
                self.animals[str(id(animal))] = animal
                
        except Exception as e:
            logging.error(f"Error adding animal to collision detection: {e}")

    def remove_animal(self, animal: 'Animal'):
        """Remove an animal from collision detection."""
        if not animal:
            return
            
        try:
            # Remove from tracking
            animal_id = str(id(animal))
            if animal_id in self.animals:
                del self.animals[animal_id]
                
            # Remove collision node
            if hasattr(animal, 'collision_np') and animal.collision_np:
                try:
                    # Remove from traverser
                    if hasattr(self.traverser, 'removeCollider'):
                        self.traverser.removeCollider(animal.collision_np)
                        
                    # Remove the node
                    if hasattr(animal.collision_np, 'removeNode'):
                        animal.collision_np.removeNode()
                        
                    # Clear collision reference
                    if hasattr(animal, 'collision_np'):
                        delattr(animal, 'collision_np')
                        
                except Exception as e:
                    logging.error(f"Error removing animal collision node: {e}")
                    
        except Exception as e:
            logging.error(f"Error in remove_animal: {e}")
            raise

    def add_projectile(self, projectile: 'Projectile'):
        """Add a projectile to collision detection."""
        if not projectile:
            return
            
        try:
            # Set up collision node and Python tag
            # Create collision node for projectile
            collision_node = CollisionNode(f"projectile_collision_{id(projectile)}")
            collision_node.addSolid(CollisionSphere(0, 0, 0, 0.1))  # Small sphere for projectile
            collision_node.setFromCollideMask(self.ANIMAL_MASK)
            collision_node.setIntoCollideMask(self.PROJECTILE_MASK)
            
            projectile.collision_node = collision_node
            
            # Attach to render and set Python tag
            if hasattr(self.app, 'render'):
                projectile.collision_np = self.app.render.attachNewNode(collision_node)
                projectile.collision_np.setPythonTag('projectile', projectile)
                self.traverser.addCollider(projectile.collision_np, self.handler)
                
                # Add to tracking
                projectile.collision_id = str(id(projectile))
                self.projectiles[projectile.collision_id] = projectile
                
        except Exception as e:
            logging.error(f"Error adding projectile to collision detection: {e}")

    def remove_projectile(self, projectile: 'Projectile'):
        """Remove a collision node from collision detection."""
        if not projectile:
            return
            
        try:
            # Remove from tracking
            if hasattr(projectile, 'collision_id') and projectile.collision_id:
                projectile_id = projectile.collision_id
                if projectile_id in self.projectiles:
                    del self.projectiles[projectile_id]
                    
            # Remove collision node
            if projectile.collision_np:
                try:
                    if projectile.collision_np in self.traverser.getColliders():
                        self.traverser.removeCollider(projectile.collision_np)
                        
                    if projectile.collision_np.hasParent():
                        projectile.collision_np.removeNode()
                        
                        # Clear collision reference
                        projectile.collision_np = None
                        
                except Exception as e:
                    logging.error(f"Error removing projectile collision node: {e}")
                    
        except Exception as error:
            logging.error(f"Error in remove_projectile: {error}")
            raise

    def update(self):
        """Update collision detection and process collisions."""
        try:
            # Perform collision detection
            if hasattr(self.app, 'render') and self.app.render:
                self.traverser.traverse(self.app.render)
                
                # Process collisions
                for i in range(self.handler.getNumEntries()):
                    entry = self.handler.getEntry(i)

                    # Get the collision nodes
                    from_node_path = entry.getFromNodePath()
                    into_node_path = entry.getIntoPath()
                    
                    # Validate that we have valid nodes
                    if not from_node_path or not into_node_path:
                        continue

                    # Retrieve projectile and animal from collision nodes
                    projectile = None
                    animal = None
                    
                    # Try to get projectile from either node
                    if from_node_path.hasPythonTag('projectile'):
                        projectile = from_node_path.getPythonTag('projectile')
                    if into_node_path.hasPythonTag('projectile'):
                        projectile = into_node_path.getPythonTag('projectile')
                        
                    # Try to get animal from either node
                    if from_node_path.hasPythonTag('animal'):
                        animal = from_node_path.getPythonTag('animal')
                    if into_node_path.hasPythonTag('animal'):
                        animal = into_node_path.getPythonTag('animal')

                    # Validate that we have both objects
                    if projectile is None or animal is None:
                        continue

                    # Validate that we have proper objects
                    if not (hasattr(projectile, 'active') and hasattr(projectile, 'damage')):
                        continue
                    if not (hasattr(animal, 'is_dead') and callable(animal.is_dead)):
                        continue
                        
                    # Check if this is a valid collision
                    if projectile.active and not animal.is_dead():
                        # Process the collision
                        self._process_collision(projectile, animal)
                        # Mark projectile as inactive
                        projectile.active = False
                        
        except Exception as e:
            logging.error(f"Collision update error: {e}")
            return False

    def _process_collision(self, projectile: 'Projectile', animal: 'Animal'):
        """Process a collision between projectile and animal."""
        try:
            # Apply damage to animal
            animal.take_damage(projectile.damage)
            
            # Notify callbacks
            for callback in self.hit_callbacks:
                callback(projectile, animal)
        except Exception as e:
            logging.error(f"Collision processing error: {e}")
            raise

    def add_hit_callback(self, callback: Callable[['Projectile', 'Animal'], None]):
        """Add a callback function to be called when a projectile hits an animal."""
        if callback not in self.hit_callbacks:
            self.hit_callbacks.append(callback)
            logging.debug(f"Added hit callback: {callback.__name__ if hasattr(callback, '__name__') else 'anonymous'}")

    def remove_hit_callback(self, callback: Callable[['Projectile', 'Animal'], None]):
        """Remove a hit callback function."""
        if callback in self.hit_callbacks:
            self.hit_callbacks.remove(callback)
            logging.debug(f"Removed hit callback: {callback.__name__ if hasattr(callback, '__name__') else 'anonymous'}")

    def cleanup(self):
        """Clean up collision manager resources."""
        try:
            # Clear callbacks
            self.hit_callbacks.clear()
            
            # Clear object references
            self.animals.clear()
            self.projectiles.clear()
            
            # Clear traverser colliders
            if hasattr(self.traverser, 'clearColliders'):
                self.traverser.clearColliders()
                
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")