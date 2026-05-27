"""Path Container for Waypoint Following.

This module defines the Path class, which stores a sequence of waypoints. 
It supports both open and looped paths and provides a cursor mechanism 
to track progress through the path. It also handles the generation of 
random organic paths for testing.

Created by
    Clinton Woodward (2019)
    contact: cwoodward@swin.edu.au

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""

from random import uniform
from matrix33 import Matrix33
from vector2d import Vector2D
from graphics import window, PolyLine, COLOUR_NAMES
from math import pi

TWO_PI = pi * 2.0

def vec2D_rotate_around_origin(vec, rads):
    """Rotates a vector in-place by a given angle around (0,0)."""
    mat = Matrix33()
    mat.rotate_update(rads)
    mat.transform_vector2d(vec)

class Path:
    """Simple 2-point patrol path."""

    def __init__(self, p1=None, p2=None):
        self._pts = []
        self._cur_pt_idx = 0
        self.renderable = None

        if p1 and p2:
            self._pts = [p1, p2]

    def current_pt(self):
        return self._pts[self._cur_pt_idx]

    def inc_current_pt(self):
        # Toggle between 0 and 1
        self._cur_pt_idx = 1 - self._cur_pt_idx

    def is_finished(self):
        # Never "finishes" in a patrol loop
        return False

    def set_pts(self, p1, p2):
        self._pts = [p1, p2]
        self._cur_pt_idx = 0

    def get_pts(self):
        return self._pts