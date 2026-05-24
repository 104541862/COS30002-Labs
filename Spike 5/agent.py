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

import pyglet
from vector2d import Vector2D, Point2D
from graphics import COLOUR_NAMES, window, ArrowLine
from math import sin, cos, radians
from random import random, randrange, uniform
from path import Path
from matrix33 import Matrix33

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
    pyglet.window.key._9: 'hide',
}

class Agent(object):
    """A vehicle agent with steering behaviours."""

    # Deceleration rates for the Arrive behaviour
    DECELERATION_SPEEDS = {
        'slow': 0.9,
        'normal': 0.6,
        'fast': 0.3,
    }

    def __init__(self, world=None, scale=30.0, mass=1.0, color="LIGHT_BLUE", mode='seek'):
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
        
        # Forces and limits
        self.force = Vector2D()
        self.accel = Vector2D()
        self.max_speed = 20.0 * scale
        self.max_force = 100.0 * scale

        # New Wander-specific state
        self.wander_target = Vector2D(1, 0)
        self.wander_dist = 2.0 * scale
        self.wander_radius = 1.5 * scale
        self.wander_jitter = 15.0

        # Pathing
        self.path = Path()
        self.randomise_path()
        self.waypoint_threshold = 30.0

        # ---- Graphical Representation ----
        self.color = color
        # Local space vertices for a simple triangle vehicle
        self.vehicle_shape = [
            Point2D(-10,  6),
            Point2D( 10,  0),
            Point2D(-10, -6)
        ]
        # List of hiding spot candidates
        self.debug_hide_candidates = []
        
        # Main vehicle primitive
        self.vehicle = pyglet.shapes.Triangle(
            self.pos.x + self.vehicle_shape[1].x, self.pos.y + self.vehicle_shape[1].y,
            self.pos.x + self.vehicle_shape[0].x, self.pos.y + self.vehicle_shape[0].y,
            self.pos.x + self.vehicle_shape[2].x, self.pos.y + self.vehicle_shape[2].y,
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

        self.debug_hide_line = pyglet.shapes.Line(
            0, 0, 0, 0,
            color=COLOUR_NAMES['GREEN'],
            batch=window.get_batch("info")
        )

        self.debug_extend_line = pyglet.shapes.Line(
            0, 0, 0, 0,
            color=COLOUR_NAMES['YELLOW'],
            batch=window.get_batch("info")
        )

        self.debug_hide_marker = pyglet.shapes.Star(
            0, 0,
            8, 5, 2,
            color=COLOUR_NAMES['RED'],
            batch=window.get_batch("info")
        )

    def calculate(self, delta):
        """Calculates the accumulated steering force based on the current mode."""
        mode = self.mode
        self._delta = delta
        target_pos = Vector2D(self.world.target.x, self.world.target.y)
        
        if mode == 'seek':
            force = self.seek(target_pos)
        elif mode == 'arrive_slow':
            force = self.arrive(target_pos, 'slow')
        elif mode == 'arrive_normal':
            force = self.arrive(target_pos, 'normal')
        elif mode == 'arrive_fast':
            force = self.arrive(target_pos, 'fast')
        elif mode == 'flee':
            force = self.flee(target_pos)
        elif mode == 'hide':
            force = self.hide(self.world.hunter, self.world.rocks)
        elif mode == 'pursuit':
            prey = self.world.prey

            if prey and self.has_line_of_sight(prey):
                force = self.pursuit(prey)
            else:
                # LOST SIGHT → wander to search
                force = self.wander(self._delta)
        elif mode == 'wander':
            force = self.wander(self._delta)
        elif mode == 'follow_path':
            force = self.follow_path()
        else:
            force = Vector2D()
        
        force += self.avoid_rocks()

        self.force = force
        return force

    def update(self, delta):
        """Updates the agent's physics and graphical representation."""
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

        # 7. Handle collisions between rocks
        self.resolve_rock_collisions()
        
        # 8. Update graphical vehicle position and rotation
        # Note: Pyglet shapes rotation is in degrees, clockwise.
        self.vehicle.x = self.pos.x
        self.vehicle.y = self.pos.y
        self.vehicle.rotation = -self.heading.angle_degrees()

        # 9. Update debug vector visuals
        s = 0.5 # Scale factor for vector drawing
        self.info_force_vector.position = self.pos
        self.info_force_vector.end_pos = self.pos + self.force * s
        
        self.info_vel_vector.position = self.pos
        self.info_vel_vector.end_pos = self.pos + self.vel * s
        
        # Net change vectors (showing how force modifies velocity)
        self.info_net_vectors[0].position = self.pos + self.vel * s
        self.info_net_vectors[0].end_pos = self.pos + (self.force + self.vel) * s
        self.info_net_vectors[1].position = self.pos
        self.info_net_vectors[1].end_pos = self.pos + (self.force + self.vel) * s

        self.update_hide_debug()

    def speed(self):
        return self.vel.length()

    # ---- Steering Behaviour Implementations ----

    def seek(self, target_pos):
        """Calculates a force to move the agent towards a target."""
        desired_vel = (target_pos - self.pos).normalise() * self.max_speed
        return (desired_vel - self.vel)

    def flee(self, hunter_pos):
        """Calculates a force to move the agent away from a hunter."""
        panic_distance = 250
        to_hunter = hunter_pos - self.pos

        if to_hunter.length() <= panic_distance:
            desired_vel = (hunter_pos + self.pos).normalise() * self.max_speed
            return (desired_vel - self.vel)
        else: 
            return(Vector2D())
        
    def hide(self, hunter, rocks):

        if not hunter or not rocks:
            return self.flee(hunter.pos if hunter else self.pos)

        buffer = 50.0

        best_hide = None
        best_score = float('inf')

        # ---------------- DEBUG STORAGE ----------------
        self._debug_candidates = []
        self._debug_selected_rock = None
        # ----------------------------------------------

        for rock in rocks:

            to_rock = rock.pos - hunter.pos
            if to_rock.length() == 0:
                continue

            direction = to_rock.normalise()
            hide_pos = rock.pos + direction * (rock.hit_radius + buffer)

            # store candidate BEFORE filtering
            self._debug_candidates.append((rock.pos, hide_pos))

            # validation: reject if inside ANY rock (except itself)
            if self.is_point_blocked(hide_pos, rocks, ignore=rock):
                continue

            score = (self.pos - hide_pos).length()

            if score < best_score:
                best_score = score
                best_hide = hide_pos
                self._debug_selected_rock = rock

        if best_hide is not None:
            return self.arrive(best_hide, 'fast')

        # fallback if everything failed
        return self.flee(hunter.pos)

        

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

    def pursuit(self, evader):
        """Predicts evader future position and accounts for line-of-sight blockers."""

        if not evader:
            return Vector2D()

        to_evader = evader.pos - self.pos
        dist = to_evader.length()

        speed = self.speed()

        if speed > 0.0001:
            t = dist / speed
        else:
            t = 0.0

        future_pos = evader.pos + evader.vel * t

        closest_blocker = None
        closest_t = float('inf')

        for rock in self.world.rocks:
            to_rock = rock.pos - self.pos

            # Project rock onto path direction
            path_dir = (future_pos - self.pos)
            path_len = path_dir.length()

            if path_len == 0:
                continue

            path_dir = path_dir.normalise()

            projection = to_rock.x * path_dir.x + to_rock.y * path_dir.y

            # Only consider rocks in front of hunter
            if projection < 0 or projection > path_len:
                continue

            # closest point on path to rock
            closest_point = self.pos + path_dir * projection
            dist_to_path = (rock.pos - closest_point).length()

            # check if rock blocks path
            if dist_to_path <= rock.hit_radius:
                if projection < closest_t:
                    closest_t = projection
                    closest_blocker = rock

        if closest_blocker:
            to_rock = closest_blocker.pos - self.pos

            if to_rock.length() == 0:
                return self.seek(future_pos)

            # steer toward center of rock (keeps pressure on prey)
            intercept_point = closest_blocker.pos

            return self.seek(intercept_point)

        return self.seek(future_pos)

    def wander(self, delta):
        """Smooth wandering used for search behaviour."""

        jitter = self.wander_jitter * delta

        # random displacement
        self.wander_target += Vector2D(
            uniform(-1, 1) * jitter,
            uniform(-1, 1) * jitter
        )

        self.wander_target.normalise()
        self.wander_target *= self.wander_radius

        # project forward
        target_local = self.wander_target + Vector2D(self.wander_dist, 0)

        world_target = self.transform_point(
            target_local,
            self.pos,
            self.heading,
            self.side
        )

        return self.arrive(world_target, 'slow')

    def follow_path(self):
        """Moves the agent along a predefined set of waypoints."""
        current_pt = self.path.current_pt()

        # Advance if close enough
        if (current_pt - self.pos).length() <= self.waypoint_threshold:
            self.path.inc_current_pt()
            current_pt = self.path.current_pt()

        # Final waypoint uses arrive
        if self.path.is_finished():
            return self.arrive(current_pt, 'slow')

        # Intermediate waypoints use seek
        return self.arrive(current_pt, 'normal')
    
    def avoid_rocks(self):
        """Steering force to avoid rocks before collision."""

        ahead = self.pos + self.heading * 40
        avoidance = Vector2D()

        most_threatening = None
        min_dist = float('inf')

        for rock in self.world.rocks:
            dist = (rock.pos - ahead).length()

            if dist < rock.hit_radius + 10:
                if dist < min_dist:
                    min_dist = dist
                    most_threatening = rock

        if most_threatening:
            away = ahead - most_threatening.pos

            if away.length() > 0:
                avoidance = away.normalise() * self.max_force

        return avoidance
    
    def has_line_of_sight(self, target):
        """Returns True if no rock blocks view to target."""

        start = self.pos
        end = target.pos

        to_target = end - start
        dist = to_target.length()

        if dist == 0:
            return True

        direction = to_target.normalise()

        for rock in self.world.rocks:

            to_rock = rock.pos - start

            projection = to_rock.x * direction.x + to_rock.y * direction.y

            # rock not in front or beyond target
            if projection < 0 or projection > dist:
                continue

            closest_point = start + direction * projection
            dist_to_line = (rock.pos - closest_point).length()

            if dist_to_line <= rock.hit_radius:
                return False  # blocked

        return True
    
    def is_point_blocked(self, point, rocks, ignore=None):
        """Checks if a point lies inside any obstacle."""

        for rock in rocks:
            if rock is ignore:
                continue

            if (point - rock.pos).length() <= rock.hit_radius:
                return True

        return False
    
    def resolve_rock_collisions(self):
        """Pushes agent out of overlapping rocks (hard constraint)."""

        for rock in self.world.rocks:
            to_agent = self.pos - rock.pos
            dist = to_agent.length()

            min_dist = rock.hit_radius + self.scale.x * 0.5

            if dist < min_dist and dist > 0.0001:
                # push agent out of rock
                overlap = min_dist - dist
                correction = to_agent.normalise() * overlap

                self.pos += correction

    def randomise_path(self):
        cx, cy = self.world.cx, self.world.cy 
        margin = min(cx, cy) * (1/6)
        self.path.create_random_path(100, margin, margin, cx-margin, cy-margin, looped=True)

    def transform_point(self, point, pos, forward, side):
        """Transforms a single local space point into world space."""
        world_pt = point.copy()
        
        mat = Matrix33()
        mat.rotate_by_vectors_update(forward, side)
        mat.translate_update(pos.x, pos.y)
        
        mat.transform_vector2d(world_pt)
        return world_pt
    
    def update_hide_debug(self):

        # clear previous candidate visuals
        for marker, line1, line2 in self.debug_hide_candidates:
            marker.visible = False
            line1.visible = False
            line2.visible = False

        if self.mode != 'hide' or not hasattr(self, "_debug_candidates"):
            return

        hunter = self.world.hunter

        # create visuals if needed
        while len(self.debug_hide_candidates) < len(self._debug_candidates):

            marker = pyglet.shapes.Star(
                0, 0,
                6, 4, 2,
                color=COLOUR_NAMES['LIGHT_GREEN'],
                batch=window.get_batch("info")
            )

            line1 = pyglet.shapes.Line(
                0, 0, 0, 0,
                color=COLOUR_NAMES['GREEN'],
                batch=window.get_batch("info")
            )

            line2 = pyglet.shapes.Line(
                0, 0, 0, 0,
                color=COLOUR_NAMES['YELLOW'],
                batch=window.get_batch("info")
            )

            self.debug_hide_candidates.append((marker, line1, line2))

        # render every candidate
        for i, (rock_pos, hide_pos) in enumerate(self._debug_candidates):

            marker, line1, line2 = self.debug_hide_candidates[i]

            marker.visible = True
            line1.visible = True
            line2.visible = True

            # hunter -> obstacle
            line1.x = hunter.pos.x
            line1.y = hunter.pos.y
            line1.x2 = rock_pos.x
            line1.y2 = rock_pos.y

            # obstacle -> hiding spot
            line2.x = rock_pos.x
            line2.y = rock_pos.y
            line2.x2 = hide_pos.x
            line2.y2 = hide_pos.y

            # hiding spot marker
            marker.x = hide_pos.x
            marker.y = hide_pos.y

        # highlight chosen hiding spot
        if hasattr(self, "_debug_selected_rock") and self._debug_selected_rock:

            rock = self._debug_selected_rock

            to_rock = rock.pos - hunter.pos

            if to_rock.length() > 0:

                direction = to_rock.normalise()

                best_hide = rock.pos + direction * (rock.hit_radius + 50.0)

                # selected line
                self.debug_hide_line.x = hunter.pos.x
                self.debug_hide_line.y = hunter.pos.y
                self.debug_hide_line.x2 = rock.pos.x
                self.debug_hide_line.y2 = rock.pos.y

                # selected extension
                self.debug_extend_line.x = rock.pos.x
                self.debug_extend_line.y = rock.pos.y
                self.debug_extend_line.x2 = best_hide.x
                self.debug_extend_line.y2 = best_hide.y

                # selected marker
                self.debug_hide_marker.x = best_hide.x
                self.debug_hide_marker.y = best_hide.y