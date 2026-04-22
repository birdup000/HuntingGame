# 3D Hunting Simulator

A fully-featured 3D hunting simulation game built with Python and Panda3D. Track, stalk, and harvest wildlife across procedurally generated terrain with dynamic weather, day/night cycles, and realistic ballistics.

## Features

- **Procedural Terrain**: Infinite variety with OpenSimplex noise-generated landscapes, rivers, hills, and forests
- **Realistic Ballistics**: Bullet drop, weapon sway, recoil, and scoped zoom
- **Dynamic Wildlife AI**: Deer, rabbits, bears, wolves, and birds with distinct behaviors — fleeing, foraging, resting, and pack hunting
- **Predator Danger**: Bears and wolves will attack if you get too close
- **Day/Night Cycle**: Full 24-hour lighting with dawn, noon, dusk, and night visuals
- **Dynamic Weather**: Clear, rain, snow, and fog that affect visibility and animal behavior
- **Stamina & Survival System**: Manage hunger, thirst, and stamina while exploring
- **Weapon Arsenal**: Hunting rifle, pistol, and bow with unique ballistics and ammo types
- **Difficulty Levels**: Easy, Normal, Hard, and Extreme modes
- **Save/Load System**: Auto-save every 5 minutes + manual F9/F10 quicksave
- **Score & Progression**: Points per kill, accuracy tracking, and harvest objectives
- **PBR Graphics**: Physically-based rendering, dynamic lighting, SSAO, bloom, and FXAA

## Controls

| Key | Action |
|-----|--------|
| W/A/S/D | Move |
| Shift | Sprint |
| Space | Jump |
| C | Crouch |
| Mouse | Look around |
| Left Click | Shoot |
| Right Click (hold) | Zoom / ADS |
| R | Reload |
| 1/2/3 | Switch weapon |
| Tab | Cycle weapons |
| E | Use health potion |
| Escape | Pause Menu |
| F5 | Toggle debug lights |
| F9 | Quick Save |
| F10 | Quick Load |

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Requirements

- Python 3.8+
- Panda3D
- NumPy
- OpenSimplex
- Pygame (optional, for additional audio)

## Gameplay Tips

- **Crouch** to reduce noise and avoid spooking animals
- **Watch the wind** — animals can smell you if you're downwind
- **Aim for headshots** — they deal more damage and preserve meat quality
- **Bears and wolves are dangerous** — keep your distance or be ready to fight
- **Manage your stamina** — sprinting drains it fast, and low stamina reduces accuracy
- **Hunt at dawn and dusk** — animals are most active during these times

## License

Open source — hunt responsibly.
