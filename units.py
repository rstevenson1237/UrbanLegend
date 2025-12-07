import random, math
def clamp(v,a,b): return max(a,min(b,v))
class Unit:
    def __init__(self, uid, team='player', x=0, y=0):
        self.id = uid; self.name = uid; self.team = team; self.x = x; self.y = y
        self.hp = 100; self.ammo = random.randint(20,60); self.morale = random.uniform(0.6,1.0)
        self.alive = True; self.speed = random.uniform(24,40)
    def receive_damage(self, amount):
        if not self.alive: return
        self.hp -= amount; self.morale = clamp(self.morale - amount*0.002, 0, 2)
        if self.hp <= 0: self.alive = False
    def draw(self, surf, color):
        import pygame
        if not self.alive: color = (90,90,90)
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), 3)

class Squad:
    def __init__(self, name, team='player', x=0,y=0):
        self.name = name; self.team = team; self.x = x; self.y = y
        self.units = []; self.order = ('idle', None); self.engaged = False
    def add_unit(self, u):
        self.units.append(u); u.x = self.x + random.randint(-16,16); u.y = self.y + random.randint(-16,16)
    def contains_point(self, px,py): return abs(px - self.x) < 28 and abs(py - self.y) < 28
    def set_order(self, t, payload=None): self.order = (t, payload)
    def center_update(self):
        alive = [u for u in self.units if u.alive]
        if alive: self.x = sum(u.x for u in alive)/len(alive); self.y = sum(u.y for u in alive)/len(alive)
    def update(self, dt, world):
        if self.order[0] == 'move' and self.order[1]:
            tx,ty = self.order[1]; vx = tx - self.x; vy = ty - self.y
            d = math.hypot(vx,vy)
            if d > 4:
                nx,ny = vx/d, vy/d; sp = 26
                self.x += nx*sp*dt; self.y += ny*sp*dt
                for u in self.units:
                    if u.alive:
                        u.x += nx*sp*dt + random.uniform(-4,4); u.y += ny*sp*dt + random.uniform(-4,4)
            else:
                self.order = ('hold', None)
        enemies = [s for s in world.squads if s.team!=self.team and s.units]
        for e in enemies:
            d = math.hypot(self.x - e.x, self.y - e.y)
            if d < 110:
                self.engaged = True; e.engaged = True; self.resolve_fire(e)
        self.units = [u for u in self.units if u.alive]
        self.center_update()
    def resolve_fire(self, enemy):
        my = [u for u in self.units if u.alive and u.ammo>0]
        en = [u for u in enemy.units if u.alive and u.ammo>0]
        for shooter in my:
            if not enemy.units: break
            target = random.choice(enemy.units)
            dmg = random.uniform(6,18)*(1.0 + shooter.morale*0.2)
            target.receive_damage(dmg); shooter.ammo = max(0, shooter.ammo-1)
        for shooter in en:
            if not self.units: break
            target = random.choice(self.units)
            dmg = random.uniform(6,18)*(1.0 + shooter.morale*0.2)
            target.receive_damage(dmg); shooter.ammo = max(0, shooter.ammo-1)

class Drone:
    def __init__(self, name, team='player', x=0,y=0):
        self.name = name; self.team = team; self.x=x; self.y=y
        self.hp=80; self.ammo=6; self.speed=150; self.controlled=False; self.cooldown=0.0; self.auto_target=None
    def update(self, dt, world):
        if self.controlled: return
        if random.random()<0.01:
            enemies=[s for s in world.squads if s.team!=self.team and s.units]
            if enemies: t=random.choice(enemies); self.auto_target=(t.x,t.y)
        if self.auto_target:
            vx=self.auto_target[0]-self.x; vy=self.auto_target[1]-self.y
            d=math.hypot(vx,vy)
            if d>4:
                self.x += (vx/d)*self.speed*dt*0.35; self.y += (vy/d)*self.speed*dt*0.35
            else: self.auto_target=None
        if self.cooldown>0: self.cooldown=max(0,self.cooldown-dt)
    def fire_at(self, tx,ty, world):
        if self.ammo<=0 or self.cooldown>0: return False
        self.ammo-=1; self.cooldown=0.5
        for s in world.squads:
            if s.team!=self.team:
                for u in s.units:
                    if u.alive and math.hypot(u.x-tx,u.y-ty)<26:
                        u.receive_damage(random.uniform(25,50)); return True
        return True
    def draw(self, surf):
        import pygame
        col=(140,220,240) if self.team=='player' else (240,160,120)
        pygame.draw.polygon(surf, col, [(self.x,self.y-6),(self.x-6,self.y+6),(self.x+6,self.y+6)])

class Vehicle:
    def __init__(self,name, team='player', x=0,y=0, vtype='APC'):
        self.name=name; self.team=team; self.x=x; self.y=y
        self.hp=200 if vtype=='APC' else 300; self.ammo=40; self.fuel=100; self.vtype=vtype
        self.speed=80 if vtype=='APC' else 55; self.controlled=False; self.cooldown=0.0
    def fire_at(self, tx,ty, world):
        if self.ammo<=0 or self.cooldown>0: return False
        self.ammo-=1; self.cooldown=0.6; hit=False
        for s in world.squads:
            if s.team!=self.team:
                for u in s.units:
                    if u.alive and math.hypot(u.x-tx,u.y-ty)<30:
                        u.receive_damage(random.uniform(20,45)); hit=True
        return hit
    def update(self, dt):
        if self.cooldown>0: self.cooldown=max(0,self.cooldown-dt)
        self.fuel = max(0, self.fuel-dt*0.15)
    def draw(self, surf):
        import pygame
        col=(100,200,230) if self.team=='player' else (220,100,100)
        pygame.draw.rect(surf, col, (int(self.x)-10, int(self.y)-6, 20, 12))
