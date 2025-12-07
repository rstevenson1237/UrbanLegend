"""
Tutorial system for Urban Legend.
Guides new players through basic commands and mechanics.
"""

import time


class Tutorial:
    """
    Interactive tutorial that guides players through game mechanics.
    Includes terrain and cover system explanation.
    """
    
    def __init__(self, world, ui, commander):
        self.world = world
        self.ui = ui
        self.commander = commander
        self.step = 0
        self.active = True
        self.step_timer = 0
        self.messages_shown = set()
    
    def update(self):
        """Update tutorial state based on game events."""
        if not self.active:
            return
        
        # Step 0: Welcome
        if self.step == 0:
            if 'welcome' not in self.messages_shown:
                self.world.log('='*40)
                self.world.log('TUTORIAL: Welcome Commander!')
                self.world.log(f'Map: {self.world.map.name}')
                self.world.log('Click Alpha_1 on the map to select.')
                self.world.log('='*40)
                self.messages_shown.add('welcome')
            self.step = 1
            return
        
        # Step 1: Wait for selection
        if self.step == 1:
            if self.ui.selected:
                selected_name = getattr(self.ui.selected, 'name', '').lower()
                if selected_name.startswith('alpha'):
                    self.world.log('')
                    self.world.log('TUTORIAL: Good! You selected a squad.')
                    self.world.log('Notice the terrain info on the right panel.')
                    self.world.log('')
                    self.world.log('Type: "Alpha move north" and press Enter.')
                    self.step = 2
                    return
        
        # Step 2: Wait for move command
        if self.step == 2:
            for ln in list(self.world.log_lines)[:8]:
                ln_lower = ln.lower()
                if 'alpha' in ln_lower and 'moving' in ln_lower:
                    self.world.log('')
                    self.world.log('TUTORIAL: Units are moving!')
                    self.world.log('Green tiles = Cover (reduces damage)')
                    self.world.log('Gray tiles = Buildings (enter via doors)')
                    self.world.log('')
                    self.world.log('Type: "Alpha attack" to engage enemies.')
                    self.step = 3
                    return
        
        # Step 3: Wait for attack command
        if self.step == 3:
            for ln in list(self.world.log_lines)[:12]:
                ln_lower = ln.lower()
                if 'attack' in ln_lower or 'engaging' in ln_lower:
                    self.world.log('')
                    self.world.log('TUTORIAL: Combat started!')
                    self.world.log('Units in cover take less damage.')
                    self.world.log('')
                    self.world.log('Press G to toggle the grid overlay.')
                    self.step = 4
                    return
        
        # Step 4: Wait for grid toggle
        if self.step == 4:
            for ln in list(self.world.log_lines)[:6]:
                if 'Grid' in ln:
                    self.world.log('')
                    self.world.log('TUTORIAL: Grid shows tile boundaries.')
                    self.world.log('')
                    self.world.log('Press M to cycle through different maps.')
                    self.step = 5
                    return
        
        # Step 5: Map cycling
        if self.step == 5:
            for ln in list(self.world.log_lines)[:6]:
                if 'Map changed' in ln:
                    self.world.log('')
                    self.world.log('TUTORIAL: Each map has different terrain!')
                    self.world.log('')
                    self.world.log('Tutorial complete. Good luck, Commander!')
                    self.world.log('')
                    self.world.log('Commands: attack, move, scout, hold, retreat, flank')
                    self.world.log('Keys: SPACE=pause, F=fast, S=save, L=load')
                    self.world.log('='*40)
                    self.active = False
                    return
    
    def skip(self):
        """Skip the tutorial."""
        if self.active:
            self.world.log('Tutorial skipped.')
            self.active = False
    
    def reset(self):
        """Reset tutorial to beginning."""
        self.step = 0
        self.active = True
        self.messages_shown.clear()
        self.world.log('Tutorial reset.')


class TutorialStep:
    """Individual tutorial step (for future expansion)."""
    
    def __init__(self, message, condition_fn, on_complete_fn=None):
        self.message = message
        self.condition_fn = condition_fn
        self.on_complete_fn = on_complete_fn
        self.completed = False
    
    def check(self, world, ui):
        """Check if step condition is met."""
        if not self.completed and self.condition_fn(world, ui):
            self.completed = True
            if self.on_complete_fn:
                self.on_complete_fn(world, ui)
            return True
        return False
