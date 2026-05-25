import pyglet
from graphics import window, COLOUR_NAMES

class Slider:

    def __init__(self, x, y, width, min_val, max_val, value, label):

        self.x = x
        self.y = y
        self.width = width

        self.min_val = min_val
        self.max_val = max_val
        self.value = value

        self.label = label

        self.dragging = False

        # background bar
        self.bar = pyglet.shapes.Rectangle(
            x, y,
            width, 6,
            color=COLOUR_NAMES['LIGHT_GREY'],
            batch=window.get_batch("info")
        )

        # draggable knob
        self.knob = pyglet.shapes.Circle(
            x, y + 3,
            8,
            color=COLOUR_NAMES['RED'],
            batch=window.get_batch("info")
        )

        self.text = pyglet.text.Label(
            '',
            x=x,
            y=y + 20,
            color=COLOUR_NAMES['WHITE'],
            batch=window.get_batch("info")
        )

        self.update_knob()

    def update_knob(self):

        t = (self.value - self.min_val) / (self.max_val - self.min_val)

        self.knob.x = self.x + t * self.width

        self.text.text = f'{self.label}: {self.value:.2f}'

    def contains(self, mx, my):

        dx = mx - self.knob.x
        dy = my - self.knob.y

        return dx * dx + dy * dy <= self.knob.radius * self.knob.radius

    def set_from_mouse(self, mx):

        mx = max(self.x, min(self.x + self.width, mx))

        t = (mx - self.x) / self.width

        self.value = self.min_val + t * (self.max_val - self.min_val)

        self.update_knob()