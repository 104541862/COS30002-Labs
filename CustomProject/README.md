# D-Level Custom Project
This is a simulation showcasing agent marksmanship, grid pathfinding using graph and searching algorithms and agent movement.

## Features
- **Visual Telemetry**: Real-time visualization of agent aiming trajectory
- **Interactive Controls**: Move your player agent with WASD and shoot with left click. Try to beat all of the levels, or make your own!
- **Bouncing Bullets**: Bullets can bounce off walls.
- **Different AI tanks**: There are 9 different types of AI tanks. Some are immobile, some are highly accurate, and others have aggression parameters.

## Key Bindings
- `W`: Move player upward
- `A`: Turn player left
- `S`: Move player down
- `D`: Turn player right
- `SPACE`: Player shoot
- `I`: Render debugging information

## Technical Requirements
- Python 3.13+
- Pyglet 2.1.14+

## Installation
Ensure you have the dependencies installed:
```bash
uv add pyglet
```

## Runtime
To run this code, ensure that your terminal is opened to the CustomProject folder. Run `Python main.py` in the terminal to start the program, then select a level when prompted with an integer (1-9)

## Attribution
- AI logic and map design code written by Edward Herrod.
- Original main, game, graphics, matrix33, point2d and vector2d code by Clinton Woodward, James Bonner, and Steve Dower.