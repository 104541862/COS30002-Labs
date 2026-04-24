"""Pyglet-based rendering and GUI for PlanetWars.

This module contains all graphical components:

- **Colour palette** — a named colour map used to assign each player a
  distinct hue.
- **RenderableEntity / RenderablePlanet / RenderableFleet** — lightweight
  wrappers that convert game-space coordinates into screen-space positions
  and create pyglet shape primitives.
- **PlanetWarsEntityRenderer** — batches and synchronises all renderable
  entities so they can be drawn in a single pass.
- **PlanetWarsUI** — heads-up display elements (FPS counter, step label).
- **PlanetWarsWindow** — the pyglet Window subclass that owns the game loop,
  background sprite, and keyboard input handling.

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""

import pyglet
import pathlib
from entities import NEUTRAL_ID, SCALE_FACTOR


PLANET_RADIUS_FACTOR = 12
FLEET_SIZE_FACTOR = 0.25
WINDOW_X = 1000
WINDOW_Y = 800

# region colours
COLOR_NAMES = {
    "BLACK": (0.0, 0.0, 0.0, 1),
    "WHITE": (1.0, 1.0, 1.0, 1),
    "GREY": (0.6, 0.6, 0.6, 1),
    "LIGHT_GREY": (0.9, 0.9, 0.9, 1),
    "PLAYER_1_BLUE": (0.4, 0.7, 1.0, 1),
    "PLAYER_2_YELLOW": (0.8, 0.8, 0.2, 1),
    "RED": (1.0, 0.0, 0.0, 1),
    "GREEN": (0.0, 1.0, 0.0, 1),
    "BLUE": (0.0, 0.0, 1.0, 1),
    "PINK": (1.0, 0.7, 0.7, 1),
    "YELLOW": (1.0, 1.0, 0.0, 1),
    "ORANGE": (1.0, 0.7, 0.0, 1),
    "PURPLE": (1.0, 0.0, 0.7, 1),
    "BROWN": (0.5, 0.35, 0.0, 1),
    "AQUA": (0.0, 1.0, 1.0, 1),
    "DARK_GREEN": (0.0, 0.4, 0.0, 1),
    "LIGHT_BLUE": (0.6, 0.6, 1.0, 1),
    "LIGHT_RED": (1.0, 0.6, 0.6, 1),
    "LIGHT_GREEN": (0.6, 1.0, 0.6, 1),
}


def to_rgb(a_gl_color):
    """Convert a normalised (0.0–1.0) RGBA tuple to 0–255 integer RGBA."""
    return tuple([int(x * 255) for x in a_gl_color])


COLOR_NAMES_255 = {k: to_rgb(v) for k, v in COLOR_NAMES.items()}
# endregion colours

IMAGES = {
    "background": "images/space.jpg",
}


class RenderableEntity:
    """Base wrapper that maps a game entity to screen-space coordinates."""

    def __init__(self, entity):
        self.entity = entity
        # Convert from normalised game space (0–1) to window pixel space,
        # with a 0.9 scale factor and 0.5 offset for centring.
        self.x = ((entity.x / SCALE_FACTOR - 0.5) * 0.9 + 0.5) * WINDOW_X
        self.y = ((entity.y / SCALE_FACTOR - 0.5) * 0.9 + 0.5) * WINDOW_Y

    def update(self, displayproperty):
        """Refresh the label text to show the current display property."""
        self.label.text = str(self.entity.__getattribute__(displayproperty))


class RenderablePlanet(RenderableEntity):
    """Draws a planet as two concentric circles (white outline + player colour)."""

    def __init__(self, planet, batch, displayproperty, colour):
        super().__init__(planet)

        detail_colour = tuple(int(c * 0.6) for c in colour[:3]) + (255,)
        
        self.circles = [
            pyglet.shapes.Circle(
                self.x,
                self.y,
                (planet.growth + 1) * PLANET_RADIUS_FACTOR,
                color=detail_colour,
                segments=40,
                batch=batch,
            ),
            pyglet.shapes.Circle(
                self.x,
                self.y,
                (planet.growth + 1) * PLANET_RADIUS_FACTOR - 2,
                color=colour,
                segments=40,
                batch=batch,
            ),
        ]
        self.label = pyglet.text.Label(
            str(planet.__getattribute__(displayproperty)),
            x=self.x - 2,
            y=self.y + 4,  # centering is weirdly off
            anchor_x="center",
            anchor_y="center",
            batch=batch,
            color=detail_colour
        )


class RenderableFleet(RenderableEntity):
    """Draws a fleet as a directional triangle pointing along its heading."""

    def __init__(self, fleet, batch, displayproperty, colour):
        super().__init__(fleet)
        triangle_half_size = min(max(FLEET_SIZE_FACTOR * fleet.ships // 2, 10), 50)

        # Vector pointing along the x-axis defines the triangle size;
        # rotate to the fleet's travel direction for the 'forward' vertex.
        v_temp = pyglet.math.Vec2(triangle_half_size, 0)
        self.v1 = v_temp.from_heading(fleet.heading)

        # A slightly shorter vector forms the two trailing vertices,
        # each rotated ±120° off the travel direction.
        v_temp = pyglet.math.Vec2(triangle_half_size * 0.75, 0)
        v_temp = v_temp.from_heading(fleet.heading)
        v2 = v_temp.rotate(2.094)  # 120 deg in radians
        v3 = v_temp.rotate(-2.094)  # 120 deg in radians

        self.triangle = pyglet.shapes.Triangle(
            self.v1.x,  # x
            self.v1.y,  # y
            v2.x,  # x2
            v2.y,  # y2
            v3.x,  # x3
            v3.y,  # y3
            color=colour,
            batch=batch,
        )
        self.label = pyglet.text.Label(
            str(fleet.__getattribute__(displayproperty)),
            x=self.x,
            y=self.y,
            anchor_x="center",
            anchor_y="center",
            batch=batch,
            font_size=10,
            color=colour,
        )

    def update(self, displayproperty):
        """Refresh label text and reposition the triangle."""
        super().update(displayproperty)
        self.triangle.x = self.x + self.v1.x
        self.triangle.y = self.y + self.v1.y
        self.label.x = self.x
        self.label.y = self.y


class PlanetWarsEntityRenderer:
    """Manages rendering of all game entities (planets and fleets).

    Handles cached positions, colour assignment, and batch drawing for a
    PlanetWars game instance. Supports switching between the global view
    and individual player fog-of-war views.
    """

    def __init__(self, game, window):
        self.game = game
        # Assign a unique colour to each player
        self.playercolours = {NEUTRAL_ID: "GREY"}
        for p in game.players:
            if p == NEUTRAL_ID:
                continue
            # Players cannot be BLACK, WHITE, GREY or LIGHT_GREY
            for k in list(COLOR_NAMES.keys())[4:]:
                # Colours must be unique per player
                # TODO: check for running out of colours
                if k not in self.playercolours.values():
                    self.playercolours[p] = k
                    break
        self.batch = pyglet.graphics.Batch()
        self.displayproperty = "ships"
        self.view_id = 0
        self.sync_all()

    def draw(self):
        """Draw all game entities; re-syncs if the game state is dirty."""
        # dirty is set whenever a planet changes hands or a fleet is created
        if self.game.dirty:
            self.sync_all()
        # Update planet text labels
        for planet in self.renderableplanets:
            planet.update(self.displayproperty)
        # Update fleet positions & labels
        for fleet in self.renderablefleets:
            fleet.update(self.displayproperty)
        # Draw everything in one batch call
        self.batch.draw()

    def sync_all(self):
        """Rebuild all renderable entities from the current game state.

        Used when planet ownership changes, fleets are created/destroyed,
        or the player view is switched.
        TODO: this is actually called every tick, which is not ideal.
        """
        if self.view_id == 0:
            planets = self.game.planets.values()
            fleets = self.game.fleets.values()
        else:
            player = list(self.game.players.keys())[self.view_id - 1]
            planets = self.game.players[player].planets.values()
            fleets = self.game.players[player].fleets.values()

        self.renderableplanets = []
        for p in planets:
            self.renderableplanets.append(
                RenderablePlanet(
                    p,
                    self.batch,
                    self.displayproperty,
                    COLOR_NAMES_255[self.playercolours[p.owner]],
                )
            )

        self.renderablefleets = []
        for f in fleets:
            self.renderablefleets.append(
                RenderableFleet(
                    f,
                    self.batch,
                    self.displayproperty,
                    COLOR_NAMES_255[self.playercolours[f.owner]],
                )
            )
        self.game.dirty = False

    def update(self):
        """Placeholder for future per-tick rendering updates."""
        pass


class PlanetWarsUI:
    """Heads-up display elements (FPS counter, step label)."""

    def __init__(self, window):
        self.fps_display = pyglet.window.FPSDisplay(window)
        self.step_label = pyglet.text.Label(
            "STEP", x=5, y=window.height - 20, color=COLOR_NAMES_255["WHITE"]
        )

    def draw(self):
        """Draw the FPS counter and the step/status label."""
        self.fps_display.draw()
        self.step_label.draw()


class PlanetWarsWindow(pyglet.window.Window):
    """Main application window — owns the game loop and input handling."""

    def __init__(self, game):
        self.game = game

        # Initialise the pyglet window
        super(PlanetWarsWindow, self).__init__(
            WINDOW_X,
            WINDOW_Y,
            vsync=True,
            resizable=False,
            caption="Planet Wars",
            # Anti-aliasing config. TODO: enable fallback if the graphics
            # card does not support multisampling.
            config=pyglet.gl.Config(double_buffer=True, sample_buffers=1, samples=8),
        )
        # Position the window near the top-left of the screen.
        # The window is not resizable so there is a 1:1 mapping between
        # screen size and the displayable map area.
        self.set_location(10, 10)

        # Load the background image and scale it to fill the window
        self.bg = pyglet.sprite.Sprite(
            pyglet.image.load(pathlib.PurePath().joinpath("./images/space.jpg"))
        )
        self.bg.scale_x = self.width / self.bg.image.width
        self.bg.scale_y = self.height / self.bg.image.height
        # Load the global UI elements (FPS counter, status bar)
        self.ui = PlanetWarsUI(self)
        # Load the renderer for game entities (planets, fleets)
        self.gamerenderer = PlanetWarsEntityRenderer(self.game, self)

        self.target_fps = 60.0
        pyglet.clock.schedule_interval(self.update, 1 / self.target_fps)
        pyglet.app.run()

    def update(self, args):
        """Called by the pyglet scheduler — advances game and updates HUD."""
        # Build the status-bar message
        msg = "Step:" + str(self.game.tick)
        if self.game.paused:
            msg += " [PAUSED]"
        msg += f"  --  POV: [{self.gamerenderer.view_id}] "
        if self.gamerenderer.view_id == 0:
            msg += "ALL"
        else:
            view_id = list(self.game.players.keys())[self.gamerenderer.view_id - 1]
            msg += self.game.players[view_id].name
        msg += "  --  Show: " + self.gamerenderer.displayproperty
        self.ui.step_label.text = msg

        # Advance the game simulation by one tick
        if self.game:
            self.game.update()
            # Has the game ended? (Should we close?)
            if not self.game.is_alive() or self.game.tick >= self.game.max_ticks:
                self.close()
            # "or True" bypasses the game.dirty render optimisation
            # TODO: figure out a way to bring it back
            if self.game.dirty or True:
                self.gamerenderer.sync_all()

    def on_key_press(self, symbol, modifiers):
        """Handle keyboard input for view cycling, stepping, and speed."""
        # Cycle player view backward with '['
        # TODO: Pass input into GameRenderer
        if symbol == pyglet.window.key.BRACKETLEFT:
            if self.gamerenderer.view_id > 0:
                self.gamerenderer.view_id -= 1
            else:
                self.gamerenderer.view_id = len(self.game.players)
        # Cycle player view forward with ']'
        if symbol == pyglet.window.key.BRACKETRIGHT:
            if self.gamerenderer.view_id < len(self.game.players):
                self.gamerenderer.view_id += 1
            else:
                self.gamerenderer.view_id = 0
        # Return to the all-player view with 'A'
        elif symbol == pyglet.window.key.A:
            self.gamerenderer.view_id = 0  # == "all"
        # Cycle the displayed planet attribute with 'L'
        elif symbol == pyglet.window.key.L:
            i = self.gamerenderer.displayproperty
            l = ["ID", "ships", "vision_age", "owner"]
            self.gamerenderer.displayproperty = (
                l[l.index(i) + 1] if l.index(i) < (len(l) - 1) else l[0]
            )
        # Single-step with 'N'
        elif symbol == pyglet.window.key.N:
            self.game.update(manual=True)
        # Toggle pause with 'P'
        elif symbol == pyglet.window.key.P:
            self.game.paused = not self.game.paused
        # Speed up (+) or slow down (-) the simulation
        elif symbol in [pyglet.window.key.PLUS, pyglet.window.key.EQUAL]:
            self.set_fps(self.target_fps + 5)
        elif symbol == pyglet.window.key.MINUS:
            self.set_fps(self.target_fps - 5)
        elif symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()

    def set_fps(self, new_fps):
        """Update the simulation tick rate."""
        self.target_fps = max(5, new_fps)
        pyglet.clock.unschedule(self.update)
        pyglet.clock.schedule_interval(self.update, 1 / self.target_fps)

    def on_draw(self):
        """Clear the screen and draw background, UI, then game entities."""
        self.clear()
        self.bg.draw()
        self.ui.draw()
        self.gamerenderer.draw()
