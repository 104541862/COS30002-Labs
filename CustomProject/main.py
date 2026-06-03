"""
D-LEVEL CUSTOM PROJECT

This is the main entry point for the D-Level Custom Project. It initializes the game, sets up the main loop, and starts the application.
Created by Edward Herrod
"""



if __name__ == '__main__':
    level_number = input("Enter level number to load (e.g. '1' for level1.txt): ")
    map_filename = f"levels/level{level_number}.txt"

    import pyglet

    # ---- Module Imports ----
    # Importing graphics for side-effects: it initializes the 'egi' and global window objects.
    # This approach ensures that the graphical context is available to other modules.
    import graphics

    # The game module exports a global 'game' object which is populated during startup.
    import game
    import os

    # ---- Initialization ----
    # Create the core game instance which sets up the world and initial agents.
    game.game = game.Game(map_filename)
    
    # ---- Event Loop & Scheduling ----
    # Schedule the world update at approximately 60 Frames Per Second (1/60s).
    # This keeps the physics/movement logic consistent regardless of frame rate.
    pyglet.clock.schedule_interval(game.game.update, 1/60.0)
    
    # Start the pyglet application event loop to begin rendering and interaction.
    pyglet.app.run()