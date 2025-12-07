import json, os
SAVE_FILE = os.path.join(os.path.expanduser('~'), 'alpha1_1_1_save.json')
def save(world, path=SAVE_FILE):
    try:
        data={'squads':[], 'vehicles':[], 'drones':[]}
        for s in world.squads:
            data['squads'].append({'name':s.name,'team':s.team,'x':s.x,'y':s.y,'units':[{'hp':u.hp,'ammo':u.ammo,'alive':u.alive,'x':u.x,'y':u.y} for u in s.units]})
        for v in world.vehicles:
            data['vehicles'].append({'name':v.name,'team':v.team,'x':v.x,'y':v.y,'hp':v.hp,'ammo':v.ammo,'fuel':v.fuel,'vtype':v.vtype})
        for d in world.drones:
            data['drones'].append({'name':d.name,'team':d.team,'x':d.x,'y':d.y,'hp':d.hp,'ammo':d.ammo})
        with open(path,'w') as f: json.dump(data,f,indent=2)
        world.log(f'Saved to {path}')
    except Exception as e:
        world.log(f'Save failed: {e}')
def load(world, path=SAVE_FILE):
    if not os.path.exists(path): world.log('No save'); return
    try:
        with open(path,'r') as f: data=json.load(f)
        world.squads.clear(); world.vehicles.clear(); world.drones.clear()
        from units import Squad, Unit, Vehicle, Drone
        for sdata in data.get('squads',[]):
            s=Squad(sdata['name'], sdata['team'], sdata['x'], sdata['y'])
            for u in sdata.get('units',[]):
                uu=Unit('u', sdata['team'], u.get('x', s.x), u.get('y', s.y)); uu.hp=u.get('hp',uu.hp); uu.ammo=u.get('ammo',uu.ammo); uu.alive=u.get('alive', True)
                s.add_unit(uu)
            world.squads.append(s)
        for v in data.get('vehicles',[]):
            vv=Vehicle(v['name'], v['team'], v['x'], v['y'], v.get('vtype','APC')); vv.hp=v.get('hp',vv.hp); vv.ammo=v.get('ammo',vv.ammo); vv.fuel=v.get('fuel',vv.fuel)
            world.vehicles.append(vv)
        for d in data.get('drones',[]):
            dd=Drone(d['name'], d['team'], d['x'], d['y']); dd.hp=d.get('hp',dd.hp); dd.ammo=d.get('ammo',dd.ammo); world.drones.append(dd)
        world.log('Loaded save')
    except Exception as e:
        world.log(f'Load failed: {e}')
