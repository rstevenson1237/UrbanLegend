"""
A* Pathfinding System for Urban Legend
Phase 1.2 Implementation

Provides:
- A* pathfinding algorithm with terrain costs
- Path smoothing for natural movement
- Separate handling for infantry and vehicles
- Integration with Map terrain system
"""

import heapq
import math
from typing import List, Tuple, Optional, Set, Dict
from map import Map, TILE_SIZE, TerrainType, TERRAIN_PROPERTIES


class PathNode:
    """Node in the A* search graph."""

    __slots__ = ['x', 'y', 'g', 'h', 'f', 'parent']

    def __init__(self, x: int, y: int, g: float = 0, h: float = 0, parent=None):
        self.x = x
        self.y = y
        self.g = g  # Cost from start
        self.h = h  # Heuristic to goal
        self.f = g + h  # Total cost
        self.parent = parent

    def __lt__(self, other):
        return self.f < other.f

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


class Pathfinder:
    """
    A* pathfinding implementation with terrain awareness.

    Features:
    - Respects terrain passability for infantry vs vehicles
    - Uses terrain movement costs for optimal paths
    - Supports 8-directional movement
    - Path caching for performance (optional)
    """

    # 8-directional movement: (dx, dy, cost_multiplier)
    DIRECTIONS = [
        (0, -1, 1.0),   # North
        (1, -1, 1.414), # NE (diagonal)
        (1, 0, 1.0),    # East
        (1, 1, 1.414),  # SE
        (0, 1, 1.0),    # South
        (-1, 1, 1.414), # SW
        (-1, 0, 1.0),   # West
        (-1, -1, 1.414) # NW
    ]

    def __init__(self, game_map: Map):
        self.map = game_map
        self.width = game_map.width
        self.height = game_map.height

        # Path cache (optional optimization)
        self._cache: Dict[Tuple, List[Tuple[int, int]]] = {}
        self._cache_max_size = 100

    def find_path(self, start_x: float, start_y: float,
                  goal_x: float, goal_y: float,
                  is_vehicle: bool = False,
                  max_iterations: int = 1000) -> Optional[List[Tuple[float, float]]]:
        """
        Find a path from start to goal using A*.

        Args:
            start_x, start_y: Starting position in pixels
            goal_x, goal_y: Goal position in pixels
            is_vehicle: True for vehicle pathfinding (restricted terrain)
            max_iterations: Safety limit to prevent infinite loops

        Returns:
            List of (x, y) waypoints in pixels, or None if no path found
        """
        # Convert to tile coordinates
        start_tx = int(start_x // TILE_SIZE)
        start_ty = int(start_y // TILE_SIZE)
        goal_tx = int(goal_x // TILE_SIZE)
        goal_ty = int(goal_y // TILE_SIZE)

        # Clamp to map bounds
        start_tx = max(0, min(start_tx, self.width - 1))
        start_ty = max(0, min(start_ty, self.height - 1))
        goal_tx = max(0, min(goal_tx, self.width - 1))
        goal_ty = max(0, min(goal_ty, self.height - 1))

        # Check if goal is reachable
        if not self.map.is_tile_passable(goal_tx, goal_ty, is_vehicle):
            # Find nearest passable tile to goal
            goal_tx, goal_ty = self._find_nearest_passable(
                goal_tx, goal_ty, is_vehicle
            )
            if goal_tx is None:
                return None

        # Check cache
        cache_key = (start_tx, start_ty, goal_tx, goal_ty, is_vehicle)
        if cache_key in self._cache:
            return self._tile_path_to_pixels(self._cache[cache_key])

        # A* algorithm
        open_set: List[PathNode] = []
        closed_set: Set[Tuple[int, int]] = set()

        start_node = PathNode(
            start_tx, start_ty,
            g=0,
            h=self._heuristic(start_tx, start_ty, goal_tx, goal_ty)
        )
        heapq.heappush(open_set, start_node)

        # Track best g-score for each position
        g_scores: Dict[Tuple[int, int], float] = {(start_tx, start_ty): 0}

        iterations = 0

        while open_set and iterations < max_iterations:
            iterations += 1

            current = heapq.heappop(open_set)

            # Goal reached
            if current.x == goal_tx and current.y == goal_ty:
                path = self._reconstruct_path(current)

                # Cache the result
                self._add_to_cache(cache_key, path)

                # Smooth and convert to pixels
                smoothed = self._smooth_path(path, is_vehicle)
                return self._tile_path_to_pixels(smoothed)

            closed_set.add((current.x, current.y))

            # Explore neighbors
            for dx, dy, base_cost in self.DIRECTIONS:
                nx, ny = current.x + dx, current.y + dy

                # Skip if out of bounds or in closed set
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                if (nx, ny) in closed_set:
                    continue

                # Skip if not passable
                if not self.map.is_tile_passable(nx, ny, is_vehicle):
                    continue

                # Check diagonal movement (prevent corner cutting)
                if dx != 0 and dy != 0:
                    if not self._can_move_diagonal(current.x, current.y, dx, dy, is_vehicle):
                        continue

                # Calculate movement cost
                terrain = self.map.get_tile(nx, ny)
                terrain_cost = self._get_terrain_cost(terrain, is_vehicle)

                # Skip impassable terrain
                if terrain_cost <= 0:
                    continue

                move_cost = base_cost / terrain_cost  # Lower terrain cost = faster = lower path cost
                tentative_g = current.g + move_cost

                # Check if this path is better
                if (nx, ny) in g_scores and tentative_g >= g_scores[(nx, ny)]:
                    continue

                g_scores[(nx, ny)] = tentative_g

                neighbor = PathNode(
                    nx, ny,
                    g=tentative_g,
                    h=self._heuristic(nx, ny, goal_tx, goal_ty),
                    parent=current
                )
                heapq.heappush(open_set, neighbor)

        # No path found
        return None

    def _heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Octile distance heuristic for 8-directional movement."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        return max(dx, dy) + (1.414 - 1) * min(dx, dy)

    def _get_terrain_cost(self, terrain: TerrainType, is_vehicle: bool) -> float:
        """Get movement cost for terrain type."""
        props = TERRAIN_PROPERTIES[terrain]

        if is_vehicle and not props['vehicle_passable']:
            return 0  # Impassable
        if not is_vehicle and not props['infantry_passable']:
            return 0  # Impassable

        return props['movement_cost']

    def _can_move_diagonal(self, x: int, y: int, dx: int, dy: int,
                           is_vehicle: bool) -> bool:
        """Check if diagonal movement is valid (no corner cutting)."""
        # Both adjacent tiles must be passable
        return (self.map.is_tile_passable(x + dx, y, is_vehicle) and
                self.map.is_tile_passable(x, y + dy, is_vehicle))

    def _find_nearest_passable(self, tx: int, ty: int,
                               is_vehicle: bool) -> Tuple[Optional[int], Optional[int]]:
        """Find nearest passable tile using BFS."""
        from collections import deque

        visited = set()
        queue = deque([(tx, ty, 0)])

        while queue:
            x, y, dist = queue.popleft()

            if (x, y) in visited:
                continue
            visited.add((x, y))

            if dist > 10:  # Limit search radius
                break

            if (0 <= x < self.width and 0 <= y < self.height and
                self.map.is_tile_passable(x, y, is_vehicle)):
                return (x, y)

            for dx, dy, _ in self.DIRECTIONS:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited:
                    queue.append((nx, ny, dist + 1))

        return (None, None)

    def _reconstruct_path(self, node: PathNode) -> List[Tuple[int, int]]:
        """Reconstruct path from goal node to start."""
        path = []
        current = node
        while current:
            path.append((current.x, current.y))
            current = current.parent
        path.reverse()
        return path

    def _smooth_path(self, path: List[Tuple[int, int]],
                     is_vehicle: bool) -> List[Tuple[int, int]]:
        """
        Smooth path by removing unnecessary waypoints.
        Uses line-of-sight checks to skip intermediate nodes.
        """
        if len(path) <= 2:
            return path

        smoothed = [path[0]]
        current_idx = 0

        while current_idx < len(path) - 1:
            # Try to skip ahead as far as possible
            best_skip = current_idx + 1

            for check_idx in range(len(path) - 1, current_idx + 1, -1):
                if self._has_clear_path(
                    path[current_idx][0], path[current_idx][1],
                    path[check_idx][0], path[check_idx][1],
                    is_vehicle
                ):
                    best_skip = check_idx
                    break

            smoothed.append(path[best_skip])
            current_idx = best_skip

        return smoothed

    def _has_clear_path(self, x1: int, y1: int, x2: int, y2: int,
                        is_vehicle: bool) -> bool:
        """Check if there's a clear straight-line path between tiles."""
        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1

        while True:
            if not self.map.is_tile_passable(x, y, is_vehicle):
                return False

            if x == x2 and y == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

        return True

    def _tile_path_to_pixels(self, path: List[Tuple[int, int]]) -> List[Tuple[float, float]]:
        """Convert tile coordinates to pixel coordinates (center of tiles)."""
        return [
            (tx * TILE_SIZE + TILE_SIZE / 2, ty * TILE_SIZE + TILE_SIZE / 2)
            for tx, ty in path
        ]

    def _add_to_cache(self, key: Tuple, path: List[Tuple[int, int]]):
        """Add path to cache, evicting old entries if needed."""
        if len(self._cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[key] = path

    def clear_cache(self):
        """Clear the path cache (call when map changes)."""
        self._cache.clear()


class PathFollower:
    """
    Helper class for units to follow a computed path.
    Handles waypoint progression and movement interpolation.
    """

    def __init__(self):
        self.path: List[Tuple[float, float]] = []
        self.current_waypoint: int = 0
        self.arrival_threshold: float = 8.0  # Pixels

    def set_path(self, path: List[Tuple[float, float]]):
        """Set a new path to follow."""
        self.path = path if path else []
        self.current_waypoint = 0

    def has_path(self) -> bool:
        """Check if there's an active path."""
        return len(self.path) > 0 and self.current_waypoint < len(self.path)

    def get_current_waypoint(self) -> Optional[Tuple[float, float]]:
        """Get the current target waypoint."""
        if not self.has_path():
            return None
        return self.path[self.current_waypoint]

    def update(self, current_x: float, current_y: float) -> Optional[Tuple[float, float]]:
        """
        Update path following state.

        Args:
            current_x, current_y: Current position

        Returns:
            Next waypoint to move toward, or None if path complete
        """
        if not self.has_path():
            return None

        waypoint = self.path[self.current_waypoint]

        # Check if we've reached current waypoint
        dist = math.hypot(waypoint[0] - current_x, waypoint[1] - current_y)

        if dist < self.arrival_threshold:
            self.current_waypoint += 1
            if self.current_waypoint >= len(self.path):
                # Path complete
                return None
            waypoint = self.path[self.current_waypoint]

        return waypoint

    def get_remaining_distance(self, current_x: float, current_y: float) -> float:
        """Calculate total remaining distance along path."""
        if not self.has_path():
            return 0.0

        total = 0.0
        prev_x, prev_y = current_x, current_y

        for i in range(self.current_waypoint, len(self.path)):
            wx, wy = self.path[i]
            total += math.hypot(wx - prev_x, wy - prev_y)
            prev_x, prev_y = wx, wy

        return total

    def clear(self):
        """Clear the current path."""
        self.path = []
        self.current_waypoint = 0
