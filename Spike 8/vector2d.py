"""2D Vector with related methods for game physics.

This module provides a custom 2D Vector implementation with standard 
mathematical operations (addition, subtraction, normalization, etc.) 
tailored for autonomous agent steering and physics.

Created by
    Clinton Woodward (2019)
    Steve Dower (2020)
    contact: cwoodward@swin.edu.au

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""

from math import sqrt, atan2, degrees
from point2d import Point2D

MIN_FLOAT = 1e-300

def is_equal(a, b):
    """Helper for floating point equality within a tolerance."""
    return abs(a - b) < 1e-12

class Vector2D(object):
    """A 2D Vector class with overloaded operators for easy math."""
    __slots__ = ('x', 'y')

    def __init__(self, x=0., y=0.):
        self.x = float(x)
        self.y = float(y)

    def zero(self):
        """Sets the vector components to zero."""
        self.x = 0.
        self.y = 0.

    def is_zero(self):
        """Checks if the vector is effectively zero."""
        return (self.x**2 + self.y**2) < MIN_FLOAT

    def length(self):
        """Calculates the magnitude of the vector."""
        return sqrt(self.x**2 + self.y**2)

    def lengthSq(self):
        """Calculates the squared magnitude (avoids expensive sqrt)."""
        return self.x**2 + self.y**2

    def normalise(self):
        """Normalises self to unit length (1.0). Mutates the vector."""
        l = self.length()
        if l > 0:
            self.x /= l
            self.y /= l
        else:
            self.x = 0.
            self.y = 0.
        return self

    def get_normalised(self):
        """Returns a normalised copy of the vector."""
        result = self.copy()
        result.normalise()
        return result

    def dot(self, v2):
        """Calculates the dot product with another vector."""
        return self.x * v2.x + self.y * v2.y

    def sign(self, v2):
        """Returns +1 if v2 is clockwise, -1 if anti-clockwise (assuming y-down)."""
        if self.y * v2.x > self.x * v2.y:
            return -1
        return 1

    def perp(self):
        """Returns a vector perpendicular to self."""
        return Vector2D(-self.y, self.x)

    def truncate(self, maxlength):
        """Limits the vector's magnitude to maxlength."""
        if self.lengthSq() > maxlength**2:
            self.normalise()
            self *= maxlength

    def distance(self, v2):
        """Calculates Euclidean distance to another vector."""
        return sqrt((v2.x - self.x)**2 + (v2.y - self.y)**2)

    def distanceSq(self, v2):
        """Calculates squared distance to another vector."""
        return (v2.x - self.x)**2 + (v2.y - self.y)**2

    def reflect(self, norm):
        """Reflects self around the provided normal vector."""
        self += 2.0 * self.dot(norm) * norm.get_reverse()

    def get_reverse(self):
        """Returns a negated copy of the vector."""
        return Vector2D(-self.x, -self.y)
    
    def angle(self):
        """Returns the angle of the vector in radians."""
        return atan2(self.y, self.x)
    
    def angle_degrees(self):
        """Returns the angle of the vector in degrees."""
        return degrees(self.angle())
    
    def __neg__(self):
        return Vector2D(-self.x, -self.y)

    def copy(self):
        return Vector2D(self.x, self.y)

    # Overloaded In-place Operators
    def __iadd__(self, rhs):
        self.x += rhs.x
        self.y += rhs.y
        return self

    def __isub__(self, rhs):
        self.x -= rhs.x
        self.y -= rhs.y
        return self

    def __imul__(self, rhs):
        self.x *= rhs
        self.y *= rhs
        return self

    def __itruediv__(self, rhs):
        self.x /= rhs
        self.y /= rhs
        return self

    # Comparison
    def __eq__(self, rhs):
        return is_equal(self.x, rhs.x) and is_equal(self.y, rhs.y)

    def __ne__(self, rhs):
        return not self.__eq__(rhs)

    # Arithmetic Operators
    def __add__(self, rhs):
        return Vector2D(self.x + rhs.x, self.y + rhs.y)

    def __sub__(self, rhs):
        return Vector2D(self.x - rhs.x, self.y - rhs.y)

    def __mul__(self, rhs):
        return Vector2D(self.x * rhs, self.y * rhs)

    def __rmul__(self, lhs):
        return Vector2D(self.x * lhs, self.y * lhs)

    def __truediv__(self, rhs):
        return Vector2D(self.x / rhs, self.y / rhs)

    def __str__(self):
        return '[%7.2f, %7.2f]' % (self.x, self.y)
