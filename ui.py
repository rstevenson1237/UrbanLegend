"""
User Interface for Urban Legend.
Updated with terrain rendering and map display.
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


class UI:
    """Main UI class handling rendering and input."""
    
    def __init__(self, screen, world):
        self.screen = screen
        self.world = world
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

        # Terrain surface cache (regenerated when map changes)
        self.terrain_surface = None
        self.current_map_name = None
        self._generate_terrain_surface()
    
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
        """Draw highlight around selected unit/squad."""
        if hasattr(self.selected, 'x'):
            x, y = int(self.selected.x), int(self.selected.y)
            
            # Pulsing effect
            pulse = int(pygame.time.get_ticks() / 100) % 10
            radius = 26 + pulse // 2
            
            pygame.draw.circle(self.screen, COL_HIGHLIGHT,
                             (x, y), radius, 2)
    
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
        
        # Buttons
        y = 68
        labels = [
            'Take Control (D)',
            'Hold Order',
            'Attack Order',
            'Resupply Selected',
            'Pause (SPACE)',
            'Fast (F)',
            'Save (S)',
            'Load (L)',
            f'Grid (G): {"ON" if self.show_grid else "OFF"}',
        ]
        
        for lab in labels:
            pygame.draw.rect(self.screen, (10, 30, 50),
                           (MAP_W + 18, y, PANEL_W - 36, 28), 
                           border_radius=6)
            self.screen.blit(self.font.render(lab, True, COL_TEXT),
                           (MAP_W + 26, y + 6))
            y += 36
        
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
