import re
from difflib import get_close_matches
ACTION_KEYWORDS = {
    'attack': ['attack','engage','strike','assault','charge','hit','destroy','engage'],
    'move': ['move','advance','go','push','shift','march','proceed'],
    'hold': ['hold','defend','stay','hold position','stay put'],
    'scout': ['scout','recon','observe','survey','spot'],
    'retreat': ['retreat','fall back','withdraw','pull back'],
    'resupply': ['resupply','rearm','refill','replenish'],
    'flank': ['flank','flanking','encircle','circle'],
}
DIR_KEYWORDS = {'north':['north','n'],'south':['south','s'],'east':['east','e'],'west':['west','w'],'left':['left','west'],'right':['right','east'],'center':['center','centre']}
GROUP_KEYWORDS = {'all':['all','everyone','all units','everybody'],'alpha':['alpha','alpha squad','alpha_1','alpha1'],'bravo':['bravo','bravo squad'],'drones':['drone','drones'],'vehicles':['vehicle','vehicles','apc','apcs','tank','tanks'],'enemy':['enemy','enemies','hostiles']}
class CommandParser:
    def __init__(self, world): self.world = world
    def parse(self, text):
        txt = text.lower().strip()
        txt = re.sub(r'[^\w\s]', ' ', txt)
        tokens = txt.split()
        # action scoring
        scores = {a:0 for a in ACTION_KEYWORDS}
        for a, words in ACTION_KEYWORDS.items():
            for w in words:
                if w in txt: scores[a]+=1.4
            for t in tokens:
                for w in words:
                    if t.startswith(w[:3]) and len(t)>2: scores[a]+=0.35
        best = max(scores.items(), key=lambda x: x[1])
        action = best[0] if best[1] > 0 else 'unknown'
        group=None; target_entity=None; direction=None
        # detect explicit unit numbers
        m = re.search(r'drone\s*(\d+)', txt)
        if m: target_entity = f'drone_{int(m.group(1))}'
        # detect group names
        for g, words in GROUP_KEYWORDS.items():
            for w in words:
                if w in txt: group = g; break
            if group: break
        # fuzzy entity detection by tokens
        if not target_entity:
            words = txt.split()
            for size in (3,2,1):
                for i in range(len(words)-size+1):
                    token = '_'.join(words[i:i+size])
                    match = self._fuzzy_entity(token)
                    if match: target_entity = match; break
                if target_entity: break
        for d, words in DIR_KEYWORDS.items():
            for w in words:
                if w in txt: direction = d; break
            if direction: break
        return {'raw': text, 'action': action, 'group': group, 'target_entity': target_entity, 'direction': direction, 'confidence': best[1]}
    def _fuzzy_entity(self, token):
        names = [e.name.lower() for e in (self.world.squads + self.world.vehicles + self.world.drones)]
        matches = get_close_matches(token, names, n=1, cutoff=0.5)
        return matches[0] if matches else None
