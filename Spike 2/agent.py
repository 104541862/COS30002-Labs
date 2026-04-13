import math
import random
import pyglet
from graphics import COLOUR_NAMES, window
from searches import SEARCHES

# An agent is an AI that has behaviour and moves within this environment
class Agent:
    def __init__(self, world, start_box, team, role="attacker"):
        self.world = world
        self.current_box = start_box
        self.team = team
        self.role = role

        self.x = start_box.center().x
        self.y = start_box.center().y

        # Setting up parameters
        self.speed = 100.0
        self.path = []
        self.segment = 0
        self.progress = 0.0

        self.alive = True

        # Repath interval can be changed to set how long the AI will take to path
        self.repath_timer = 0.0
        self.repath_interval = 0.3

        # For now, just set the defender's home tile to its starting tile
        self.home_box = start_box

        # Create the triangle for the agent
        color = COLOUR_NAMES["RED"] if team == 0 else COLOUR_NAMES["BLUE"]

        self.shape = pyglet.shapes.Triangle(
            self.x, self.y,
            self.x, self.y,
            self.x, self.y,
            color=color,
            batch=window.get_batch("path")
        )

    # Update loop which runs through the three things this AI does - think for a target, move to the target, and check the current tile for enemies
    def update(self, dt):
        if not self.alive:
            return

        self.think(dt)
        self.move(dt)
        self.check_combat()

    # Delegates the behaviour depending on which role this agent is
    def think(self, dt):
        self.repath_timer -= dt

        if self.repath_timer > 0:
            return

        if self.role == "attacker":
            self.attacker_behaviour()
        elif self.role == "defender":
            self.defender_behaviour()

        self.repath_timer = self.repath_interval

    # Simple attacker AI - if there's an enemy, find it and move to it
    def attacker_behaviour(self):
        target = self.find_target()
        if target:
            self.plan_path_to(target.current_box.index)

    # Randomly wanders around its starting point and attacks enemies which get near it
    def defender_behaviour(self):
        enemies = self.world.get_enemy_agents(self.team)

        # Chase nearby enemies
        for enemy in enemies:
            if self.distance_to(enemy) < 100:
                self.plan_path_to(enemy.current_box.index)
                return

        # Otherwise patrol
        self.patrol()

    # Finds all of the enemies then returns the closest one
    def find_target(self):
        enemies = self.world.get_enemy_agents(self.team)
        if not enemies:
            return None

        return min(enemies, key=lambda e: self.distance_to(e))

    def distance_to(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)

    # Uses A* searching to find a path towards the enemy
    def plan_path_to(self, target_idx):
        start_idx = self.current_box.index

        path_obj = SEARCHES[3](self.world.graph, start_idx, target_idx)

        if path_obj.path:
            self.path = [self.world.boxes[i].center() for i in path_obj.path]
            self.segment = 0
            self.progress = 0.0

    # Movement handler
    def move(self, dt):
        if not self.path or self.segment >= len(self.path) - 1:
            return

        start = self.path[self.segment]
        end = self.path[self.segment + 1]

        dx = end.x - start.x
        dy = end.y - start.y
        dist = math.hypot(dx, dy)

        if dist == 0:
            self.segment += 1
            return

        self.progress += self.speed * dt
        t = self.progress / dist

        if t >= 1.0:
            self.segment += 1
            self.progress = 0.0
            self.x = end.x
            self.y = end.y

            # update current box
            box = self.world.get_box_by_pos(self.x, self.y)
            if box:
                self.current_box = box
        else:
            self.x = start.x + dx * t
            self.y = start.y + dy * t

        angle = math.degrees(math.atan2(dy, dx))
        self.update_shape(angle)

    # The agent's direction of movement is shown by a triangle, and this code here updates the agent's appearance to be consistent with where it's facing
    def update_shape(self, angle):
        size = 10

        pts = []
        for a in [0, 140, -140]:  # arrow shape
            rad = math.radians(angle + a)
            pts.append((
                self.x + size * math.cos(rad),
                self.y + size * math.sin(rad)
            ))

        (x1, y1), (x2, y2), (x3, y3) = pts

        self.shape.x, self.shape.y = x1, y1
        self.shape.x2, self.shape.y2 = x2, y2
        self.shape.x3, self.shape.y3 = x3, y3
    
    # Checks the current tile for an enemy. If there is one, kill it
    def check_combat(self):
        for enemy in self.world.get_enemy_agents(self.team):
            if self.distance_to(enemy) < 10:
                enemy.alive = False
                enemy.shape.visible = False

    # Randomly patrol in an area
    def patrol(self):
        idx = self.home_box.index
        nx = self.world.x_boxes

        col = idx % nx
        row = idx // nx

        if col % 2 == 0:
            candidates = [
                (col+1, row),
                (col-1, row),
                (col, row+1),
                (col, row-1),
                (col+1, row-1),
                (col-1, row-1),
            ]
        else:
            candidates = [
                (col+1, row),
                (col-1, row),
                (col, row+1),
                (col, row-1),
                (col+1, row+1),
                (col-1, row+1),
            ]

        valid = []
        for c, r in candidates:
            if 0 <= c < self.world.x_boxes and 0 <= r < self.world.y_boxes:
                valid.append(self.world.get_box_by_xy(c, r))

        if valid:
            target_box = random.choice(valid)
            self.plan_path_to(target_box.index)