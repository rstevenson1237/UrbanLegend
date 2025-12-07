import pygame
from collections import deque
MAP_W=960; HEIGHT=780; PANEL_W=320
COL_PANEL=(6,14,30); COL_TEXT=(180,230,255)
FONT_NAME='Consolas'
class UI:
    def __init__(self, screen, world):
        self.screen=screen; self.world=world
        self.font=pygame.font.SysFont(FONT_NAME,16); self.big=pygame.font.SysFont(FONT_NAME,20,bold=True)
        self.input_text=''; self.selected=None; self.controlled=None
    def draw(self):
        # right panel - translucent blue HUD
        s = pygame.Surface((PANEL_W, HEIGHT), pygame.SRCALPHA)
        s.fill((8,20,40,220))
        self.screen.blit(s, (MAP_W,0))
        # title
        self.screen.blit(self.big.render('URBAN LEGEND', True, COL_TEXT), (MAP_W+18, 10))
        self.screen.blit(self.font.render('COMMAND TERMINAL (Blue HUD)', True, COL_TEXT), (MAP_W+18, 36))
        # buttons (visual only)
        y=68
        labels=['Take Control (D)','Hold Order','Attack Order','Resupply Selected','Pause (SPACE)','Fast (F)','Save (S)','Load (L)']
        for lab in labels:
            pygame.draw.rect(self.screen, (10,30,50), (MAP_W+18, y, PANEL_W-36, 28), border_radius=6)
            self.screen.blit(self.font.render(lab, True, COL_TEXT), (MAP_W+26, y+6))
            y+=36
        # selected summary
        self.screen.blit(self.font.render('Selected:', True, COL_TEXT), (MAP_W+18, 360))
        if self.selected:
            self.screen.blit(self.font.render(self._repr_selected(), True, COL_TEXT), (MAP_W+18, 388))
        else:
            self.screen.blit(self.font.render('None', True, (120,160,180)), (MAP_W+18, 388))
        # event log
        self.screen.blit(self.font.render('Event Log:', True, COL_TEXT), (MAP_W+18, 420))
        for i, ln in enumerate(list(self.world.log_lines)[:12]):
            self.screen.blit(self.font.render(ln, True, (140,200,220)), (MAP_W+18, 448 + i*18))
        # command input
        box_rect = pygame.Rect(12, HEIGHT-46, MAP_W-24, 36)
        pygame.draw.rect(self.screen, (2,10,18), box_rect); pygame.draw.rect(self.screen, (60,140,200), box_rect, 2)
        txt = self.font.render(self.input_text, True, (200,240,255))
        self.screen.blit(txt, (18, HEIGHT-40))
    def click_map(self, pos):
        x,y = pos
        for s in self.world.squads + self.world.vehicles + self.world.drones:
            if hasattr(s, 'contains_point') and s.contains_point(x,y): self.selected=s; self.world.log(f'Selected {s.name}'); return True
            if hasattr(s,'x') and abs(x-s.x)<16 and abs(y-s.y)<12: self.selected = s; self.world.log(f'Selected {s.name}'); return True
        return False
    def right_click_map(self, pos):
        x,y = pos
        if self.selected is None: self.world.log('No selection'); return
        if hasattr(self.selected, 'set_order'):
            self.selected.set_order('move', (x,y)); self.world.log(f'Ordered {self.selected.name} to move to {(int(x),int(y))}')
        else:
            self.selected.x, self.selected.y = x,y; self.world.log(f'Moved {self.selected.name} to {(int(x),int(y))}')
    def submit(self, parser, commander):
        txt = self.input_text.strip(); self.input_text = ''
        if not txt: return
        parsed = parser.parse(txt); self.world.log(f'CMD: {txt}'); commander.execute(parsed)
    def _repr_selected(self):
        s = self.selected
        if hasattr(s,'units'): return f'{s.name} Units:{len(s.units)}'
        if hasattr(s,'vtype'): return f'{s.name} {s.vtype} HP:{s.hp} Ammo:{s.ammo}'
        if hasattr(s,'ammo') and not hasattr(s,'units'): return f'{s.name} Drone HP:{s.hp} Ammo:{s.ammo}'
        return str(s)
