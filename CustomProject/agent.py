"""
D-LEVEL CUSTOM PROJECT - Agent Module
This module defines the Agent class.
"""

from turtle import shape

import pyglet
from vector2d import Vector2D, Point2D
from graphics import COLOUR_NAMES, PolyLine, window, ArrowLine
from math import dist, sin, cos, radians
from random import random, randrange, uniform
from path import Path
from matrix33 import Matrix33

class Agent(object):
    """A tank agent."""

    # Deceleration rates for the Arrive behaviour
    DECELERATION_SPEEDS = {
        'slow': 0.9,
        'normal': 0.6,
        'fast': 0.3,
    }

    def __init__(self, world=None, scale=30.0, speed_scale=30.0, mass=1.0, color="LIGHT_BLUE", mode='seek'):
        # Reference to the simulation world
        self.world = world
        self.mode = mode

        # Physics state: position, velocity, and orientation
        angle = radians(random() * 360)
        self.pos = Vector2D(randrange(world.cx), randrange(world.cy))
        self.vel = Vector2D()
        self.heading = Vector2D(sin(angle), cos(angle))
        self.side = self.heading.perp()
        self.scale = Vector2D(scale, scale)
        self.mass = mass
        self.max_speed = speed_scale
        self.max_force = 200.0
        self.movement_locked = False

        self.path_visual = PolyLine(
            self.path.get_pts(),
            colour=COLOUR_NAMES['PINK'],
            batch=window.get_batch("info"),
            closed=False
        )

        # ---- Graphical Representation ----
        self.color = color
        
        # Main vehicle primitive
        self.vehicle = pyglet.shapes.Rectangle(
            self.pos.x,
            self.pos.y,
            scale,  # width
            scale,  # height
            color=COLOUR_NAMES[self.color],
            batch=window.get_batch("main")
        )


        # ---- Debug/Info Visuals ----
        # Wander logic visuals (placeholders)
        self.info_wander_circle = pyglet.shapes.Circle(0, 0, 0, color=COLOUR_NAMES['WHITE'], batch=window.get_batch("info"))
        self.info_wander_target = pyglet.shapes.Circle(0, 0, 0, color=COLOUR_NAMES['GREEN'], batch=window.get_batch("info"))
        
        # Vectors: Blue = Steering Force, Aqua = Velocity, Grey = Desired Change
        self.info_force_vector = ArrowLine(Vector2D(0,0), Vector2D(0,0), colour=COLOUR_NAMES['BLUE'], batch=window.get_batch("info"))
        self.info_vel_vector = ArrowLine(Vector2D(0,0), Vector2D(0,0), colour=COLOUR_NAMES['AQUA'], batch=window.get_batch("info"))
        self.info_net_vectors = [
            ArrowLine(Vector2D(0,0), Vector2D(0,0), colour=COLOUR_NAMES['GREY'], batch=window.get_batch("info")),
            ArrowLine(Vector2D(0,0), Vector2D(0,0), colour=COLOUR_NAMES['GREY'], batch=window.get_batch("info")),
        ]

    def calculate(self, delta):
        """Calculates the accumulated steering force based on the current mode."""

    def update(self, delta):
        """Updates the agent's physics and graphical representation."""
        force = self.calculate(delta)

    def speed(self):
        return self.vel.length()

