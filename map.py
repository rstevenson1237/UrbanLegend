"""
Map & Terrain System for Urban Legend
Phase 1.1 Implementation

Provides:
- Tile-based terrain with multiple terrain types
- Cover mechanics with damage reduction
- Building interiors with entry points
- Line-of-sight blocking
- Multiple map layouts
"""

import json
import os
from enum import Enum, auto
from typing import List, Tuple, Optional, Dict, Any

# Map dimensions (must align with MAP_W=960, HEIGHT=780)
TILE_SIZE = 32
MAP_TILES_X = 30  # 960 / 32
MAP_TILES_Y = 24  # 768 / 32 (leaves 12px for UI at bottom)
MAP_PIXEL_W = TILE_SIZE * MAP_TILES_X  # 960
MAP_PIXEL_H = TILE_SIZE * MAP_TILES_Y  # 768


class TerrainType(Enum):
    """Terrain types with associated properties."""
    OPEN = auto()       # Default terrain, no modifiers
    COVER = auto()      # Light cover (sandbags, cars, debris)
    URBAN = auto()      # Dense urban - heavy cover, slow movement
    WATER = auto()      # Impassable for infantry, some vehicles
    IMPASSABLE = auto() # Walls, solid buildings exterior
    ROAD = auto()       # Fast movement for vehicles
    BUILDING_FLOOR = auto()  # Inside a building


# Terrain properties lookup
TERRAIN_PROPERTIES = {
    TerrainType.OPEN: {
        'name': 'Open Ground',
        'cover_bonus': 0.0,        # Damage reduction multiplier
        'movement_cost': 1.0,      # Movement speed multiplier (lower = slower)
        'infantry_passable': True,
        'vehicle_passable': True,
        'blocks_los': False,       # Line of sight blocking
        'color': (20, 35, 20),     # Dark green-gray
    },
    TerrainType.COVER: {
        'name': 'Light Cover',
        'cover_bonus': 0.3,        # 30% damage reduction
        'movement_cost': 0.85,
        'infantry_passable': True,
        'vehicle_passable': True,
        'blocks_los': False,
        'color': (40, 50, 35),     # Slightly lighter
    },
    TerrainType.URBAN: {
        'name': 'Heavy Cover',
        'cover_bonus': 0.5,        # 50% damage reduction
        'movement_cost': 0.6,
        'infantry_passable': True,
        'vehicle_passable': False,
        'blocks_los': False,
        'color': (50, 55, 60),     # Gray urban
    },
    TerrainType.WATER: {
        'name': 'Water',
        'cover_bonus': 0.0,
        'movement_cost': 0.3,
        'infantry_passable': False,
        'vehicle_passable': False,  # Could be True for amphibious
        'blocks_los': False,
        'color': (15, 40, 70),     # Dark blue
    },
    TerrainType.IMPASSABLE: {
        'name': 'Impassable',
        'cover_bonus': 1.0,        # Full cover (can't be hit through)
        'movement_cost': 0.0,
        'infantry_passable': False,
        'vehicle_passable': False,
        'blocks_los': True,
        'color': (30, 30, 35),     # Dark gray
    },
    TerrainType.ROAD: {
        'name': 'Road',
        'cover_bonus': 0.0,
        'movement_cost': 1.3,      # Faster on roads
        'infantry_passable': True,
        'vehicle_passable': True,
        'blocks_los': False,
        'color': (45, 45, 50),     # Asphalt gray
    },
    TerrainType.BUILDING_FLOOR: {
        'name': 'Building Interior',
        'cover_bonus': 0.4,        # Good cover inside
        'movement_cost': 0.8,
        'infantry_passable': True,
        'vehicle_passable': False,
        'blocks_los': False,       # Can see inside once entered
        'color': (55, 50, 45),     # Interior brown-gray
    },
}


class Building:
    """
    Represents an enterable building structure.
    Buildings have an exterior (impassable walls) and interior (floor tiles).
    Entry points allow units to move inside.
    """
    
    def __init__(self, building_id: str, x: int, y: int, width: int, height: int,
                 entry_points: List[Tuple[int, int]] = None, name: str = None):
        """
        Args:
            building_id: Unique identifier
            x, y: Top-left corner in tile coordinates
            width, height: Size in tiles
            entry_points: List of (tile_x, tile_y) positions that allow entry
            name: Display name
        """
        self.id = building_id
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.name = name or f"Building_{building_id}"
        self.entry_points = entry_points or []
        self.units_inside: List[str] = []  # Track unit IDs inside
        
    def contains_tile(self, tx: int, ty: int) -> bool:
        """Check if a tile coordinate is within this building's bounds."""
        return (self.x <= tx < self.x + self.width and 
                self.y <= ty < self.y + self.height)
    
    def is_entry_point(self, tx: int, ty: int) -> bool:
        """Check if a tile is an entry point."""
        return (tx, ty) in self.entry_points
    
    def is_wall_tile(self, tx: int, ty: int) -> bool:
        """Check if a tile is part of the building's walls (perimeter, non-entry)."""
        if not self.contains_tile(tx, ty):
            return False
        # Perimeter check
        is_perimeter = (tx == self.x or tx == self.x + self.width - 1 or
                        ty == self.y or ty == self.y + self.height - 1)
        return is_perimeter and not self.is_entry_point(tx, ty)
    
    def is_interior_tile(self, tx: int, ty: int) -> bool:
        """Check if a tile is inside the building (not a wall)."""
        if not self.contains_tile(tx, ty):
            return False
        return not self.is_wall_tile(tx, ty) or self.is_entry_point(tx, ty)
    
    def get_center_pixel(self) -> Tuple[float, float]:
        """Get the pixel coordinates of the building's center."""
        cx = (self.x + self.width / 2) * TILE_SIZE
        cy = (self.y + self.height / 2) * TILE_SIZE
        return (cx, cy)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for save/load."""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'name': self.name,
            'entry_points': self.entry_points,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Building':
        """Deserialize from dictionary."""
        return cls(
            building_id=data['id'],
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height'],
            name=data.get('name'),
            entry_points=[tuple(ep) for ep in data.get('entry_points', [])],
        )


class Map:
    """
    The game map containing terrain tiles and buildings.
    Provides methods for querying terrain, cover, and pathability.
    """
    
    def __init__(self, name: str = "default", width: int = MAP_TILES_X, height: int = MAP_TILES_Y):
        self.name = name
        self.width = width
        self.height = height
        
        # Initialize all tiles as OPEN
        self.tiles: List[List[TerrainType]] = [
            [TerrainType.OPEN for _ in range(width)] for _ in range(height)
        ]
        
        self.buildings: Dict[str, Building] = {}
        
        # Zones for special areas (spawn points, objectives, etc.)
        self.zones: Dict[str, Dict[str, Any]] = {}
        
    def get_tile(self, tx: int, ty: int) -> TerrainType:
        """Get terrain type at tile coordinates."""
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.tiles[ty][tx]
        return TerrainType.IMPASSABLE  # Out of bounds
    
    def set_tile(self, tx: int, ty: int, terrain: TerrainType) -> None:
        """Set terrain type at tile coordinates."""
        if 0 <= tx < self.width and 0 <= ty < self.height:
            self.tiles[ty][tx] = terrain
    
    def get_terrain_at_pixel(self, px: float, py: float) -> TerrainType:
        """Get terrain type at pixel coordinates."""
        tx = int(px // TILE_SIZE)
        ty = int(py // TILE_SIZE)
        return self.get_tile(tx, ty)
    
    def pixel_to_tile(self, px: float, py: float) -> Tuple[int, int]:
        """Convert pixel coordinates to tile coordinates."""
        return (int(px // TILE_SIZE), int(py // TILE_SIZE))
    
    def tile_to_pixel(self, tx: int, ty: int, center: bool = True) -> Tuple[float, float]:
        """Convert tile coordinates to pixel coordinates."""
        if center:
            return (tx * TILE_SIZE + TILE_SIZE / 2, ty * TILE_SIZE + TILE_SIZE / 2)
        return (tx * TILE_SIZE, ty * TILE_SIZE)
    
    def get_cover_bonus(self, px: float, py: float) -> float:
        """
        Get the cover bonus (damage reduction) at pixel coordinates.
        Returns a value between 0.0 (no cover) and 1.0 (full cover).
        """
        terrain = self.get_terrain_at_pixel(px, py)
        return TERRAIN_PROPERTIES[terrain]['cover_bonus']
    
    def get_movement_cost(self, px: float, py: float) -> float:
        """
        Get movement cost multiplier at pixel coordinates.
        Higher values = faster movement. 0 = impassable.
        """
        terrain = self.get_terrain_at_pixel(px, py)
        return TERRAIN_PROPERTIES[terrain]['movement_cost']
    
    def is_passable(self, px: float, py: float, is_vehicle: bool = False) -> bool:
        """Check if a pixel position is passable for infantry or vehicles."""
        terrain = self.get_terrain_at_pixel(px, py)
        props = TERRAIN_PROPERTIES[terrain]
        if is_vehicle:
            return props['vehicle_passable']
        return props['infantry_passable']
    
    def is_tile_passable(self, tx: int, ty: int, is_vehicle: bool = False) -> bool:
        """Check if a tile is passable for infantry or vehicles."""
        terrain = self.get_tile(tx, ty)
        props = TERRAIN_PROPERTIES[terrain]
        if is_vehicle:
            return props['vehicle_passable']
        return props['infantry_passable']
    
    def blocks_los(self, px: float, py: float) -> bool:
        """Check if a pixel position blocks line of sight."""
        terrain = self.get_terrain_at_pixel(px, py)
        return TERRAIN_PROPERTIES[terrain]['blocks_los']
    
    def check_line_of_sight(self, x1: float, y1: float, x2: float, y2: float,
                            step_size: float = 16.0) -> bool:
        """
        Check if there's a clear line of sight between two points.
        Uses simple ray stepping (not pixel-perfect but efficient).
        Returns True if LOS is clear, False if blocked.
        """
        import math
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        
        if dist < step_size:
            return True
        
        steps = int(dist / step_size)
        for i in range(1, steps):
            t = i / steps
            check_x = x1 + dx * t
            check_y = y1 + dy * t
            if self.blocks_los(check_x, check_y):
                return False
        
        return True
    
    def add_building(self, building: Building) -> None:
        """Add a building to the map and update terrain tiles accordingly."""
        self.buildings[building.id] = building
        
        # Set wall and floor tiles
        for ty in range(building.y, building.y + building.height):
            for tx in range(building.x, building.x + building.width):
                if building.is_wall_tile(tx, ty):
                    self.set_tile(tx, ty, TerrainType.IMPASSABLE)
                elif building.is_interior_tile(tx, ty):
                    self.set_tile(tx, ty, TerrainType.BUILDING_FLOOR)
    
    def get_building_at(self, px: float, py: float) -> Optional[Building]:
        """Get the building at a pixel position, if any."""
        tx, ty = self.pixel_to_tile(px, py)
        for building in self.buildings.values():
            if building.contains_tile(tx, ty):
                return building
        return None
    
    def add_zone(self, zone_id: str, zone_type: str, x: int, y: int, 
                 width: int, height: int, **properties) -> None:
        """
        Add a named zone to the map.
        Zones can be spawn points, objectives, extraction points, etc.
        """
        self.zones[zone_id] = {
            'type': zone_type,
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            **properties
        }
    
    def get_zone(self, zone_id: str) -> Optional[Dict[str, Any]]:
        """Get a zone by ID."""
        return self.zones.get(zone_id)
    
    def get_zones_by_type(self, zone_type: str) -> List[Dict[str, Any]]:
        """Get all zones of a specific type."""
        return [z for z in self.zones.values() if z['type'] == zone_type]
    
    def fill_rect(self, x: int, y: int, width: int, height: int, terrain: TerrainType) -> None:
        """Fill a rectangular area with a terrain type."""
        for ty in range(y, min(y + height, self.height)):
            for tx in range(x, min(x + width, self.width)):
                self.set_tile(tx, ty, terrain)
    
    def draw_road(self, points: List[Tuple[int, int]], width: int = 2) -> None:
        """Draw a road connecting a series of tile points."""
        import math
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            
            # Bresenham-style line with width
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            sx = 1 if x1 < x2 else -1
            sy = 1 if y1 < y2 else -1
            err = dx - dy
            
            x, y = x1, y1
            while True:
                # Draw road tile with width
                for wy in range(-(width // 2), (width + 1) // 2):
                    for wx in range(-(width // 2), (width + 1) // 2):
                        self.set_tile(x + wx, y + wy, TerrainType.ROAD)
                
                if x == x2 and y == y2:
                    break
                    
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    x += sx
                if e2 < dx:
                    err += dx
                    y += sy
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize map to dictionary for save/load."""
        # Convert tiles to simple integer representation
        tile_data = [[t.value for t in row] for row in self.tiles]
        
        return {
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'tiles': tile_data,
            'buildings': [b.to_dict() for b in self.buildings.values()],
            'zones': self.zones,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Map':
        """Deserialize map from dictionary."""
        game_map = cls(
            name=data['name'],
            width=data['width'],
            height=data['height']
        )
        
        # Restore tiles
        for ty, row in enumerate(data['tiles']):
            for tx, val in enumerate(row):
                game_map.tiles[ty][tx] = TerrainType(val)
        
        # Restore buildings
        for b_data in data.get('buildings', []):
            building = Building.from_dict(b_data)
            game_map.buildings[building.id] = building
        
        # Restore zones
        game_map.zones = data.get('zones', {})
        
        return game_map
    
    def save_to_file(self, filepath: str) -> None:
        """Save map to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'Map':
        """Load map from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


# =============================================================================
# Pre-defined Map Layouts
# =============================================================================

def create_map_urban_district() -> Map:
    """
    Urban District - Dense city environment with multiple buildings.
    Good for close-quarters combat with lots of cover.
    """
    game_map = Map(name="Urban District")
    
    # Main road running north-south through center
    game_map.draw_road([(15, 0), (15, 23)], width=3)
    
    # Cross road east-west
    game_map.draw_road([(0, 12), (29, 12)], width=2)
    
    # Western building block - apartment complex
    game_map.add_building(Building(
        'apt_west_1', x=2, y=2, width=6, height=5,
        entry_points=[(4, 6), (7, 4)],
        name="West Apartments"
    ))
    
    # Eastern building block - office building
    game_map.add_building(Building(
        'office_east', x=20, y=2, width=7, height=6,
        entry_points=[(20, 5), (23, 7)],
        name="East Office"
    ))
    
    # Southern warehouse
    game_map.add_building(Building(
        'warehouse_south', x=3, y=16, width=8, height=5,
        entry_points=[(6, 16), (10, 18)],
        name="South Warehouse"
    ))
    
    # Northeast small buildings
    game_map.add_building(Building(
        'shop_ne_1', x=22, y=14, width=4, height=3,
        entry_points=[(22, 15)],
        name="Corner Shop"
    ))
    
    game_map.add_building(Building(
        'shop_ne_2', x=22, y=18, width=5, height=4,
        entry_points=[(22, 20)],
        name="Market"
    ))
    
    # Scatter cover (debris, cars, sandbags)
    cover_positions = [
        (10, 5), (10, 6), (11, 5),  # Debris pile
        (18, 8), (19, 8),            # Parked cars
        (5, 10), (5, 11),            # Sandbags
        (25, 10), (26, 10),          # More cover
        (8, 14), (9, 14),            # Street barriers
        (18, 18), (18, 19), (19, 18), # Rubble
    ]
    for tx, ty in cover_positions:
        game_map.set_tile(tx, ty, TerrainType.COVER)
    
    # Heavy urban cover (dense rubble)
    urban_positions = [
        (12, 3), (12, 4),
        (27, 8), (28, 8),
        (1, 14), (1, 15),
    ]
    for tx, ty in urban_positions:
        game_map.set_tile(tx, ty, TerrainType.URBAN)
    
    # Define zones
    game_map.add_zone('player_spawn', 'spawn', x=1, y=20, width=4, height=3, team='player')
    game_map.add_zone('enemy_spawn', 'spawn', x=25, y=1, width=4, height=3, team='enemy')
    game_map.add_zone('objective_a', 'capture', x=14, y=10, width=3, height=3, name='Town Square')
    
    return game_map


def create_map_industrial_zone() -> Map:
    """
    Industrial Zone - Open areas with scattered heavy cover.
    Mix of long sightlines and choke points.
    """
    game_map = Map(name="Industrial Zone")
    
    # Main access road
    game_map.draw_road([(0, 6), (20, 6), (20, 18), (29, 18)], width=2)
    
    # Large factory building (northwest)
    game_map.add_building(Building(
        'factory_main', x=1, y=1, width=10, height=4,
        entry_points=[(5, 4), (10, 2)],
        name="Main Factory"
    ))
    
    # Storage silos (impassable cylinders - represented as small impassable areas)
    for i, (sx, sy) in enumerate([(14, 2), (17, 2), (14, 5), (17, 5)]):
        game_map.fill_rect(sx, sy, 2, 2, TerrainType.IMPASSABLE)
    
    # Eastern warehouse complex
    game_map.add_building(Building(
        'warehouse_east', x=22, y=1, width=6, height=7,
        entry_points=[(22, 4), (25, 7)],
        name="East Warehouse"
    ))
    
    # Southern processing plant
    game_map.add_building(Building(
        'processing', x=4, y=14, width=8, height=6,
        entry_points=[(7, 14), (11, 17)],
        name="Processing Plant"
    ))
    
    # Water/cooling pond
    game_map.fill_rect(15, 12, 5, 4, TerrainType.WATER)
    
    # Scattered industrial cover
    cover_positions = [
        (12, 9), (13, 9), (12, 10),   # Crates
        (23, 10), (24, 10), (25, 10), # Pipe stacks
        (1, 10), (2, 10),             # Barrels
        (18, 20), (19, 20), (20, 20), # Equipment
        (8, 8), (8, 9),               # Machinery
    ]
    for tx, ty in cover_positions:
        game_map.set_tile(tx, ty, TerrainType.COVER)
    
    # Heavy cover / rubble
    urban_positions = [
        (26, 14), (27, 14), (26, 15),
        (3, 8), (4, 8),
    ]
    for tx, ty in urban_positions:
        game_map.set_tile(tx, ty, TerrainType.URBAN)
    
    # Zones
    game_map.add_zone('player_spawn', 'spawn', x=1, y=8, width=3, height=4, team='player')
    game_map.add_zone('enemy_spawn', 'spawn', x=24, y=14, width=4, height=4, team='enemy')
    game_map.add_zone('objective_a', 'capture', x=14, y=8, width=4, height=3, name='Central Yard')
    game_map.add_zone('extraction', 'extraction', x=26, y=20, width=3, height=3, name='Extraction Point')
    
    return game_map


def create_map_riverside() -> Map:
    """
    Riverside - Split map with river, bridges create choke points.
    Forces tactical decisions about crossing points.
    """
    game_map = Map(name="Riverside")
    
    # River running north-south (slightly diagonal)
    for ty in range(game_map.height):
        river_x = 14 + (ty // 6)  # Slight eastward drift
        game_map.fill_rect(river_x, ty, 3, 1, TerrainType.WATER)
    
    # Bridges (road over water)
    bridge_positions = [(14, 5), (15, 5), (16, 5),
                        (15, 11), (16, 11), (17, 11),
                        (16, 18), (17, 18), (18, 18)]
    for tx, ty in bridge_positions:
        game_map.set_tile(tx, ty, TerrainType.ROAD)
    
    # Roads connecting to bridges
    game_map.draw_road([(0, 5), (14, 5)], width=2)
    game_map.draw_road([(16, 5), (29, 5)], width=2)
    game_map.draw_road([(0, 11), (15, 11)], width=2)
    game_map.draw_road([(17, 11), (29, 11)], width=2)
    
    # West side buildings
    game_map.add_building(Building(
        'house_w1', x=2, y=1, width=5, height=3,
        entry_points=[(4, 3)],
        name="River House W1"
    ))
    
    game_map.add_building(Building(
        'house_w2', x=1, y=14, width=6, height=4,
        entry_points=[(3, 14), (6, 16)],
        name="River House W2"
    ))
    
    game_map.add_building(Building(
        'bunker_w', x=8, y=8, width=4, height=3,
        entry_points=[(11, 9)],
        name="West Bunker"
    ))
    
    # East side buildings
    game_map.add_building(Building(
        'house_e1', x=22, y=1, width=5, height=4,
        entry_points=[(22, 3)],
        name="River House E1"
    ))
    
    game_map.add_building(Building(
        'compound_e', x=20, y=14, width=7, height=6,
        entry_points=[(20, 17), (24, 19)],
        name="East Compound"
    ))
    
    # Cover on both sides
    west_cover = [(5, 7), (6, 7), (10, 3), (3, 20), (4, 20), (11, 15)]
    east_cover = [(20, 7), (21, 7), (25, 9), (22, 21), (23, 21), (27, 3)]
    
    for tx, ty in west_cover + east_cover:
        game_map.set_tile(tx, ty, TerrainType.COVER)
    
    # Heavy cover near bridges (defensive positions)
    bridge_cover = [(12, 4), (12, 5), (18, 5), (18, 6),
                    (13, 10), (13, 11), (19, 11), (19, 12),
                    (14, 17), (14, 18), (20, 18), (20, 19)]
    for tx, ty in bridge_cover:
        game_map.set_tile(tx, ty, TerrainType.URBAN)
    
    # Zones
    game_map.add_zone('player_spawn', 'spawn', x=1, y=8, width=3, height=4, team='player')
    game_map.add_zone('enemy_spawn', 'spawn', x=26, y=8, width=3, height=4, team='enemy')
    game_map.add_zone('bridge_north', 'control', x=14, y=4, width=3, height=3, name='North Bridge')
    game_map.add_zone('bridge_center', 'control', x=15, y=10, width=3, height=3, name='Center Bridge')
    game_map.add_zone('bridge_south', 'control', x=16, y=17, width=3, height=3, name='South Bridge')
    
    return game_map


def create_map_open_fields() -> Map:
    """
    Open Fields - Large open area with minimal cover.
    Tests maneuvering and use of limited cover. Good for vehicle combat.
    """
    game_map = Map(name="Open Fields")
    
    # Perimeter road
    game_map.draw_road([(2, 2), (27, 2), (27, 21), (2, 21), (2, 2)], width=2)
    
    # Central crossroads
    game_map.draw_road([(2, 11), (27, 11)], width=2)
    game_map.draw_road([(14, 2), (14, 21)], width=2)
    
    # Small outpost buildings at corners
    game_map.add_building(Building(
        'outpost_nw', x=4, y=4, width=3, height=3,
        entry_points=[(6, 5)],
        name="NW Outpost"
    ))
    
    game_map.add_building(Building(
        'outpost_ne', x=23, y=4, width=3, height=3,
        entry_points=[(23, 5)],
        name="NE Outpost"
    ))
    
    game_map.add_building(Building(
        'outpost_sw', x=4, y=17, width=3, height=3,
        entry_points=[(6, 18)],
        name="SW Outpost"
    ))
    
    game_map.add_building(Building(
        'outpost_se', x=23, y=17, width=3, height=3,
        entry_points=[(23, 18)],
        name="SE Outpost"
    ))
    
    # Central structure
    game_map.add_building(Building(
        'central', x=12, y=9, width=5, height=5,
        entry_points=[(12, 11), (16, 11), (14, 9), (14, 13)],
        name="Central Command"
    ))
    
    # Scattered light cover (trenches, foxholes, hay bales)
    cover_spots = [
        (8, 6), (9, 6),
        (20, 6), (21, 6),
        (8, 16), (9, 16),
        (20, 16), (21, 16),
        (6, 11), (7, 11),
        (22, 11), (23, 11),
        (14, 6), (14, 7),
        (14, 16), (14, 17),
    ]
    for tx, ty in cover_spots:
        game_map.set_tile(tx, ty, TerrainType.COVER)
    
    # Zones
    game_map.add_zone('player_spawn', 'spawn', x=1, y=10, width=2, height=4, team='player')
    game_map.add_zone('enemy_spawn', 'spawn', x=27, y=10, width=2, height=4, team='enemy')
    game_map.add_zone('objective_center', 'capture', x=13, y=10, width=3, height=3, name='Command Center')
    
    return game_map


# Registry of available maps
MAP_REGISTRY = {
    'urban_district': create_map_urban_district,
    'industrial_zone': create_map_industrial_zone,
    'riverside': create_map_riverside,
    'open_fields': create_map_open_fields,
}


def get_map(map_name: str) -> Map:
    """Get a map by name from the registry."""
    if map_name in MAP_REGISTRY:
        return MAP_REGISTRY[map_name]()
    raise ValueError(f"Unknown map: {map_name}. Available: {list(MAP_REGISTRY.keys())}")


def list_maps() -> List[str]:
    """List all available map names."""
    return list(MAP_REGISTRY.keys())
