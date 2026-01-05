"""
Save/Load system for Urban Legend.
Supports saving and loading complete game state including map.
"""

import json
import os

SAVE_FILE = os.path.join(os.path.expanduser('~'), 'alpha1_2_0_save.json')


def save(world, path=SAVE_FILE):
    """
    Save the current game state to a JSON file.
    Includes map data, all units, and game settings.
    """
    try:
        data = {
            'version': '1.3.0',
            'map_name': world.map.name,
            'tick': world.tick,
            'paused': world.paused,
            'fast': world.fast,
            'squads': [],
            'vehicles': [],
            'drones': [],
        }
        
        # Save squads
        for s in world.squads:
            squad_data = {
                'name': s.name,
                'team': s.team,
                'x': s.x,
                'y': s.y,
                'order': list(s.order) if s.order[1] else [s.order[0], None],
                'path': s.path_follower.path if hasattr(s, 'path_follower') else [],
                'path_waypoint': s.path_follower.current_waypoint if hasattr(s, 'path_follower') else 0,
                'units': []
            }
            for u in s.units:
                squad_data['units'].append({
                    'name': u.name,
                    'hp': u.hp,
                    'ammo': u.ammo,
                    'morale': u.morale,
                    'alive': u.alive,
                    'x': u.x,
                    'y': u.y,
                    'in_cover': u.in_cover,
                    'cover_bonus': u.cover_bonus,
                })
            data['squads'].append(squad_data)
        
        # Save vehicles
        for v in world.vehicles:
            data['vehicles'].append({
                'name': v.name,
                'team': v.team,
                'x': v.x,
                'y': v.y,
                'hp': v.hp,
                'ammo': v.ammo,
                'fuel': v.fuel,
                'vtype': v.vtype,
                'controlled': v.controlled,
                'path': v.path_follower.path if hasattr(v, 'path_follower') else [],
                'path_waypoint': v.path_follower.current_waypoint if hasattr(v, 'path_follower') else 0,
            })
        
        # Save drones
        for d in world.drones:
            data['drones'].append({
                'name': d.name,
                'team': d.team,
                'x': d.x,
                'y': d.y,
                'hp': d.hp,
                'ammo': d.ammo,
                'controlled': d.controlled,
                'auto_target': list(d.auto_target) if d.auto_target else None,
            })
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        world.log(f'Game saved to {path}')
        
    except Exception as e:
        world.log(f'Save failed: {e}')


def load(world, path=SAVE_FILE):
    """
    Load game state from a JSON file.
    Restores map, units, and game settings.
    """
    if not os.path.exists(path):
        world.log('No save file found')
        return False
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Check version compatibility
        version = data.get('version', '1.0.0')
        if version < '1.3.0':
            world.log(f'Warning: Loading save from older version {version}')
        
        # Load map
        map_name = data.get('map_name', 'urban_district')
        # Convert map name to function key format if needed
        map_key = map_name.lower().replace(' ', '_')
        
        from map import get_map, list_maps
        available_maps = list_maps()
        
        if map_key in available_maps:
            world.map = get_map(map_key)
        else:
            world.log(f'Map "{map_name}" not found, using default')
            world.map = get_map('urban_district')
        
        # Restore game state
        world.tick = data.get('tick', 0.0)
        world.paused = data.get('paused', False)
        world.fast = data.get('fast', False)
        
        # Clear existing units
        world.squads.clear()
        world.vehicles.clear()
        world.drones.clear()
        
        from units import Squad, Unit, Vehicle, Drone
        
        # Load squads
        for sdata in data.get('squads', []):
            s = Squad(sdata['name'], sdata['team'], sdata['x'], sdata['y'])
            
            # Restore order
            if sdata.get('order'):
                order_type = sdata['order'][0]
                order_payload = tuple(sdata['order'][1]) if sdata['order'][1] else None
                s.order = (order_type, order_payload)

            # Restore path state
            if sdata.get('path'):
                s.path_follower.path = [tuple(p) for p in sdata['path']]
                s.path_follower.current_waypoint = sdata.get('path_waypoint', 0)

            # Load units
            for udata in sdata.get('units', []):
                u = Unit(udata.get('name', 'unit'), sdata['team'],
                        udata.get('x', s.x), udata.get('y', s.y))
                u.hp = udata.get('hp', 100)
                u.ammo = udata.get('ammo', 30)
                u.morale = udata.get('morale', 0.8)
                u.alive = udata.get('alive', True)
                u.in_cover = udata.get('in_cover', False)
                u.cover_bonus = udata.get('cover_bonus', 0.0)
                s.units.append(u)
            
            world.squads.append(s)
        
        # Load vehicles
        for vdata in data.get('vehicles', []):
            v = Vehicle(vdata['name'], vdata['team'],
                       vdata['x'], vdata['y'], vdata.get('vtype', 'APC'))
            v.hp = vdata.get('hp', v.hp)
            v.ammo = vdata.get('ammo', v.ammo)
            v.fuel = vdata.get('fuel', v.fuel)
            v.controlled = vdata.get('controlled', False)

            # Restore path state
            if vdata.get('path'):
                v.path_follower.path = [tuple(p) for p in vdata['path']]
                v.path_follower.current_waypoint = vdata.get('path_waypoint', 0)

            world.vehicles.append(v)
        
        # Load drones
        for ddata in data.get('drones', []):
            d = Drone(ddata['name'], ddata['team'], ddata['x'], ddata['y'])
            d.hp = ddata.get('hp', d.hp)
            d.ammo = ddata.get('ammo', d.ammo)
            d.controlled = ddata.get('controlled', False)
            if ddata.get('auto_target'):
                d.auto_target = tuple(ddata['auto_target'])
            world.drones.append(d)
        
        world.log(f'Game loaded from {path}')
        return True
        
    except Exception as e:
        world.log(f'Load failed: {e}')
        return False


def get_save_info(path=SAVE_FILE):
    """
    Get information about a save file without fully loading it.
    Useful for displaying save slots.
    """
    if not os.path.exists(path):
        return None
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        return {
            'version': data.get('version', 'unknown'),
            'map_name': data.get('map_name', 'unknown'),
            'tick': data.get('tick', 0),
            'squad_count': len(data.get('squads', [])),
            'file_path': path,
            'file_size': os.path.getsize(path),
        }
    except Exception:
        return None
