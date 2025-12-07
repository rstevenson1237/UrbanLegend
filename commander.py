"""
Command executor for Urban Legend.
Translates parsed NLP commands into game actions.
Updated with terrain awareness.
"""

import random
import math
from math import hypot
from map import TILE_SIZE, MAP_PIXEL_W, MAP_PIXEL_H


def dist(a, b):
    return hypot(a[0] - b[0], a[1] - b[1])


class Commander:
    """
    Executes parsed commands, translating NLP output into game actions.
    Respects terrain constraints when issuing movement orders.
    """
    
    def __init__(self, world, ui):
        self.world = world
        self.ui = ui
    
    def execute(self, parsed):
        """Execute a parsed command."""
        action = parsed.get('action')
        group = parsed.get('group')
        target_token = parsed.get('target_entity')
        direction = parsed.get('direction')
        
        self.world.log(f'Parsed: {parsed}')
        
        # Resolve target units
        targets = self._resolve_group(group)
        
        # Override with specific entity if provided
        if target_token:
            ent = self.world.find_unit_by_name(target_token)
            if ent:
                targets = [ent]
        
        if not targets:
            self.ui.log('No valid targets for command')
            return
        
        # Execute action
        if action == 'attack':
            self._execute_attack(targets)
        elif action == 'move':
            self._execute_move(targets, direction)
        elif action == 'scout':
            self._execute_scout(targets, direction)
        elif action == 'hold':
            self._execute_hold(targets)
        elif action == 'retreat':
            self._execute_retreat(targets)
        elif action == 'resupply':
            self._execute_resupply(targets)
        elif action == 'flank':
            self._execute_flank(targets, direction)
        else:
            self.ui.log('Command not understood. Try: attack, move, scout, hold, retreat, resupply, flank')
    
    def _execute_attack(self, targets):
        """Order units to attack nearest enemy."""
        for t in targets:
            enemy = self._nearest_enemy(t)
            if enemy:
                # Calculate attack position (near enemy but in cover if possible)
                attack_pos = self._find_attack_position(t, enemy)
                
                if hasattr(t, 'set_order'):
                    t.set_order('move', attack_pos)
                else:
                    setattr(t, 'target_move', attack_pos)
                
                self.ui.log(f'{self._name(t)} attacking {enemy.name}')
            else:
                self.ui.log(f'No enemy found for {self._name(t)}')
    
    def _execute_move(self, targets, direction):
        """Order units to move to a position."""
        for t in targets:
            base_x, base_y = self._dir_point(direction) if direction else (t.x + 120, t.y)
            
            # Find valid move position
            is_vehicle = hasattr(t, 'vtype')
            tx, ty = self._find_valid_position(base_x, base_y, is_vehicle)
            
            if hasattr(t, 'set_order'):
                t.set_order('move', (tx, ty))
            elif hasattr(t, 'target_pos'):
                t.target_pos = (tx, ty)
            else:
                t.x, t.y = tx, ty
            
            terrain_info = self.world.get_terrain_info(tx, ty)
            self.ui.log(f'{self._name(t)} moving to ({int(tx)},{int(ty)}) - {terrain_info["name"]}')
    
    def _execute_scout(self, targets, direction):
        """Order drones to scout an area."""
        for t in targets:
            if hasattr(t, 'auto_target'):
                # Drones ignore terrain
                tx, ty = self._dir_point(direction) if direction else (t.x + 220, t.y)
                t.auto_target = (tx, ty)
                self.ui.log(f'{self._name(t)} scouting to ({int(tx)},{int(ty)})')
            else:
                self.ui.log(f'{self._name(t)} cannot scout (not a drone)')
    
    def _execute_hold(self, targets):
        """Order units to hold position."""
        for t in targets:
            if hasattr(t, 'set_order'):
                t.set_order('hold', None)
            
            # Report cover status
            if hasattr(t, 'x'):
                cover = self.world.get_cover_at(t.x, t.y)
                cover_str = f' ({int(cover * 100)}% cover)' if cover > 0 else ' (no cover)'
                self.ui.log(f'{self._name(t)} holding position{cover_str}')
            else:
                self.ui.log(f'{self._name(t)} holding position')
    
    def _execute_retreat(self, targets):
        """Order units to retreat to base/spawn."""
        # Find player spawn zone
        player_spawn = self.world.map.get_zone('player_spawn')
        
        if player_spawn:
            home_x = player_spawn['x'] * TILE_SIZE + (player_spawn['width'] * TILE_SIZE) // 2
            home_y = player_spawn['y'] * TILE_SIZE + (player_spawn['height'] * TILE_SIZE) // 2
        else:
            home_x, home_y = 120, 680
        
        for t in targets:
            is_vehicle = hasattr(t, 'vtype')
            tx, ty = self._find_valid_position(home_x, home_y, is_vehicle)
            
            if hasattr(t, 'set_order'):
                t.set_order('move', (tx, ty))
            elif hasattr(t, 'target_pos'):
                t.target_pos = (tx, ty)
            else:
                t.x, t.y = tx, ty
            
            self.ui.log(f'{self._name(t)} retreating to base')
    
    def _execute_resupply(self, targets):
        """Resupply units with ammo."""
        for s in targets:
            if hasattr(s, 'units'):
                moved = 0
                for u in s.units:
                    need = max(0, 60 - u.ammo)
                    u.ammo += need
                    moved += need
                self.ui.log(f'{s.name} resupplied: +{moved} ammo')
            elif hasattr(s, 'ammo'):
                # Vehicle or drone
                max_ammo = 40 if hasattr(s, 'vtype') else 6
                need = max(0, max_ammo - s.ammo)
                s.ammo = max_ammo
                self.ui.log(f'{s.name} resupplied: +{need} ammo')
    
    def _execute_flank(self, targets, direction):
        """Order units to flank the enemy."""
        for t in targets:
            enemy = self._nearest_enemy(t)
            if not enemy:
                self.ui.log(f'No enemy to flank')
                continue
            
            # Calculate flanking position (perpendicular to enemy)
            dx = enemy.x - t.x
            dy = enemy.y - t.y
            d = math.hypot(dx, dy)
            
            if d > 0:
                # Perpendicular vector
                perp_x = -dy / d
                perp_y = dx / d
                
                # Choose flank side based on direction or default right
                flank_dist = 150
                if direction == 'left' or direction == 'west':
                    flank_x = enemy.x - perp_x * flank_dist
                    flank_y = enemy.y - perp_y * flank_dist
                else:
                    flank_x = enemy.x + perp_x * flank_dist
                    flank_y = enemy.y + perp_y * flank_dist
                
                is_vehicle = hasattr(t, 'vtype')
                tx, ty = self._find_valid_position(flank_x, flank_y, is_vehicle)
                
                if hasattr(t, 'set_order'):
                    t.set_order('move', (tx, ty))
                
                self.ui.log(f'{self._name(t)} flanking {enemy.name}')
    
    def _resolve_group(self, group):
        """Resolve group keyword to list of units."""
        if group in (None, 'all'):
            return [s for s in self.world.squads if s.team == 'player']
        
        if group == 'alpha':
            return [s for s in self.world.squads 
                   if s.team == 'player' and s.name.lower().startswith('alpha')]
        
        if group == 'bravo':
            return [s for s in self.world.squads 
                   if s.team == 'player' and s.name.lower().startswith('bravo')]
        
        if group == 'drones':
            return [d for d in self.world.drones if d.team == 'player']
        
        if group == 'vehicles':
            return [v for v in self.world.vehicles if v.team == 'player']
        
        # Default to player squads
        return [s for s in self.world.squads if s.team == 'player']
    
    def _nearest_enemy(self, ent):
        """Find nearest enemy to an entity."""
        enemies = [s for s in self.world.squads if s.team != 'player' and s.units]
        
        if not enemies:
            return None
        
        if hasattr(ent, 'x'):
            return min(enemies, key=lambda e: dist((e.x, e.y), (ent.x, ent.y)))
        
        return random.choice(enemies)
    
    def _dir_point(self, d):
        """Convert direction keyword to map coordinates."""
        # Map boundaries
        max_x = MAP_PIXEL_W - 60
        max_y = MAP_PIXEL_H - 60
        center_x = MAP_PIXEL_W // 2
        center_y = MAP_PIXEL_H // 2
        
        if not d:
            return (center_x, center_y)
        
        directions = {
            'north': (center_x, 60),
            'south': (center_x, max_y),
            'east': (max_x, center_y),
            'west': (60, center_y),
            'left': (60, center_y),
            'right': (max_x, center_y),
            'center': (center_x, center_y),
        }
        
        return directions.get(d, (center_x, center_y))
    
    def _find_valid_position(self, x, y, is_vehicle=False):
        """
        Find a valid position near the requested coordinates.
        Searches nearby tiles if the exact position is impassable.
        """
        # Clamp to map bounds
        x = max(30, min(x, MAP_PIXEL_W - 30))
        y = max(30, min(y, MAP_PIXEL_H - 30))
        
        if self.world.map.is_passable(x, y, is_vehicle):
            return (x, y)
        
        # Search in expanding circles
        for radius in range(1, 10):
            for angle_step in range(8):
                angle = angle_step * (math.pi / 4)
                test_x = x + math.cos(angle) * radius * TILE_SIZE
                test_y = y + math.sin(angle) * radius * TILE_SIZE
                
                if self.world.map.is_passable(test_x, test_y, is_vehicle):
                    return (test_x, test_y)
        
        # Fallback
        return (x, y)
    
    def _find_attack_position(self, attacker, target):
        """
        Find an optimal attack position near the target.
        Prefers positions with cover.
        """
        target_x, target_y = target.x, target.y
        
        # Get direction from attacker to target
        dx = target_x - attacker.x
        dy = target_y - attacker.y
        d = math.hypot(dx, dy)
        
        if d == 0:
            return (target_x, target_y)
        
        # Stop 80 pixels from target
        attack_dist = max(0, d - 80)
        attack_x = attacker.x + (dx / d) * attack_dist
        attack_y = attacker.y + (dy / d) * attack_dist
        
        # Look for nearby cover
        best_pos = (attack_x, attack_y)
        best_cover = self.world.get_cover_at(attack_x, attack_y)
        
        # Check nearby positions for better cover
        for offset_x in range(-2, 3):
            for offset_y in range(-2, 3):
                test_x = attack_x + offset_x * TILE_SIZE
                test_y = attack_y + offset_y * TILE_SIZE
                
                is_vehicle = hasattr(attacker, 'vtype')
                if self.world.map.is_passable(test_x, test_y, is_vehicle):
                    cover = self.world.get_cover_at(test_x, test_y)
                    if cover > best_cover:
                        best_cover = cover
                        best_pos = (test_x, test_y)
        
        return best_pos
    
    def _name(self, ent):
        """Get display name for an entity."""
        return getattr(ent, 'name', str(ent))
