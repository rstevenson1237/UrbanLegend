"""
Urban Legend - Main Entry Point
Alpha 1.3.0 - Pathfinding Update

Controls:
    Left Click  - Select unit / Click buttons
    Right Click - Move selected unit
    Enter       - Submit command
    Space       - Pause/Unpause
    F           - Toggle fast mode
    G           - Toggle grid overlay
    D           - Take control of selected drone/vehicle
    V           - Take control of vehicle
    S           - Save game
    L           - Load game
    M           - Cycle through maps
    Escape      - Exit
    
Commands (type in input box):
    "alpha squad move north"
    "all units attack"
    "drone 1 scout east"
    "tanks hold position"
    "map urban_district" - Change map
    
Phase 2.1 Updates:
    - All panel buttons are now clickable
    - Buttons show hover feedback (color change)
    - Buttons show click feedback (brief flash)
"""

import pygame
import sys
import time
from world import World
from ui import UI
from nlp_parser import CommandParser
from commander import Commander
from tutorial import Tutorial
from save_load import save, load
from map import list_maps

WIDTH, HEIGHT = 1280, 780
MAP_W = 960


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Alpha1.2.1 - Urban Legend (Interactive UI)')
    clock = pygame.time.Clock()

    # Initialize game world
    world = World(map_name='urban_district')
    parser = CommandParser(world)
    
    # Create save/load callbacks (defined before UI so we can pass them)
    def do_save():
        save(world)
    
    def do_load():
        load(world)
        ui._generate_terrain_surface()
    
    # Initialize UI with callbacks
    ui = UI(screen, world, save_callback=do_save, load_callback=do_load)
    
    # Create commander and set it on UI (circular dependency resolved via setter)
    commander = Commander(world, ui)
    ui.set_commander(commander)
    ui.set_parser(parser)
    
    # Initialize tutorial
    tutorial = Tutorial(world, ui, commander)
    
    # Track available maps for cycling
    available_maps = list_maps()
    current_map_index = 0

    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
                
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                    
                elif ev.key == pygame.K_RETURN:
                    ui.submit(parser, commander)
                    
                elif ev.key == pygame.K_BACKSPACE:
                    ui.input_text = ui.input_text[:-1]
                    
                elif ev.key == pygame.K_SPACE:
                    world.paused = not world.paused
                    world.log('Paused' if world.paused else 'Unpaused')
                    
                elif ev.key == pygame.K_f:
                    world.fast = not world.fast
                    world.log('Fast' if world.fast else 'Normal')
                    
                elif ev.key == pygame.K_g:
                    ui.toggle_grid()
                    
                elif ev.key == pygame.K_s:
                    save(world)
                    
                elif ev.key == pygame.K_l:
                    load(world)
                    ui._generate_terrain_surface()  # Refresh terrain after load
                    
                elif ev.key == pygame.K_m:
                    # Cycle through maps
                    current_map_index = (current_map_index + 1) % len(available_maps)
                    new_map = available_maps[current_map_index]
                    if world.change_map(new_map):
                        ui._generate_terrain_surface()
                    
                elif ev.key == pygame.K_d:
                    # Drone/unit control toggle
                    if ui.selected is None:
                        if world.drones:
                            d = world.drones[0]
                            d.controlled = not d.controlled
                            world.log(f'Controlling {d.name}' if d.controlled else f'Released {d.name}')
                    else:
                        if hasattr(ui.selected, 'controlled'):
                            ui.selected.controlled = not ui.selected.controlled
                            status = 'Controlling' if ui.selected.controlled else 'Released'
                            world.log(f'{status} {ui.selected.name}')
                            
                elif ev.key == pygame.K_v:
                    # Vehicle control toggle
                    if ui.selected is None:
                        if world.vehicles:
                            v = world.vehicles[0]
                            v.controlled = not v.controlled
                            world.log(f'Controlling {v.name}' if v.controlled else f'Released {v.name}')
                    else:
                        if hasattr(ui.selected, 'controlled'):
                            ui.selected.controlled = not ui.selected.controlled
                            status = 'Controlling' if ui.selected.controlled else 'Released'
                            world.log(f'{status} {ui.selected.name}')
                else:
                    if ev.unicode:
                        ui.input_text += ev.unicode
                        
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                mx, my = ev.pos
                if ev.button == 1:  # Left click
                    if mx >= MAP_W:
                        # Click on panel (buttons)
                        ui.click_panel((mx, my))
                    else:
                        # Click on map
                        ui.click_map((mx, my))
                elif ev.button == 3:  # Right click
                    if mx < MAP_W:
                        ui.right_click_map((mx, my))
        
        # Update game state
        world.update(dt)
        tutorial.update()
        ui.update(dt)  # Update UI (button animations, hover states)
        
        # Render
        screen.fill((2, 8, 18))
        pygame.draw.rect(screen, (6, 14, 30), (0, 0, MAP_W, HEIGHT))
        
        # Draw squads with team colors
        for s in world.squads:
            color = (80, 220, 180) if s.team == 'player' else (220, 100, 100)
            s.draw(screen, color)
        
        # Draw vehicles
        for v in world.vehicles:
            v.draw(screen)
        
        # Draw drones
        for d in world.drones:
            d.draw(screen)
        
        # Draw UI overlay
        ui.draw()
        
        # Update display
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
