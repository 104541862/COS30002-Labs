"""
D-LEVEL CUSTOM PROJECT - Agent Module
This module defines the Agent class.
"""

from turtle import shape

import pyglet
from vector2d import Vector2D, Point2D
from graphics import COLOUR_NAMES, PolyLine, window, ArrowLine
import math
from math import dist, sin, cos, radians
from random import random, randrange, uniform
from path import Path
from matrix33 import Matrix33
from projectile import Projectile

class Agent:
    """Base class for all tanks (no movement logic here)."""

    def __init__(self, world, spawn_pos, size = 30, color="LIGHT_BLUE"):
        self.world = world

        self.pos = Vector2D(spawn_pos[0], spawn_pos[1])
        self.color = color
        self.size = size

        self.heading = Vector2D(1, 0)

        self.projectiles = []
        self.max_projectiles = 5

        # Graphics only
        self.vehicle = pyglet.shapes.Rectangle(
            self.pos.x,
            self.pos.y,
            self.size,
            self.size,
            color=COLOUR_NAMES[self.color],
            batch=window.get_batch("main")
        )
        
        dark_color = self.darken(self.color, 0.8)
        self.front_marker = pyglet.shapes.Triangle(
            0, 0,
            0, 0,
            0, 0,
            color=dark_color,
            batch=window.get_batch("main")
        )

        self.vehicle.anchor_x = self.size / 2
        self.vehicle.anchor_y = self.size / 2

        self.turret_length = self.size * 0.8
        self.turret_width = 6
        self.turret_angle = 0.0

        self.turret = pyglet.shapes.Rectangle(
            self.pos.x,
            self.pos.y,
            self.size * 0.6,
            self.size * 0.2,
            color=(0, 0, 0),
            batch=window.get_batch("main")
        )

        self.turret.anchor_x = 0
        self.turret.anchor_y = self.turret.height / 2

    def sync_graphics(self):
        self.vehicle.x = self.pos.x
        self.vehicle.y = self.pos.y

        # body rotation only
        self.vehicle.rotation = -self.heading.angle_degrees()

        # turret always sits on top of tank
        self.turret.x = self.pos.x
        self.turret.y = self.pos.y

        half = self.size / 2

        forward = self.heading.get_normalised()
        side = forward.perp().get_normalised()

        # tip of triangle (front)
        tip = self.pos + forward * half

        # rear base of triangle (slightly behind center)
        base_center = self.pos - forward * (half * 0.4)

        base_left = base_center + side * (self.size * 0.25)
        base_right = base_center - side * (self.size * 0.25)

        self.front_marker.x = tip.x
        self.front_marker.y = tip.y

        # pyglet Triangle uses (x1,y1, x2,y2, x3,y3)
        self.front_marker.x2 = base_left.x
        self.front_marker.y2 = base_left.y

        self.front_marker.x3 = base_right.x
        self.front_marker.y3 = base_right.y

    def darken(self, color, factor):
        r, g, b, a = COLOUR_NAMES[color]
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return (r, g, b, a)
    
    def get_aabb(self):
        half = self.size / 2
        return (
            self.pos.x - half,
            self.pos.y - half,
            self.size,
            self.size
        )
    
    def shoot(self):
        if len(self.projectiles) >= self.max_projectiles:
            return

        # spawn slightly in front of tank
        forward = self.turret_direction()

        spawn_pos = self.pos + forward * (self.size * 0.9)

        speed = 200.0
        vel = forward * speed

        projectile = Projectile(
            pos=spawn_pos,
            vel=vel,
            owner=self
        )

        self.projectiles.append(projectile)
        self.world.projectiles.append(projectile)
    
    def turret_direction(self):
        angle_rad = math.radians(-self.turret.rotation)
        return Vector2D(math.cos(angle_rad), math.sin(angle_rad))
    
    def destroy(self):
        self.vehicle.delete()
        self.turret.delete()

        if hasattr(self, "front_marker"):
            self.front_marker.delete()

class PlayerAgent(Agent):
    """Player-controlled tank (no physics, only input state)."""

    def __init__(self, world, spawn_pos, size = 30, color="LIGHT_BLUE"):
        super().__init__(world, spawn_pos, size, color)

        self.velocity = Vector2D()

        self.acceleration = 800.0      # fast build-up
        self.max_speed = 120.0         # cap speed
        self.deceleration = 1200.0     # fast stopping

        self.input_state = {
            "forward": False,
            "left": False,
            "right": False,
            "backward": False,
            "shoot": False,
        }

        self.turn_speed = 2.0

    def update(self, delta):

        # direction tank faces (we assume facing right initially)
        direction = self.heading.get_normalised()

        # --- TURNING ---
        if self.input_state["left"]:
            self.heading = self.heading.rotate(self.turn_speed * delta)

        if self.input_state["right"]:
            self.heading = self.heading.rotate(-self.turn_speed * delta)

        # --- ACCELERATION INPUT ---
        accel = Vector2D()

        if self.input_state["forward"]:
            accel += self.heading * self.acceleration

        if self.input_state["backward"]:
            accel -= self.heading * self.acceleration

        self.velocity += accel * delta

        # --- SPEED LIMIT (vector-aware) ---
        speed = self.velocity.length()

        if speed > self.max_speed:
            self.velocity = self.velocity.get_normalised() * self.max_speed

        # --- FRICTION (always applied when no input or even slightly) ---
        if self.input_state["forward"] is False and self.input_state["backward"] is False:
            speed = self.velocity.length()

            if speed > 0:
                drop = self.deceleration * delta

                if drop > speed:
                    self.velocity.zero()
                else:
                    self.velocity = self.velocity.get_normalised() * (speed - drop)

        # --- APPLY MOVEMENT ---
        new_pos = self.pos + self.velocity * delta

        if not self.world.check_wall_collision(self, new_pos):
            self.pos = new_pos
        else:
            # simple response: stop movement on collision
            self.velocity.zero()
        
        # --- TURRET AIMING (PLAYER ONLY) ---
        mx = self.world.mouse_pos.x
        my = self.world.mouse_pos.y

        dx = mx - self.pos.x
        dy = my - self.pos.y

        self.turret.rotation = -math.degrees(math.atan2(dy, dx))

        # --- SYNC GRAPHICS ---
        self.sync_graphics()

    def set_input(self, key, value):
        if key == "W":
            self.input_state["forward"] = value
        elif key == "S":
            self.input_state["backward"] = value
        elif key == "A":
            self.input_state["left"] = value
        elif key == "D":
            self.input_state["right"] = value
        elif key == " ":
            self.input_state["shoot"] = value
            if value:  # only shoot on key press, not release
                self.shoot()

class EnemyAgent(Agent):
    """Enemy tank (AI handled by World later)."""

    def __init__(self, world, spawn_pos, size = 30, color="RED"):
        super().__init__(world, spawn_pos, size, color)

        self.target = None
    
    def update(self, delta):
        self.sync_graphics()

class Brown(Agent):
    def __init__(self, world, spawn_pos):
        super().__init__(world, spawn_pos, color="ENEMY_BROWN")
    
    def update(self, delta):
        self.sync_graphics()

class Grey(Agent):
    def __init__(self, world, spawn_pos):
        super().__init__(world, spawn_pos, color="ENEMY_GREY")

    def update(self, delta):
        self.sync_graphics()

class Teal(EnemyAgent):
    def __init__(self, world, spawn_pos):
        super().__init__(world, spawn_pos, color="ENEMY_TEAL")  

    def update(self, delta):
        self.sync_graphics()

class Yellow(EnemyAgent):
    def __init__(self, world, spawn_pos):
        super().__init__(world, spawn_pos, color="ENEMY_YELLOW")

    def update(self, delta):
        self.sync_graphics()

class Red(EnemyAgent):
    def __init__(self, world, spawn_pos):
        super().__init__(world, spawn_pos, color="ENEMY_RED")

    def update(self, delta):
        self.sync_graphics()

class Green(EnemyAgent):
    def __init__(self, world, spawn_pos):
        super().__init__(world, spawn_pos, color="ENEMY_GREEN")

    def update(self, delta):
        self.sync_graphics()

class Purple(EnemyAgent):
    def __init__(self, world, spawn_pos):
        super().__init__(world, spawn_pos, color="ENEMY_PURPLE")

    def update(self, delta):
        self.sync_graphics()

class White(EnemyAgent):    
    def __init__(self, world, spawn_pos):
        super().__init__(world, spawn_pos, color="ENEMY_WHITE")

    def update(self, delta):
        self.sync_graphics()

class Black(EnemyAgent):
    def __init__(self, world, spawn_pos):
        super().__init__(world, spawn_pos, color="ENEMY_BLACK")

    def update(self, delta):
        self.sync_graphics()