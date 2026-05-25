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
from slider import Slider
import random

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
            color=(40, 120, 160),
            batch=window.get_batch("main")
        )

        # State flags
        self.paused = True
        self.show_info = True
        
        # Simulation entities
        self.agents = []
        self.prey_agents = []
        self.rocks = []
        self.hunter = None # Placeholder for pursuit behaviour target
        self.prey = None # Placeholder for prey behaviour target

        self.killCount = 0

        # Flocking tuning parameters
        self.sep_weight = 0.02
        self.coh_weight = 15.0
        self.ali_weight = 1.2
        self.fear_radius = 200.0

        # Slider state
        self.active_slider = None

        self.sliders = [
            Slider(20, 760, 200, 0.0, 0.2, self.sep_weight, 'Separation'),
            Slider(20, 720, 200, 0.0, 50.0, self.coh_weight, 'Cohesion'),
            Slider(20, 680, 200, 0.0, 5.0, self.ali_weight, 'Alignment'),
            Slider(20, 640, 200, 20.0, 300.0, self.fear_radius, 'Fear Radius'),
        ]
        
        self.create_rocks()

        # spawn hunter
        hunter = Agent(
            self,
            color='GREY',
            speed_scale=8.0,
            mode='pursuit',
        )

        self.agents.append(hunter)

        self.hunter = hunter

        # spawn prey group
        for i in range(5):
            self.spawn_prey()

        # compatibility reference (temporary)
        self.prey = self.prey_agents[0]

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

        if button == 1:

            # slider selection
            for slider in self.sliders:

                if slider.contains(x, y):
                    self.active_slider = slider
                    return
    
    def input_keyboard(self, symbol, modifiers):
        """Handles keyboard events (e.g., pausing, changing agent modes)."""
        if symbol == pyglet.window.key.P:
            self.paused = not self.paused
        if symbol == pyglet.window.key.C:
            self.create_rocks()
        if symbol == pyglet.window.key.SPACE:
            self.spawn_prey()
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
        """Creates a new prey agent."""

        prey = Agent(
            self,
            color='LIGHT_BLUE',
            mode='wander',
            scale=25.0,
            is_prey=True,
        )

        self.agents.append(prey)

        self.prey_agents.append(prey)

        # temporary compatibility target
        self.prey = prey

        return prey        
    
    def check_hunter_kill(self):
        """Kills any prey the hunter collides with and respawns it."""

        if not self.hunter:
            return

        kill_radius = 0

        # detects prey dynamically instead of relying on self.prey (as in spike 5)
        for agent in list(self.agents):  # copy list to safely modify it

            if agent is self.hunter:
                continue

            # only prey agents are killable
            if not agent.is_prey:
                continue

            to_agent = agent.pos - self.hunter.pos
            dist = to_agent.length()

            kill_radius = agent.scale.x

            if dist <= kill_radius:

                # remove agent safely
                if agent in self.agents:
                    self.agents.remove(agent)
                    self.prey_agents.remove(agent)

                # update reference if needed
                if agent is self.prey:
                    self.prey = None

                print(f'PREY KILLED: {self.killCount}')
                self.killCount += 1

                # respawn a new prey
                self.spawn_prey()

                # stop after one kill per frame
                break

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