# PlanetWars — COS30002 AI for Games

Deceptive PlanetWars simulation for the COS30002 unit at Swinburne University of Technology.

## Quick Start

```bash
# Install dependencies (requires Python 3.13+ and uv)
uv sync

# Run a headless game between two bots on a specific map
uv run python main.py -p Blanko OneSlowMove -m map001

# Run with the graphical interface
uv run python main.py --gui -p Blanko OneSlowMove -m map001
```

## CLI Parameters

| Flag | Description |
|------|-------------|
| `-h`, `--help` | Show help message and exit. |
| `-p [PLAYERS...]`, `--players [PLAYERS...]` | Space-separated bot names (no `.py` extension) from `bots/`. |
| `-m MAP`, `--map MAP` | Filename (no extension) of a map in `maps/`. |
| `-r REPLAY`, `--replay REPLAY` | Filename (no extension) of a replay in `replays/`. |
| `--gui` | Launch the graphical window (pyglet). |
| `--logscript LOGSCRIPT` | Name of a log output script from `logscripts/`. |
| `--save-replay [NAME]` | Save a replay file. Optional name; defaults to auto-generated. |
| `--max-ticks N` | Maximum number of game ticks (default: 10 000). |

## GUI Controls

| Key | Action |
|-----|--------|
| `N` | Step the game forward by one frame. |
| `P` | Toggle pause/un-pause. |
| `-` / `+` | Decrease / increase frame rate. |
| `[` / `]` | Cycle through player views. |
| `A` | Return to the all-player view. |
| `L` | Cycle displayed planet property (ID, ships, vision_age, owner). |
| `Esc` | Quit the application. |

## Display Properties

When running the GUI, you can press the `L` key to cycle through different properties of the planets and fleets to see real-time state numbers overlaid on the game map.

| Property | Description |
|----------|-------------|
| **ID** | The unique game-level string identifier used to specify the planet or fleet. Note: All unique keys in this project are strictly capitalised as `ID` instead of `id` to prevent conflicts with Python's built-in `id()` function. |
| **ships** | The current number of ships garrisoned on a planet, or the number in transit within a fleet. |
| **vision_age**| The number of ticks since the planet or fleet was last seen by the player in the current fog-of-war view. |
| **owner** | The ID of the player who currently owns the entity (`0` indicates neutral/unowned). |

### Fog of War (`vision_age`)

The simulation enforces a strict Fog of War mechanics. A player can only "see" planets and fleets that fall within the vision radius of their own currently owned planets or passing fleets. 

When you cycle to the individual player view (using `[` or `]`) and show the `vision_age` property, any entity within active vision will display a value of `0`. 

When an entity leaves a player's vision radius, the game engine stops updating that entity's details for that specific player, and its `vision_age` increases by `1` every tick. This means the number of `ships` or the `owner` you are seeing is the *last known state* and might be completely inaccurate in reality. This creates a strong incentive for bot code to actively send tiny scout fleets to update their façade knowledge before committing to major attacks!

## Project Structure

| Path | Description |
|------|-------------|
| `main.py` | Entry point — CLI parsing and game bootstrap. |
| `planet_wars.py` | Core game engine (simulation loop, combat, fog-of-war). |
| `entities.py` | `Entity`, `Planet`, and `Fleet` classes. |
| `players.py` | `Player` class (façade) and bot controller loader. |
| `planet_wars_draw.py` | Pyglet rendering (window, shapes, batches). |
| `bots/` | Bot controllers (e.g. `Blanko.py`, `OneMove.py`). **Class name MUST match filename.** |
| `maps/*.json` | Planet map definitions. |
| `replays/*.json` | Recorded game replays. |
| `logscripts/` | Optional log output scripts. |
| `map_generator.py` | Utility for procedurally generating new maps. |

## Authors

- Michael Jensen (2011)
- Clinton Woodward (2012)
- James Bonner (2023/4)
- Comments and code refactored by Enrique Ketterer — S1 2026

ADDITIONS BY EDWARD HERROD: 
2 bots: 
- "Rando" who chooses inputs on planets almost entirely at random.
- "BestWorst" who sends from the planet with the most of their ships to the enemy planet with the least amount defending it.

To run these two bots against one another, use:
python main.py --gui -p BestWorst Rando -m map001