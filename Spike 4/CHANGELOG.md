# Changelog

All notable changes to this project will be documented in this file.

## 2026-04-20 - 22:12

### Fixed
- **Critical NameError** in `main.py`: running without `--map` or `--replay` caused a `NameError` because `gamestate` was never assigned in the `else: pass` branch. Now prints a helpful error message and exits.
- Typo in `--max-ticks` help text (was copy-pasted from `--save-replay`).
- Spelling: `Michale` → `Michael` in author credits (`main.py`).
- Spelling: `playour` → `player`, `widnow` → `window`, `upate` → `update` (`planet_wars_draw.py`).
- Spelling: `aded` → `added`, `inital` → `initial` (`planet_wars.py`).
- Spelling: `prvoiding` → `providing` (`players.py`).
- Grammar: `--maps` → `--map` in error message (`main.py`).
- **Capitalisation standardisation**: Changed `src.id` to `src.ID` in `planet_wars.py` and `self.id` to `self.ID` in `players.py` mapping string identifiers securely to `ID` across the app to prevent overrides of Python's built-in `id()` function.
- **FPS Controls Bug** in `planet_wars_draw.py`: The `+` and `-` keys crashed the application because they relied on Pyglet 1.x `set_fps` attributes. Replaced with Pyglet 2.x-compatible clock scheduler interval tracking.
- **API mismatch** in `bots/OneMove.py`: `_my_planets` and `_not_my_planets` were accessed as properties instead of method calls `_my_planets()` / `_not_my_planets()`. This prevented the baseline demo (Step 1-2 of task) from running.
- **Wrong attribute** in `bots/OneMove.py`: `src.num_ships` → `src.ships` (matching the actual `Planet` attribute).
- Removed stale `gameinfo.log()` call in `bots/OneMove.py` (method does not exist on `Player`).

### Improved
- Added comprehensive module-level docstrings with attribution to all Python files.
- Added proper docstrings to all classes and public methods across: `entities.py`, `players.py`, `planet_wars.py`, `planet_wars_draw.py`, `logscripts/logger.py`.
- Converted freestanding comment blocks to proper docstrings (e.g. `Entity.distance_to`, `Player` class, `Blanko.py`).
- Improved clarity and consistency of inline comments throughout the codebase.
- Added attribution: "Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au> - S1 2026".

### Preserved (intentional educational design)
- `Blanko.py`: Docstring references helper method names without the underscore prefix (e.g. `my_planets` instead of `_my_planets`) — by design, to encourage students to explore the `Player` class and discover the correct API.
- Task spec Step 3 (`Rando.py` code example) uses `src.num_ships` instead of `src.ships` — this is in the task instructions, not in the codebase, and serves as a debugging exercise for students.
