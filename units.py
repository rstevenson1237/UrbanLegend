"""
Unit classes for Urban Legend.
Updated with cover mechanics and terrain-aware movement.
"""

import random
import math

def clamp(v, a, b):
    return max(a, min(b, v))


class Unit:
    """Individual soldier unit within a squad."""
    
    def __init__(self, uid, team='player', x=0, y=0):
        self.id = uid
        self.name = uid
        self.team = team
        self.x = x
        self.y = y
        self.hp = 100
        self.max_hp = 100
        self.ammo = random.randint(20, 60)
        self.morale = random.uniform(0.6, 1.0)
        self.alive = True
        self.speed = random.uniform(24, 40)
        
        # Cover state
        self.in_cover = False
        self.cover_bonus = 0.0
    
    def receive_damage(self, amount: float, ignore_cover: bool = False):
        """
        Apply damage to this unit, reduced by cover if applicable.
        
        Args:
            amount: Base damage amount
            ignore_cover: If True, bypasses cover reduction (e.g., explosives)
        """
        if not self.alive:
            return
        
        # Apply cover damage reduction
        if not ignore_cover and self.cover_bonus > 0:
            reduction = amount * self.cover_bonus
            amount = amount - reduction
        
        self.hp -= amount
        self.morale = clamp(self.morale - amount * 0.002, 0, 2)
        
        if self.hp <= 0:
            self.alive = False
    
    def update_cover_status(self, world):
        """Update this unit's cover status based on terrain."""
        self.cover_bonus = world.get_cover_at(self.x, self.y)
        self.in_cover = self.cover_bonus > 0
    
    def draw(self, surf, color):
        import pygame
        
        if not self.alive:
            color = (90, 90, 90)
        
        # Draw unit dot
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), 3)
        
        # Draw cover indicator (small shield icon)
        if self.alive and self.in_cover:
            # Small blue-ish arc above unit to indicate cover
            cover_color = (100, 180, 220)
            pygame.draw.arc(surf, cover_color, 
                          (int(self.x) - 5, int(self.y) - 8, 10, 6),
                          0, math.pi, 2)


class Squad:
    """A group of units that move and fight together."""
    
    def __init__(self, name, team='player', x=0, y=0):
        self.name = name
        self.team = team
        self.x = x
        self.y = y
        self.units = []
        self.order = ('idle', None)
        self.engaged = False
        
        # Movement properties
        self.base_speed = 26
        self.current_speed = self.base_speed
    
    def add_unit(self, u):
        self.units.append(u)
        u.x = self.x + random.randint(-16, 16)
        u.y = self.y + random.randint(-16, 16)
    
    def contains_point(self, px, py):
        return abs(px - self.x) < 28 and abs(py - self.y) < 28
    
    def set_order(self, t, payload=None):
        self.order = (t, payload)
    
    def center_update(self):
        """Recalculate squad center position based on living units."""
        alive = [u for u in self.units if u.alive]
        if alive:
            self.x = sum(u.x for u in alive) / len(alive)
            self.y = sum(u.y for u in alive) / len(alive)
    
    def update(self, dt, world):
        """Update squad state, respecting terrain."""
        # Update cover status for all units
        for u in self.units:
            if u.alive:
                u.update_cover_status(world)
        
        # Process movement orders
        if self.order[0] == 'move' and self.order[1]:
            self._process_movement(dt, world)
        
        # Combat resolution
        self._check_combat(world)
        
        # Clean up dead units
        self.units = [u for u in self.units if u.alive]
        self.center_update()
    
    def _process_movement(self, dt, world):
        """Process movement order with terrain awareness."""
        tx, ty = self.order[1]
        vx = tx - self.x
        vy = ty - self.y
        d = math.hypot(vx, vy)
        
        if d > 4:
            nx, ny = vx / d, vy / d
            
            # Get movement cost from terrain
            movement_cost = world.map.get_movement_cost(self.x, self.y)
            effective_speed = self.base_speed * movement_cost
            
            # Calculate proposed new position
            new_x = self.x + nx * effective_speed * dt
            new_y = self.y + ny * effective_speed * dt
            
            # Check if new position is passable
            if world.map.is_passable(new_x, new_y, is_vehicle=False):
                self.x = new_x
                self.y = new_y
                self.current_speed = effective_speed
                
                # Move individual units
                for u in self.units:
                    if u.alive:
                        # Individual unit movement with slight randomness
                        unit_new_x = u.x + nx * effective_speed * dt + random.uniform(-2, 2)
                        unit_new_y = u.y + ny * effective_speed * dt + random.uniform(-2, 2)
                        
                        # Only move if passable
                        if world.map.is_passable(unit_new_x, unit_new_y, is_vehicle=False):
                            u.x = unit_new_x
                            u.y = unit_new_y
            else:
                # Try to find alternative path (simple obstacle avoidance)
                for angle_offset in [0.3, -0.3, 0.6, -0.6, 0.9, -0.9]:
                    alt_nx = nx * math.cos(angle_offset) - ny * math.sin(angle_offset)
                    alt_ny = nx * math.sin(angle_offset) + ny * math.cos(angle_offset)
                    alt_x = self.x + alt_nx * effective_speed * dt
                    alt_y = self.y + alt_ny * effective_speed * dt
                    
                    if world.map.is_passable(alt_x, alt_y, is_vehicle=False):
                        self.x = alt_x
                        self.y = alt_y
                        break
        else:
            self.order = ('hold', None)
    
    def _check_combat(self, world):
        """Check for nearby enemies and resolve combat."""
        enemies = [s for s in world.squads if s.team != self.team and s.units]
        
        for e in enemies:
            d = math.hypot(self.x - e.x, self.y - e.y)
            
            if d < 110:
                # Check line of sight
                if world.check_los(self.x, self.y, e.x, e.y):
                    self.engaged = True
                    e.engaged = True
                    self.resolve_fire(e, world)
    
    def resolve_fire(self, enemy, world):
        """
        Resolve combat between this squad and enemy squad.
        Cover mechanics applied to damage calculations.
        """
        my_shooters = [u for u in self.units if u.alive and u.ammo > 0]
        enemy_shooters = [u for u in enemy.units if u.alive and u.ammo > 0]
        
        # Our squad fires
        for shooter in my_shooters:
            if not enemy.units:
                break
            
            alive_targets = [u for u in enemy.units if u.alive]
            if not alive_targets:
                break
            
            target = random.choice(alive_targets)
            
            # Base damage with morale modifier
            base_dmg = random.uniform(6, 18) * (1.0 + shooter.morale * 0.2)
            
            # Check line of sight from shooter to target
            if world.check_los(shooter.x, shooter.y, target.x, target.y):
                # Apply damage (cover is handled in receive_damage)
                target.receive_damage(base_dmg)
                shooter.ammo = max(0, shooter.ammo - 1)
        
        # Enemy squad fires back
        for shooter in enemy_shooters:
            if not self.units:
                break
            
            alive_targets = [u for u in self.units if u.alive]
            if not alive_targets:
                break
            
            target = random.choice(alive_targets)
            
            base_dmg = random.uniform(6, 18) * (1.0 + shooter.morale * 0.2)
            
            if world.check_los(shooter.x, shooter.y, target.x, target.y):
                target.receive_damage(base_dmg)
                shooter.ammo = max(0, shooter.ammo - 1)
    
    def get_average_cover(self) -> float:
        """Get average cover bonus across all living units."""
        alive = [u for u in self.units if u.alive]
        if not alive:
            return 0.0
        return sum(u.cover_bonus for u in alive) / len(alive)
    
    def draw(self, screen, color):
        """Draw the squad and its units."""
        import pygame
        
        # Draw individual units
        for u in self.units:
            u.draw(screen, color)
        
        # Draw squad selection circle (if any units alive)
        if self.units:
            alive_count = len([u for u in self.units if u.alive])
            if alive_count > 0:
                # Outer circle for squad bounds
                pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 
                                 22, 1)
                
                # Squad name label
                font = pygame.font.SysFont('Consolas', 10)
                label = font.render(self.name, True, color)
                screen.blit(label, (int(self.x) - 20, int(self.y) - 32))


class Drone:
    """Aerial reconnaissance and light attack drone."""
    
    def __init__(self, name, team='player', x=0, y=0):
        self.name = name
        self.team = team
        self.x = x
        self.y = y
        self.hp = 80
        self.max_hp = 80
        self.ammo = 6
        self.speed = 150
        self.controlled = False
        self.cooldown = 0.0
        self.auto_target = None
        
        # Drones ignore terrain (they fly)
        self.ignores_terrain = True
    
    def update(self, dt, world):
        if self.controlled:
            return
        
        # Random target acquisition
        if random.random() < 0.01:
            enemies = [s for s in world.squads if s.team != self.team and s.units]
            if enemies:
                t = random.choice(enemies)
                self.auto_target = (t.x, t.y)
        
        # Move towards target (drones ignore terrain)
        if self.auto_target:
            vx = self.auto_target[0] - self.x
            vy = self.auto_target[1] - self.y
            d = math.hypot(vx, vy)
            
            if d > 4:
                self.x += (vx / d) * self.speed * dt * 0.35
                self.y += (vy / d) * self.speed * dt * 0.35
            else:
                self.auto_target = None
        
        if self.cooldown > 0:
            self.cooldown = max(0, self.cooldown - dt)
    
    def fire_at(self, tx, ty, world):
        """Fire at a target position."""
        if self.ammo <= 0 or self.cooldown > 0:
            return False
        
        self.ammo -= 1
        self.cooldown = 0.5
        
        # Drone attacks ignore cover (attacking from above)
        for s in world.squads:
            if s.team != self.team:
                for u in s.units:
                    if u.alive and math.hypot(u.x - tx, u.y - ty) < 26:
                        u.receive_damage(random.uniform(25, 50), ignore_cover=True)
                        return True
        return True
    
    def draw(self, surf):
        import pygame
        
        col = (140, 220, 240) if self.team == 'player' else (240, 160, 120)
        
        # Triangle shape for drone
        pygame.draw.polygon(surf, col, [
            (self.x, self.y - 6),
            (self.x - 6, self.y + 6),
            (self.x + 6, self.y + 6)
        ])
        
        # Name label
        font = pygame.font.SysFont('Consolas', 10)
        label = font.render(self.name, True, col)
        surf.blit(label, (int(self.x) - 15, int(self.y) - 18))


class Vehicle:
    """Ground vehicle - APC or Tank."""
    
    def __init__(self, name, team='player', x=0, y=0, vtype='APC'):
        self.name = name
        self.team = team
        self.x = x
        self.y = y
        self.vtype = vtype
        
        # Stats based on vehicle type
        if vtype == 'APC':
            self.hp = 200
            self.max_hp = 200
            self.ammo = 40
            self.speed = 80
            self.armor = 0.3  # 30% damage reduction
        else:  # Tank
            self.hp = 300
            self.max_hp = 300
            self.ammo = 30
            self.speed = 55
            self.armor = 0.5  # 50% damage reduction
        
        self.fuel = 100
        self.controlled = False
        self.cooldown = 0.0
        
        # Movement state
        self.target_pos = None
    
    def receive_damage(self, amount: float, is_explosive: bool = False):
        """Apply damage to vehicle with armor reduction."""
        if is_explosive:
            # Explosives do extra damage to vehicles
            amount *= 1.2
        else:
            # Regular fire reduced by armor
            amount *= (1.0 - self.armor)
        
        self.hp -= amount
        
        if self.hp <= 0:
            # Vehicle destroyed
            pass
    
    def fire_at(self, tx, ty, world):
        """Fire at a target position."""
        if self.ammo <= 0 or self.cooldown > 0:
            return False
        
        self.ammo -= 1
        self.cooldown = 0.6
        hit = False
        
        # Vehicle weapons ignore some cover
        for s in world.squads:
            if s.team != self.team:
                for u in s.units:
                    if u.alive and math.hypot(u.x - tx, u.y - ty) < 30:
                        # Heavy weapons partially ignore cover
                        u.receive_damage(random.uniform(20, 45), 
                                        ignore_cover=(random.random() < 0.3))
                        hit = True
        
        return hit
    
    def move_to(self, tx, ty, world, dt):
        """Move towards target position, respecting vehicle passability."""
        vx = tx - self.x
        vy = ty - self.y
        d = math.hypot(vx, vy)
        
        if d > 4:
            nx, ny = vx / d, vy / d
            
            # Get movement cost (vehicles get road bonus)
            movement_cost = world.map.get_movement_cost(self.x, self.y)
            effective_speed = self.speed * movement_cost
            
            new_x = self.x + nx * effective_speed * dt
            new_y = self.y + ny * effective_speed * dt
            
            # Check vehicle passability
            if world.map.is_passable(new_x, new_y, is_vehicle=True):
                self.x = new_x
                self.y = new_y
                self.fuel = max(0, self.fuel - dt * 0.25)
                return True
        
        return False
    
    def update(self, dt, world=None):
        if self.cooldown > 0:
            self.cooldown = max(0, self.cooldown - dt)
        
        # Passive fuel consumption
        self.fuel = max(0, self.fuel - dt * 0.15)
        
        # Process movement if we have a target
        if self.target_pos and world:
            self.move_to(self.target_pos[0], self.target_pos[1], world, dt)
    
    def draw(self, surf):
        import pygame
        
        col = (100, 200, 230) if self.team == 'player' else (220, 100, 100)
        
        # Rectangle for vehicle
        rect_w = 20 if self.vtype == 'APC' else 24
        rect_h = 12 if self.vtype == 'APC' else 14
        pygame.draw.rect(surf, col, 
                        (int(self.x) - rect_w // 2, int(self.y) - rect_h // 2, 
                         rect_w, rect_h))
        
        # Name label
        font = pygame.font.SysFont('Consolas', 10)
        label = font.render(self.name, True, col)
        surf.blit(label, (int(self.x) - 18, int(self.y) - 20))
        
        # Health bar
        bar_width = 20
        bar_height = 3
        hp_pct = self.hp / self.max_hp
        
        pygame.draw.rect(surf, (60, 60, 60),
                        (int(self.x) - bar_width // 2, int(self.y) + rect_h // 2 + 2,
                         bar_width, bar_height))
        pygame.draw.rect(surf, (100, 200, 100) if hp_pct > 0.5 else (200, 100, 100),
                        (int(self.x) - bar_width // 2, int(self.y) + rect_h // 2 + 2,
                         int(bar_width * hp_pct), bar_height))
