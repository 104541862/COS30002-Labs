from time import time
import pyglet
from vector2d import Vector2D, Point2D
from graphics import COLOUR_NAMES, PolyLine, window, ArrowLine
from math import sin, cos, radians
from random import random, randrange, uniform
from matrix33 import Matrix33

class Projectile:
    def __init__(self, pos, vel, lifetime, explosive=False, damage=100, color=(255, 255, 0), radius=3):
        self.pos = pos
        self.vel = vel
        self.radius = radius
        self.explosive = explosive
        self.damage = damage

        self.spawn_time = time()
        self.lifetime = lifetime

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

    def is_expired(self):
        return (time() - self.spawn_time) >= self.lifetime