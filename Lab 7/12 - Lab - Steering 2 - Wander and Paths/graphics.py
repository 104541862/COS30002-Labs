"""Graphics and Window Management for Autonomous Agents.

This module provides a abstraction layer for rendering shapes and managing 
the application window using pyglet. It defines custom shape groups (LineGroup, 
PolyLine, ArrowLine) that wrap pyglet.shapes for more complex multi-primitive 
rendering tasks used in steering simulations.

Created by
    Clinton Woodward (2019)
    James Bonner (2024)
    contact: jbonner@swin.edu.au

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""

import pyglet
import math

# ---- Standard Color Palette ----
COLOUR_NAMES = {
    'BLACK':  (0, 0, 0, 255),
    'WHITE':  (255, 255, 255, 255),
    'RED':    (255, 0, 0, 255),
    'GREEN':  (0, 255, 0, 255),
    'BLUE':   (0, 0, 255, 255),
    'GREY':   (100, 100, 100, 255),
    'PINK':   (255, 175, 175, 255),
    'YELLOW': (255, 255, 0, 255),
    'ORANGE': (255, 175, 0, 255),
    'PURPLE': (200, 0, 175, 200),
    'BROWN':  (125, 125, 100, 255),
    'AQUA':   (100, 230, 255, 255),
    'DARK_GREEN': (0, 100, 0, 255),
    'LIGHT_GREEN':(150, 255, 150, 255),
    'LIGHT_BLUE': (150, 150, 255, 255),
    'LIGHT_GREY': (200, 200, 200, 255),
    'LIGHT_PINK': (255, 230, 230, 255)
}

class ShapeGroup:
    """Base class for managing groups of pyglet shapes as a single entity.
    
    Provides common properties for position, color, opacity, and visibility, 
    propagating changes to all member shapes.
    """
    def __init__(self, anchor, batch):
        self._x = anchor.x
        self._y = anchor.y
        self._anchor_x = self._x
        self._anchor_y = self._y
        self._rgba = (255, 255, 255, 255)
        self._visible = True
        self._batch = batch
        self.shapes = []

    def draw(self):
        """Explicit draw call for the group (if not using batches)."""
        if self._visible:
            for shape in self.shapes:
                shape.draw()

    def translate(self, v):
        """Moves all shapes in the group by a translation vector."""
        for shape in self.shapes:
            shape.x += v.x
            shape.y += v.y
        self._anchor_x += v.x
        self._anchor_y += v.y

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self.position = pyglet.math.Vec2(value, self._y)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self.position = pyglet.math.Vec2(self._x, value)

    @property
    def position(self):
        return pyglet.math.Vec2(self._x, self._y)

    @position.setter
    def position(self, values):
        if isinstance(values, tuple):
            values = pyglet.math.Vec2(values[0], values[1])
        pos = pyglet.math.Vec2(self._x, self._y)
        v = values - pos
        self.translate(v)
        self._x = values.x
        self._y = values.y

    @property
    def color(self):
        return self._rgba

    @color.setter
    def color(self, values):
        # Handle RGB and RGBA
        if len(values) == 3:
            r, g, b = values
            a = self._rgba[3]
        else:
            r, g, b, a = values
        
        self._rgba = (r, g, b, a)
        for shape in self.shapes:
            shape.color = self._rgba

    @property
    def colour(self):
        return self.color

    @colour.setter
    def colour(self, values):
        self.color = values

    @property
    def opacity(self):
        return self._rgba[3]

    @opacity.setter
    def opacity(self, value):
        self._rgba = (*self._rgba[:3], value)
        for shape in self.shapes:
            shape.color = self._rgba

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value
        for shape in self.shapes:
            shape.visible = value

    @property
    def batch(self):
        return self._batch

    @batch.setter
    def batch(self, batch):
        if self._batch == batch:
            return
        for shape in self.shapes:
            shape.batch = batch 
        self._batch = batch
        
class LineGroup(ShapeGroup):
    """A ShapeGroup specifically for primitives defined by lines."""
    def __init__(self, position, rotation=0, batch=None):
        super().__init__(position, batch=batch)
        self._rotation = rotation

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        """Rotates all lines in the group around the anchor point."""
        a_v = pyglet.math.Vec2(self._anchor_x, self._anchor_y)
        rel_r = value - self._rotation
        for line in self.shapes:
            # Move vertices into relative space
            v1 = pyglet.math.Vec2(line.x, line.y) - a_v
            v2 = pyglet.math.Vec2(line.x2, line.y2) - a_v
            # Rotate using pyglet's built-in math
            v1 = v1.rotate(rel_r)
            v2 = v2.rotate(rel_r)
            # Transform back to world space
            v1 = v1 + a_v
            v2 = v2 + a_v
            # Update line primitive
            line.x, line.y = v1.x, v1.y
            line.x2, line.y2 = v2.x, v2.y
        self._rotation = value

class PolyLine(LineGroup):
    """A series of connected lines forming a path or polygon."""
    def __init__(self, vertices, width=1, colour=COLOUR_NAMES['AQUA'], batch=None, closed=False):
        super().__init__(vertices[0], batch=batch)
        
        # Create line primitives between consecutive vertices
        for i in range(len(vertices) - 1):
            self.shapes.append(
                pyglet.shapes.Line(
                    vertices[i].x, vertices[i].y,
                    vertices[i+1].x, vertices[i+1].y,
                    width, color=colour, batch=batch
                )
            )
        
        # Optionally close the shape by connecting the end back to the start
        if closed and len(vertices) > 2:
            self.shapes.append(
                pyglet.shapes.Line(
                    vertices[-1].x, vertices[-1].y,
                    vertices[0].x, vertices[0].y,
                    width, color=colour, batch=batch
                )
            )

class ArrowLine(LineGroup):
    """A directed line with an arrow head at the tip."""
    def __init__(self, v1, v2, width=1, colour=COLOUR_NAMES['AQUA'], batch=None, 
                 arrow_length=10, arrow_offset=0, arrow_angle=math.pi/4):
        super().__init__(v1, batch=batch)
        self._endx = v2.x
        self._endy = v2.y
        self.width = width
        self.colour = colour
        self.arrow_length = arrow_length
        self.arrow_offset = arrow_offset
        self.arrow_angle = arrow_angle
        
        # Main shaft
        self.shapes.append(
            pyglet.shapes.Line(v1.x, v1.y, v2.x, v2.y, width, color=colour, batch=batch)
        )
        self.update_arrow_tines()
        
    def update_arrow_tines(self):
        """Re-calculates the arrow head geometry when the line moves or changes."""
        start = self.position
        end = self.end_pos
        arrow_vec = end - start
        
        # Calculate anchor for the arrow head (handles offsets)
        arrow_anchor = start + arrow_vec * (1 - self.arrow_offset)
        
        # Calculate tine directions
        # Invert direction and rotate by arrow_angle
        if arrow_vec.length() > 0:
            dir_vec = -arrow_vec.normalize() * self.arrow_length
            av1 = dir_vec.rotate(self.arrow_angle) + end
            av2 = dir_vec.rotate(-self.arrow_angle) + end
        else:
            av1 = end
            av2 = end
        
        # Update or create the tine primitives
        if len(self.shapes) > 1:
            self.shapes[1].x, self.shapes[1].y = arrow_anchor.x, arrow_anchor.y
            self.shapes[1].x2, self.shapes[1].y2 = av1.x, av1.y
        else:
            self.shapes.append(pyglet.shapes.Line(arrow_anchor.x, arrow_anchor.y, av1.x, av1.y, 
                                                 self.width, color=self.colour, batch=self.batch))
            
        if len(self.shapes) > 2:
            self.shapes[2].x, self.shapes[2].y = arrow_anchor.x, arrow_anchor.y
            self.shapes[2].x2, self.shapes[2].y2 = av2.x, av2.y
        else:
            self.shapes.append(pyglet.shapes.Line(arrow_anchor.x, arrow_anchor.y, av2.x, av2.y, 
                                                 self.width, color=self.colour, batch=self.batch))

    @property
    def end_pos(self):
        return pyglet.math.Vec2(self._endx, self._endy)

    @end_pos.setter
    def end_pos(self, value):
        self._endx, self._endy = value.x, value.y
        self.shapes[0].x2, self.shapes[0].y2 = value.x, value.y
        self.update_arrow_tines()

class GameWindow(pyglet.window.Window):
    """The main application window, extending pyglet.window.Window.
    
    Handles input routing, event management, and batch-based rendering.
    """
    def __init__(self, **kwargs):
        # Enable anti-aliasing via multisampling
        kwargs['config'] = pyglet.gl.Config(double_buffer=True, sample_buffers=1, samples=8)
        super().__init__(**kwargs)

        self.fps_display = pyglet.window.FPSDisplay(self)
        self.cfg = {'INFO': False}
        
        # Use batches to group draw calls for better performance
        self.batches = {
            "main": pyglet.graphics.Batch(),
            "info": pyglet.graphics.Batch()
        }
        
        # Standard UI labels
        self.labels = {
            'mode':   pyglet.text.Label('', x=200, y=self.height-20, color=COLOUR_NAMES['WHITE']),
            'status': pyglet.text.Label('', x=400, y=self.height-20, color=COLOUR_NAMES['WHITE']) 
        }
        self._add_handlers()

    def _add_handlers(self):
        """Internal helper to register event handlers."""
        
        @self.event
        def on_resize(width, height):
            from game import game
            if game and game.world:
                game.world.cx = width
                game.world.cy = height

        @self.event
        def on_mouse_press(x, y, button, modifiers):
            from game import game
            if game:
                game.input_mouse(x, y, button, modifiers)

        @self.event
        def on_key_press(symbol, modifiers):
            # Toggle debug info with 'I'
            if symbol == pyglet.window.key.I:
                self.cfg['INFO'] = not self.cfg['INFO']
            
            from game import game
            if game:
                game.input_keyboard(symbol, modifiers)

        @self.event
        def on_draw():
            self.clear()
            # Draw game objects
            self.batches["main"].draw()
            # Draw debug info if enabled
            if self.cfg['INFO']:
                self.batches["info"].draw()
            # Draw UI elements
            self.fps_display.draw()
            for label in self.labels.values():
                label.draw()
        
    def get_batch(self, batch_name="main"):
        return self.batches.get(batch_name, self.batches["main"])

# ---- Global Window Initialization ----
# Window creation occurs at module level to provide a global graphical context.
settings = {
    'width': 800,
    'height': 800,
    'vsync': True,
    'resizable': False,
    'caption': "Autonomous Agent Steering - Lab 12",
}
    
window = GameWindow(**settings)