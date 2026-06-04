"""
D-LEVEL CUSTOM PROJECT - Geometry Utilities
Pure geometric helper functions for AI prediction, raycasts, and collision tests.
This module contains NO game state and NO rendering logic.
"""

from math import inf


# ------------------------------------------------------------
# SEGMENT vs AABB (core AI visibility / hit detection)
# ------------------------------------------------------------

def segment_hits_aabb(start, end, ax, ay, aw, ah):
    """
    Returns True if a line segment intersects an axis-aligned bounding box.

    Used for:
    - line of sight checks
    - bullet trajectory prediction
    - AI safety evaluation
    """

    dx = end.x - start.x
    dy = end.y - start.y

    t_min = 0.0
    t_max = 1.0

    def clip(p, q, tmin, tmax):
        if p == 0:
            # Parallel line
            if q < 0:
                return tmin, tmax, False
            return tmin, tmax, True

        r = q / p

        if p < 0:
            if r > tmax:
                return tmin, tmax, False
            if r > tmin:
                tmin = r
        else:
            if r < tmin:
                return tmin, tmax, False
            if r < tmax:
                tmax = r

        return tmin, tmax, True

    # X slabs
    t_min, t_max, ok = clip(-dx, start.x - ax, t_min, t_max)
    if not ok:
        return False

    t_min, t_max, ok = clip(dx, ax + aw - start.x, t_min, t_max)
    if not ok:
        return False

    # Y slabs
    t_min, t_max, ok = clip(-dy, start.y - ay, t_min, t_max)
    if not ok:
        return False

    t_min, t_max, ok = clip(dy, ay + ah - start.y, t_min, t_max)
    if not ok:
        return False

    return True


# ------------------------------------------------------------
# RAY vs AABB (for shooting prediction / wall collision AI)
# ------------------------------------------------------------

def ray_hits_aabb(origin, direction, ax, ay, aw, ah, max_dist=1000.0):
    """
    Ray-AABB intersection using slab method.

    Used for:
    - bullet trajectory simulation
    - bounce prediction
    - AI safety checks
    """

    inv_dx = 1.0 / direction.x if direction.x != 0 else inf
    inv_dy = 1.0 / direction.y if direction.y != 0 else inf

    tx1 = (ax - origin.x) * inv_dx
    tx2 = (ax + aw - origin.x) * inv_dx

    ty1 = (ay - origin.y) * inv_dy
    ty2 = (ay + ah - origin.y) * inv_dy

    tmin = max(min(tx1, tx2), min(ty1, ty2))
    tmax = min(max(tx1, tx2), max(ty1, ty2))

    if tmax < 0 or tmin > tmax:
        return False

    if tmin < 0 or tmin > max_dist:
        return False

    return True


# Optional: Ray-AABB intersection that also returns the hit distance (for bounce prediction)
def _ray_aabb_t(origin, direction, ax, ay, aw, ah):
    inv_x = 1.0 / direction.x if direction.x != 0 else float("inf")
    inv_y = 1.0 / direction.y if direction.y != 0 else float("inf")

    t1 = (ax - origin.x) * inv_x
    t2 = (ax + aw - origin.x) * inv_x
    t3 = (ay - origin.y) * inv_y
    t4 = (ay + ah - origin.y) * inv_y

    tmin = max(min(t1, t2), min(t3, t4))
    tmax = min(max(t1, t2), max(t3, t4))

    if tmax < 0 or tmin > tmax:
        return False, float("inf")

    return True, tmin


# ------------------------------------------------------------
# SIMPLE DISTANCE HELPERS (AI convenience)
# ------------------------------------------------------------

def distance(a, b):
    dx = b.x - a.x
    dy = b.y - a.y
    return (dx * dx + dy * dy) ** 0.5


def distance_sq(a, b):
    dx = b.x - a.x
    dy = b.y - a.y
    return dx * dx + dy * dy


# ------------------------------------------------------------
# AABB helper (optional convenience)
# ------------------------------------------------------------

def point_in_aabb(px, py, ax, ay, aw, ah):
    return ax <= px <= ax + aw and ay <= py <= ay + ah