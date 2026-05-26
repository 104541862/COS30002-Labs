# Agent Marksmanship: Task 15

This project is a pedagogical simulation of autonomous agent steering behaviours using Python and the Pyglet library. It demonstrates fundamental AI concepts such as Seek, Flee, Arrive, Wander, and Path Following.

## Features
- **Steering Behaviours**: Implementations for Seek, Arrive (Slow/Normal/Fast), and placeholders for Flee, Pursuit, Wander, and Path Following.
- **Visual Telemetry**: Real-time visualization of steering forces, velocity, and desired changes using color-coded vectors.
- **Toroidal World**: Agents wrap around screen boundaries for continuous movement.
- **Interactive Controls**: Move the target with the mouse and change agent modes via keyboard.

## Key Bindings
- `1`: Seek Mode
- `2`: Arrive Slow
- `3`: Arrive Normal
- `4`: Arrive Fast
- `5`: Flee Mode
- `6`: Pursuit Mode
- `7`: Follow Path Mode
- `8`: Wander Mode
- `P`: Pause/Resume Simulation
- `I`: Toggle Debug Information (Vectors and Info Batch)

## Technical Requirements
- Python 3.13+
- Pyglet 2.1.14+

## Installation
Ensure you have the dependencies installed:
```bash
uv add pyglet
```

## Attribution
- Original code by Clinton Woodward, James Bonner, and Steve Dower.
- Comments and code refactored by **Enrique Ketterer** <ekettererortiz@swin.edu.au> - S1 2026.

Additions by Edward Herrod:
Hit Q/E to switch between weapon types. 
Left click to shoot. The agent aims automatically.