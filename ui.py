"""
User Interface for Urban Legend.
Updated with terrain rendering and map display.
Phase 2.1: Interactive buttons with hover/click feedback.
"""

import pygame
from collections import deque
from map import (TILE_SIZE, MAP_PIXEL_W, MAP_PIXEL_H, MAP_TILES_X, MAP_TILES_Y,
                 TerrainType, TERRAIN_PROPERTIES)

MAP_W = 960
HEIGHT = 780
PANEL_W = 320

COL_PANEL = (6, 14, 30)
COL_TEXT = (180, 230, 255)
COL_HIGHLIGHT = (80, 180, 220)
FONT_NAME = 'Consolas'

# Button colors
COL_BTN_NORMAL = (10, 30, 50)
COL_BTN_HOVER = (20, 50, 80)
COL_BTN_CLICK = (40, 100, 140)
COL_BTN_BORDER = (60, 140, 200)
COL_BTN_BORDER_HOVER = (100, 180, 240)


class Button:
    """
    Interactive button with hover and click feedback.
    
    Attributes:
        rect: pygame.Rect defining button bounds
        label: Text displayed on button
        callback: Function called when button is clicked
        hover_state: True if mouse is over button
        click_flash: Timer for click animation (counts down from flash duration)
    """
    
    FLASH_DURATION = 0.15  # seconds
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 label: str, callback=None, font=None):
        """
        Initialize a button.
        
        Args:
            x, y: Top-left position
            width, height: Button dimensions
            label: Text to display
            callback: Function to call on click (can be None)
            font: Pygame font for rendering (uses default if None)
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.callback = callback
        self.font = font
        self.hover_state = False
        self.click_flash = 0.0
        self.enabled = True
    
    def update(self, dt: float):
        """Update button state (animations)."""
        if self.click_flash > 0:
            self.click_flash = max(0, self.click_flash - dt)
    
    def update_hover(self, mouse_pos: tuple):
        """Update hover state based on mouse position."""
        self.hover_state = self.rect.collidepoint(mouse_pos) and self.enabled
    
    def handle_click(self, mouse_pos: tuple) -> bool:
        """
        Handle a click event.
        
        Returns:
            True if this button was clicked, False otherwise
        """
        if not self.enabled:
            return False
            
        if self.rect.collidepoint(mouse_pos):
            self.click_flash = self.FLASH_DURATION
            if self.callback:
                self.callback()
            return True
        return False
    
    def draw(self, surface: pygame.Surface):
        """Draw the button with appropriate visual state."""
        # Determine colors based on state
        if self.click_flash > 0:
            bg_color = COL_BTN_CLICK
            border_color = COL_BTN_BORDER_HOVER
        elif self.hover_state:
            bg_color = COL_BTN_HOVER
            border_color = COL_BTN_BORDER_HOVER
        else:
            bg_color = COL_BTN_NORMAL
            border_color = COL_BTN_BORDER if self.enabled else (40, 60, 80)
        
        # Draw button background
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=6)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=6)
        
        # Draw label
        if self.font:
            text_color = COL_TEXT if self.enabled else (100, 120, 140)
            text_surf = self.font.render(self.label, True, text_color)
            text_x = self.rect.x + (self.rect.width - text_surf.get_width()) // 2
            text_y = self.rect.y + (self.rect.height - text_surf.get_height()) // 2
            surface.blit(text_surf, (text_x, text_y))


class UI:
    """Main UI class handling rendering and input."""
    
    def __init__(self, screen, world, commander=None, parser=None,
                 save_callback=None, load_callback=None):
        """
        Initialize the UI.
        
        Args:
            screen: Pygame display surface
            world: Game world instance
            commander: Command executor for issuing orders
            parser: NLP command parser
            save_callback: Function to call for saving game
            load_callback: Function to call for loading game
        """
        self.screen = screen
        self.world = world
        self.commander = commander
        self.parser = parser
        self.save_callback = save_callback
        self.load_callback = load_callback
        
        self.font = pygame.font.SysFont(FONT_NAME, 16)
        self.small_font = pygame.font.SysFont(FONT_NAME, 12)
        self.big = pygame.font.SysFont(FONT_NAME, 20, bold=True)
        self.input_text = ''
        self.selected = None
        self.controlled = None

        # UI state (must be initialized before _generate_terrain_surface)
        self.show_grid = False
        self.show_zones = True
        self.hover_tile = None
        
        # Initialize buttons
        self.buttons = []
        self._create_buttons()

        # Terrain surface cache (regenerated when map changes)
        self.terrain_surface = None
        self.current_map_name = None
        self._generate_terrain_surface()
    
    def _create_buttons(self):
        """Create all UI buttons with their callbacks."""
        btn_x = MAP_W + 18
        btn_w = PANEL_W - 36
        btn_h = 28
        start_y = 68
        spacing = 36
        
        button_configs = [
            ('Take Control (D)', self._on_take_control),
            ('Hold Order', self._on_hold_order),
            ('Attack Order', self._on_attack_order),
            ('Resupply Selected', self._on_resupply),
            ('Pause (SPACE)', self._on_pause),
            ('Fast (F)', self._on_fast),
            ('Save (S)', self._on_save),
            ('Load (L)', self._on_load),
            ('Grid (G)', self._on_grid),
        ]
        
        self.buttons = []
        for i, (label, callback) in enumerate(button_configs):
            btn = Button(
                x=btn_x,
                y=start_y + i * spacing,
                width=btn_w,
                height=btn_h,
                label=label,
                callback=callback,
                font=self.font
            )
            self.buttons.append(btn)
        
        # Store references to specific buttons for dynamic label updates
        self.btn_pause = self.buttons[4]
        self.btn_fast = self.buttons[5]
        self.btn_grid = self.buttons[8]
    
    def set_commander(self, commander):
        """Set the commander reference (for deferred initialization)."""
        self.commander = commander
    
    def set_parser(self, parser):
        """Set the parser reference (for deferred initialization)."""
        self.parser = parser
    
    def set_save_callback(self, callback):
        """Set the save callback function."""
        self.save_callback = callback
    
    def set_load_callback(self, callback):
        """Set the load callback function."""
        self.load_callback = callback
    
    def update(self, dt: float):
        """Update UI state (button animations, etc.)."""
        # Update button animations
        for btn in self.buttons:
            btn.update(dt)
        
        # Update button labels based on game state
        self.btn_pause.label = 'Resume (SPACE)' if self.world.paused else 'Pause (SPACE)'
        self.btn_fast.label = 'Normal (F)' if self.world.fast else 'Fast (F)'
        self.btn_grid.label = f'Grid (G): {"ON" if self.show_grid else "OFF"}'
        
        # Update hover states
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update_hover(mouse_pos)
    
    # =========================================================================
    # Button Callbacks
    # =========================================================================
    
    def _on_take_control(self):
        """Toggle control of selected unit or first available drone/vehicle."""
        if self.selected is None:
            # Try drones first, then vehicles
            if self.world.drones:
                d = self.world.drones[0]
                d.controlled = not d.controlled
                self.world.log(f'Controlling {d.name}' if d.controlled else f'Released {d.name}')
            elif self.world.vehicles:
                v = self.world.vehicles[0]
                v.controlled = not v.controlled
                self.world.log(f'Controlling {v.name}' if v.controlled else f'Released {v.name}')
            else:
                self.world.log('No drone or vehicle to control')
        else:
            if hasattr(self.selected, 'controlled'):
                self.selected.controlled = not self.selected.controlled
                status = 'Controlling' if self.selected.controlled else 'Released'
                self.world.log(f'{status} {self.selected.name}')
            else:
                self.world.log(f'{self.selected.name} cannot be directly controlled')
    
    def _on_hold_order(self):
        """Issue hold order to selected unit."""
        if self.selected is None:
            self.world.log('No unit selected for hold order')
            return
        
        if self.commander:
            parsed = {'action': 'hold', 'group': None, 'target_entity': self.selected.name, 'direction': None}
            self.commander.execute(parsed)
        elif hasattr(self.selected, 'set_order'):
            self.selected.set_order('hold', None)
            self.world.log(f'{self.selected.name} holding position')
    
    def _on_attack_order(self):
        """Issue attack order to selected unit."""
        if self.selected is None:
            self.world.log('No unit selected for attack order')
            return
        
        if self.commander:
            parsed = {'action': 'attack', 'group': None, 'target_entity': self.selected.name, 'direction': None}
            self.commander.execute(parsed)
        else:
            self.world.log(f'{self.selected.name} ordered to attack')
    
    def _on_resupply(self):
        """Resupply selected unit."""
        if self.selected is None:
            self.world.log('No unit selected for resupply')
            return
        
        if self.commander:
            parsed = {'action': 'resupply', 'group': None, 'target_entity': self.selected.name, 'direction': None}
            self.commander.execute(parsed)
        else:
            self.world.log(f'{self.selected.name} resupply requested')
    
    def _on_pause(self):
        """Toggle pause state."""
        self.world.paused = not self.world.paused
        self.world.log('Paused' if self.world.paused else 'Unpaused')
    
    def _on_fast(self):
        """Toggle fast mode."""
        self.world.fast = not self.world.fast
        self.world.log('Fast' if self.world.fast else 'Normal')
    
    def _on_save(self):
        """Save the game."""
        if self.save_callback:
            self.save_callback()
        else:
            self.world.log('Save not available')
    
    def _on_load(self):
        """Load the game."""
        if self.load_callback:
            self.load_callback()
            self._generate_terrain_surface()  # Refresh terrain after load
        else:
            self.world.log('Load not available')
    
    def _on_grid(self):
        """Toggle grid overlay."""
        self.toggle_grid()
    
    # =========================================================================
    # Terrain Rendering
    # =========================================================================
    
    def _generate_terrain_surface(self):
        """
        Pre-render the terrain to a surface for efficient drawing.
        Called once when map loads or changes.
        """
        self.terrain_surface = pygame.Surface((MAP_PIXEL_W, MAP_PIXEL_H))
        game_map = self.world.map
        self.current_map_name = game_map.name
        
        for ty in range(MAP_TILES_Y):
            for tx in range(MAP_TILES_X):
                terrain = game_map.get_tile(tx, ty)
                props = TERRAIN_PROPERTIES[terrain]
                color = props['color']
                
                # Draw base tile
                rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, 
                                  TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.terrain_surface, color, rect)
                
                # Add visual details based on terrain type
                self._draw_terrain_details(tx, ty, terrain, rect)
        
        # Draw building outlines
        for building in game_map.buildings.values():
            self._draw_building_outline(building)
        
        # Draw zones if enabled
        if self.show_zones:
            self._draw_zones()
    
    def _draw_terrain_details(self, tx, ty, terrain, rect):
        """Add visual details to terrain tiles."""
        if terrain == TerrainType.COVER:
            # Draw small debris/cover markers
            cx = rect.centerx
            cy = rect.centery
            pygame.draw.circle(self.terrain_surface, (60, 70, 55), 
                             (cx - 4, cy), 3)
            pygame.draw.circle(self.terrain_surface, (60, 70, 55), 
                             (cx + 4, cy + 2), 2)
        
        elif terrain == TerrainType.URBAN:
            # Draw rubble pattern
            for i in range(3):
                x = rect.x + 5 + i * 8
                y = rect.y + 4 + (i % 2) * 10
                pygame.draw.rect(self.terrain_surface, (65, 70, 75),
                               (x, y, 6, 4))
        
        elif terrain == TerrainType.WATER:
            # Draw wave pattern
            pygame.draw.line(self.terrain_surface, (25, 55, 90),
                           (rect.x + 4, rect.centery),
                           (rect.x + TILE_SIZE - 4, rect.centery), 1)
            pygame.draw.line(self.terrain_surface, (25, 55, 90),
                           (rect.x + 8, rect.centery + 6),
                           (rect.x + TILE_SIZE - 8, rect.centery + 6), 1)
        
        elif terrain == TerrainType.ROAD:
            # Draw road markings (center line)
            if tx % 3 == 0:
                pygame.draw.line(self.terrain_surface, (70, 70, 75),
                               (rect.centerx - 4, rect.centery),
                               (rect.centerx + 4, rect.centery), 2)
        
        elif terrain == TerrainType.BUILDING_FLOOR:
            # Draw floor tile pattern
            pygame.draw.rect(self.terrain_surface, (60, 55, 50),
                           (rect.x + 1, rect.y + 1, 
                            TILE_SIZE - 2, TILE_SIZE - 2), 1)
        
        elif terrain == TerrainType.IMPASSABLE:
            # Draw wall texture
            pygame.draw.rect(self.terrain_surface, (40, 40, 45),
                           (rect.x + 2, rect.y + 2, 
                            TILE_SIZE - 4, TILE_SIZE - 4))
    
    def _draw_building_outline(self, building):
        """Draw a building's outline and entry points."""
        x = building.x * TILE_SIZE
        y = building.y * TILE_SIZE
        w = building.width * TILE_SIZE
        h = building.height * TILE_SIZE
        
        # Building outline
        pygame.draw.rect(self.terrain_surface, (70, 70, 80),
                        (x, y, w, h), 2)
        
        # Entry points (green markers)
        for ex, ey in building.entry_points:
            entry_x = ex * TILE_SIZE + TILE_SIZE // 2
            entry_y = ey * TILE_SIZE + TILE_SIZE // 2
            pygame.draw.circle(self.terrain_surface, (60, 140, 80),
                             (entry_x, entry_y), 4)
            pygame.draw.circle(self.terrain_surface, (80, 180, 100),
                             (entry_x, entry_y), 4, 1)
        
        # Building name label
        label = self.small_font.render(building.name, True, (100, 110, 120))
        label_x = x + (w - label.get_width()) // 2
        label_y = y + h // 2 - 6
        self.terrain_surface.blit(label, (label_x, label_y))
    
    def _draw_zones(self):
        """Draw map zones (spawn points, objectives, etc.)."""
        for zone_id, zone in self.world.map.zones.items():
            x = zone['x'] * TILE_SIZE
            y = zone['y'] * TILE_SIZE
            w = zone['width'] * TILE_SIZE
            h = zone['height'] * TILE_SIZE
            
            # Zone color based on type
            if zone['type'] == 'spawn':
                if zone.get('team') == 'player':
                    color = (40, 100, 60, 80)  # Green tint
                    border_color = (60, 150, 80)
                else:
                    color = (100, 40, 40, 80)  # Red tint
                    border_color = (150, 60, 60)
            elif zone['type'] == 'capture':
                color = (80, 80, 40, 80)  # Yellow tint
                border_color = (150, 150, 60)
            elif zone['type'] == 'extraction':
                color = (40, 60, 100, 80)  # Blue tint
                border_color = (60, 100, 180)
            else:
                color = (60, 60, 60, 80)
                border_color = (100, 100, 100)
            
            # Draw semi-transparent zone fill
            zone_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            zone_surf.fill(color)
            self.terrain_surface.blit(zone_surf, (x, y))
            
            # Draw border
            pygame.draw.rect(self.terrain_surface, border_color,
                           (x, y, w, h), 2)
            
            # Zone label
            zone_name = zone.get('name', zone_id)
            label = self.small_font.render(zone_name, True, border_color)
            self.terrain_surface.blit(label, (x + 4, y + 4))
    
    def log(self, msg: str):
        """Add message to world log (convenience method)."""
        self.world.log(msg)
    
    # =========================================================================
    # Drawing Methods
    # =========================================================================
    
    def draw(self):
        """Main draw method - renders entire UI."""
        # Check if map changed and regenerate terrain if needed
        if self.world.map.name != self.current_map_name:
            self._generate_terrain_surface()
        
        # Draw terrain
        self.screen.blit(self.terrain_surface, (0, 0))
        
        # Draw grid overlay if enabled
        if self.show_grid:
            self._draw_grid()
        
        # Draw hover tile info
        if self.hover_tile:
            self._draw_hover_info()
        
        # Draw selection highlight
        if self.selected:
            self._draw_selection_highlight()
        
        # Draw right panel (HUD)
        self._draw_panel()
        
        # Draw command input box
        self._draw_input_box()
    
    def _draw_grid(self):
        """Draw tile grid overlay."""
        grid_color = (40, 50, 60)
        
        for x in range(0, MAP_PIXEL_W, TILE_SIZE):
            pygame.draw.line(self.screen, grid_color, 
                           (x, 0), (x, MAP_PIXEL_H), 1)
        
        for y in range(0, MAP_PIXEL_H, TILE_SIZE):
            pygame.draw.line(self.screen, grid_color,
                           (0, y), (MAP_PIXEL_W, y), 1)
    
    def _draw_hover_info(self):
        """Draw terrain info at cursor position."""
        mx, my = pygame.mouse.get_pos()
        
        if mx >= MAP_W:
            return
        
        tx = mx // TILE_SIZE
        ty = my // TILE_SIZE
        
        terrain_info = self.world.get_terrain_info(mx, my)
        
        # Info box background
        info_w = 140
        info_h = 70
        info_x = min(mx + 15, MAP_W - info_w - 5)
        info_y = min(my + 15, HEIGHT - info_h - 5)
        
        info_surf = pygame.Surface((info_w, info_h), pygame.SRCALPHA)
        info_surf.fill((10, 20, 30, 200))
        self.screen.blit(info_surf, (info_x, info_y))
        
        # Info text
        lines = [
            f"Tile: ({tx}, {ty})",
            f"Type: {terrain_info['name']}",
            f"Cover: {int(terrain_info['cover_bonus'] * 100)}%",
            f"Move: {terrain_info['movement_cost']:.1f}x",
        ]
        
        for i, line in enumerate(lines):
            text = self.small_font.render(line, True, COL_TEXT)
            self.screen.blit(text, (info_x + 5, info_y + 5 + i * 15))
    
    def _draw_selection_highlight(self):
        """Draw highlight around selected unit/squad and movement path."""
        if not hasattr(self.selected, 'x'):
            return

        x, y = int(self.selected.x), int(self.selected.y)

        # Pulsing selection circle
        pulse = int(pygame.time.get_ticks() / 100) % 10
        radius = 26 + pulse // 2
        pygame.draw.circle(self.screen, COL_HIGHLIGHT, (x, y), radius, 2)

        # Draw movement path if unit has one
        if hasattr(self.selected, 'path_follower'):
            pf = self.selected.path_follower
            if pf.has_path() and pf.current_waypoint < len(pf.path):
                # Draw path line
                points = [(x, y)]
                for i in range(pf.current_waypoint, len(pf.path)):
                    px, py = pf.path[i]
                    points.append((int(px), int(py)))

                if len(points) > 1:
                    pygame.draw.lines(self.screen, (60, 180, 120), False, points, 2)

                    # Draw waypoint markers
                    for px, py in points[1:]:
                        pygame.draw.circle(self.screen, (80, 200, 140), (px, py), 4, 1)

        # Draw order destination marker
        if hasattr(self.selected, 'order') and self.selected.order[0] == 'move':
            dest = self.selected.order[1]
            if dest:
                dx, dy = int(dest[0]), int(dest[1])
                # Pulsing destination marker
                marker_pulse = (pygame.time.get_ticks() // 300) % 2
                marker_size = 6 + marker_pulse * 2
                pygame.draw.rect(self.screen, (100, 220, 160),
                               (dx - marker_size, dy - marker_size,
                                marker_size * 2, marker_size * 2), 2)
    
    def _draw_panel(self):
        """Draw the right-side HUD panel."""
        # Panel background
        s = pygame.Surface((PANEL_W, HEIGHT), pygame.SRCALPHA)
        s.fill((8, 20, 40, 220))
        self.screen.blit(s, (MAP_W, 0))
        
        # Title
        self.screen.blit(self.big.render('URBAN LEGEND', True, COL_TEXT), 
                        (MAP_W + 18, 10))
        self.screen.blit(self.font.render(f'Map: {self.world.map.name}', True, COL_TEXT),
                        (MAP_W + 18, 36))
        
        # Draw interactive buttons
        for btn in self.buttons:
            btn.draw(self.screen)
        
        # Selected unit summary
        self.screen.blit(self.font.render('Selected:', True, COL_TEXT),
                        (MAP_W + 18, 400))
        
        if self.selected:
            info_lines = self._get_selected_info()
            for i, line in enumerate(info_lines):
                self.screen.blit(self.font.render(line, True, COL_TEXT),
                               (MAP_W + 18, 425 + i * 20))
        else:
            self.screen.blit(self.font.render('None', True, (120, 160, 180)),
                           (MAP_W + 18, 425))
        
        # Terrain info for selected
        if self.selected and hasattr(self.selected, 'x'):
            terrain_info = self.world.get_terrain_info(self.selected.x, 
                                                       self.selected.y)
            self.screen.blit(self.font.render(
                f'Terrain: {terrain_info["name"]}', True, (140, 180, 200)),
                (MAP_W + 18, 490))
            self.screen.blit(self.font.render(
                f'Cover: {int(terrain_info["cover_bonus"] * 100)}%', 
                True, (140, 180, 200)),
                (MAP_W + 18, 510))
        
        # Event log
        self.screen.blit(self.font.render('Event Log:', True, COL_TEXT),
                        (MAP_W + 18, 540))
        
        for i, ln in enumerate(list(self.world.log_lines)[:10]):
            # Truncate long lines
            display_ln = ln[:38] + '...' if len(ln) > 40 else ln
            self.screen.blit(self.small_font.render(display_ln, True, (140, 200, 220)),
                           (MAP_W + 18, 565 + i * 18))
    
    def _get_selected_info(self) -> list:
        """Get info lines for selected unit."""
        s = self.selected
        lines = []
        
        if hasattr(s, 'units'):
            # Squad
            alive = len([u for u in s.units if u.alive])
            total_ammo = sum(u.ammo for u in s.units if u.alive)
            avg_cover = s.get_average_cover() if hasattr(s, 'get_average_cover') else 0
            lines.append(f'{s.name}')
            lines.append(f'Units: {alive}/{len(s.units)}')
            lines.append(f'Ammo: {total_ammo}')
            lines.append(f'Avg Cover: {int(avg_cover * 100)}%')
        elif hasattr(s, 'vtype'):
            # Vehicle
            lines.append(f'{s.name} ({s.vtype})')
            lines.append(f'HP: {int(s.hp)}/{s.max_hp}')
            lines.append(f'Ammo: {s.ammo}')
            lines.append(f'Fuel: {int(s.fuel)}%')
        elif hasattr(s, 'ammo') and not hasattr(s, 'units'):
            # Drone
            lines.append(f'{s.name} (Drone)')
            lines.append(f'HP: {int(s.hp)}/{s.max_hp}')
            lines.append(f'Ammo: {s.ammo}')
        
        return lines
    
    def _draw_input_box(self):
        """Draw the command input box at the bottom."""
        box_rect = pygame.Rect(12, HEIGHT - 46, MAP_W - 24, 36)
        pygame.draw.rect(self.screen, (2, 10, 18), box_rect)
        pygame.draw.rect(self.screen, (60, 140, 200), box_rect, 2)
        
        # Prompt
        prompt = '> '
        prompt_surf = self.font.render(prompt, True, (100, 150, 180))
        self.screen.blit(prompt_surf, (18, HEIGHT - 40))
        
        # Input text
        txt = self.font.render(self.input_text, True, (200, 240, 255))
        self.screen.blit(txt, (18 + prompt_surf.get_width(), HEIGHT - 40))
        
        # Cursor blink
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            cursor_x = 18 + prompt_surf.get_width() + txt.get_width() + 2
            pygame.draw.line(self.screen, (200, 240, 255),
                           (cursor_x, HEIGHT - 42),
                           (cursor_x, HEIGHT - 18), 2)
    
    # =========================================================================
    # Input Handling
    # =========================================================================
    
    def click_map(self, pos):
        """Handle left click on map."""
        x, y = pos
        
        # Check squads
        for s in self.world.squads + self.world.vehicles + self.world.drones:
            if hasattr(s, 'contains_point') and s.contains_point(x, y):
                self.selected = s
                self.world.log(f'Selected {s.name}')
                return True
            if hasattr(s, 'x') and abs(x - s.x) < 16 and abs(y - s.y) < 12:
                self.selected = s
                self.world.log(f'Selected {s.name}')
                return True
        
        return False
    
    def right_click_map(self, pos):
        """Handle right click on map (issue move order)."""
        x, y = pos
        
        if self.selected is None:
            self.world.log('No selection')
            return
        
        # Check if target position is passable
        is_vehicle = hasattr(self.selected, 'vtype')
        if not self.world.map.is_passable(x, y, is_vehicle):
            terrain_info = self.world.get_terrain_info(x, y)
            self.world.log(f'Cannot move there: {terrain_info["name"]}')
            return
        
        if hasattr(self.selected, 'set_order'):
            self.selected.set_order('move', (x, y))
            self.world.log(f'Ordered {self.selected.name} to move to ({int(x)}, {int(y)})')
        else:
            self.selected.x, self.selected.y = x, y
            self.world.log(f'Moved {self.selected.name} to ({int(x)}, {int(y)})')
    
    def click_panel(self, pos) -> bool:
        """
        Handle click on the panel area (buttons).
        
        Args:
            pos: Mouse position (x, y)
            
        Returns:
            True if a button was clicked, False otherwise
        """
        x, y = pos
        if x < MAP_W:
            return False
        
        for btn in self.buttons:
            if btn.handle_click(pos):
                return True
        return False
    
    def submit(self, parser, commander):
        """Submit typed command."""
        txt = self.input_text.strip()
        self.input_text = ''
        
        if not txt:
            return
        
        # Check for map change command
        if txt.lower().startswith('map '):
            map_name = txt[4:].strip().lower().replace(' ', '_')
            if self.world.change_map(map_name):
                self._generate_terrain_surface()
            return
        
        parsed = parser.parse(txt)
        self.world.log(f'CMD: {txt}')
        commander.execute(parsed)
    
    def toggle_grid(self):
        """Toggle grid overlay display."""
        self.show_grid = not self.show_grid
        self.world.log(f'Grid: {"ON" if self.show_grid else "OFF"}')
    
    def _repr_selected(self):
        """Get string representation of selected unit."""
        s = self.selected
        if hasattr(s, 'units'):
            return f'{s.name} Units:{len(s.units)}'
        if hasattr(s, 'vtype'):
            return f'{s.name} {s.vtype} HP:{s.hp} Ammo:{s.ammo}'
        if hasattr(s, 'ammo') and not hasattr(s, 'units'):
            return f'{s.name} Drone HP:{s.hp} Ammo:{s.ammo}'
        return str(s)
