# Emergent Group Behaviour - Spike 6

This project is a pedagogical simulation of autonomous agent steering behaviours using Python and the Pyglet library. It demonstrates fundamental AI concepts such as Seek, Flee, Arrive, Wander, and Path Following. The main aim of this spike is to demonstrate a working simulation of a hunter and a prey agents navigating a toroidal world with multiple circular objects (“rocks”).

## Features
- **Steering Behaviours**: Implementations for Seek, Arrive (Slow/Normal/Fast), and placeholders for Flee, Pursuit, Wander, and Path Following.
- **Visual Telemetry**: Real-time visualization of steering forces, velocity, and desired changes using color-coded vectors.

## Key Bindings
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
Hit C to randomise the obstacle positions (don't worry, this doesn't hurt our agents)
Hit SPACE to create a new prey.
Adjust the sliders to create different behaviours among groupings of prey. (Only visible if debug information is on)