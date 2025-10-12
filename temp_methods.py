def setup_lighting(self):
        """Set up realistic lighting for the scene."""
        # Lighting is now handled by DynamicLighting class
        # This method kept for backward compatibility
        pass

    def _apply_terrain_materials(self):
        """Apply PBR materials to terrain based on height and conditions."""
        if not self.terrain or not self.terrain.terrain_node:
            return
            
        # Sample terrain heights to determine material zones
        terrain_size = config.TERRAIN_CONFIG['width']
        
        # Apply different materials to terrain patches based on height
        for x in range(-terrain_size//4, terrain_size//4, 10):
            for y in range(-terrain_size//4, terrain_size//4, 10):
                height = self.terrain.get_height(x, y)
                material = self.terrain_pbr.get_material_for_height(height)
                
                # Create material region
                region_node = self.terrain.terrain_node.find(f"**/terrain_patch_{x}_{y}")
                if not region_node.isEmpty():
                    material.apply_to(region_node)
                else:
                    # Apply to all terrain children
                    material.apply_to(self.terrain.terrain_node)
        
        print("PBR materials applied to terrain")

    def _setup_grass_fields(self):
        """Create and position grass fields for enhanced realism."""
        terrain_cfg = config.TERRAIN_CONFIG
        
        # Create multiple grass fields across the terrain
        field_configs = [
            {'width': 40, 'height': 30, 'density': 500},
            {'width': 30, 'height': 25, 'density': 300},
            {'width': 35, 'height': 20, 'density': 400}
        ]
        
        for i, cfg in enumerate(field_configs):
            field = GrassField(
                width=cfg['width'],
                height=cfg['height'], 
                density=cfg['density'],
                render_node=self.app.render
            )
            
            # Position fields around the map
            positions = [(30, 30), (-30, 20), (0, -25)]
            if i < len(positions):
                field.generate_field()
                field.grass_node.setPos(positions[i][0], positions[i][1], 0)
                self.foliage_renderer.add_grass_field(field)
        
        print(f"Created {len(field_configs)} grass fields with {sum(c['density'] for c in field_configs)} grass blades")

    def update(self, task):
        """Update game state each frame."""
        if not self.is_running:
            return task.done

        # Calculate delta time
        current_time = self.app.taskMgr.globalClock.getFrameTime()
        if self.last_time == 0:
            dt = 0.016  # Default 60 FPS
        else:
            dt = current_time - self.last_time
        self.last_time = current_time

        # Only update game components if actively playing
        if self.game_state == 'playing':
            # Update advanced graphics systems
            self._update_graphics_systems(dt)
            
            # Update game components
            if self.player:
                self.player.update(dt)

            # Update animals
            player_pos = self.player.position if self.player else Vec3(0, 0, 0)
            alive_animals = []

            for animal in self.animals:
                terrain_height = self.terrain.get_height(animal.position.x, animal.position.y) if self.terrain else 0.0
                animal.update(dt, player_pos, terrain_height)

                if not animal.is_dead():
                    alive_animals.append(animal)
                else:
                    # Handle animal death - add score
                    self.handle_animal_killed(animal)
                    # Remove dead animal from collision detection
                    if self.player:
                        self.player.remove_animal_from_collision(animal)
                    animal.cleanup()

            self.animals = alive_animals

            # Check for game over conditions (e.g., player health)
            if self.player and hasattr(self.player, 'health') and self.player.health <= 0:
                self.game_over()

        # Update UI regardless of game state
        if self.ui_manager:
            self.ui_manager.update_hud(dt)

        # Render the scene (Panda3D handles this automatically)
        # Additional rendering setup can be done here if needed

        return task.cont
        
    def _update_graphics_systems(self, dt):
        """Update advanced graphics systems for photorealistic rendering."""
        if not hasattr(self, 'game_time'):
            self.game_time = 0.0
            
        self.game_time += dt
        
        # Update dynamic lighting
        # Simulate time progression (1 minute = 1 real second)
        virtual_hour = (self.game_time * 0.016) % 24
        self.dynamic_lighting.update_time_of_day(virtual_hour)
        
        # Update weather system
        self.weather_system.update_weather(dt)
        
        # Adjust lighting for current weather
        # Get weather intensities safely
        precipitation = getattr(self.weather_system, 'precipitation', None)
        rain_intensity = precipitation.intensity if precipitation else 0
        
        fog_effect = getattr(self.weather_system, 'fog_effect', None)
        fog_density = fog_effect.density if fog_effect else 0
        self.dynamic_lighting.adjust_for_weather(rain_intensity, fog_density)
        
        # Update terrain LOD and materials
        if self.player and self.terrain:
            player_pos = self.player.position
            self.terrain_renderer.update_lod(player_pos)
            
            # Update terrain materials based on weather
            if self.weather_system.current_weather == 'rain':
                self.terrain.apply_dynamic_materials(player_pos)
        
        # Update foliage systems
        self.foliage_renderer.update(dt, self.game_time)
        
        # Track player movement for interactive foliage
        if self.player:
            player_pos = self.player.position
            player_speed = getattr(self.player, 'velocity', Vec3(0, 0, 0)).length()
            self.foliage_renderer.player_moved(player_pos, player_speed)
            
        # Track animal movement for interactive foliage
        for animal in self.animals:
            if not animal.is_dead():
                self.foliage_renderer.animal_moved(animal.position, getattr(animal, 'species', 'unknown'))

    def stop(self):
        """Stop the game loop."""
        self.is_running = False
        if self.player:
            self.player.cleanup()

        # Clean up animals
        for animal in self.animals:
            animal.cleanup()
        self.animals.clear()

        # Clean up terrain
        if self.terrain:
            self.terrain.cleanup()

        # Clean up UI
        if self.ui_manager:
            self.ui_manager.cleanup()

        print("Hunting Simulator Game Stopped")

    def handle_animal_killed(self, animal):
        """Handle when an animal is killed - update score and statistics."""
        if self.ui_manager and self.ui_manager.hud:
            # Award points based on animal type
            points = 10  # Base points
            if hasattr(animal, 'species'):
                if animal.species.lower() == 'deer':
                    points = 50
                elif animal.species.lower() == 'rabbit':
                    points = 25

            self.ui_manager.add_score(points)
            self.ui_manager.record_shot(hit=True)
            self.ui_manager.show_message(f"{animal.species} killed! +{points} points", 2.0)

    def cleanup_game(self):
        """Clean up current game session for restart."""
        # Clean up animals
        for animal in self.animals:
            if self.player:
                self.player.remove_animal_from_collision(animal)
            animal.cleanup()
        self.animals.clear()

        # Clean up player
        if self.player:
            self.player.cleanup()
            self.player = None

        # Clean up terrain
        if self.terrain:
            self.terrain.cleanup()
            self.terrain = None

        # Reset UI but keep the manager
        if self.ui_manager:
            self.ui_manager.hide_menus()
            if hasattr(self.ui_manager, 'hud') and self.ui_manager.hud:
                self.ui_manager.hud.cleanup()
                self.ui_manager.hud = None
