"""Autonomous Agent Movement: Paths and Wandering — Entry Point.

This module bootstraps the autonomous agent steering simulation. It initializes 
the game world, schedules the simulation update at a fixed frequency, and 
launches the pyglet application event loop.

Created by
    Clinton Woodward (2019)
    James Bonner (2024)
    contact: jbonner@swin.edu.au

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""

import pyglet

# ---- Module Imports ----
# Importing graphics for side-effects: it initializes the 'egi' and global window objects.
# This approach ensures that the graphical context is available to other modules.
import graphics

# The game module exports a global 'game' object which is populated during startup.
import game

if __name__ == '__main__':
    # ---- Initialization ----
    # Create the core game instance which sets up the world and initial agents.
    game.game = game.Game()
    
    # ---- Event Loop & Scheduling ----
    # Schedule the world update at approximately 60 Frames Per Second (1/60s).
    # This keeps the physics/movement logic consistent regardless of frame rate.
    pyglet.clock.schedule_interval(game.game.update, 1/60.0)
    
    # Start the pyglet application event loop to begin rendering and interaction.
    pyglet.app.run()
