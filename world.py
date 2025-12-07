import random
import time
from collections import deque
from units import Squad, Unit, Drone, Vehicle
from map import Map, get_map, list_maps, TILE_SIZE, TerrainType, TERRAIN_PROPERTIES


class World:
    """
    Game world state containing map, units, and game logic.
    Integrates terrain system for cover and movement.
    """
    
    def __init__(self, map_name: str = 'urban_district'):
        self.squads = []
        self.drones = []
        self.vehicles = []
        self.log_lines = deque(maxlen=500)
        self.tick = 0.0
        self.paused = False
        self.fast = False
        
        # Initialize map
        self.map = get_map(map_name)
        self.log(f'Map loaded: {self.map.name}')
        
        self.init_forces()
        self.log('World created')
    
    def init_forces(self):
        """Initialize player and enemy forces using map spawn zones."""
        # Get spawn zones from map
        player_spawn = self.map.get_zone('player_spawn')
        enemy_spawn = self.map.get_zone('enemy_spawn')
        
        # Default spawn positions if zones not defined
        if player_spawn:
            px = player_spawn['x'] * TILE_SIZE + (player_spawn['width'] * TILE_SIZE) // 2
            py = player_spawn['y'] * TILE_SIZE + (player_spawn['height'] * TILE_SIZE) // 2
        else:
            px, py = 160, 400
        
        if enemy_spawn:
            ex = enemy_spawn['x'] * TILE_SIZE + (enemy_spawn['width'] * TILE_SIZE) // 2
            ey = enemy_spawn['y'] * TILE_SIZE + (enemy_spawn['height'] * TILE_SIZE) // 2
        else:
            ex, ey = 800, 200
        
        # Create player squads near spawn
        for i in range(3):
            spawn_x = px + (i - 1) * 60 + random.randint(-20, 20)
            spawn_y = py + (i % 2) * 50 + random.randint(-20, 20)
            
            # Ensure spawn position is valid
            spawn_x, spawn_y = self._find_valid_spawn(spawn_x, spawn_y, is_vehicle=False)
            
            s = Squad(f'Alpha_{i+1}', 'player', x=spawn_x, y=spawn_y)
            for j in range(random.randint(8, 14)):
                s.add_unit(Unit(f'P_{i+1}_{j+1}', 'player'))
            self.squads.append(s)
        
        # Create player vehicles
        for i in range(2):
            vx = px + 40 + i * 50
            vy = py + 100
            vx, vy = self._find_valid_spawn(vx, vy, is_vehicle=True)
            self.vehicles.append(Vehicle(f'APC_{i+1}', 'player', x=vx, y=vy, vtype='APC'))
        
        # Create player drones
        for i in range(2):
            dx = px + 60 + i * 40
            dy = py + 130
            self.drones.append(Drone(f'Drone_{i+1}', 'player', x=dx, y=dy))
        
        # Create enemy squads near enemy spawn
        for i in range(4):
            spawn_x = ex + (i - 2) * 45 + random.randint(-15, 15)
            spawn_y = ey + (i % 3) * 80 + random.randint(-15, 15)
            spawn_x, spawn_y = self._find_valid_spawn(spawn_x, spawn_y, is_vehicle=False)
            
            s = Squad(f'Enemy_{i+1}', 'enemy', x=spawn_x, y=spawn_y)
            for j in range(random.randint(9, 18)):
                s.add_unit(Unit(f'E_{i+1}_{j+1}', 'enemy'))
            self.squads.append(s)
        
        # Enemy vehicles
        for i in range(1):
            vx = ex + 20 + i * 40
            vy = ey + 80
            vx, vy = self._find_valid_spawn(vx, vy, is_vehicle=True)
            self.vehicles.append(Vehicle(f'Tank_E{i+1}', 'enemy', x=vx, y=vy, vtype='Tank'))
        
        # Enemy drones
        for i in range(1):
            self.drones.append(Drone(f'Drone_E{i+1}', 'enemy', x=ex + 30, y=ey + 140))
    
    def _find_valid_spawn(self, x: float, y: float, is_vehicle: bool, 
                          max_attempts: int = 20) -> tuple:
        """
        Find a valid spawn position near the requested coordinates.
        Searches outward in a spiral pattern if initial position is invalid.
        """
        if self.map.is_passable(x, y, is_vehicle):
            return (x, y)
        
        # Search in expanding circles
        for radius in range(1, max_attempts):
            for angle_step in range(8):
                import math
                angle = angle_step * (math.pi / 4)
                test_x = x + math.cos(angle) * radius * TILE_SIZE
                test_y = y + math.sin(angle) * radius * TILE_SIZE
                
                if self.map.is_passable(test_x, test_y, is_vehicle):
                    return (test_x, test_y)
        
        # Fallback to original position
        return (x, y)
    
    def change_map(self, map_name: str) -> bool:
        """
        Change to a different map. Clears existing units and reinitializes.
        Returns True on success, False if map not found.
        """
        try:
            self.map = get_map(map_name)
            self.squads.clear()
            self.drones.clear()
            self.vehicles.clear()
            self.init_forces()
            self.log(f'Map changed to: {self.map.name}')
            return True
        except ValueError as e:
            self.log(f'Failed to change map: {e}')
            return False
    
    def update(self, dt: float):
        """Update game state by one time step."""
        if self.paused:
            return
        
        steps = 4 if self.fast else 1
        for _ in range(steps):
            for s in list(self.squads):
                s.update(dt, self)
            for d in list(self.drones):
                d.update(dt, self)
            for v in list(self.vehicles):
                v.update(dt, self)
            self.enemy_ai_step()
            self.tick += dt
    
    def enemy_ai_step(self):
        """Simple enemy AI behavior."""
        enemies = [s for s in self.squads if s.team == 'enemy' and s.units]
        targets = [s for s in self.squads if s.team == 'player' and s.units]
        
        if not enemies or not targets:
            return
        
        if random.random() < 0.02:
            e = random.choice(enemies)
            t = random.choice(targets)
            
            # Find a valid move target (considering terrain)
            target_x = t.x + random.randint(-30, 30)
            target_y = t.y + random.randint(-30, 30)
            target_x, target_y = self._find_valid_spawn(target_x, target_y, is_vehicle=False)
            
            e.set_order('move', (target_x, target_y))
            self.log(f'Enemy {e.name} maneuvers toward {t.name}')
    
    def log(self, txt: str):
        """Add a message to the game log."""
        ts = time.strftime('%H:%M:%S')
        self.log_lines.appendleft(f'[{ts}] {txt}')
        print(f'[{ts}] {txt}')
    
    def find_unit_by_name(self, token: str):
        """Find a unit by name using fuzzy matching."""
        token = token.lower()
        names = [e.name.lower() for e in (self.squads + self.vehicles + self.drones)]
        
        from difflib import get_close_matches
        matches = get_close_matches(token, names, n=1, cutoff=0.5)
        
        if matches:
            m = matches[0]
            for e in (self.squads + self.vehicles + self.drones):
                if e.name.lower() == m:
                    return e
        return None
    
    def get_cover_at(self, x: float, y: float) -> float:
        """Get cover bonus at a position (convenience wrapper)."""
        return self.map.get_cover_bonus(x, y)
    
    def get_terrain_info(self, x: float, y: float) -> dict:
        """Get full terrain information at a pixel position."""
        terrain = self.map.get_terrain_at_pixel(x, y)
        props = TERRAIN_PROPERTIES[terrain]
        return {
            'type': terrain,
            'name': props['name'],
            'cover_bonus': props['cover_bonus'],
            'movement_cost': props['movement_cost'],
            'infantry_passable': props['infantry_passable'],
            'vehicle_passable': props['vehicle_passable'],
        }
    
    def check_los(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        """Check line of sight between two points."""
        return self.map.check_line_of_sight(x1, y1, x2, y2)
    
    def get_units_in_zone(self, zone_id: str) -> list:
        """Get all units within a named zone."""
        zone = self.map.get_zone(zone_id)
        if not zone:
            return []
        
        zone_x = zone['x'] * TILE_SIZE
        zone_y = zone['y'] * TILE_SIZE
        zone_w = zone['width'] * TILE_SIZE
        zone_h = zone['height'] * TILE_SIZE
        
        units_in_zone = []
        for squad in self.squads:
            if (zone_x <= squad.x < zone_x + zone_w and
                zone_y <= squad.y < zone_y + zone_h):
                units_in_zone.append(squad)
        
        for vehicle in self.vehicles:
            if (zone_x <= vehicle.x < zone_x + zone_w and
                zone_y <= vehicle.y < zone_y + zone_h):
                units_in_zone.append(vehicle)
        
        for drone in self.drones:
            if (zone_x <= drone.x < zone_x + zone_w and
                zone_y <= drone.y < zone_y + zone_h):
                units_in_zone.append(drone)
        
        return units_in_zone
