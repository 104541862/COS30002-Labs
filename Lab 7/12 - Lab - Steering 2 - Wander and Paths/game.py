"""Game Controller for Autonomous Agents.

This module acts as the high-level controller, orchestrating the interaction 
between the world, input handling, and the application update loop.

Created by
    Clinton Woodward (2019)
    James Bonner (2024)
    contact: jbonner@swin.edu.au

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""

from world import World
from graphics import window
from agent import Agent

# Global game instance (initialized in main.py)
game = None

class Game():
    """Main game application class."""

    def __init__(self):
        # Initialise the world based on the window size
        self.world = World(window.width, window.height)
        
        # Add a single agent to the world for the student to observe
        self.world.agents.append(Agent(self.world))
        
        # Ensure the world is active upon startup
        self.world.paused = False

    def input_mouse(self, x, y, button, modifiers):
        """Routes mouse events to the world."""
        self.world.input_mouse(x, y, button, modifiers)

    def input_keyboard(self, symbol, modifiers):
        """Routes keyboard events to the world."""
        self.world.input_keyboard(symbol, modifiers)

    def update(self, delta):
        """Routes clock update events to the world."""
        self.world.update(delta)