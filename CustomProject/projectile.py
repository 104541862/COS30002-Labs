"""
D-LEVEL CUSTOM PROJECT - Projectile Module
This module defines the Projectile class, which represents projectiles fired by agents in the simulation.
Projectiles have properties such as position, velocity and lifetime.
"""

from time import time
import pyglet
from vector2d import Vector2D, Point2D
from graphics import COLOUR_NAMES, PolyLine, window, ArrowLine
from math import sin, cos, radians
from random import random, randrange, uniform
from matrix33 import Matrix33

class Projectile:
    def __init__(self, pos, vel, owner=None, damage=100, color=(255, 255, 200), radius=5):
        self.pos = pos
        self.vel = vel
        self.radius = radius
        self.damage = damage
        self.owner = owner
        self.bounce_count = 0
        self.max_bounces = 1

        self.spawn_time = time()

        self.shape = self._create_shape(color, radius)

    def update(self, delta):
        self.pos += self.vel * delta

        self.shape.x = self.pos.x
        self.shape.y = self.pos.y

    def _create_shape(self, color, radius):
        return pyglet.shapes.Circle(
            self.pos.x, self.pos.y,
            radius,
            color=color,
            batch=window.get_batch("main")
        )