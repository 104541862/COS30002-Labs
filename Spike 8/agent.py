"""Autonomous Agent Steering Logic.

This module defines the Agent class, which implements various steering 
behaviours such as Seek, Flee, Arrive, and placeholders for Pursuit, 
Wander, and Path Following. It handles the physics integration (force -> 
acceleration -> velocity -> position) and updates the graphical representation.

Created by
    Clinton Woodward (2019)
    James Bonner (2024)
    contact: jbonner@swin.edu.au

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""

from turtle import shape

import pyglet
from vector2d import Vector2D, Point2D
from graphics import COLOUR_NAMES, PolyLine, window, ArrowLine
from math import dist, sin, cos, radians
from random import random, randrange, uniform
from path import Path
from matrix33 import Matrix33
from weapon import Weapon
from fsm import AgentFSM, PatrolState, AttackState, CombatFSM, ShootingState, MovementFSM, SeekState, ArriveState

# Mapping of keyboard keys to steering modes
AGENT_MODES = {
    pyglet.window.key._1: 'seek',
    pyglet.window.key._2: 'arrive_slow',
    pyglet.window.key._3: 'arrive_normal',
    pyglet.window.key._4: 'arrive_fast',
    pyglet.window.key._5: 'flee',
    pyglet.window.key._6: 'pursuit',
    pyglet.window.key._7: 'follow_path',
    pyglet.window.key._8: 'wander',
}

class Agent(object):
    """A vehicle agent with steering behaviours."""

    # Deceleration rates for the Arrive behaviour
    DECELERATION_SPEEDS = {
        'slow': 0.9,
        'normal': 0.6,
        'fast': 0.3,
    }

    def __init__(self, world=None, scale=30.0, speed_scale=30.0, mass=1.0, color="LIGHT_BLUE", mode='seek'):
        # Reference to the simulation world
        self.world = world
        self.mode = mode

        # Physics state: position, velocity, and orientation
        angle = radians(random() * 360)
        self.pos = Vector2D(randrange(world.cx), randrange(world.cy))
        self.vel = Vector2D()
        self.heading = Vector2D(sin(angle), cos(angle))
        self.side = self.heading.perp()
        self.scale = Vector2D(scale, scale)
        self.mass = mass

        # Create weapon
        self.weapons = [
            Weapon(self, weapon_type="rifle"),
            Weapon(self, weapon_type="handgun"),
            Weapon(self, weapon_type="shotgun"),
            Weapon(self, weapon_type="rocket"),
            Weapon(self, weapon_type="grenade"),
        ]

        # Start with the first weapon active
        self.active_weapon_index = 0
        self.weapon = self.weapons[self.active_weapon_index]

        self.weapon.is_active = True
        self.weapon.sync_to_owner()
        
        # Forces and limits
        self.force = Vector2D()
        self.accel = Vector2D()
        self.max_speed = 30.0 * speed_scale
        self.max_force = 100.0 * scale

        # New Wander-specific state
        self.wander_target = Vector2D(1, 0)
        self.wander_dist = 2.0 * scale
        self.wander_radius = 1.5 * scale
        self.wander_jitter = 15.0

        # FSM for high-level behaviour control
        self.fsm = AgentFSM(self)
        self.movement_fsm = MovementFSM(self)
        self.combat_fsm = None
        self.movement_locked = False

        # Pathing
        self.path = Path()
        self.reached_waypoint = False

        p1 = Vector2D(self.world.cx - 200, 150)
        p2 = Vector2D(self.world.cx - 200, self.world.cy - 150)

        self.path.set_pts(p1, p2)
        self.path_visual = None
        self.waypoint_threshold = 30.0

        self.path_visual = PolyLine(
            self.path.get_pts(),
            colour=COLOUR_NAMES['PINK'],
            batch=window.get_batch("info"),
            closed=False
        )

        self.info_predicted_target = pyglet.shapes.Circle(
            0,
            0,
            8,
            color=COLOUR_NAMES['YELLOW'],
            batch=window.get_batch("info")
        )
        
        self.info_aim_line = ArrowLine(
            Vector2D(0, 0),
            Vector2D(0, 0),
            colour=COLOUR_NAMES['YELLOW'],
            batch=window.get_batch("info")
        )

        self.info_rocket_timer = pyglet.text.Label(
            '',
            x=0,
            y=0,
            anchor_x='center',
            anchor_y='bottom',
            color=(255, 120, 120, 255),
            batch=window.get_batch("info")
        )

        self.info_state_label = pyglet.text.Label(
            '',
            x=self.pos.x,
            y=self.pos.y + 75,
            anchor_x='center',
            anchor_y='bottom',
            color=(255, 255, 255, 255),
            batch=window.get_batch("info")
        )

        for shape in self.info_aim_line.shapes:
            shape.opacity = 120

        self.info_predicted_target.opacity = 180

        # ---- Graphical Representation ----
        self.color = color
        
        # Main vehicle primitive
        self.vehicle = pyglet.shapes.Circle(
            self.pos.x,
            self.pos.y,
            scale,  # radius (you can tune this)
            color=COLOUR_NAMES[self.color],
            batch=window.get_batch("main")
        )


        # ---- Debug/Info Visuals ----
        # Wander logic visuals (placeholders)
        self.info_wander_circle = pyglet.shapes.Circle(0, 0, 0, color=COLOUR_NAMES['WHITE'], batch=window.get_batch("info"))
        self.info_wander_target = pyglet.shapes.Circle(0, 0, 0, color=COLOUR_NAMES['GREEN'], batch=window.get_batch("info"))
        
        # Vectors: Blue = Steering Force, Aqua = Velocity, Grey = Desired Change
        self.info_force_vector = ArrowLine(Vector2D(0,0), Vector2D(0,0), colour=COLOUR_NAMES['BLUE'], batch=window.get_batch("info"))
        self.info_vel_vector = ArrowLine(Vector2D(0,0), Vector2D(0,0), colour=COLOUR_NAMES['AQUA'], batch=window.get_batch("info"))
        self.info_net_vectors = [
            ArrowLine(Vector2D(0,0), Vector2D(0,0), colour=COLOUR_NAMES['GREY'], batch=window.get_batch("info")),
            ArrowLine(Vector2D(0,0), Vector2D(0,0), colour=COLOUR_NAMES['GREY'], batch=window.get_batch("info")),
        ]

    def calculate(self, delta):
        """Calculates the accumulated steering force based on the current mode."""
        if getattr(self, "movement_locked", False):
            return Vector2D()

        return self.movement_fsm.update(delta)    

    def update(self, delta):
        """Updates the agent's physics and graphical representation."""
        # Update high-level decision state first
        self.fsm.update(delta)

        # 1. Calculate steering force
        force = self.calculate(delta)

        force.truncate(self.max_force) # Prevent erratic 'snapping'
        
        # 2. Integrate physics: F = ma -> a = F/m
        self.accel = force / self.mass
        
        # 3. Update velocity and clamp to max speed
        self.vel += self.accel * delta
        self.vel.truncate(self.max_speed)
        
        # 4. Update position
        self.pos += self.vel * delta
        
        # 5. Update orientation if moving
        if self.vel.lengthSq() > 0.00000001:
            self.heading = self.vel.get_normalised()
            self.side = self.heading.perp()
            
        # 6. Handle world boundaries (wrap-around)
        self.world.wrap_around(self.pos)
        
        # 7. Update graphical vehicle position and rotation
        # Note: Pyglet shapes rotation is in degrees, clockwise.
        self.vehicle.x = self.pos.x
        self.vehicle.y = self.pos.y

        # 8. Update debug vector visuals
        s = 0.5 # Scale factor for vector drawing
        self.info_force_vector.position = self.pos
        self.info_force_vector.end_pos = self.pos + self.force * s
        
        self.info_vel_vector.position = self.pos
        self.info_vel_vector.end_pos = self.pos + self.vel * s

        # 9. Update weapon
        self.weapon.set_position(self.pos)
        self.weapon.update(delta)
        self.weapon.set_aim(self.get_aim_direction(self.world.target_agent))
        
        # Net change vectors (showing how force modifies velocity)
        self.info_net_vectors[0].position = self.pos + self.vel * s
        self.info_net_vectors[0].end_pos = self.pos + (self.force + self.vel) * s
        self.info_net_vectors[1].position = self.pos
        self.info_net_vectors[1].end_pos = self.pos + (self.force + self.vel) * s

        window.labels['status'].text = (
            f"Weapon: {self.weapon.weapon_type.upper()} "
            f"[{self.weapon.ammo}/{self.weapon.magazine_size}]"
        )

        self.info_state_label.text = self.fsm.get_full_state(self)
        self.info_state_label.x = self.pos.x
        self.info_state_label.y = self.pos.y + 75

        if hasattr(self, "predicted_target_pos"):
            self.info_predicted_target.x = self.predicted_target_pos.x
            self.info_predicted_target.y = self.predicted_target_pos.y

        # --- Rocket lock-on timer display ---
        if self.weapon.weapon_type == "rocket":

            timer = getattr(self, "rocket_aim_timer", 0.0)

            self.info_rocket_timer.text = f"{4.0 - timer:.1f}"

            self.info_rocket_timer.x = self.pos.x
            self.info_rocket_timer.y = self.pos.y + 55

        else:
            self.info_rocket_timer.text = ""

        muzzle = self.weapon.get_muzzle_position()

        self.info_aim_line.position = muzzle
        self.info_aim_line.end_pos = self.predicted_target_pos

    def speed(self):
        return self.vel.length()

    # ---- Steering Behaviour Implementations ----

    def seek(self, target_pos):
        """Calculates a force to move the agent towards a target."""
        desired_vel = (target_pos - self.pos).normalise() * self.max_speed
        return (desired_vel - self.vel)
    
    def stop(self, hard=True):
        """
        Immediately or gradually stops the agent.

        hard=True  -> instant stop (used for rifle firing stance)
        hard=False -> damped stop (useful for softer braking)
        """


        # Stop velocity
        if hard:
            self.vel = Vector2D()
            self.accel = Vector2D()
        else:
            self.vel *= 0.1  # gentle damping

        # Prevent FSM/movement layer from re-applying force that frame
        self.movement_locked = True

    def flee(self, hunter_pos):
        """Calculates a force to move the agent away from a hunter."""
        panic_distance = 250
        to_hunter = hunter_pos - self.pos

        if to_hunter.length() <= panic_distance:
            desired_vel = (hunter_pos + self.pos).normalise() * self.max_speed * 3
            return (desired_vel - self.vel)
        else: 
            return(Vector2D())

    def arrive(self, target_pos, speed):
        """Steers the agent to arrive at a target with zero velocity."""
        decel_rate = self.DECELERATION_SPEEDS.get(speed, 0.6)
        to_target = target_pos - self.pos
        dist = to_target.length()
        
        if dist > 0.1:
            # Required speed to decelerate over the remaining distance
            req_speed = dist / decel_rate
            req_speed = min(req_speed, self.max_speed)
            desired_vel = to_target * (req_speed / dist)
            return (desired_vel - self.vel)
        return Vector2D(0, 0)

    def pursuit(self, target):
        to_target = target.pos - self.pos
        dist = to_target.length()

        safe_distance = self.weapon.length + target.radius + 20

        # already too close → stop or circle
        if dist < safe_distance:
            return self.flee(target.pos)

        # normal pursuit prediction
        if self.speed() > 0:
            t = dist / self.speed()
        else:
            t = 0

        future_pos = target.pos + target.vel * t
        return self.seek(future_pos)

    def wander(self, delta):
        """ Random wandering using a projected jitter circle. """
        # Add a small random jitter to the target's position
        jitter = self.wander_jitter * delta
        self.wander_target += Vector2D(uniform(-1,1) * jitter, uniform(-1,1) * jitter)

        # Re-project the target back onto the unit circle and scale by radius
        self.wander_target.normalise()
        self.wander_target *= self.wander_radius

        # Project the target into world space in front of the agent
        target_local = self.wander_target + Vector2D(self.wander_dist, 0)
        world_target = self.transform_point(target_local, self.pos, self.heading, self.side)

        # Update debug visuals (if enabled)
        self.info_wander_target.x, self.info_wander_target.y = world_target.x, world_target.y
        
        return self.arrive(world_target, 'slow')


    def follow_path(self):
        current_pt = self.path.current_pt()
        to_target = current_pt - self.pos
        dist = to_target.length()

        # ---- ENTERING the waypoint ----
        if not self.reached_waypoint:
            if dist <= self.waypoint_threshold:
                self.reached_waypoint = True
                self.path.inc_current_pt()

        # ---- EXITING the waypoint ----
        else:
            # only allow re-arming once we've moved away enough
            if dist > self.waypoint_threshold * 1.5:
                self.reached_waypoint = False

        # ---- movement ----
        return self.seek(self.path.current_pt())
    
    def predict_target_position(self, target, projectile_speed):
        shooter_pos = self.pos
        target_pos = target.pos
        target_vel = target.vel

        to_target = target_pos - shooter_pos

        a = target_vel.lengthSq() - projectile_speed * projectile_speed
        b = 2 * to_target.dot(target_vel)
        c = to_target.lengthSq()

        # solve quadratic: at^2 + bt + c = 0
        discriminant = b * b - 4 * a * c

        if discriminant < 0 or abs(a) < 1e-6:
            # fallback: no solution → aim at current position
            return target_pos.copy()

        sqrt_disc = discriminant ** 0.5

        t1 = (-b - sqrt_disc) / (2 * a)
        t2 = (-b + sqrt_disc) / (2 * a)

        # choose smallest positive time
        t = min([t for t in (t1, t2) if t > 0], default=0)

        return target_pos + target_vel * t
    
    def get_aim_direction(self, target):
        if target is None:
            return Vector2D(1, 0)

        weapon = self.weapon
        muzzle = weapon.get_muzzle_position()

        predicted = self.predict_target_position(target, weapon.projectile_speed)
        self.predicted_target_pos = predicted

        return (predicted - muzzle).normalise()

    def transform_point(self, point, pos, forward, side):
        """Transforms a single local space point into world space."""
        world_pt = point.copy()
        
        mat = Matrix33()
        mat.rotate_by_vectors_update(forward, side)
        mat.translate_update(pos.x, pos.y)
        
        mat.transform_vector2d(world_pt)
        return world_pt
    
    def switch_weapon(self, direction=1):
        self.active_weapon_index = (self.active_weapon_index + direction) % len(self.weapons)

        for w in self.weapons:
            w.is_active = False
            w.line.opacity = 0
            w.line.x = self.pos.x
            w.line.y = self.pos.y

        self.weapon = self.weapons[self.active_weapon_index]
        self.weapon.is_active = True
        self.weapon.line.opacity = 255

    def can_see_target(self):
        target = self.world.target_agent

        if target is None or not target.alive:
            return False

        dist = (target.pos - self.pos).length()

        # weapon-specific engagement ranges
        if self.weapon.weapon_type == "rocket":
            return dist < 1400

        elif self.weapon.weapon_type == "rifle":
            return dist < 900

        elif self.weapon.weapon_type == "handgun":
            return dist < 700

        elif self.weapon.weapon_type == "shotgun":
            return dist < 500
        
        elif self.weapon.weapon_type == "grenade":
            return dist < 700

        # fallback
        return dist < 400
    
    def target_distance(self):
        if not self.world.target_agent or self.world.target_agent is None or not self.world.target_agent.alive:
            return float("inf")
        return (self.world.target_agent.pos - self.pos).length()


class TargetAgent:
    """A stationary target that can be interacted with."""

    def __init__(self, x, y, radius=40, max_speed=30.0, color='RED', world=None):
        self.world = world
        self.pos = Vector2D(x, y)
        self.radius = radius

        self.vel = Vector2D()
        self.max_speed = max_speed

        self.target_point = self._pick_new_point()

        self.max_health = 1000
        self.health = self.max_health
        self.alive = True

        # Visual representation (bullseye core)
        self.outer = pyglet.shapes.Circle(
            self.pos.x,
            self.pos.y,
            radius,
        color=COLOUR_NAMES[color],
        batch=window.get_batch("main")
        )
        
        self.body = pyglet.shapes.Circle(
            self.pos.x,
            self.pos.y,
            radius*0.67,
            color=COLOUR_NAMES["WHITE"],
            batch=window.get_batch("main")
        )

        self.core = pyglet.shapes.Circle(
            self.pos.x,
            self.pos.y,
            radius*0.34,
            color=COLOUR_NAMES[color],
            batch=window.get_batch("main")
        )

        self.debug_ring = pyglet.shapes.Circle(
            self.pos.x,
            self.pos.y,
            self.radius + 5,
            color=COLOUR_NAMES['GREY'],
            batch=window.get_batch("info")
        )
        self.debug_ring.opacity = 80

        self.hit_flash_timer = 0.0
        self.hit_flash_duration = 0.08

    def update(self, delta):
        if not self.alive:
            return
        
        to_target = self.target_point - self.pos
        dist = to_target.length()

        # if reached point → pick new one
        if dist < 10:
            self.target_point = self._pick_new_point()

        # steering
        steering = self.seek(self.target_point)

        self.vel += steering * delta
        self.vel.truncate(self.max_speed)

        self.pos += self.vel * delta

        # sync visuals
        self.set_position(self.pos.x, self.pos.y)

        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= delta
            self.body.color = COLOUR_NAMES["PINK"]
        else:
            self.body.color = COLOUR_NAMES["WHITE"]

    def seek(self, target):
        desired = (target - self.pos).normalise() * self.max_speed
        return desired - self.vel
    
    def on_hit(self):
        self.hit_flash_timer = self.hit_flash_duration

    def set_position(self, x, y):
        self.pos.x = x
        self.pos.y = y
        self.outer.x = x
        self.outer.y = y
        self.body.x = x
        self.body.y = y
        self.core.x = x
        self.core.y = y
        self.debug_ring.x = x
        self.debug_ring.y = y

    def _pick_new_point(self):
        cx, cy = self.world.cx, self.world.cy
        return Vector2D(
            randrange(120, cx-200),
            randrange(120, cy-120)
        )
    
    def take_damage(self, amount):
        if not self.alive:
            return

        self.health -= amount

        self.on_hit()  # still keeps your flash effect

        if self.health <= 0:
            self.die()

    def die(self):
        self.alive = False

        # hide visuals (optional but clean)
        self.outer.opacity = 0
        self.body.opacity = 0
        self.core.opacity = 0
        self.debug_ring.opacity = 0
