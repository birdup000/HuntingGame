"""
Player module for the 3D Hunting Simulator.
Handles player character, controls, and inventory.
"""

from panda3d.core import Vec3, Point3, CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerQueue, CollisionRay, BitMask32
from direct.task import Task
from typing import List, Optional
import math
from physics.collision import CollisionManager, Projectile


class Weapon:
    """Represents a weapon that can shoot projectiles."""

    def __init__(self, name: str = "Rifle", fire_rate: float = 0.5, damage: float = 25.0,
                 projectile_speed: float = 100.0, max_ammo: int = 30):
        self.name = name
        self.fire_rate = fire_rate  # Time between shots
        self.damage = damage
        self.projectile_speed = projectile_speed
        self.max_ammo = max_ammo
        self.current_ammo = max_ammo
        self.last_shot_time = 0.0
        self.reloading = False
        self.reload_time = 2.0
        self.reload_start_time = 0.0

    def can_shoot(self, current_time: float) -> bool:
        """Check if weapon can shoot."""
        if self.reloading or self.current_ammo <= 0:
            return False
        return current_time - self.last_shot_time >= self.fire_rate

    def shoot(self, position: Point3, direction: Vec3, current_time: float) -> Optional[Projectile]:
        """Attempt to shoot. Returns projectile if successful."""
        if not self.can_shoot(current_time):
            return None

        self.current_ammo -= 1
        self.last_shot_time = current_time

        return Projectile(position, direction, self.projectile_speed, self.damage)

    def reload(self, current_time: float) -> bool:
        """Start reloading if not already reloading."""
        if self.reloading or self.current_ammo == self.max_ammo:
            return False

        self.reloading = True
        self.reload_start_time = current_time
        return True

    def update_reload(self, current_time: float) -> bool:
        """Update reload progress. Returns True if reload completed."""
        if not self.reloading:
            return False

        if current_time - self.reload_start_time >= self.reload_time:
            self.current_ammo = self.max_ammo
            self.reloading = False
            return True

        return False


class Player:
    """Player character class handling movement, camera, and controls."""

    def __init__(self, app, setup_controls=True):
        """Initialize the player with the Panda3D application."""
        self.app = app
        self.position = Point3(0, 0, 1)  # Starting position
        self.velocity = Vec3(0, 0, 0)
        self.move_speed = 10.0
        self.mouse_sensitivity = 0.2
        self.camera_distance = 5.0
        self.health = 100  # Player health
        self.max_health = 100

        # Camera setup
        self.camera_node = getattr(self.app, 'camera', None)
        if self.camera_node is not None:
            self.camera_node.setPos(0, -self.camera_distance, 2)
            self.camera_node.lookAt(self.position)
        else:
            print("Warning: Camera not available - running in headless mode")

        # Player model (simple sphere for now)
        self.model = None
        if hasattr(self.app, 'loader') and hasattr(self.app, 'render'):
            try:
                self.model = self.app.loader.loadModel("models/misc/sphere")
                self.model.reparentTo(self.app.render)
                self.model.setPos(self.position)
                self.model.setScale(0.5)
            except Exception as e:
                print(f"Warning: Could not load player model: {e}")
        else:
            print("Warning: Loader or render not available - running in headless mode")

        # Collision setup
        self.collision_node = CollisionNode('player')
        self.collision_node.addSolid(CollisionSphere(0, 0, 0, 0.5))
        self.collision_np = None
        self.collision_traverser = None
        self.collision_handler = None

        if self.model is not None:
            self.collision_np = self.model.attachNewNode(self.collision_node)
            self.collision_traverser = CollisionTraverser('player_traverser')
            self.collision_handler = CollisionHandlerQueue()
            self.collision_traverser.addCollider(self.collision_np, self.collision_handler)
        else:
            print("Warning: Collision system not available - model not loaded")

        # Weapon and shooting setup
        self.weapon = Weapon("Hunting Rifle", fire_rate=0.5, damage=25.0, projectile_speed=150.0, max_ammo=10)
        self.projectiles: List[Projectile] = []
        self.collision_manager = CollisionManager(app)
        self.collision_manager.add_hit_callback(self.on_projectile_hit)

        # Input setup
        if setup_controls:
            self.setup_controls()

    def setup_controls(self):
        """Set up keyboard and mouse controls."""
        # Check if we have the necessary components for input
        if not hasattr(self.app, 'accept') or not hasattr(self.app, 'taskMgr'):
            print("Warning: Input system not available - running in headless mode")
            self.movement = {
                'forward': False,
                'backward': False,
                'left': False,
                'right': False
            }
            return

        # Keyboard controls
        self.app.accept('w', self.set_move, ['forward', True])
        self.app.accept('w-up', self.set_move, ['forward', False])
        self.app.accept('s', self.set_move, ['backward', True])
        self.app.accept('s-up', self.set_move, ['backward', False])
        self.app.accept('a', self.set_move, ['left', True])
        self.app.accept('a-up', self.set_move, ['left', False])
        self.app.accept('d', self.set_move, ['right', True])
        self.app.accept('d-up', self.set_move, ['right', False])

        # Shooting controls
        self.app.accept('mouse1', self.shoot)
        self.app.accept('r', self.reload_weapon)

        # Mouse controls
        if hasattr(self.app, 'disableMouse'):
            self.app.disableMouse()
        if hasattr(self.app, 'taskMgr'):
            self.app.taskMgr.add(self.mouse_look, 'mouse_look')

        # Movement state
        self.movement = {
            'forward': False,
            'backward': False,
            'left': False,
            'right': False
        }

    def set_move(self, direction, state):
        """Set movement direction state."""
        self.movement[direction] = state

    def mouse_look(self, task):
        """Handle mouse look for camera rotation."""
        if self.camera_node is None:
            return Task.cont

        if hasattr(self.app, 'mouseWatcherNode') and self.app.mouseWatcherNode and self.app.mouseWatcherNode.hasMouse():
            mouse_x = self.app.mouseWatcherNode.getMouseX()
            mouse_y = self.app.mouseWatcherNode.getMouseY()

            # Rotate camera based on mouse movement
            self.camera_node.setH(self.camera_node.getH() - mouse_x * 100 * self.mouse_sensitivity)
            self.camera_node.setP(self.camera_node.getP() - mouse_y * 100 * self.mouse_sensitivity)

            # Clamp pitch to prevent flipping
            if self.camera_node.getP() > 90:
                self.camera_node.setP(90)
            elif self.camera_node.getP() < -90:
                self.camera_node.setP(-90)

            # Reset mouse to center
            if hasattr(self.app, 'win'):
                self.app.win.movePointer(0, self.app.win.getXSize() // 2, self.app.win.getYSize() // 2)

        return Task.cont

    def update(self, dt):
        """Update player position and handle movement."""
        # Calculate movement direction based on camera orientation
        move_dir = Vec3(0, 0, 0)

        if self.camera_node is not None:
            if self.movement['forward']:
                move_dir += self.camera_node.getQuat().getForward()
            if self.movement['backward']:
                move_dir -= self.camera_node.getQuat().getForward()
            if self.movement['left']:
                move_dir -= self.camera_node.getQuat().getRight()
            if self.movement['right']:
                move_dir += self.camera_node.getQuat().getRight()

        # Normalize movement direction and apply speed
        if move_dir.length() > 0:
            move_dir.normalize()
            move_dir *= self.move_speed * dt

        # Update position
        self.position += move_dir
        if self.model is not None:
            self.model.setPos(self.position)

        # Update camera position to follow player
        if self.camera_node is not None:
            camera_offset = self.camera_node.getQuat().getForward() * -self.camera_distance
            camera_offset.setZ(2)  # Keep camera at eye level
            self.camera_node.setPos(self.position + camera_offset)

        # Basic collision detection
        if self.collision_traverser is not None and hasattr(self.app, 'render'):
            self.collision_traverser.traverse(self.app.render)
            if self.collision_handler.getNumEntries() > 0:
                # Simple collision response - prevent movement into obstacles
                self.position -= move_dir
                if self.model is not None:
                    self.model.setPos(self.position)
                if self.camera_node is not None:
                    self.camera_node.setPos(self.position + camera_offset)

        # Update weapon reload
        if hasattr(self.app, 'taskMgr') and self.app.taskMgr is not None:
            self.weapon.update_reload(self.app.taskMgr.globalClock.getFrameTime())

        # Update collision detection
        self.collision_manager.update()

        # Update projectiles
        self.update_projectiles(dt)

    def shoot(self):
        """Handle shooting input."""
        if self.camera_node is None or not hasattr(self.app, 'taskMgr'):
            return

        current_time = self.app.taskMgr.globalClock.getFrameTime()

        # Calculate shot origin and direction
        if hasattr(self.app, 'render'):
            shot_origin = self.camera_node.getPos(self.app.render)
        else:
            shot_origin = self.position + Vec3(0, 0, 2)  # Default position if render not available

        shot_direction = self.camera_node.getQuat().getForward()

        # Attempt to shoot
        projectile = self.weapon.shoot(shot_origin, shot_direction, current_time)
        if projectile:
            self.projectiles.append(projectile)
            # Add projectile to collision manager
            self.collision_manager.add_projectile(projectile)

    def reload_weapon(self):
        """Handle weapon reload input."""
        if hasattr(self.app, 'taskMgr'):
            current_time = self.app.taskMgr.globalClock.getFrameTime()
            self.weapon.reload(current_time)

    def update_projectiles(self, dt: float):
        """Update all active projectiles."""
        active_projectiles = []

        for projectile in self.projectiles:
            if projectile.update(dt):
                active_projectiles.append(projectile)
            else:
                # Remove from collision manager before cleanup
                self.collision_manager.remove_projectile(projectile)
                projectile.cleanup()

        self.projectiles = active_projectiles

    def get_projectiles(self) -> List[Projectile]:
        """Get list of active projectiles."""
        return self.projectiles

    def on_projectile_hit(self, projectile: Projectile, animal):
        """Handle projectile hitting an animal."""
        # This method is called when a projectile hits an animal
        # Additional effects like sound, particles, etc. can be added here
        print(f"Hit {animal.species} with {projectile.damage} damage!")

    def take_damage(self, damage: float):
        """Reduce player health by the given amount."""
        self.health = max(0, self.health - damage)
        print(f"Player took {damage} damage. Health: {self.health}")

        # Check for death
        if self.health <= 0:
            self.die()

    def heal(self, amount: float):
        """Increase player health by the given amount."""
        self.health = min(self.max_health, self.health + amount)
        print(f"Player healed {amount}. Health: {self.health}")

    def die(self):
        """Handle player death."""
        print("Player died!")
        # Additional death handling can be added here
        # The game over logic is handled in the Game class

    def add_animal_to_collision(self, animal):
        """Add an animal to collision detection."""
        self.collision_manager.add_animal(animal)

    def remove_animal_from_collision(self, animal):
        """Remove an animal from collision detection."""
        self.collision_manager.remove_animal(animal)

    def cleanup(self):
        """Clean up player resources."""
        if hasattr(self.app, 'taskMgr'):
            self.app.taskMgr.remove('mouse_look')

        if self.model is not None:
            self.model.removeNode()

        # Clean up projectiles
        for projectile in self.projectiles:
            self.collision_manager.remove_projectile(projectile)
            projectile.cleanup()
        self.projectiles.clear()

        # Clean up collision manager
        self.collision_manager.cleanup()