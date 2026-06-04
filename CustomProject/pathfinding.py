# pathfinding.py

import heapq
from vector2d import Vector2D

class GridNode:
    def __init__(self, x, y, walkable=True, cost=1.0):
        self.x = x
        self.y = y
        self.walkable = walkable
        self.cost = cost

        self.g = float("inf")
        self.h = 0
        self.f = float("inf")
        self.parent = None


class Grid:
    def __init__(self, world, cell_size=40):
        self.world = world
        self.cell_size = cell_size
        self.nodes = {}

        self.width = int(world.cx // cell_size)
        self.height = int(world.cy // cell_size)

        self._build_grid()

    def _build_grid(self):
        for x in range(self.width):
            for y in range(self.height):
                world_x = x * self.cell_size
                world_y = y * self.cell_size

                walkable = not self.world.point_in_wall(world_x, world_y)

                self.nodes[(x, y)] = GridNode(x, y, walkable)

    def tactical_cost(self, node, player_pos):
        world = self.world_from_node((node.x, node.y))

        to_player = (world - player_pos)
        dist = to_player.length()

        # preferred band (grey tank behaviour)
        ideal = 800.0
        distance_score = abs(dist - ideal)

        # wall proximity bonus (encourage cover)
        cover_bonus = 0.0
        for wall in self.world.wall_rects:
            wx, wy = wall.x, wall.y
            if abs(world.x - wx) < 80 or abs(world.y - wy) < 80:
                cover_bonus -= 10.0

        return distance_score + cover_bonus
    
    def best_tactical_node(self, player_pos):
        best = None
        best_score = float("inf")

        for node in self.nodes.values():
            if not node.walkable:
                continue

            score = self.tactical_cost(node, player_pos)

            if score < best_score:
                best_score = score
                best = (node.x, node.y)

        return best

    def update_costs_for_grey(self, player_pos):
        for node in self.nodes.values():
            world = self.world.grid.world_from_node((node.x, node.y))
            dist = (world - player_pos).length()

            # Grey tanks prefer medium distance (not too close, not too far)
            ideal = 800.0

            node.cost = abs(dist - ideal) / 100.0 + 1.0

    def node_from_world(self, pos):
        return (int(pos.x // self.cell_size), int(pos.y // self.cell_size))

    def world_from_node(self, node):
        x, y = node
        return Vector2D(
            x * self.cell_size + self.cell_size / 2,
            y * self.cell_size + self.cell_size / 2
        )

    def neighbors(self, node):
        x, y = node

        dirs = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]

        result = []

        for dx, dy in dirs:
            nx, ny = x + dx, y + dy

            if (nx, ny) not in self.nodes:
                continue

            neighbor = self.nodes[(nx, ny)]
            if not neighbor.walkable:
                continue

            # --- CRITICAL CORNER-SAFETY RULE ---
            # block diagonal movement through corners
            if dx != 0 and dy != 0:
                n1 = self.nodes.get((x + dx, y))
                n2 = self.nodes.get((x, y + dy))

                if n1 is None or n2 is None:
                    continue

                if (not n1.walkable) or (not n2.walkable):
                    continue

            result.append((nx, ny))

        return result

    def heuristic(self, a, b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1])

    def reset(self):
        for node in self.nodes.values():
            node.g = float("inf")
            node.f = float("inf")
            node.parent = None

def astar(grid, start_pos, goal_pos):
    start = grid.node_from_world(start_pos)
    goal = grid.node_from_world(goal_pos)

    grid.reset()

    start_node = grid.nodes[start]
    start_node.g = 0
    start_node.f = grid.heuristic(start, goal)

    open_set = []
    heapq.heappush(open_set, (start_node.f, start))

    closed = set()

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            return reconstruct(grid, current)

        closed.add(current)

        for n in grid.neighbors(current):
            if n in closed:
                continue

            node = grid.nodes[n]

            tentative_g = grid.nodes[current].g + node.cost

            if tentative_g < node.g:
                node.parent = current
                node.g = tentative_g
                node.f = tentative_g + grid.heuristic(n, goal)

                heapq.heappush(open_set, (node.f, n))

    return []


def reconstruct(grid, current):
    path = []

    while current:
        path.append(grid.world_from_node(current))
        current = grid.nodes[current].parent

    return list(reversed(path))