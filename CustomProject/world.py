"""
D-LEVEL CUSTOM PROJECT - World Module
This module defines the World class, which serves as the main container for the simulation. 
It manages the agents, projectiles, and overall state of the environment.
"""
import main
from random import randrange
from unittest import loader
from vector2d import Vector2D
from matrix33 import Matrix33
import pyglet
from graphics import COLOUR_NAMES, window
from agent import PlayerAgent, EnemyAgent
from projectile import Projectile
from time import time
from map_loader import MapLoader
import math
from agent import (
    Brown,
    Grey,
    Teal,
    Yellow,
    Red,
    Green,
    Purple,
    White,
    Black
)

ENEMY_TYPES = {
    "B": Brown,
    "G": Grey,
    "T": Teal,
    "Y": Yellow,
    "R": Red,
    "N": Green,
    "P": Purple,
    "W": White,
    "K": Black,
}

class World(object):
    """The simulation container holding agents and environmental state."""

    def __init__(self, cx, cy, map_filename):
        # Dimensions of the world
        self.cx = cx
        self.cy = cy
        self.map_filename = map_filename
        self.mouse_pos = Vector2D(0, 0)

        # Create background rectangle (must be before agents for correct layering)
        self.background = pyglet.shapes.Rectangle(
            0, 0,
            self.cx,
            self.cy,
            color=(210, 170, 110),  # A light brown for the ground
            batch=window.get_batch("main")
        )

        # Create background grid (optional, can be commented out if not needed)
        self.grid_lines = []
        grid_size = 40
        for x in range(0, self.cx, grid_size):
            line = pyglet.shapes.Line(x, 0, x, self.cy, color=(50, 25, 15), batch=window.get_batch("info"))
            self.grid_lines.append(line)
        for y in range(0, self.cy, grid_size):
            line = pyglet.shapes.Line(0, y, self.cx, y, color=(50, 25, 15), batch=window.get_batch("info"))
            self.grid_lines.append(line)
                
        # Simulation entities
        self.agents = []
        self.projectiles = []

        # Load map data from file
        loader = MapLoader()
        map_data = loader.load(self.map_filename, tile_size=40)
        self.map_data = map_data

        # Player
        if self.map_data.player_spawn:
            self.player = PlayerAgent(world=self, spawn_pos=self.map_data.player_spawn, color="PLAYER_BLUE")
            self.agents.append(self.player)

        # Enemies
        for pos, enemy_type in self.map_data.enemy_spawns:
            enemy_class = ENEMY_TYPES.get(enemy_type)

            if enemy_class:
                enemy = enemy_class(self, pos)
                self.agents.append(enemy)

        # Walls
        self.wall_rects = []
        for pos in self.map_data.walls:
            wall = pyglet.shapes.Rectangle(
                pos[0], pos[1],
                40, 40,
                color=(100, 60, 30), # A darker brown for walls
                batch=window.get_batch("main")
            )
            self.wall_rects.append(wall)
        
        # Holes
        self.hole_circles = []
        for pos in self.map_data.holes:
            hole = pyglet.shapes.Circle(
                pos[0] + 20, pos[1] + 20,  # Center the hole in the tile
                20,
                color=(30, 15, 10),  # A very dark brown for holes
                batch=window.get_batch("main")
            )
            self.hole_circles.append(hole)

        # State flags
        self.paused = True
        self.show_info = True
        
    def update(self, delta):
        if self.paused:
            return

        # --- AGENTS ---
        for agent in self.agents:
            agent.update(delta)

        # --- PROJECTILES ---
        alive_projectiles = []

        for projectile in self.projectiles:
            projectile.update(delta)
            
            hit_agent = None
            
            for agent in self.agents:
                if self.projectile_hits_agent(projectile, agent):
                    hit_agent = agent
                    break

            if hit_agent is not None:
                hit_agent.destroy()

                if hit_agent in self.agents:
                    self.agents.remove(hit_agent)

                projectile.shape.delete()
                if projectile.owner and projectile in projectile.owner.projectiles:
                    projectile.owner.projectiles.remove(projectile)
                continue

            hit = self.projectile_wall_collision(projectile)

            if hit is not None:
                # --- APPLY BOUNCE ---
                if hit in ("LEFT", "RIGHT"):
                    projectile.vel.x *= -1

                    # push OUT of wall on X axis
                    if hit == "LEFT":
                        projectile.pos.x = projectile.pos.x - 2
                    else:  # RIGHT
                        projectile.pos.x = projectile.pos.x + 2

                elif hit in ("TOP", "BOTTOM"):
                    projectile.vel.y *= -1

                    # push OUT of wall on Y axis
                    if hit == "BOTTOM":
                        projectile.pos.y = projectile.pos.y - 2
                    else:  # TOP
                        projectile.pos.y = projectile.pos.y + 2

                projectile.bounce_count += 1

            # --- REMOVE IF DEAD ---
            if projectile.bounce_count > projectile.max_bounces:
                projectile.shape.delete()
                if projectile.owner and projectile in projectile.owner.projectiles:
                    projectile.owner.projectiles.remove(projectile)
            else:
                alive_projectiles.append(projectile)

        self.projectiles = alive_projectiles

    def update_player_aim(self, mouse_x, mouse_y):
        if not hasattr(self, "player"):
            return

        p = self.player

        dx = mouse_x - p.pos.x
        dy = mouse_y - p.pos.y

        angle = math.degrees(math.atan2(dy, dx))

        p.turret_angle = angle

    def spawn_projectiles(self, weapon, shots):
        for shot in shots:
            projectile = Projectile(
                pos=shot["pos"],
                vel=shot["vel"],
                damage=shot["damage"]
            )
            self.projectiles.append(projectile)

    def projectile_wall_collision(self, projectile):
        for wall in self.wall_rects:

            bx = wall.x
            by = wall.y
            bw = wall.width
            bh = wall.height

            px = projectile.pos.x
            py = projectile.pos.y

            if (
                px >= bx and px <= bx + bw and
                py >= by and py <= by + bh
            ):
                # determine bounce direction (simple axis separation)

                dx_left = abs(px - bx)
                dx_right = abs((bx + bw) - px)
                dy_bottom = abs(py - by)
                dy_top = abs((by + bh) - py)

                min_dist = min(dx_left, dx_right, dy_bottom, dy_top)

                if min_dist == dx_left:
                    return "LEFT"
                if min_dist == dx_right:
                    return "RIGHT"
                if min_dist == dy_bottom:
                    return "BOTTOM"
                return "TOP"

        return None

    def projectile_hits_agent(self, projectile, agent):
        px, py = projectile.pos.x, projectile.pos.y

        ax, ay, aw, ah = agent.get_aabb()

        return (
            px >= ax and px <= ax + aw and
            py >= ay and py <= ay + ah
        )

    def transform_points(self, points, pos, forward, side, scale):
        """Transforms a list of local space points into world space.
        
        Useful for rendering complex shapes that rotate and scale with an agent.
        """
        # Create copies of points to avoid mutating the original definitions
        world_pts = [pt.copy() for pt in points]
        
        # Construct transformation matrix
        mat = Matrix33()
        mat.scale_update(scale.x, scale.y)
        mat.rotate_by_vectors_update(forward, side)
        mat.translate_update(pos.x, pos.y)
        
        # Apply transformation
        mat.transform_vector2d_list(world_pts)
        return world_pts
    
    def check_wall_collision(self, agent, new_pos):
        half = agent.size / 2

        ax = new_pos.x - half
        ay = new_pos.y - half
        aw = agent.size
        ah = agent.size

        for wall in self.wall_rects:
            bx = wall.x
            by = wall.y
            bw = wall.width
            bh = wall.height

            if self.rects_overlap(ax, ay, aw, ah, bx, by, bw, bh):
                return True

        return False
    
    @staticmethod
    def rects_overlap(ax, ay, aw, ah, bx, by, bw, bh):
        return (
            ax < bx + bw and
            ax + aw > bx and
            ay < by + bh and
            ay + ah > by
        )

    def input_mouse(self, x, y, button, modifiers):
        self.mouse_pos.x = x
        self.mouse_pos.y = y
        
    def input_keyboard(self, symbol, modifiers):
        if symbol == pyglet.window.key.P:
            self.paused = not self.paused



        player = getattr(self, "player", None)
        if not player:
            return

        key_map = {
            pyglet.window.key.W: ("W", True),
            pyglet.window.key.S: ("S", True),
            pyglet.window.key.A: ("A", True),
            pyglet.window.key.D: ("D", True),
            pyglet.window.key.SPACE: (" ", True),
        }

        if symbol in key_map:
            key, value = key_map[symbol]
            player.set_input(key, value)

    def input_key_release(self, symbol, modifiers):
        player = getattr(self, "player", None)
        if not player:
            return

        key_map = {
            pyglet.window.key.W: "W",
            pyglet.window.key.S: "S",
            pyglet.window.key.A: "A",
            pyglet.window.key.D: "D",
            pyglet.window.key.SPACE: " ",
        }

        if symbol in key_map:
            player.set_input(key_map[symbol], False)