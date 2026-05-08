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

class Path(object):
    """A container for waypoints defining a navigational route."""

    def __init__(self, num_pts=0, minx=0, miny=0, maxx=0, maxy=0, looped=False):
        self.looped = looped
        self._num_pts = num_pts
        self._cur_pt_idx = -1
        self._pts = []
        self.renderable = None
        
        # Optionally generate a random path immediately
        if num_pts > 0:
            self.create_random_path(num_pts, minx, miny, maxx, maxy, looped)
        else:
            self._reset()

    def current_pt(self):
        """Returns the current target waypoint."""
        return self._pts[self._cur_pt_idx]

    def inc_current_pt(self):
        """Advances the path cursor to the next waypoint."""
        assert self._num_pts > 0
        self._cur_pt_idx += 1
        
        # If looped, wrap back to the start
        if self.is_finished() and self.looped:
            self._cur_pt_idx = 0

    def is_finished(self):
        """Checks if the path cursor has reached the final point."""
        return self._cur_pt_idx >= self._num_pts - 1

    def create_random_path(self, num_pts, minx, miny, maxx, maxy, looped=False):
        """Generates an organic, circular-ish random path within bounds."""
        self.looped = looped
        self.clear()
        
        mid_x = (maxx + minx) / 2.0
        mid_y = (maxy + miny) / 2.0
        radius = min(mid_x - minx, mid_y - miny)
        spacing = TWO_PI / num_pts

        for i in range(num_pts):
            # Jitter the radial distance for a less perfect circle
            radial_dist = uniform(radius * 0.2, radius)
            pt = Vector2D(radial_dist, 0.0)
            vec2D_rotate_around_origin(pt, i * spacing)
            pt.x += mid_x
            pt.y += mid_y
            self._pts.append(pt)

        self._reset()
        return self._pts

    def add_way_pt(self, new_pt):
        """Appends a new waypoint to the path."""
        self._pts.append(new_pt)
        self._reset()

    def set_pts(self, path_pts):
        """Replaces current waypoints with a new set."""
        self._pts = path_pts
        self._reset()

    def _reset(self):
        """Resets the cursor and synchronises the graphical PolyLine."""
        self._cur_pt_idx = 0
        self._num_pts = len(self._pts)
        
        # Update or create the visual representation
        if self._num_pts > 0:
            self.renderable = PolyLine(
                self._pts,
                colour=COLOUR_NAMES['PINK'],
                batch=window.get_batch("info"),
                closed=self.looped
            )

    def clear(self):
        """Removes all waypoints."""
        self._pts = []
        self._reset()

    def get_pts(self):
        """Returns the internal list of waypoints."""
        return self._pts
