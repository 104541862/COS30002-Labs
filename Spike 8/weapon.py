from time import time
import pyglet
from vector2d import Vector2D, Point2D
from graphics import COLOUR_NAMES, PolyLine, window, ArrowLine
from math import sin, cos, radians
from random import random, randrange, uniform
from path import Path
from matrix33 import Matrix33

WEAPON_STATS = {
    "rifle": {
        "color": (70, 40, 60),
        "length": 48,
        "width": 6,
        "projectile_speed": 800,
        "lifetime": 2.0,
        "spread": 1.5,
        "pellets": 1,
        "fire_rate": 12.0,
        "explosive": False,
        "damage": 25,
        "magazine_size": 30,
    },
    "rocket": {
        "color": (30, 20, 20),
        "length": 60,
        "width": 12,
        "projectile_speed": 400,
        "lifetime": 6.0,
        "spread": 0.0,
        "pellets": 1,
        "fire_rate": 2.5,
        "explosive": True,
        "damage": 1000,
        "magazine_size": None,  # infinite ammo for rockets
    },
    "handgun": {
        "color": (180, 180, 180),
        "length": 36,
        "width": 4,
        "projectile_speed": 600,
        "lifetime": 1.5,
        "spread": 4.0,
        "pellets": 1,
        "fire_rate": 3.0,
        "explosive": False,
        "damage": 20,
        "magazine_size": 12,
    },
    "grenade": {
        "color": (0, 60, 10),
        "length": 20,
        "width": 20,
        "projectile_speed": 250,
        "lifetime": 3.5,
        "spread": 0.0,
        "pellets": 1,
        "fire_rate": 0.6,
        "explosive": True,
        "damage": 1000,
        "magazine_size": 6,
    },
    "shotgun": {
        "color": (80, 70, 40),
        "length": 40,
        "width": 8,
        "projectile_speed": 450,
        "lifetime": 0.8,
        "spread": 12.0,
        "pellets": 8,
        "fire_rate": 1.5,
        "explosive": False,
        "damage": 20,
        "magazine_size": 8,
    },
}

class Weapon:
    """Base weapon class for firing projectiles + visual identity."""

    def __init__(self, owner, weapon_type="rifle"):
        self.owner = owner
        
        self.is_active = False
        self.trigger_held = False

        self.weapon_type = weapon_type
        
        # visual orientation (direction weapon is aiming)
        self.aim_direction = Vector2D(1, 0)

        # Visual representation of the weapon (a line)
        self.hold_offset = 8  # distance to side of agent
        self.forward_offset = 4  # small forward shift so it doesn't clip body

        

        stats = WEAPON_STATS[self.weapon_type]

        self.color = stats["color"]
        self.length = stats["length"]
        self.width = stats["width"]
        self.projectile_speed = stats["projectile_speed"]
        self.projectile_lifetime = stats["lifetime"]
        self.spread = stats["spread"]
        self.pellets = stats["pellets"]
        self.fire_rate = stats["fire_rate"]
        self.explosive = stats["explosive"]
        self.damage = stats["damage"]
        self.magazine_size = stats["magazine_size"]

        if self.magazine_size is not None:
            self.ammo = self.magazine_size
        else:
            self.ammo = float('inf')  # infinite ammo for weapons like rockets

        
        self.fire_cooldown = 1.0 / self.fire_rate
        self._last_fire_time = 0.0

        self.line = pyglet.shapes.Rectangle(
            self.owner.pos.x,
            self.owner.pos.y,
            self.length,
            self.width,
            color=self.color,
            batch=window.get_batch("main")
        )

        self.line.anchor_x = 0
        self.line.anchor_y = self.line.height / 2

        self.sync_to_owner()

        self.line.opacity = 0
        self.line.visible = False  # optional but nice for clarity

    def update(self, delta):
        owner = self.owner

        if not self.is_active:
            self.line.opacity = 0
            self.line.visible = False
            return

        self.line.opacity = 255
        self.line.visible = True

        hold_pos = owner.pos + (-owner.side * self.hold_offset)
        hold_pos += owner.heading * self.forward_offset

        self.line.x = hold_pos.x
        self.line.y = hold_pos.y

        if self.aim_direction.lengthSq() > 0:
            self.line.rotation = -self.aim_direction.angle_degrees()

    def set_aim(self, direction):
        self.aim_direction = direction.normalise()

    def set_position(self, pos):
        self.line.x = pos.x
        self.line.y = pos.y

    def sync_to_owner(self):
        owner = self.owner

        hold_pos = owner.pos + (-owner.side * self.hold_offset)
        hold_pos += owner.heading * self.forward_offset

        self.line.x = hold_pos.x
        self.line.y = hold_pos.y

        if self.aim_direction.lengthSq() > 0:
            self.line.rotation = -self.aim_direction.angle_degrees()

    def get_muzzle_position(self):
        owner = self.owner

        hold_pos = owner.pos + (-owner.side * self.hold_offset)
        hold_pos += owner.heading * self.forward_offset

        muzzle = hold_pos + self.aim_direction * self.length
        return muzzle
    
    def apply_spread(self, direction, spread_degrees):
        angle = radians(uniform(-spread_degrees, spread_degrees))

        x = direction.x * cos(angle) - direction.y * sin(angle)
        y = direction.x * sin(angle) + direction.y * cos(angle)

        return Vector2D(x, y).normalise()

    def can_fire(self):
        """Checks cooldown."""
        return (time() - self._last_fire_time) >= self.fire_cooldown

    def fire(self, direction):
        if self.ammo <= 0:
            return []

        self._last_fire_time = time()

        muzzle = self.get_muzzle_position()

        # ensure direction is normalized
        base_dir = direction.normalise()

        stats = WEAPON_STATS[self.weapon_type]

        pellets = stats["pellets"]
        spread = stats["spread"]

        shots = []

        for _ in range(pellets):
            dir_with_spread = self.apply_spread(base_dir, spread)

            shots.append({
                "pos": muzzle.copy(),
                "vel": dir_with_spread * self.projectile_speed,
                "lifetime": self.projectile_lifetime,
                "explosive": stats["explosive"],
                "damage": stats["damage"],
            })

        if self.magazine_size is not None:
            self.ammo -= 1
                
        return shots
    
class Projectile:
    def __init__(self, pos, vel, lifetime, explosive=False, damage=100, color=(255, 255, 0), radius=3):
        self.pos = pos
        self.vel = vel
        self.radius = radius
        self.explosive = explosive
        self.damage = damage

        self.spawn_time = time()
        self.lifetime = lifetime

        self.shape = self._create_shape(color, radius)

    def update(self, delta):
        self.pos += self.vel * delta

        self.shape.x = self.pos.x
        self.shape.y = self.pos.y

    def _create_shape(self, color, radius):
        if self.explosive:
            return pyglet.shapes.Rectangle(
                self.pos.x, self.pos.y,
                20, 20,
                color=(0, 60, 10),
                batch=window.get_batch("main")
            )
        elif not self.explosive: 
            return pyglet.shapes.Circle(
                self.pos.x, self.pos.y,
                radius,
                color=color,
                batch=window.get_batch("main")
            )

    def is_expired(self):
        return (time() - self.spawn_time) >= self.lifetime
    
class Explosion:
    def __init__(self, pos, radius=60, duration=0.3):
        self.pos = pos
        self.duration = duration
        self.start_time = time()

        self.shape = pyglet.shapes.Circle(
            pos.x, pos.y,
            radius,
            color=(255, 120, 40),
            batch=window.get_batch("main")
        )

    def update(self, delta):
        # simple fade-out expansion
        t = (time() - self.start_time) / self.duration
        self.shape.radius = 60 + t * 30
        self.shape.opacity = int(255 * max(0, 1 - t))

    def expired(self):
        return (time() - self.start_time) > self.duration