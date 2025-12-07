# Urban Legend Development Plan

After reviewing the codebase, here's my assessment and a structured plan for your development team.

---

## Current State Summary

**What's Working:**
- Core game loop with squads, drones, and vehicles
- Natural language command parser with fuzzy matching
- Basic combat resolution system
- Save/load functionality
- Tutorial framework
- Blue HUD aesthetic foundation

**Key Gaps:**
- No terrain, obstacles, or map structure
- Enemy AI is random/trivial
- No win/lose conditions or mission objectives
- UI buttons are non-functional (visual only)
- No pathfinding system
- Limited feedback and "game feel"

---

## Plan 1: Increasing Complexity

### Phase 1.1 — Map & Terrain System (Priority: High)
1. **Define a tile-based or zone-based map structure** — Add a `Map` class in a new `map.py` module that stores terrain types (urban, open, cover, water, impassable)
2. **Implement cover mechanics** — Units in cover zones receive damage reduction; expose a `cover_bonus` property
3. **Add building interiors** — Define enterable structures with line-of-sight blocking
4. **Create 3-4 distinct map layouts** — Store as JSON or hardcoded configurations for alpha testing

### Phase 1.2 — Pathfinding (Priority: High)
1. **Implement A* pathfinding** — New `pathfinding.py` module; units path around obstacles
2. **Integrate pathfinding with `Squad.update()`** — Replace direct vector movement with waypoint following
3. **Add pathfinding for vehicles** — Respect road/terrain restrictions (tanks can cross rubble, APCs cannot)

### Phase 1.3 — Enhanced Unit Abilities (Priority: Medium)
1. **Add unit classes within squads** — Rifleman, Grenadier, Medic, Sniper with distinct stats
2. **Implement special abilities** — Grenade throw (area damage), Medic heal, Sniper overwatch
3. **Add cooldown tracking per ability** — Extend `Unit` class with `abilities: dict` and `cooldowns: dict`
4. **Vehicle abilities** — APC: deploy smoke, Tank: artillery strike with delay

### Phase 1.4 — Advanced Enemy AI (Priority: High)
1. **Replace random AI with behavior trees** — New `ai.py` module with `BehaviorTree` class
2. **Implement tactical behaviors:**
   - Flanking (detect player position, route around)
   - Retreat when outnumbered
   - Focus fire on weakest unit
   - Use cover positions
3. **Add AI difficulty levels** — Easy (delayed reactions), Normal, Hard (optimal play)
4. **Enemy coordination** — Squads communicate targets to avoid overkill

### Phase 1.5 — Mission & Objective System (Priority: High)
1. **Create `Mission` class** — Tracks objectives, time limits, success/fail conditions
2. **Implement objective types:**
   - Eliminate all enemies
   - Capture and hold zone for X seconds
   - Escort VIP unit to extraction
   - Defend position for X waves
3. **Add mission briefing screen** — Display objectives before gameplay starts
4. **Victory/defeat screens** — Show stats (casualties, time, accuracy)

### Phase 1.6 — Progression Systems (Priority: Low, Post-Alpha)
1. **Experience and veterancy** — Units gain XP, improve accuracy/speed
2. **Persistent roster** — Carry surviving units between missions
3. **Unlock system** — New unit types or abilities unlocked by campaign progress

---

## Plan 2: Polishing the User Interface

### Phase 2.1 — Make UI Interactive (Priority: Critical)
1. **Implement button click handling** — Add `Button` class in `ui.py` with `rect`, `callback`, `hover_state`
2. **Wire up existing button labels:**
   - "Take Control (D)" → toggle control on selected
   - "Hold Order" → issue hold command
   - "Attack Order" → issue attack command
   - "Resupply Selected" → trigger resupply
   - Pause/Fast/Save/Load → call existing functions
3. **Add hover and click feedback** — Color shift on hover, brief flash on click

### Phase 2.2 — Visual Feedback & Polish (Priority: High)
1. **Unit selection indicators** — Draw pulsing circle around selected squad/unit
2. **Order visualization** — Draw line from unit to destination when move ordered
3. **Damage numbers** — Floating text showing damage dealt (fade out over 0.5s)
4. **Muzzle flash and hit effects** — Simple particle sprites on fire/impact
5. **Health bars** — Small bars above squads showing aggregate HP

### Phase 2.3 — Improved Information Display (Priority: High)
1. **Minimap** — Add 200×200 minimap in corner showing unit positions and fog
2. **Unit tooltips** — Hover over unit shows detailed stats panel
3. **Command feedback toast** — Brief message confirming command ("Alpha_1: Moving to position")
4. **Engagement indicators** — Flashing icon or line between squads in combat

### Phase 2.4 — Sound Design (Priority: Medium)
1. **Replace placeholder beep.wav** — Source or create actual sound assets
2. **Implement sound manager** — `sound.py` with `play(event_name)` interface
3. **Add sounds for:**
   - Gunfire (per unit type)
   - Explosions (grenades, vehicle destruction)
   - UI clicks and confirmations
   - Ambient battlefield sounds
   - Voice lines for command acknowledgment (optional, high polish)

### Phase 2.5 — Input & Accessibility (Priority: Medium)
1. **Camera pan with arrow keys or WASD** — Allow map scrolling for larger maps
2. **Zoom in/out** — Mouse wheel or +/- keys
3. **Keyboard shortcuts panel** — Toggle overlay showing all hotkeys
4. **Command history** — Up arrow recalls previous commands
5. **Tab autocomplete** — For unit names in command input

### Phase 2.6 — Visual Theming Consistency (Priority: Low)
1. **Design grid overlay** — Subtle tactical grid on map
2. **Improve unit sprites** — Replace circles/rectangles with simple but distinct shapes
3. **Add faction color coding** — Consistent blue vs red with clear contrast
4. **Night/day variants** — Palette swap for atmosphere (stretch goal)

---

## Plan 3: Making It Fun to Play

### Phase 3.1 — Core Loop Tightening (Priority: Critical)
1. **Reduce time-to-action** — First engagement should happen within 30 seconds of mission start
2. **Increase unit responsiveness** — Reduce perceived input lag; units acknowledge immediately
3. **Balance lethality** — Tune damage so firefights last 5-15 seconds, not instant or endless
4. **Add tension mechanics** — Ammo scarcity, reinforcement timers, shrinking safe zone

### Phase 3.2 — Player Agency & Meaningful Choices (Priority: High)
1. **Pre-mission loadout** — Choose which squads/vehicles to deploy (limited slots)
2. **Risk/reward positioning** — Aggressive positions deal more damage but take more
3. **Resource management** — Limited resupply points on map; decide when to pull back
4. **Branching mission outcomes** — Save civilians = bonus units; speed bonus = extra supplies

### Phase 3.3 — Combat Feel Improvements (Priority: High)
1. **Suppression system** — Heavy fire pins units, reducing accuracy and speed
2. **Morale matters more** — Low morale causes hesitation, retreat, or surrender
3. **Flanking bonus** — Attacking from sides/rear deals bonus damage
4. **Overkill prevention** — Dead units don't absorb shots; shots retarget

### Phase 3.4 — Moment-to-Moment Excitement (Priority: Medium)
1. **Critical hits** — Random chance for high damage with visual/audio flourish
2. **Last stand mechanic** — Final squad member gets accuracy boost
3. **Killcam/highlight reel** — Brief slowdown on important kills (optional)
4. **Dynamic events** — Random reinforcements, civilian crossings, weather changes

### Phase 3.5 — Onboarding & Learning Curve (Priority: High)
1. **Expand tutorial** — Cover all command types, not just move/attack
2. **Difficulty ramp** — First mission is trivially easy; complexity introduced gradually
3. **Hint system** — Detect player struggling (high casualties) and offer tips
4. **Practice/sandbox mode** — Spawn custom units to experiment

### Phase 3.6 — Replayability (Priority: Medium)
1. **Scoring system** — Grade missions (A-F) based on speed, casualties, objectives
2. **Leaderboard (local)** — Track best scores per mission
3. **Random mission generator** — Procedural objective placement for endless mode
4. **Ironman mode** — No save/load during mission; permadeath for tension

---

## Recommended Priority Order

| Sprint | Focus Area | Key Deliverables |
|--------|-----------|------------------|
| 1 | Playability Foundation | Interactive UI buttons, selection feedback, basic pathfinding |
| 2 | Combat Feel | Damage tuning, health bars, engagement indicators, flanking bonus |
| 3 | Map & Terrain | Tile system, cover mechanics, 2 map layouts |
| 4 | Enemy AI | Behavior tree basics, cover-seeking, retreat logic |
| 5 | Missions | Objective system, win/lose conditions, 3 missions |
| 6 | Polish | Sound, minimap, tooltips, visual effects |
| 7 | Depth | Unit abilities, suppression, progression |
| 8 | Replayability | Scoring, random generation, difficulty modes |

---

## Questions for the Team

Before starting, clarify these with stakeholders:

1. **Scope target** — Are we aiming for 5 missions or 20? Campaign or skirmish focus?
2. **Art direction** — Will we get proper sprites, or should we design around geometric primitives?
3. **NLP investment** — Is the natural language parser a core differentiator, or should we add traditional RTS controls as primary input?
4. **Platform targets** — Linux only, or cross-platform? This affects packaging and testing.
5. **Multiplayer** — Any future plans? This affects architecture decisions now.

Let me know if you want me to expand any section into detailed technical specs or user stories.
