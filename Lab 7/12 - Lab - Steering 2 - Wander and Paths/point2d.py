"""2D Point structure for simple coordinate storage.

This module provides a lightweight Point2D class used primarily for 
defining local space vertex data for agent shapes and paths.

Created by
    Clinton Woodward (2019)
    contact: cwoodward@swin.edu.au

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
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
