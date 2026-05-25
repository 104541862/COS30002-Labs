"""World Environment for Steering Simulation.

This module defines the World class, which manages the simulation space, 
the target object, and the collection of agents. It handles spatial 
constraints (like toroidal wrap-around) and routes input events to 
relevant simulation entities.

Created by
    Clinton Woodward (2019)
    James Bonner (2024)
    contact: jbonner@swin.edu.au

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""

from vector2d import Vector2D
from matrix33 import Matrix33
import pyglet
from graphics import COLOUR_NAMES, window
from agent import Agent, AGENT_MODES, TargetAgent
from weapon import Projectile, Explosion
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
            color=(40, 90, 50),  # A light green background
            batch=window.get_batch("main")
        )
        
        # State flags
        self.paused = True
        self.show_info = True
        
        # Simulation entities
        self.agents = []
        self.hunter = Agent(self, speed_scale=4.0, scale=24, color="GREEN", mode='follow_path')
        self.agents.append(self.hunter)

        self.target_agent = TargetAgent(cx / 2, cy / 2, max_speed=200.0, world=self)
        
        self.projectiles = []
        self.explosions = []
        
    def update(self, delta):
        """Advances the simulation by one tick."""
        if not self.paused:
            self.target_agent.update(delta)

            for agent in self.agents:
                agent.update(delta)

            alive_projectiles = []

            for projectile in self.projectiles:
                projectile.update(delta)

                # collision check
                if self.check_collision(projectile, self.target_agent):
                    self.target_agent.on_hit()
                    if projectile.explosive:
                        self.explosions.append(Explosion(projectile.pos.copy()))
                    continue  # don't keep projectile

                # expiry check
                if projectile.is_expired():
                    if projectile.explosive:
                        self.explosions.append(Explosion(projectile.pos.copy()))
                    continue

                alive_projectiles.append(projectile)

            self.projectiles = alive_projectiles

            alive_explosions = []

            for e in self.explosions:
                e.update(delta)
                if not e.expired():
                    alive_explosions.append(e)

            self.explosions = alive_explosions

    def wrap_around(self, pos):
        """Treats the world as a toroidal (wrap-around) space.
        
        Updates the x and y coordinates of the provided position object.
        """
        if pos.x > self.cx:
            pos.x -= self.cx
        elif pos.x < 0:
            pos.x += self.cx
            
        if pos.y > self.cy:
            pos.y -= self.cy
        elif pos.y < 0:
            pos.y += self.cy

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
    
    def check_collision(self, projectile, target):
        radius = 45  # Collision radius
        dx = projectile.pos.x - target.pos.x
        dy = projectile.pos.y - target.pos.y
        return (dx*dx + dy*dy) < (radius * radius)

    def input_mouse(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT:
            agent = self.agents[0]
            weapon = agent.weapon
            
            if weapon.can_fire():
                direction = self.agents[0].get_aim_direction(self.target_agent)

                shots = weapon.fire(direction)

                for shot in shots:
                    projectile = Projectile(
                        pos=shot["pos"],
                        vel=shot["vel"],
                        lifetime=shot["lifetime"],
                        explosive=weapon.explosive,
                    )
                    self.projectiles.append(projectile)
    
    def input_keyboard(self, symbol, modifiers):
        """Handles keyboard events (e.g., pausing, changing agent modes)."""
        if symbol == pyglet.window.key.P:
            self.paused = not self.paused
        if symbol == pyglet.window.key.Q:
            self.agents[0].switch_weapon(-1)
        if symbol == pyglet.window.key.E:
            self.agents[0].switch_weapon(1)
        elif symbol in AGENT_MODES:
            self.agents[0].mode = AGENT_MODES[symbol]