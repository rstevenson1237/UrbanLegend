import time
class Tutorial:
    def __init__(self, world, ui, commander):
        self.world=world; self.ui=ui; self.commander=commander; self.step=0; self.active=True
    def update(self):
        if not self.active: return
        if self.step==0:
            self.world.log('TUTORIAL: Welcome Commander. Select Alpha_1 by left-clicking.')
            self.step=1; return
        if self.step==1:
            if self.ui.selected and getattr(self.ui.selected,'name','').lower().startswith('alpha_1'):
                self.world.log('TUTORIAL: Good. Type: Alpha squad move north and press Enter.')
                self.step=2; return
        if self.step==2:
            for ln in list(self.world.log_lines)[:8]:
                if 'alpha_1' in ln.lower() and 'move' in ln.lower():
                    self.world.log('TUTORIAL: Now: Alpha squad engage the enemy')
                    self.step=3; return
        if self.step==3:
            for ln in list(self.world.log_lines)[:12]:
                if 'attack' in ln.lower() or 'engage' in ln.lower():
                    self.world.log('TUTORIAL: Complete. Use the console to command units.')
                    self.active=False; return
