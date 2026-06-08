import pyglet
from vector2d import Vector2D
from graphics import COLOUR_NAMES, window

class Mine:
    def __init__(self, pos, owner, fuse=10.0, radius=60):
        self.pos = pos.copy()
        self.owner = owner
        self.fuse = fuse
        self.radius = radius
        self.arm_time = 2.0  # seconds
        self.timer = 0.0
        self.armed = False
        self.yellowness = 10.0

        self.shape = pyglet.shapes.Circle(
            self.pos.x,
            self.pos.y,
            20,
            color = (255, 22 * int(self.yellowness), 0),  # yellow
            batch=window.get_batch("main")
        )

    def update(self, delta):
        self.timer += delta
        self.yellowness -= delta

        self.shape.color = (255, 22 * int(self.yellowness), 0)
        
        if self.timer >= self.arm_time:
            self.armed = True

    def is_expired(self):
        return self.timer >= self.fuse

    def destroy(self):
        self.shape.delete()

import pyglet
from graphics import window

class Explosion:
    """
    Short-lived visual + logical explosion.
    Exists for a few frames, then deletes itself.
    """

    def __init__(self, pos, radius, life=0.15):
        self.pos = pos.copy()
        self.radius = radius

        self.life = life
        self.timer = 0.0

        # visual representation (IMPORTANT: must be in a batch)
        self.shape = pyglet.shapes.Circle(
            self.pos.x,
            self.pos.y,
            self.radius,
            color=(255, 140, 0),  # orange explosion
            batch=window.get_batch("main")
        )

        self._alive = True

    def update(self, dt):
        if not self._alive:
            return

        self.timer += dt

        # optional: fade out effect
        if hasattr(self.shape, "opacity"):
            t = self.timer / self.life
            self.shape.opacity = int(max(0, 255 * (1.0 - t)))

        if self.timer >= self.life:
            self.destroy()

    def alive(self):
        return self._alive

    def destroy(self):
        if not self._alive:
            return

        self._alive = False

        if self.shape is not None:
            self.shape.delete()
            self.shape = None