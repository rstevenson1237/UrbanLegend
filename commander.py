import random, math
from math import hypot
def dist(a,b): return hypot(a[0]-b[0], a[1]-b[1])
class Commander:
    def __init__(self, world, ui): self.world = world; self.ui = ui
    def execute(self, parsed):
        action = parsed.get('action'); group = parsed.get('group'); target_token = parsed.get('target_entity'); direction = parsed.get('direction')
        self.world.log(f'Parsed: {parsed}')
        targets = self._resolve_group(group)
        # override with specific entity
        if target_token:
            ent = self.world.find_unit_by_name(target_token)
            if ent:
                targets = [ent]
        if action == 'attack':
            for t in targets:
                enemy = self._nearest_enemy(t)
                if enemy:
                    if hasattr(t, 'set_order'): t.set_order('move', (enemy.x, enemy.y))
                    else: setattr(t, 'target_move', (enemy.x, enemy.y))
                    self.ui.log(f'{self._name(t)} ordered to ATTACK {enemy.name}')
                else:
                    self.ui.log(f'No enemy found for {self._name(t)}')
        elif action == 'move':
            for t in targets:
                tx,ty = self._dir_point(direction) if direction else (t.x+120, t.y)
                if hasattr(t, 'set_order'): t.set_order('move', (tx,ty))
                else: t.x, t.y = tx, ty
                self.ui.log(f'{self._name(t)} moving to {(int(tx),int(ty))}')
        elif action == 'scout':
            for t in targets:
                if hasattr(t, 'auto_target'):
                    tx,ty = self._dir_point(direction) if direction else (t.x+220, t.y)
                    t.auto_target = (tx,ty); self.ui.log(f'{self._name(t)} scouting to {(int(tx),int(ty))}')
                else:
                    self.ui.log(f'{self._name(t)} cannot scout (not a drone)')
        elif action == 'hold':
            for t in targets:
                if hasattr(t, 'set_order'): t.set_order('hold', None)
                self.ui.log(f'{self._name(t)} hold position')
        elif action == 'retreat':
            for t in targets:
                home = (120, 680)
                if hasattr(t, 'set_order'): t.set_order('move', home)
                else: t.x, t.y = home
                self.ui.log(f'{self._name(t)} retreating to base')
        elif action == 'resupply':
            for s in targets:
                if hasattr(s, 'units'):
                    moved = 0
                    for u in s.units:
                        need = max(0, 60 - u.ammo)
                        u.ammo += need; moved += need
                    self.ui.log(f'{s.name} resupplied ammo: {moved}')
        else:
            self.ui.log('Command not understood. Use attack/move/scout/hold/retreat/resupply.')
    def _resolve_group(self, group):
        if group in (None, 'all'): return [s for s in self.world.squads if s.team=='player']
        if group == 'alpha': return [s for s in self.world.squads if s.team=='player' and s.name.lower().startswith('alpha')]
        if group == 'drones': return list(self.world.drones)
        if group == 'vehicles': return list(self.world.vehicles)
        return [s for s in self.world.squads if s.team=='player']
    def _nearest_enemy(self, ent):
        enemies = [s for s in self.world.squads if s.team!='player' and s.units]
        if not enemies: return None
        if hasattr(ent, 'x'): return min(enemies, key=lambda e: dist((e.x,e.y),(ent.x,ent.y)))
        return random.choice(enemies)
    def _dir_point(self, d):
        if not d: return (480, 380)
        if d == 'north': return (480, 120)
        if d == 'south': return (480, 680)
        if d == 'east': return (MAP_W-120, 380) if 'MAP_W' in globals() else (900, 380)
        if d == 'west': return (120, 380)
        return (480, 380)
    def _name(self, ent): return getattr(ent, 'name', str(ent))
