"""3x3 Matrix for 2D Affine Transformations.

This module provides a 3x3 matrix implementation optimized for 2D game operations 
such as translation, scaling, and rotation. It is used to transform agent 
vertex data from local object space to global world space.

Created by
    Clinton Woodward (2019)
    Steve Dower (2020)
    contact: cwoodward@swin.edu.au

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""

from math import cos, sin

class Matrix33(object):
    """A 3x3 matrix for two-dimensional coordinate transformations."""

    def __init__(self, m=None):
        # Flattened 3x3 list: [a11, a12, a13, a21, a22, a23, a31, a32, a33]
        if isinstance(m, Matrix33):
            m = list(m._m)
        self._m = m or [1., 0., 0., 0., 1., 0., 0., 0., 1.]

    def reset(self):
        """Resets to the Identity Matrix."""
        self._m = [1., 0., 0., 0., 1., 0., 0., 0., 1.]

    # ---- Transformation Creation ----

    def translate(self, x, y):
        """Returns a new matrix translated by x, y."""
        return self * Matrix33([1., 0., 0., 0., 1., 0., x, y, 1.])

    def translate_update(self, x, y):
        """Updates the current matrix with a translation of x, y."""
        self._fast_imul(Matrix33([1., 0., 0., 0., 1., 0., x, y, 1.]))

    def scale(self, xscale, yscale):
        """Returns a new matrix scaled by xscale, yscale."""
        return self * Matrix33([xscale, 0., 0., 0., yscale, 0., 0., 0., 1.])

    def scale_update(self, xscale, yscale):
        """Updates the current matrix with a scaling of xscale, yscale."""
        self._fast_imul(Matrix33([xscale, 0., 0., 0., yscale, 0., 0., 0., 1.]))

    def rotate(self, rads):
        """Returns a new matrix rotated by rads (radians)."""
        s, c = sin(rads), cos(rads)
        return self * Matrix33([c, s, 0., -s, c, 0., 0., 0., 1.])

    def rotate_update(self, rads):
        """Updates the current matrix with a rotation of rads."""
        s, c = sin(rads), cos(rads)
        self._fast_imul(Matrix33([c, s, 0., -s, c, 0., 0., 0., 1.]))

    def rotate_by_vectors_update(self, fwd, side):
        """Updates rotation using forward and side orientation vectors."""
        self._fast_imul(Matrix33([fwd.x, fwd.y, 0., side.x, side.y, 0., 0., 0., 1.]))

    # ---- Point Transformations ----

    def transform_vector2d_list(self, points):
        """Applies matrix transformation to a list of Vector2D/Point2D objects."""
        a11, a12, _, a21, a22, _, a31, a32, _ = self._m
        for pt in points:
            tx, ty = pt.x, pt.y
            pt.x = a11 * tx + a21 * ty + a31
            pt.y = a12 * tx + a22 * ty + a32

    def transform_vector2d(self, pt):
        """Applies matrix transformation to a single point."""
        a11, a12, _, a21, a22, _, a31, a32, _ = self._m
        tx, ty = pt.x, pt.y
        pt.x = a11 * tx + a21 * ty + a31
        pt.y = a12 * tx + a22 * ty + a32

    # ---- Multiplication Logic ----

    def __mul__(self, rhs):
        """Full 3x3 matrix multiplication (self * rhs)."""
        a = self._m
        b = rhs._m
        ret = [
            a[0]*b[0] + a[1]*b[3] + a[2]*b[6], a[0]*b[1] + a[1]*b[4] + a[2]*b[7], a[0]*b[2] + a[1]*b[5] + a[2]*b[8],
            a[3]*b[0] + a[4]*b[3] + a[5]*b[6], a[3]*b[1] + a[4]*b[4] + a[5]*b[7], a[3]*b[2] + a[4]*b[5] + a[5]*b[8],
            a[6]*b[0] + a[7]*b[3] + a[8]*b[6], a[6]*b[1] + a[7]*b[4] + a[8]*b[7], a[6]*b[2] + a[7]*b[5] + a[8]*b[8]
        ]
        return Matrix33(ret)

    def _fast_imul(self, rhs):
        """Optimised in-place multiplication for standard affine transforms.
        
        Assumes column 3 is [0, 0, 1], which is true for all standard 2D transforms.
        """
        a = self._m
        b = rhs._m
        self._m = [
            a[0]*b[0] + a[1]*b[3], a[0]*b[1] + a[1]*b[4], 0.0,
            a[3]*b[0] + a[4]*b[3], a[3]*b[1] + a[4]*b[4], 0.0,
            a[6]*b[0] + a[7]*b[3] + b[6], a[6]*b[1] + a[7]*b[4] + b[7], 1.0
        ]

    def __str__(self):
        return '[%5.1f, %5.1f, %5.1f]\n[%5.1f, %5.1f, %5.1f]\n[%5.1f, %5.1f, %5.1f]' % tuple(self._m)
