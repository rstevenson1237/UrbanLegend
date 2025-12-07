import random, time
from collections import deque
from units import Squad, Unit, Drone, Vehicle
class World:
    def __init__(self):
        self.squads = []; self.drones = []; self.vehicles = []
        self.log_lines = deque(maxlen=500); self.tick=0.0; self.paused=False; self.fast=False
        self.init_forces(); self.log('World created')
    def init_forces(self):
        for i in range(3):
            s = Squad(f'Alpha_{i+1}', 'player', x=160 + i*80, y=240 + (i%2)*120)
            for j in range(random.randint(8,14)): s.add_unit(Unit(f'P_{i+1}_{j+1}', 'player'))
            self.squads.append(s)
        for i in range(2): self.vehicles.append(Vehicle(f'APC_{i+1}', 'player', x=220+i*60, y=520, vtype='APC'))
        for i in range(2): self.drones.append(Drone(f'Drone_{i+1}', 'player', x=260+i*60, y=560))
        for i in range(4):
            s = Squad(f'Enemy_{i+1}', 'enemy', x=700 + i*50, y=120 + (i%3)*110)
            for j in range(random.randint(9,18)): s.add_unit(Unit(f'E_{i+1}_{j+1}', 'enemy'))
            self.squads.append(s)
        for i in range(1): self.vehicles.append(Vehicle(f'Tank_E{i+1}', 'enemy', x=760+i*40, y=300, vtype='Tank'))
        for i in range(1): self.drones.append(Drone(f'Drone_E{i+1}', 'enemy', x=740+i*40, y=460))
    def update(self, dt):
        if self.paused: return
        steps = 4 if self.fast else 1
        for _ in range(steps):
            for s in list(self.squads): s.update(dt, self)
            for d in list(self.drones): d.update(dt, self)
            for v in list(self.vehicles): v.update(dt)
            self.enemy_ai_step(); self.tick += dt
    def enemy_ai_step(self):
        enemies = [s for s in self.squads if s.team=='enemy' and s.units]
        targets = [s for s in self.squads if s.team=='player' and s.units]
        if not enemies or not targets: return
        if random.random() < 0.02:
            e = random.choice(enemies); t = random.choice(targets); e.set_order('move', (t.x + random.randint(-30,30), t.y + random.randint(-30,30)))
            self.log(f'Enemy {e.name} maneuvers toward {t.name}')
    def log(self, txt):
        ts = time.strftime('%H:%M:%S'); self.log_lines.appendleft(f'[{ts}] {txt}'); print(f'[{ts}] {txt}')
    def find_unit_by_name(self, token):
        token = token.lower()
        names = [e.name.lower() for e in (self.squads + self.vehicles + self.drones)]
        from difflib import get_close_matches
        matches = get_close_matches(token, names, n=1, cutoff=0.5)
        if matches:
            m = matches[0]
            for e in (self.squads + self.vehicles + self.drones):
                if e.name.lower() == m: return e
        return None
