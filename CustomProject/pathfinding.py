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

        self.cell_walls = {}
        self._build_grid()
        self._build_wall_lookup()

    def _build_grid(self):
        for x in range(self.width):
            for y in range(self.height):
                world_x = x * self.cell_size + self.cell_size / 2
                world_y = y * self.cell_size + self.cell_size / 2

                walkable = not self.world.point_in_wall(world_x, world_y) and not self.world.point_in_hole(world_x, world_y)

                self.nodes[(x, y)] = GridNode(x, y, walkable)

    def _build_wall_lookup(self):

        for wall in self.world.wall_rects:

            min_x = int(wall.x // self.cell_size)
            max_x = int((wall.x + wall.width) // self.cell_size)

            min_y = int(wall.y // self.cell_size)
            max_y = int((wall.y + wall.height) // self.cell_size)

            for gx in range(min_x, max_x + 1):
                for gy in range(min_y, max_y + 1):

                    self.cell_walls.setdefault(
                        (gx, gy),
                        []
                    ).append(wall)
    
    def nearby_walls(self, pos, radius_cells=1):

        cx = int(pos.x // self.cell_size)
        cy = int(pos.y // self.cell_size)

        result = []

        for dx in range(-radius_cells, radius_cells + 1):
            for dy in range(-radius_cells, radius_cells + 1):

                cell = (cx + dx, cy + dy)

                if cell in self.cell_walls:
                    result.extend(
                        self.cell_walls[cell]
                    )

        return result

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