"""
Player module for the 3D Hunting Simulator.
Handles player character, controls, and inventory.
"""

import logging
from panda3d.core import Vec3, Point3, CollisionNode, CollisionSphere, CollisionTraverser, CollisionHandlerQueue
from direct.task import Task
from typing import List, Optional
from physics.collision import CollisionManager, Projectile


class Weapon:
    """Represents a weapon that can shoot projectiles."""

    def __init__(self, name: str = "Rifle", fire_rate: float = 0.5, damage: float = 25.0,
                 projectile_speed: float = 100.0, max_ammo: int = 30, weapon_type: str = "rifle"):
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
        self.weapon_type = weapon_type  # rifle, bow, pistol, etc.
        self.accuracy = 1.0  # Accuracy factor (1.0 = perfect)
        self.range = 100.0  # Maximum effective range
        self.is_scope = weapon_type == "rifle"  # Rifle has scope for zoom
        self.zoom_level = 1.0  # Zoom multiplier (1.0 = normal, 2.0 = zoomed)

    def can_shoot(self, current_time: float) -> bool:
        """Check if weapon can shoot with epsilon for timing precision."""
        if self.reloading or self.current_ammo <= 0:
            return False
        
        # Use epsilon for floating-point comparison
        time_since_last_shot = current_time - self.last_shot_time
        return time_since_last_shot >= self.fire_rate - 0.001

    def shoot(self, position: Point3, direction: Vec3, current_time: float) -> Optional[Projectile]:
        """Attempt to shoot. Returns projectile if successful."""
        if not self.can_shoot(current_time):
            return None

        self.current_ammo -= 1
        self.last_shot_time = current_time

        return Projectile(position, direction, self.projectile_speed, self.damage)

    def reload(self, current_time: float) -> bool:
        """Start reloading if not already reloading."""
        if self.reloading or (self.current_ammo == self.max_ammo and self.max_ammo > 0):
            return False

        self.reloading = True
        self.reload_start_time = current_time
        return True

    def update_reload(self, current_time: float) -> bool:
        """Update reload progress. Returns True if reload completed."""
        if not self.reloading:
            return False

        # Use epsilon for timing precision
        time_elapsed = current_time - self.reload_start_time
        if time_elapsed >= self.reload_time - 0.001:
            self.current_ammo = self.max_ammo
            self.reloading = False
            return True

        return False

    def get_accuracy(self) -> float:
        """Get current accuracy considering zoom and weapon type."""
        if self.is_scope and self.zoom_level > 1.0:
            return self.accuracy * self.zoom_level
        return self.accuracy

    def set_zoom(self, zoom_level: float):
        """Set zoom level for scoped weapons."""
        if self.is_scope:
            self.zoom_level = min(max(zoom_level, 1.0), 3.0)  # Clamp between 1.0 and 3.0


class Inventory:
    """Player inventory system for managing weapons and items."""

    def __init__(self):
        self.weapons: List[Weapon] = []
        self.current_weapon_index = 0
        self.ammo_by_type: Dict[str, int] = {}
        self.items: Dict[str, int] = {}  # Health packs, etc.
        self.max_inventory_slots = 10

    def add_weapon(self, weapon: Weapon) -> bool:
        """Add a weapon to inventory if there's space."""
        if len(self.weapons) >= self.max_inventory_slots:
            return False
        self.weapons.append(weapon)
        return True

    def remove_weapon(self, weapon_index: int) -> Optional[Weapon]:
        """Remove weapon from inventory."""
        if 0 <= weapon_index < len(self.weapons):
            return self.weapons.pop(weapon_index)
        return None

    def switch_weapon(self, direction: int = 1):
        """Switch to next or previous weapon."""
        if not self.weapons:
            return
        
        self.current_weapon_index = (self.current_weapon_index + direction) % len(self.weapons)

    def get_current_weapon(self) -> Optional[Weapon]:
        """Get currently selected weapon."""
        if self.weapons and 0 <= self.current_weapon_index < len(self.weapons):
            return self.weapons[self.current_weapon_index]
        return None

    def add_ammo(self, ammo_type: str, amount: int):
        """Add ammo to inventory."""
        self.ammo_by_type[ammo_type] = self.ammo_by_type.get(ammo_type, 0) + amount

    def get_ammo(self, ammo_type: str) -> int:
        """Get ammo count for specific type."""
        return self.ammo_by_type.get(ammo_type, 0)

    def add_item(self, item_name: str, quantity: int = 1):
        """Add item to inventory."""
        current = self.items.get(item_name, 0)
        self.items[item_name] = current + quantity

    def use_item(self, item_name: str) -> bool:
        """Use an item from inventory."""
        if self.items.get(item_name, 0) > 0:
            self.items[item_name] -= 1
            if self.items[item_name] == 0:
                del self.items[item_name]
            return True
        return False

    def get_item_count(self, item_name: str) -> int:
        """Get count of specific item."""
        return self.items.get(item_name, 0)


class Player:
    """Player character class handling movement, camera, and controls."""

    def __init__(self, app, setup_controls=True):
        """Initialize the player with the Panda3D application."""
        self.app = app
        # Start at a fixed height initially, will be adjusted when terrain is available
        initial_height = 10.0  # Start higher to ensure terrain is visible
        self.position = Point3(0, 0, initial_height)
        self.velocity = Vec3(0, 0, 0)
        self.move_speed = 10.0
        self.sprint_speed = 15.0
        self.sprint_stamina_cost = 0.5  # Stamina per second while sprinting
        self.stamina = 100.0  # Player stamina
        self.max_stamina = 100.0
        self.stamina_regen_rate = 10.0  # Stamina regen per second
        self.is_sprinting = False
        self.mouse_sensitivity = 0.2
        self.camera_distance = 4.0  # Reduced distance for better visibility
        self.health = 100  # Player health
        self.max_health = 100

        # Advanced player attributes
        self.experience = 0
        self.level = 1
        self.hunger = 100.0
        self.thirst = 100.0
        self.hunger_depletion_rate = 0.1  # Per second
        self.thirst_depletion_rate = 0.05  # Per second
        self.hunger_threshold = 20.0
        self.thirst_threshold = 10.0

        # Camera setup - ensure better positioning
        self.camera_node = getattr(self.app, 'camera', None)
        if self.camera_node is not None:
            # Position camera properly - start higher for better visibility
            camera_height = initial_height + 1.0  # Camera slightly above player
            self.camera_node.setPos(0, -self.camera_distance, camera_height)
            self.camera_node.lookAt(self.position)
            # Add slight upward tilt for better view
            self.camera_node.setP(10)  # Tilt up 10 degrees for better terrain visibility
        else:
            logging.warning("Camera not available - running in headless mode")

        # Player model (simple sphere for now)
        self.model = None
        if hasattr(self.app, 'loader') and hasattr(self.app, 'render'):
            try:
                self.model = self.app.loader.loadModel("models/misc/sphere")
                self.model.reparentTo(self.app.render)
                self.model.setPos(self.position)
                self.model.setScale(0.5)
            except Exception as e:
                logging.warning(f"Could not load player model: {e}")
        else:
            logging.warning("Loader or render not available - running in headless mode")

        # Collision setup (always needed for projectiles)
        self.collision_manager = CollisionManager(app)
        self.collision_manager.add_hit_callback(self.on_projectile_hit)

        # Collision setup (only if controls are enabled)
        self.collision_np = None
        self.collision_traverser = None
        self.collision_handler = None

        if setup_controls:
            self.collision_node = CollisionNode('player')
            self.collision_node.addSolid(CollisionSphere(0, 0, 0, 0.5))
            
            if self.model is not None:
                self.collision_np = self.model.attachNewNode(self.collision_node)
                self.collision_traverser = CollisionTraverser('player_traverser')
                self.collision_handler = CollisionHandlerQueue()
                self.collision_traverser.addCollider(self.collision_np, self.collision_handler)
            else:
                logging.warning("Collision system not available - model not loaded")

        # Inventory and weapon system
        self.inventory = Inventory()
        
        # Add default weapons
        rifle = Weapon("Hunting Rifle", fire_rate=0.5, damage=25.0, projectile_speed=150.0, max_ammo=10, weapon_type="rifle")
        pistol = Weapon("Pistol", fire_rate=0.2, damage=15.0, projectile_speed=120.0, max_ammo=15, weapon_type="pistol")
        bow = Weapon("Bow", fire_rate=0.8, damage=20.0, projectile_speed=180.0, max_ammo=5, weapon_type="bow")
        
        self.inventory.add_weapon(rifle)
        self.inventory.add_weapon(pistol)
        self.inventory.add_weapon(bow)
        
        # Add some ammo
        self.inventory.add_ammo("rifle_ammo", 30)
        self.inventory.add_ammo("pistol_ammo", 50)
        self.inventory.add_ammo("arrow", 20)
        
        # Add health items
        self.inventory.add_item("health_potion", 3)
        
        # Current weapon
        self.current_weapon = self.inventory.get_current_weapon()
        
        # Input setup
        if setup_controls:
            self.setup_controls()

    def setup_controls(self):
        """Set up keyboard and mouse controls with advanced features."""
        # Check if we have the necessary components for input
        if not hasattr(self.app, 'accept') or not hasattr(self.app, 'taskMgr'):
            logging.warning("Input system not available - running in headless mode")
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

        # Sprint controls
        self.app.accept('shift', self.toggle_sprint, [True])
        self.app.accept('shift-up', self.toggle_sprint, [False])

        # Weapon switching
        self.app.accept('1', self.switch_to_weapon, [0])
        self.app.accept('2', self.switch_to_weapon, [1])
        self.app.accept('3', self.switch_to_weapon, [2])
        self.app.accept('tab', self.cycle_weapons)

        # Shooting controls
        self.app.accept('mouse1', self.shoot)
        self.app.accept('r', self.reload_weapon)

        # Zoom controls (for scoped weapons)
        self.app.accept('mouse3', self.toggle_zoom, [True])
        self.app.accept('mouse3-up', self.toggle_zoom, [False])

        # Inventory/item controls
        self.app.accept('e', self.use_health_potion)

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
        
        # Additional states
        self.is_zoomed = False

    def toggle_sprint(self, state: bool):
        """Toggle sprint state."""
        if state and self.stamina > 0:
            self.is_sprinting = True
        else:
            self.is_sprinting = False

    def switch_to_weapon(self, index: int):
        """Switch to specific weapon by index."""
        if 0 <= index < len(self.inventory.weapons):
            self.inventory.current_weapon_index = index
            self.current_weapon = self.inventory.get_current_weapon()

    def cycle_weapons(self):
        """Cycle through available weapons."""
        self.inventory.switch_weapon(1)
        self.current_weapon = self.inventory.get_current_weapon()

    def toggle_zoom(self, state: bool):
        """Toggle zoom for scoped weapons."""
        if self.current_weapon and self.current_weapon.is_scope:
            if state:
                self.current_weapon.set_zoom(2.0)
                self.is_zoomed = True
            else:
                self.current_weapon.set_zoom(1.0)
                self.is_zoomed = False

    def use_health_potion(self):
        """Use a health potion from inventory."""
        if self.inventory.use_item("health_potion"):
            self.heal(30.0)
            logging.info("Used health potion!")

    def get_current_ammo(self) -> int:
        """Get current ammo for selected weapon."""
        if self.current_weapon:
            ammo_type = f"{self.current_weapon.weapon_type}_ammo"
            if self.current_weapon.weapon_type == "bow":
                ammo_type = "arrow"
            return self.inventory.get_ammo(ammo_type)
        return 0

    def set_move(self, direction, state):
        """Set movement direction state."""
        self.movement[direction] = state

    def mouse_look(self, task):
        """Handle mouse look for camera rotation with zoom support."""
        if self.camera_node is None:
            return Task.cont

        if hasattr(self.app, 'mouseWatcherNode') and self.app.mouseWatcherNode and self.app.mouseWatcherNode.hasMouse():
            mouse_x = self.app.mouseWatcherNode.getMouseX()
            mouse_y = self.app.mouseWatcherNode.getMouseY()

            # Apply zoom factor to mouse sensitivity
            zoom_factor = self.current_weapon.zoom_level if self.current_weapon else 1.0
            sensitivity = self.mouse_sensitivity * zoom_factor

            # Rotate camera based on mouse movement
            self.camera_node.setH(self.camera_node.getH() - mouse_x * 100 * sensitivity)  # Horizontal: inverted for natural feel
            self.camera_node.setP(self.camera_node.getP() + mouse_y * 100 * sensitivity)  # Vertical: fix inverted Y

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
        """Update player position and handle movement with advanced mechanics."""
        # Update basic needs (hunger, thirst)
        self._update_basic_needs(dt)
        
        # Update stamina
        self._update_stamina(dt)
        
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

        # Apply speed based on sprint and stamina
        current_speed = self.move_speed
        if self.is_sprinting and self.stamina > 0:
            current_speed = self.sprint_speed
            # Consume stamina while sprinting
            stamina_consumption = self.sprint_stamina_cost * dt
            self.stamina = max(0.0, self.stamina - stamina_consumption)

        # Normalize movement direction and apply speed
        if move_dir.length() > 0:
            move_dir.normalize()
            move_dir *= current_speed * dt

        # Update position
        self.position += move_dir
        
        # Prevent player from going below terrain
        terrain_height = self.get_terrain_height(self.position.getX(), self.position.getY())
        if self.position.getZ() < terrain_height + 1.3:  # Player height
            self.position.setZ(terrain_height + 1.3)
            
        if self.model is not None:
            self.model.setPos(self.position)

        # Update camera position to follow player
        if self.camera_node is not None:
            camera_offset = self.camera_node.getQuat().getForward() * -self.camera_distance
            camera_offset.setZ(1.5)  # Keep camera at more natural eye level
            camera_pos = self.position + camera_offset
            
            # Prevent camera from going below terrain
            terrain_height = self.get_terrain_height(camera_pos.getX(), camera_pos.getY())
            if camera_pos.getZ() < terrain_height + 1.5:  # Keep 1.5m above terrain (better visibility)
                camera_pos.setZ(terrain_height + 1.5)
            
            self.camera_node.setPos(camera_pos)

        # Basic collision detection
        if self.collision_traverser is not None and hasattr(self.app, 'render'):
            self.collision_traverser.traverse(self.app.render)
            if self.collision_handler.getNumEntries() > 0:
                # Simple collision response - prevent movement into obstacles
                self.position -= move_dir
                # Ensure player stays above terrain after collision response
                terrain_height = self.get_terrain_height(self.position.getX(), self.position.getY())
                if self.position.getZ() < terrain_height + 1.3:
                    self.position.setZ(terrain_height + 1.3)
                 
                if self.model is not None:
                    self.model.setPos(self.position)
                if self.camera_node is not None:
                    # Re-calculate camera position after collision response
                    camera_offset = self.camera_node.getQuat().getForward() * -self.camera_distance
                    camera_offset.setZ(1.5)
                    camera_pos = self.position + camera_offset
                    
                    # Ensure camera stays above terrain
                    terrain_height = self.get_terrain_height(camera_pos.getX(), camera_pos.getY())
                    if camera_pos.getZ() < terrain_height + 0.5:
                        camera_pos.setZ(terrain_height + 0.5)
                    
                    self.camera_node.setPos(camera_pos)

        # Update weapon reload
        if hasattr(self.app, 'taskMgr') and self.app.taskMgr is not None:
            current_time = self.app.taskMgr.globalClock.getFrameTime()
            if self.current_weapon:
                self.current_weapon.update_reload(current_time)

        # Update collision detection
        if self.collision_manager:
            self.collision_manager.update()

        # Update projectiles
        self.update_projectiles(dt)

    def _update_basic_needs(self, dt: float):
        """Update hunger and thirst levels."""
        # Deplete needs over time
        self.hunger = max(0.0, self.hunger - self.hunger_depletion_rate * dt)
        self.thirst = max(0.0, self.thirst - self.thirst_depletion_rate * dt)
        
        # Check for low needs and apply penalties
        if self.hunger < self.hunger_threshold:
            # Reduce stamina regen when hungry
            self.stamina_regen_rate = 5.0
        else:
            self.stamina_regen_rate = 10.0
            
        if self.thirst < self.thirst_threshold:
            # Reduce movement speed when thirsty
            self.move_speed = 8.0
        else:
            self.move_speed = 10.0

    def _update_stamina(self, dt: float):
        """Update stamina regeneration."""
        # Regenerate stamina when not sprinting
        if not self.is_sprinting and self.stamina < self.max_stamina:
            regen_amount = self.stamina_regen_rate * dt
            self.stamina = min(self.max_stamina, self.stamina + regen_amount)
        # Consume stamina when sprinting (handled in movement)

    def shoot(self):
        """Handle shooting input with advanced weapon mechanics."""
        if self.camera_node is None or not hasattr(self.app, 'taskMgr') or not self.current_weapon:
            return

        current_time = self.app.taskMgr.globalClock.getFrameTime()

        # Check if weapon has ammo
        ammo_type = f"{self.current_weapon.weapon_type}_ammo"
        if self.current_weapon.weapon_type == "bow":
            ammo_type = "arrow"
            
        if self.inventory.get_ammo(ammo_type) <= 0:
            logging.warning(f"Out of {ammo_type}!")
            return

        # Calculate shot origin and direction
        if hasattr(self.app, 'render'):
            shot_origin = self.camera_node.getPos(self.app.render)
        else:
            shot_origin = self.position + Vec3(0, 0, 2)  # Default position if render not available

        shot_direction = self.camera_node.getQuat().getForward()

        # Apply accuracy based on weapon and zoom
        accuracy = self.current_weapon.get_accuracy()
        if accuracy < 1.0:
            # Add spread based on accuracy
            spread = Vec3(
                random.uniform(-0.5, 0.5) * (1.0 - accuracy),
                random.uniform(-0.5, 0.5) * (1.0 - accuracy),
                0
            )
            shot_direction += spread
            shot_direction.normalize()

        # Attempt to shoot
        projectile = self.current_weapon.shoot(shot_origin, shot_direction, current_time)
        if projectile:
            self.projectiles.append(projectile)
            # Add projectile to collision manager
            self.collision_manager.add_projectile(projectile)
            
            # Consume ammo
            self.inventory.add_ammo(ammo_type, -1)
            
            logging.debug(f"Shot fired with {self.current_weapon.name}! Ammo remaining: {self.inventory.get_ammo(ammo_type)}")

    def reload_weapon(self):
        """Handle weapon reload input."""
        if not self.current_weapon or not hasattr(self.app, 'taskMgr'):
            return
            
        current_time = self.app.taskMgr.globalClock.getFrameTime()
        
        # Determine ammo type for current weapon
        ammo_type = f"{self.current_weapon.weapon_type}_ammo"
        if self.current_weapon.weapon_type == "bow":
            ammo_type = "arrow"
            
        # Check if ammo is available for reload
        available_ammo = self.inventory.get_ammo(ammo_type)
        if available_ammo > 0:
            # Transfer ammo from inventory to weapon
            ammo_to_transfer = min(available_ammo, self.current_weapon.max_ammo - self.current_weapon.current_ammo)
            self.current_weapon.current_ammo += ammo_to_transfer
            self.inventory.add_ammo(ammo_type, -ammo_to_transfer)
            
            logging.info(f"Reloaded {self.current_weapon.name} with {ammo_to_transfer} rounds!")
        else:
            logging.warning("No ammo available for reload!")
            
        # Start reload animation
        self.current_weapon.reload(current_time)


    def update_projectiles(self, dt: float):
        """Update all active projectiles with proper memory management."""
        active_projectiles = []

        for projectile in self.projectiles[:]:  # Iterate over copy to avoid modification during iteration
            try:
                if projectile.update(dt):
                    active_projectiles.append(projectile)
                else:
                    # Remove from collision manager before cleanup
                    if self.collision_manager and hasattr(self.collision_manager, 'remove_projectile'):
                        self.collision_manager.remove_projectile(projectile)
                    # Clean up projectile
                    if hasattr(projectile, 'cleanup'):
                        projectile.cleanup()
                    # Clear reference
                    projectile = None
            except Exception:
                # Skip problematic projectiles to prevent crashes
                continue

        self.projectiles = active_projectiles

    def get_projectiles(self) -> List[Projectile]:
        """Get list of active projectiles."""
        return self.projectiles

    def get_inventory(self) -> Inventory:
        """Get player inventory."""
        return self.inventory

    def get_current_weapon(self) -> Optional[Weapon]:
        """Get currently selected weapon."""
        return self.current_weapon

    def get_stamina(self) -> float:
        """Get current stamina level."""
        return self.stamina

    def get_hunger(self) -> float:
        """Get current hunger level."""
        return self.hunger

    def get_thirst(self) -> float:
        """Get current thirst level."""
        return self.thirst

    def eat(self, amount: float):
        """Restore hunger."""
        self.hunger = min(100.0, self.hunger + amount)
        logging.info(f"Ate food! Hunger: {self.hunger:.1f}")

    def drink(self, amount: float):
        """Restore thirst."""
        self.thirst = min(100.0, self.thirst + amount)
        logging.info(f"Drank water! Thirst: {self.thirst:.1f}")

    def level_up(self):
        """Increase player level and stats."""
        self.level += 1
        self.max_health += 10
        self.health = min(self.health + 10, self.max_health)
        self.max_stamina += 10
        self.stamina = min(self.stamina + 10, self.max_stamina)
        self.move_speed += 1.0
        logging.info(f"Level up! Now level {self.level}")

    def on_projectile_hit(self, projectile: Projectile, animal):
        """Handle projectile hitting an animal."""
        # This method is called when a projectile hits an animal
        # Additional effects like sound, particles, etc. can be added here
        logging.debug(f"Hit {animal.species} with {projectile.damage} damage!")

    def take_damage(self, damage: float):
        """Reduce player health by the given amount."""
        self.health = max(0, self.health - damage)
        logging.debug(f"Player took {damage} damage. Health: {self.health}")

        # Check for death
        if self.health <= 0:
            self.die()

    def heal(self, amount: float):
        """Increase player health by the given amount."""
        self.health = min(self.max_health, self.health + amount)
        logging.debug(f"Player healed {amount}. Health: {self.health}")

    def die(self):
        """Handle player death."""
        logging.info("Player died!")
        # Additional death handling can be added here
        # The game over logic is handled in the Game class

    def add_animal_to_collision(self, animal):
        """Add an animal to collision detection."""
        if self.collision_manager:
            self.collision_manager.add_animal(animal)

    def remove_animal_from_collision(self, animal):
        """Remove an animal from collision detection."""
        if self.collision_manager:
            self.collision_manager.remove_animal(animal)

    def get_terrain_height(self, x: float, y: float) -> float:
        """Get terrain height at given coordinates."""
        try:
            if hasattr(self.app, 'game') and self.app.game and hasattr(self.app.game, 'terrain') and self.app.game.terrain:
                return self.app.game.terrain.get_height(x, y)
        except (AttributeError, TypeError, Exception):
            pass
        return 1.0

    def adjust_to_terrain(self):
        """Adjust player position to proper height above terrain once terrain is available."""
        try:
            if hasattr(self.app, 'game') and self.app.game and hasattr(self.app.game, 'terrain') and self.app.game.terrain:
                # Get terrain height at player position
                terrain_height = self.app.game.terrain.get_height(self.position.getX(), self.position.getY())
                
                # Position player above terrain 
                self.position.setZ(terrain_height + 1.8)
                
                # Adjust camera position as well
                if self.camera_node is not None:
                    camera_height = terrain_height + 2.8  # Camera at eye level
                    self.camera_node.setZ(camera_height)
                    
                if self.model is not None:
                    self.model.setPos(self.position)
                    
                logging.info(f"Player adjusted to terrain height: {terrain_height}")
        except Exception as e:
            logging.warning(f"Failed to adjust player to terrain: {e}")

    def cleanup(self):
        """Clean up player resources."""
        # Remove mouse look task
        if hasattr(self.app, 'taskMgr'):
            try:
                self.app.taskMgr.remove('mouse_look')
            except:
                pass  # Task might not exist

        # Clean up player model
        if self.model is not None:
            try:
                self.model.removeNode()
                self.model = None
            except:
                pass  # Model might already be removed

        # Clean up projectiles
        for projectile in self.projectiles[:]:  # Iterate over copy to avoid modification during iteration
            try:
                if self.collision_manager:
                    self.collision_manager.remove_projectile(projectile)
                projectile.cleanup()
            except:
                pass  # Skip problematic projectiles
        self.projectiles.clear()

        # Clean up collision manager
        if self.collision_manager:
            try:
                self.collision_manager.cleanup()
                self.collision_manager = None
            except:
                pass  # Collision manager might already be cleaned up

        # Clean up collision nodes (if any)
        if self.collision_np:
            try:
                self.collision_np.removeNode()
                self.collision_np = None
            except:
                pass

        # Clean up collision traverser and handler
        if self.collision_traverser:
            try:
                self.collision_traverser.clearColliders()
                self.collision_traverser = None
            except:
                pass
        if self.collision_handler:
            try:
                self.collision_handler.clear()
                self.collision_handler = None
            except:
                pass