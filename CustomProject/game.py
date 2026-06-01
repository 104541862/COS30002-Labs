"""
D-LEVEL CUSTOM PROJECT - Game Module
This module defines the Game class, which serves as the main controller for the application.
It manages the world, handles input events, and updates the game state.
Created by Edward Herrod
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