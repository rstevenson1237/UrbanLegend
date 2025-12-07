# Urban Legend - Alpha 1.2.0 (Terrain System)

A futuristic squad command game with natural language controls and tactical terrain.

**Copyright (c) 2025 rstevenson1237**  
Licensed under CC BY-NC-ND 4.0 (Non-Commercial, No Derivatives)  
See LICENSE file for details.

---

## What's New in 1.2.0

### Terrain System
- **Tile-based map** with multiple terrain types
- **Cover mechanics** - Units in cover take reduced damage
- **Buildings** - Enterable structures with defined entry points
- **Line of sight** - Walls and buildings block visibility
- **4 unique maps** - Urban District, Industrial Zone, Riverside, Open Fields

### Terrain Types
| Type | Cover | Movement | Notes |
|------|-------|----------|-------|
| Open Ground | 0% | Normal | Default terrain |
| Light Cover | 30% | Slightly slow | Debris, sandbags, cars |
| Heavy Cover | 50% | Slow | Dense rubble, urban |
| Road | 0% | Fast | Vehicle bonus |
| Water | 0% | Impassable | Infantry cannot cross |
| Building Floor | 40% | Slow | Inside buildings |
| Walls | 100% | Impassable | Blocks line of sight |

---

## Quick Start

```bash
# Install dependencies
pip3 install pygame

# Run the game
python3 main.py
```

---

## Controls

### Keyboard
| Key | Action |
|-----|--------|
| **Left Click** | Select unit |
| **Right Click** | Move selected unit |
| **Enter** | Submit command |
| **Space** | Pause/Unpause |
| **F** | Toggle fast mode |
| **G** | Toggle grid overlay |
| **M** | Cycle through maps |
| **D** | Control drone |
| **V** | Control vehicle |
| **S** | Save game |
| **L** | Load game |
| **Escape** | Exit |

### Natural Language Commands
Type commands in the input box and press Enter:

```
Alpha squad move north
All units attack
Drone 1 scout east
Tanks hold position
Everyone fall back
Alpha flank right
map industrial_zone
```

---

## Available Maps

### Urban District
Dense city environment with multiple buildings, roads, and scattered cover. Good for close-quarters combat.

### Industrial Zone  
Open areas with scattered heavy cover, factories, and a water feature. Mix of long sightlines and choke points.

### Riverside
Split map with river running through center. Bridges create natural choke points for tactical decisions.

### Open Fields
Large open area with minimal cover. Tests maneuvering and use of limited cover positions.

---

## Files

```
urban_legend/
├── main.py           # Entry point
├── world.py          # Game state & logic
├── map.py            # NEW: Terrain system
├── units.py          # Unit classes with cover
├── nlp_parser.py     # Command parser
├── commander.py      # Command executor
├── ui.py             # HUD with terrain display
├── tutorial.py       # Guided tutorial
├── save_load.py      # Save/load with map data
├── requirements.txt  # Dependencies
├── LICENSE           # CC BY-NC-ND 4.0
└── README.md         # This file
```

---

## Game Mechanics

### Cover System
- Units automatically use cover based on terrain
- Cover bonus shown in unit info panel
- Hover over terrain to see cover percentage
- Some weapons (explosives, drones) ignore cover

### Combat
- Squads engage automatically when in range
- Line of sight required for combat
- Damage reduced by target's cover bonus
- Morale affects combat effectiveness

### Movement
- Infantry can traverse most terrain
- Vehicles restricted to roads and open areas
- Movement speed affected by terrain type
- Buildings require entry through doorways

---

## Tips

1. **Use cover** - Position squads in covered positions before engaging
2. **Watch sightlines** - Buildings block line of sight
3. **Flank enemies** - Attack from multiple angles for advantage
4. **Control bridges** - On Riverside map, bridges are key chokepoints
5. **Use drones** - Drones ignore terrain and attack from above

---

## Development Roadmap

- [x] Phase 1.1: Map & Terrain System
- [ ] Phase 1.2: Pathfinding (A*)
- [ ] Phase 1.3: Enhanced Unit Abilities
- [ ] Phase 1.4: Advanced Enemy AI
- [ ] Phase 1.5: Mission & Objective System

---

## License

This work is licensed under Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International.

You may share and redistribute, but you may not use commercially or create derivative works.
