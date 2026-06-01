"""
D-LEVEL CUSTOM PROJECT - Point2D Module
This module defines the Point2D class, a simple container for 2D coordinates. 
It is used throughout the project to represent positions in the world and is designed to be lightweight and efficient.
"""

class Point2D(object):
    """A simple 2D coordinate container."""
    __slots__ = ('x', 'y')

    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)

    def copy(self):
        """Returns a new Point2D with the same coordinates."""
        return Point2D(self.x, self.y)

    def __str__(self):
        return '(%5.2f,%5.2f)' % (self.x, self.y)
