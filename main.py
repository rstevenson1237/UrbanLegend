import pygame, sys, time
from world import World
from ui import UI
from nlp_parser import CommandParser
from commander import Commander
from tutorial import Tutorial
from save_load import save, load

WIDTH, HEIGHT = 1280, 780
MAP_W = 960

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Alpha1.1.1 - Urban Legend (Blue HUD)')
    clock = pygame.time.Clock()

    world = World()
    parser = CommandParser(world)
    ui = UI(screen, world)
    commander = Commander(world, ui)
    tutorial = Tutorial(world, ui, commander)

    running = True
    mouse_down = False

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
                    world.paused = not world.paused; world.log('Paused' if world.paused else 'Unpaused')
                elif ev.key == pygame.K_f:
                    world.fast = not world.fast; world.log('Fast' if world.fast else 'Normal')
                elif ev.key == pygame.K_s:
                    save(world)
                elif ev.key == pygame.K_l:
                    load(world)
                elif ev.key == pygame.K_d:
                    if ui.selected is None:
                        if world.drones:
                            d = world.drones[0]; d.controlled = not d.controlled; world.log(f'Controlling {d.name}' if d.controlled else f'Released {d.name}')
                    else:
                        if hasattr(ui.selected,'controlled'):
                            ui.selected.controlled = not ui.selected.controlled; world.log(f'{'Controlling' if ui.selected.controlled else 'Released'} {ui.selected.name}')
                elif ev.key == pygame.K_v:
                    if ui.selected is None:
                        if world.vehicles:
                            v = world.vehicles[0]; v.controlled = not v.controlled; world.log(f'Controlling {v.name}' if v.controlled else f'Released {v.name}')
                    else:
                        if hasattr(ui.selected,'controlled'):
                            ui.selected.controlled = not ui.selected.controlled; world.log(f'{'Controlling' if ui.selected.controlled else 'Released'} {ui.selected.name}')
                else:
                    if ev.unicode: ui.input_text += ev.unicode
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                mx,my = ev.pos
                if ev.button == 1:
                    if mx < MAP_W: ui.click_map((mx,my))
                elif ev.button == 3:
                    if mx < MAP_W: ui.right_click_map((mx,my))
        world.update(dt); tutorial.update()
        screen.fill((2,8,18)); pygame.draw.rect(screen, (6,14,30), (0,0,MAP_W,HEIGHT))
        for s in world.squads: s.draw(screen, (80,220,180) if s.team=='player' else (220,100,100))
        for v in world.vehicles: v.draw(screen)
        for d in world.drones: d.draw(screen)
        ui.draw(); pygame.display.flip()
    pygame.quit(); sys.exit()
if __name__ == '__main__': main()
