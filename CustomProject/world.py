"""
D-LEVEL CUSTOM PROJECT - World Module
This module defines the World class, which serves as the main container for the simulation. 
It manages the agents, projectiles, and overall state of the environment.
"""

from random import randrange
from vector2d import Vector2D
from matrix33 import Matrix33
import pyglet
from graphics import COLOUR_NAMES, window
from agent import Agent
from projectile import Projectile
from time import time

class World(object):
    """The simulation container holding agents and environmental state."""

    def __init__(self, cx, cy):
        # Dimensions of the world
        self.cx = cx
        self.cy = cy

        # Create background rectangle (must be before agents for correct layering)
        self.background = pyglet.shapes.Rectangle(
            0, 0,
            self.cx,
            self.cy,
            color=(210, 170, 110),  # A light brown background
            batch=window.get_batch("main")
        )
        
        # State flags
        self.paused = True
        self.show_info = True
        
        # Simulation entities
        self.agents = []
        self.projectiles = []
        
    def update(self, delta):
        """Advances the simulation by one tick."""
        if not self.paused:
            for agent in self.agents:
                agent.update(delta)
                
            alive_projectiles = []

            for projectile in self.projectiles:
                projectile.update(delta)

    def spawn_projectiles(self, weapon, shots):
        for shot in shots:
            projectile = Projectile(
                pos=shot["pos"],
                vel=shot["vel"],
                lifetime=shot["lifetime"],
                damage=shot["damage"]
            )
            self.projectiles.append(projectile)

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

    def input_mouse(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT:
            pass  # Placeholder for potential future mouse interactions
    
    def input_keyboard(self, symbol, modifiers):
        """Handles keyboard events (e.g., pausing)."""
        if symbol == pyglet.window.key.P:
            self.paused = not self.paused