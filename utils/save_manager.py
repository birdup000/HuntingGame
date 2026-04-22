"""
Save Manager for the 3D Hunting Simulator.
Handles save/load game state to JSON files.
"""

import json
import logging
import os
from typing import Dict, Any, Optional


class SaveManager:
    """Manages game save and load functionality."""

    def __init__(self, save_dir: str = 'saves'):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def _slot_path(self, slot: int) -> str:
        return os.path.join(self.save_dir, f'save_{slot}.json')

    def save_game(self, game, slot: int = 1) -> bool:
        """Save current game state to a slot."""
        try:
            data: Dict[str, Any] = {
                'version': 1,
                'slot': slot,
                'difficulty': getattr(game, 'difficulty', 'normal'),
                'game_time': getattr(game, 'game_time', 0.0),
            }

            # Save player state
            player = getattr(game, 'player', None)
            if player:
                data['player'] = {
                    'position': [player.position.x, player.position.y, player.position.z],
                    'health': player.health,
                    'max_health': player.max_health,
                    'stamina': player.stamina,
                    'hunger': player.hunger,
                    'thirst': player.thirst,
                    'experience': player.experience,
                    'level': player.level,
                    'ammo': dict(player.inventory.ammo_by_type),
                    'items': dict(player.inventory.items),
                    'current_weapon_index': player.inventory.current_weapon_index,
                }

            # Save animal counts
            animals = getattr(game, 'animals', [])
            data['animals'] = {
                'total_spawned': len(animals),
                'alive_counts': {}
            }
            for animal in animals:
                species = getattr(animal, 'species', 'unknown')
                if not getattr(animal, 'is_dead', lambda: True)():
                    data['animals']['alive_counts'][species] = data['animals']['alive_counts'].get(species, 0) + 1

            # Save HUD stats
            hud = getattr(getattr(game, 'ui_manager', None), 'hud', None)
            if hud:
                data['stats'] = {
                    'score': hud.score,
                    'kills': hud.kills,
                    'shots_fired': hud.shots_fired,
                    'shots_hit': hud.shots_hit
                }

            with open(self._slot_path(slot), 'w') as f:
                json.dump(data, f, indent=2)
            logging.info(f"Game saved to slot {slot}")
            return True
        except Exception as e:
            logging.error(f"Failed to save game: {e}")
            return False

    def load_game(self, game, slot: int = 1) -> bool:
        """Load game state from a slot."""
        path = self._slot_path(slot)
        if not os.path.exists(path):
            logging.warning(f"No save file found in slot {slot}")
            return False

        try:
            with open(path, 'r') as f:
                data = json.load(f)

            # Apply difficulty
            if 'difficulty' in data:
                game.difficulty = data['difficulty']

            # Apply player state
            player = getattr(game, 'player', None)
            if player and 'player' in data:
                p = data['player']
                pos = p.get('position', [0, 0, 0])
                player.position.setX(pos[0])
                player.position.setY(pos[1])
                player.position.setZ(pos[2])
                player.health = p.get('health', 100)
                player.max_health = p.get('max_health', 100)
                player.stamina = p.get('stamina', 100)
                player.hunger = p.get('hunger', 100)
                player.thirst = p.get('thirst', 100)
                player.experience = p.get('experience', 0)
                player.level = p.get('level', 1)
                player.inventory.ammo_by_type = dict(p.get('ammo', {}))
                player.inventory.items = dict(p.get('items', {}))
                player.inventory.current_weapon_index = p.get('current_weapon_index', 0)
                player.current_weapon = player.inventory.get_current_weapon()

            # Apply HUD stats
            hud = getattr(getattr(game, 'ui_manager', None), 'hud', None)
            if hud and 'stats' in data:
                s = data['stats']
                hud.score = s.get('score', 0)
                hud.kills = s.get('kills', 0)
                hud.shots_fired = s.get('shots_fired', 0)
                hud.shots_hit = s.get('shots_hit', 0)

            logging.info(f"Game loaded from slot {slot}")
            return True
        except Exception as e:
            logging.error(f"Failed to load game: {e}")
            return False

    def has_save(self, slot: int = 1) -> bool:
        return os.path.exists(self._slot_path(slot))

    def list_saves(self) -> Dict[int, Dict[str, Any]]:
        saves = {}
        for slot in range(1, 4):
            path = self._slot_path(slot)
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    saves[slot] = {
                        'difficulty': data.get('difficulty', 'normal'),
                        'game_time': data.get('game_time', 0.0),
                        'score': data.get('stats', {}).get('score', 0)
                    }
                except Exception:
                    pass
        return saves

    def delete_save(self, slot: int = 1) -> bool:
        path = self._slot_path(slot)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except Exception as e:
                logging.error(f"Failed to delete save: {e}")
        return False
