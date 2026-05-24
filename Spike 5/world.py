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
from agent import Agent, AGENT_MODES
import random

class World(object):
    """The simulation container holding agents and environmental state."""

    def __init__(self, cx, cy):
        # Dimensions of the world
        self.cx = cx
        self.cy = cy
        
        # State flags
        self.paused = True
        self.show_info = True
        
        # Simulation entities
        self.agents = []
        self.rocks = []
        self.hunter = None # Placeholder for pursuit behaviour target
        self.prey = None # Placeholder for hide behaviour target

        self.killCount = 0
        
        self.create_rocks()

        prey = Agent(self, color='YELLOW', mode='hide', scale=25.0)
        self.agents.append(prey)

        hunter = Agent(self, color='RED', mode='pursuit')
        self.agents.append(hunter)

        self.hunter = hunter
        self.prey = prey

        # Target representation (a red star that agents usually seek/arrive at)
        self.target = pyglet.shapes.Star(
            cx / 2, cy / 2, 
            30, 1, 4, 
            color=COLOUR_NAMES['BLACK'], 
            batch=window.get_batch("main")
        )

    def update(self, delta):
        """Advances the simulation by one tick."""
        if not self.paused:
            self.check_hunter_kill()

            for agent in self.agents:
                agent.update(delta)

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

    def input_mouse(self, x, y, button, modifiers):
        """Handles mouse events (e.g., moving the target)."""
        if button == 1:  # Left click
            self.target.x = x
            self.target.y = y
    
    def input_keyboard(self, symbol, modifiers):
        """Handles keyboard events (e.g., pausing, changing agent modes)."""
        if symbol == pyglet.window.key.P:
            self.paused = not self.paused
        if symbol == pyglet.window.key.R:
            for agent in self.agents:
                agent.randomise_path()
        if symbol == pyglet.window.key.C:
            self.create_rocks()
        if symbol in AGENT_MODES:
            self.agents[0].mode = AGENT_MODES[symbol]

    def create_rocks(self):
        # Delete all active rocks to make way for new rocks
        self.rocks.clear()
        # Create 5 random rocks on the screen
        for i in range(5):
            self.rocks.append(
                Rock(random.uniform(100, self.cx-100), random.uniform(100, self.cy-100), random.uniform(30, 60))
            )

    def spawn_prey(self):
        """Creates a new prey agent and registers it."""

        prey = Agent(self, color='YELLOW', mode='hide')

        self.agents.insert(0, prey)  # Keep prey at index 0 (IMPORTANT)

        self.prey = prey
        return prey
    
    def check_hunter_kill(self):
        """Kills prey and immediately respawns a new one."""

        if not self.prey or not self.hunter:
            return

        to_prey = self.prey.pos - self.hunter.pos
        dist = to_prey.length()

        kill_distance = self.prey.scale.x

        if dist <= kill_distance:

            # remove old prey
            if self.prey in self.agents:
                self.agents.remove(self.prey)

            print(f'PREY KILLED: {self.killCount}')
            self.killCount += 1

            # spawn new prey
            self.spawn_prey()

class Rock:
    def __init__(self, x, y, radius, color="LIGHT_GREY"):

        self.pos = Vector2D(x, y)

        # visual size
        self.radius = radius

        # actual collision size
        self.hit_radius = radius * 0.8

        self.shape = pyglet.shapes.Circle(
            x, y,
            radius,
            color=COLOUR_NAMES[color],
            batch=window.get_batch("main")
        )