"""
Natural Language Parser for Urban Legend.
Parses text commands into structured action data.
"""

import re
from difflib import get_close_matches

ACTION_KEYWORDS = {
    'attack': ['attack', 'engage', 'strike', 'assault', 'charge', 'hit', 'destroy', 'fight'],
    'move': ['move', 'advance', 'go', 'push', 'shift', 'march', 'proceed', 'head'],
    'hold': ['hold', 'defend', 'stay', 'hold position', 'stay put', 'stop'],
    'scout': ['scout', 'recon', 'observe', 'survey', 'spot', 'reconnoiter'],
    'retreat': ['retreat', 'fall back', 'withdraw', 'pull back', 'fallback'],
    'resupply': ['resupply', 'rearm', 'refill', 'replenish', 'reload'],
    'flank': ['flank', 'flanking', 'encircle', 'circle', 'surround'],
}

DIR_KEYWORDS = {
    'north': ['north', 'n', 'up', 'top'],
    'south': ['south', 's', 'down', 'bottom'],
    'east': ['east', 'e'],
    'west': ['west', 'w'],
    'left': ['left'],
    'right': ['right'],
    'center': ['center', 'centre', 'middle'],
}

GROUP_KEYWORDS = {
    'all': ['all', 'everyone', 'all units', 'everybody', 'everything'],
    'alpha': ['alpha', 'alpha squad', 'alpha_1', 'alpha1', 'alpha team'],
    'bravo': ['bravo', 'bravo squad', 'bravo team'],
    'drones': ['drone', 'drones', 'uav', 'uavs'],
    'vehicles': ['vehicle', 'vehicles', 'apc', 'apcs', 'tank', 'tanks', 'armor'],
    'enemy': ['enemy', 'enemies', 'hostiles', 'targets'],
}


class CommandParser:
    """Parses natural language commands into structured data."""
    
    def __init__(self, world):
        self.world = world
    
    def parse(self, text):
        """
        Parse a text command into structured data.
        
        Returns:
            dict with keys: raw, action, group, target_entity, direction, confidence
        """
        txt = text.lower().strip()
        txt = re.sub(r'[^\w\s]', ' ', txt)
        tokens = txt.split()
        
        # Score actions
        scores = {a: 0 for a in ACTION_KEYWORDS}
        for action, words in ACTION_KEYWORDS.items():
            for word in words:
                if word in txt:
                    scores[action] += 1.4
            for token in tokens:
                for word in words:
                    if token.startswith(word[:3]) and len(token) > 2:
                        scores[action] += 0.35
        
        best = max(scores.items(), key=lambda x: x[1])
        action = best[0] if best[1] > 0 else 'unknown'
        
        group = None
        target_entity = None
        direction = None
        
        # Detect explicit unit numbers (e.g., "drone 1", "alpha_2")
        drone_match = re.search(r'drone\s*(\d+)', txt)
        if drone_match:
            target_entity = f'drone_{int(drone_match.group(1))}'
        
        alpha_match = re.search(r'alpha[\s_]*(\d+)', txt)
        if alpha_match:
            target_entity = f'alpha_{int(alpha_match.group(1))}'
        
        # Detect group names
        for g, words in GROUP_KEYWORDS.items():
            for w in words:
                if w in txt:
                    group = g
                    break
            if group:
                break
        
        # Fuzzy entity detection
        if not target_entity:
            words = txt.split()
            for size in (3, 2, 1):
                for i in range(len(words) - size + 1):
                    token = '_'.join(words[i:i + size])
                    match = self._fuzzy_entity(token)
                    if match:
                        target_entity = match
                        break
                if target_entity:
                    break
        
        # Detect direction
        for d, words in DIR_KEYWORDS.items():
            for w in words:
                if w in txt:
                    direction = d
                    break
            if direction:
                break
        
        return {
            'raw': text,
            'action': action,
            'group': group,
            'target_entity': target_entity,
            'direction': direction,
            'confidence': best[1],
        }
    
    def _fuzzy_entity(self, token):
        """Find entity by fuzzy name matching."""
        names = [e.name.lower() for e in 
                (self.world.squads + self.world.vehicles + self.world.drones)]
        matches = get_close_matches(token, names, n=1, cutoff=0.5)
        return matches[0] if matches else None
