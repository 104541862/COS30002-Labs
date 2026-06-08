"""
D-LEVEL CUSTOM PROJECT - Agent Module
This module defines the Agent class.
"""

from turtle import shape
import pyglet
from vector2d import Vector2D, Point2D
from graphics import COLOUR_NAMES, PolyLine, window, ArrowLine
from pyglet.shapes import Line, Rectangle
import math
from math import dist, sin, cos, radians
import random
from path import Path
from matrix33 import Matrix33
from projectile import Projectile
from mine import Mine
from behavior_tree import *
from behavior_enemy_trees import (BROWN_COMBAT_TREE, 
                                  GREY_COMBAT_TREE, 
                                  GREY_MOVEMENT_TREE, 
                                  TEAL_COMBAT_TREE, 
                                  TEAL_MOVEMENT_TREE, 
                                  YELLOW_COMBAT_TREE, 
                                  YELLOW_MOVEMENT_TREE, 
                                  RED_COMBAT_TREE, 
                                  RED_MOVEMENT_TREE,
                                  GREEN_COMBAT_TREE,
                                  PURPLE_COMBAT_TREE,
                                  PURPLE_MOVEMENT_TREE,
                                  WHITE_COMBAT_TREE,
                                  WHITE_MOVEMENT_TREE,
                                  BLACK_COMBAT_TREE,
                                  BLACK_MOVEMENT_TREE)
from geometry_utils import (segment_hits_aabb,
                            ray_hits_aabb,
                            _ray_aabb_t,
                            distance,
                            distance_sq,
)
from enemy_profiles import ENEMY_PROFILES

class Agent:
    """Base class for all tanks (no movement logic here)."""

    def __init__(self, world, spawn_pos, size = 30, color="LIGHT_BLUE"):
        self.world = world

        self.velocity = Vector2D()

        self.acceleration = 800.0      # fast build-up
        self.max_speed = 120.0         # cap speed
        self.deceleration = 1200.0     # fast stopping

        self.pos = Vector2D(spawn_pos[0], spawn_pos[1])
        self.color = color
        self.size = size

        self.heading = Vector2D(1, 0)

        self.projectiles = []
        self.max_projectiles = 5

        # Graphics only
        self.vehicle = pyglet.shapes.Rectangle(
            self.pos.x,
            self.pos.y,
            self.size,
            self.size,
            color=COLOUR_NAMES[self.color],
            batch=window.get_batch("main")
        )
        
        dark_color = self.darken(self.color, 0.8)
        self.front_marker = pyglet.shapes.Triangle(
            0, 0,
            0, 0,
            0, 0,
            color=dark_color,
            batch=window.get_batch("main")
        )

        self.vehicle.anchor_x = self.size / 2
        self.vehicle.anchor_y = self.size / 2

        self.turret_length = self.size * 0.8
        self.turret_width = 6
        self.turret_angle = 0.0

        self.turret = pyglet.shapes.Rectangle(
            self.pos.x,
            self.pos.y,
            self.size * 0.6,
            self.size * 0.2,
            color=(0, 0, 0),
            batch=window.get_batch("main")
        )

        self.turret.anchor_x = 0
        self.turret.anchor_y = self.turret.height / 2

        self.active_mine = None

    def apply_movement(self, accel, delta):
        # acceleration
        self.velocity += accel * delta

        # speed cap
        speed = self.velocity.length()

        if speed > self.max_speed:
            self.velocity = (
                self.velocity.get_normalised()
                * self.max_speed
            )

        # friction
        if accel.length() < 0.01:
            speed = self.velocity.length()

            if speed > 0:
                drop = self.deceleration * delta

                if drop > speed:
                    self.velocity.zero()
                else:
                    self.velocity = (
                        self.velocity.get_normalised()
                        * (speed - drop)
                    )

        # move
        new_pos = self.pos + self.velocity * delta

        if not self.world.check_wall_collision(self, new_pos) and not self.world.check_hole_collision(self,new_pos):
            self.pos = new_pos
        else:
            self.velocity.zero()

    def sync_graphics(self):
        self.vehicle.x = self.pos.x
        self.vehicle.y = self.pos.y

        # body rotation only
        self.vehicle.rotation = -self.heading.angle_degrees()

        # turret always sits on top of tank
        self.turret.x = self.pos.x
        self.turret.y = self.pos.y

        half = self.size / 2

        forward = self.heading.get_normalised()
        side = forward.perp().get_normalised()

        # tip of triangle (front)
        tip = self.pos + forward * half

        # rear base of triangle (slightly behind center)
        base_center = self.pos - forward * (half * 0.4)

        base_left = base_center + side * (self.size * 0.25)
        base_right = base_center - side * (self.size * 0.25)

        self.front_marker.x = tip.x
        self.front_marker.y = tip.y

        # pyglet Triangle uses (x1,y1, x2,y2, x3,y3)
        self.front_marker.x2 = base_left.x
        self.front_marker.y2 = base_left.y

        self.front_marker.x3 = base_right.x
        self.front_marker.y3 = base_right.y

    def darken(self, color, factor):
        r, g, b, a = COLOUR_NAMES[color]
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return (r, g, b, a)
    
    def get_aabb(self):
        half = self.size / 2
        return (
            self.pos.x - half,
            self.pos.y - half,
            self.size,
            self.size
        )
    
    def shoot(self):
        if len(self.projectiles) >= self.max_projectiles:
            return

        # spawn slightly in front of tank
        forward = self.turret_direction()

        spawn_pos = self.pos + forward * (self.size * 0.9)

        speed = getattr(self, "bullet_speed", 200.0)
        vel = forward * speed

        projectile = Projectile(
            pos=spawn_pos,
            vel=vel,
            owner=self
        )

        self.projectiles.append(projectile)
        self.world.projectiles.append(projectile)

    def shoot_override_direction(self, direction):
        if len(self.projectiles) >= self.max_projectiles:
            return

        spawn_pos = self.pos + direction * (self.size * 0.9)
        vel = direction * getattr(self, "bullet_speed", 200.0)

        projectile = Projectile(spawn_pos, vel, owner=self)

        self.projectiles.append(projectile)
        self.world.projectiles.append(projectile)

    def place_mine(self):
        if not self.active_mine:
            mine = Mine(
                pos=self.pos,
                owner=self,
                fuse=10.0,
                radius=70
            )

            self.active_mine = mine
            self.world.mines.append(mine)
        else:
            return

    def turret_direction(self):
        angle_rad = math.radians(-self.turret.rotation)
        return Vector2D(math.cos(angle_rad), math.sin(angle_rad))
    
    def destroy(self):
        self.vehicle.delete()
        self.turret.delete()

        if hasattr(self, "front_marker"):
            self.front_marker.delete()
    
    def get_muzzle_position(self):
        forward = self.turret_direction().get_normalised()
        return self.pos + forward * (self.size * 0.9)

class PlayerAgent(Agent):
    """Player-controlled tank (no physics, only input state)."""

    def __init__(self, world, spawn_pos, size = 30, color="LIGHT_BLUE"):
        super().__init__(world, spawn_pos, size, color)

        self.input_state = {
            "forward": False,
            "left": False,
            "right": False,
            "backward": False,
            "mine": False,
            "shoot": False,
        }

        self.turn_speed = 2.0

    def update(self, delta):

        # direction tank faces (we assume facing right initially)
        direction = self.heading.get_normalised()

        # --- TURNING ---
        if self.input_state["left"]:
            self.heading = self.heading.rotate(self.turn_speed * delta)

        if self.input_state["right"]:
            self.heading = self.heading.rotate(-self.turn_speed * delta)

        accel = Vector2D()

        if self.input_state["forward"]:
            accel += self.heading * self.acceleration

        if self.input_state["backward"]:
            accel -= self.heading * self.acceleration

        self.apply_movement(accel, delta)
        
        # --- TURRET AIMING (PLAYER ONLY) ---
        mx = self.world.mouse_pos.x
        my = self.world.mouse_pos.y

        dx = mx - self.pos.x
        dy = my - self.pos.y

        self.turret.rotation = -math.degrees(math.atan2(dy, dx))

        # --- SYNC GRAPHICS ---
        self.sync_graphics()

    def set_input(self, key, value):
        if key == "W":
            self.input_state["forward"] = value
        elif key == "S":
            self.input_state["backward"] = value
        elif key == "A":
            self.input_state["left"] = value
        elif key == "D":
            self.input_state["right"] = value
        elif key == "E":
            self.input_state["mine"] = value
            if value:
                self.place_mine()
        elif key == " ":
            self.input_state["shoot"] = value
            if value:  # only shoot on key press, not release
                self.shoot()

class EnemyAgent(Agent):
    """Enemy tank controlled by behavior tree."""
    def __init__(self, world, spawn_pos, size=30, color="RED", movement_tree=None, combat_tree=None):
        super().__init__(world, spawn_pos, size, color)
        self.movement_tree = movement_tree
        self.combat_tree = combat_tree
        self.path = []
        self.path_timer = 0.0
        self.sway_angle = self.turret.rotation
        self.sway_target = self.turret.rotation
        self.sway_timer = 0.0
        self.sway_interval = (1.5, 3.5)  # seconds between direction changes
        self.turret.rotation += random.uniform(-180, 180)
        self.sway_target = self.turret.rotation
        self.sway_timer = random.uniform(0.0, 2.0)
        # PROFILE LOOKUP (based on colour string)
        profile = ENEMY_PROFILES.get(color.replace("ENEMY_", ""), {})
        self.max_speed = profile.get("max_speed", 80.0)
        self.max_projectiles = profile.get("max_projectiles", 2)
        self.fire_rate = profile.get("fire_rate", 2.0)
        self.bullet_speed = profile.get("bullet_speed", 200.0)
        # runtime state
        self.fire_cooldown = 0.0
        # Debugging
        self.debug_lines = []

    def update(self, delta):
        if self.fire_cooldown > 0:
            self.fire_cooldown -= delta

        if self.movement_tree:
            self.movement_tree.run(self, delta)

        if self.combat_tree:
            self.combat_tree.run(self, delta)

        self.update_debug_ray()
        self.render_path_debug()
        self.sync_graphics()
    
    def get_buffer_aabb(self, scale=2.5):
        """
        Larger "no-fire zone" around agent.
        Scale should be > 1 so it extends beyond body.
        """
        half = self.size * scale / 2
        return (
            self.pos.x - half,
            self.pos.y - half,
            half * 2,
            half * 2
        )
    
    def can_shoot(self):
        return (
            self.fire_cooldown <= 0 and
            len(self.projectiles) < self.max_projectiles
        )

    def shoot(self):
        if not self.can_shoot():
            return
        super().shoot()
        self.fire_cooldown = self.fire_rate

    def update_turret_sway(self, delta, speed=0.8):
        import random
        import math
        # countdown until we pick a new direction
        self.sway_timer -= delta

        if self.sway_timer <= 0:
            self.sway_timer = random.uniform(*self.sway_interval)

            # choose a new target angle (smooth wandering)
            self.sway_target = self.turret.rotation + random.uniform(-90, 90)

        # smooth interpolation toward target (no jitter)
        diff = (self.sway_target - self.turret.rotation)

        # wrap to [-180, 180] for shortest path rotation
        diff = (diff + 180) % 360 - 180

        self.turret.rotation += diff * (1 - math.exp(-speed * delta))

    def simulate_bullet_path(self, origin, direction, max_bounces=1, max_distance=2000.0):
        """
        Proper ray-bounce simulation using ray-AABB intersection (no stepping).
        Returns list of (start, end) segments.
        """

        from geometry_utils import _ray_aabb_t  # or wherever you placed it

        dir = direction.get_normalised()

        pos = origin.copy()
        remaining = max_bounces
        travelled = 0.0

        segments = []

        while travelled < max_distance:

            closest_t = float("inf")
            closest_hit = None
            hit_side = None

            # find closest wall hit
            for wall in self.world.wall_rects:
                bx, by = wall.x, wall.y
                bw, bh = wall.width, wall.height

                hit, t = _ray_aabb_t(pos, dir, bx, by, bw, bh)

                if hit and 0 < t < closest_t:
                    closest_t = t
                    closest_hit = pos + dir * t

                    # determine bounce axis
                    eps = 1e-5
                    if abs(closest_hit.x - bx) < eps:
                        hit_side = "LEFT"
                    elif abs(closest_hit.x - (bx + bw)) < eps:
                        hit_side = "RIGHT"
                    elif abs(closest_hit.y - by) < eps:
                        hit_side = "BOTTOM"
                    else:
                        hit_side = "TOP"

            # no hit → extend to max distance
            if closest_hit is None:
                end = pos + dir * (max_distance - travelled)
                segments.append((pos.copy(), end.copy()))
                break

            segments.append((pos.copy(), closest_hit.copy()))

            travelled += closest_t
            if travelled >= max_distance:
                break

            if remaining <= 0:
                break

            remaining -= 1

            # bounce
            if hit_side in ("LEFT", "RIGHT"):
                dir.x *= -1
            else:
                dir.y *= -1

            pos = closest_hit

        return segments

    def find_bounce_shot(self, samples=60, max_bounces=1):
        from math import cos, sin, radians
        import random

        origin = self.get_muzzle_position()
        player = self.world.player

        best_dir = None
        best_score = 0.0

        for i in range(samples):
            angle = random.uniform(0, 360)
            direction = Vector2D(cos(radians(angle)), sin(radians(angle)))

            path = self.simulate_bullet_path(origin, direction, max_bounces=max_bounces)

            hit_player = False
            score = 0.0

            for start, end in path:
                seg = end - start
                seg_len = seg.length()
                if seg_len < 1:
                    continue

                seg_dir = seg.get_normalised()

                ax, ay, aw, ah = player.get_aabb()
                hit, t = _ray_aabb_t(start, seg_dir, ax, ay, aw, ah)

                if hit and 0 <= t <= seg_len:
                    hit_player = True
                    score = 1.0 / max(1.0, (start - player.pos).length())
                    break

            if hit_player and score > best_score:
                best_score = score
                best_dir = direction

        return best_dir

    def is_shot_safe(self, direction):

        direction = direction.get_normalised()
        origin = self.get_muzzle_position()

        path = self.simulate_bullet_path(origin, direction, max_bounces=1)

        for start, end in path:

            seg_dir = end - start
            seg_len = seg_dir.length()

            if seg_len < 1:
                continue
            seg_dir = seg_dir.get_normalised()
            for agent in self.world.agents:
                if agent is self.world.player:
                    continue
                # ALWAYS include self check via buffer
                ax, ay, aw, ah = agent.get_buffer_aabb()
                hit, t = _ray_aabb_t(start, seg_dir, ax, ay, aw, ah)
                # Any intersection is unsafe
                if hit and 0 <= t <= seg_len:
                    return False
        return True
    
    # aiming heuristic
    def shot_risk(self):
        fire_dir = self.turret_direction().get_normalised()
        danger = 0.0
        for agent in self.world.agents:
            if agent is self:
                continue
            to_agent = agent.pos - self.pos
            dist = to_agent.length()
            if dist < 1:
                continue
            to_agent = to_agent.get_normalised()
            alignment = fire_dir.dot(to_agent)
            if alignment > 0.97:
                danger += 1.0 / max(dist, 1.0)
        return danger
    def separation_force(self, desired_dist=80.0):
        force = Vector2D()
        for other in self.world.agents:
            if other is self:
                continue
            if other is self.world.player:
                continue
            offset = self.pos - other.pos
            dist = offset.length()
            if dist < 0.001:
                continue
            if dist < desired_dist:
                strength = 1.0 - (dist / desired_dist)
                force += (
                    offset.get_normalised()
                    * strength
                )
        return force
    
    def wall_avoidance_force(self, desired_dist=50.0):
        force = Vector2D()
        for wall in self.world.wall_rects:
            # closest point on wall AABB
            closest_x = max(wall.x, min(self.pos.x, wall.x + wall.width))
            closest_y = max(wall.y, min(self.pos.y, wall.y + wall.height))
            offset = self.pos - Vector2D(closest_x, closest_y)
            radius = self.size * 0.5
            dist = offset.length() - radius
            if dist < 1:
                continue
            if dist < desired_dist:
                strength = (desired_dist - dist) / desired_dist
                force += offset.get_normalised() * strength
        return force

    def hole_avoidance_force(self, desired_dist=60.0):
        force = Vector2D()
        for hole in self.world.hole_circles:
            hole_pos = Vector2D(
                hole.x,
                hole.y
            )
            offset = self.pos - hole_pos
            # account for tank radius and hole radius
            dist = (
                offset.length()
                - hole.radius
                - self.size * 0.5
            )
            if dist < 1:
                continue
            if dist < desired_dist:
                strength = (
                    desired_dist - dist
                ) / desired_dist
                force += (
                    offset.get_normalised()
                    * strength
                )
        return force
    
    def mine_avoidance_force(self, desired_dist=160.0):
        force = Vector2D()

        for mine in self.world.mines:
            # ignore unarmed or already exploded mines
            if not mine.armed or getattr(mine, "exploded", False):
                continue

            offset = self.pos - mine.pos
            dist = offset.length()

            if dist < 0.001:
                continue

            if dist < desired_dist:
                strength = (desired_dist - dist) / desired_dist
                force += offset.get_normalised() * strength

        return force

    def follow_path(self, path, delta, speed=1.0):
        if not path or len(path) == 0:
            return False
        lookahead_index = min(2, len(path) - 1)
        target = path[lookahead_index]
        to_target = target - self.pos
        if to_target.length() < 5:
            return True
        path_dir = to_target.get_normalised()
        # Separation steering
        sep_force = self.separation_force()
        wall_force = self.wall_avoidance_force(desired_dist=40)
        hole_force = self.hole_avoidance_force(desired_dist=40)
        mine_force = self.mine_avoidance_force(desired_dist=160)
        desired_heading = (
            path_dir +
            wall_force * 1.5 +
            hole_force * 1.5 +
            mine_force * 1.5 +
            sep_force * 2.0
        ).get_normalised()
        if desired_heading.length() > 0:
            desired_heading = desired_heading.get_normalised()
        else:
            desired_heading = self.heading
        # Existing heading steering
        self.heading = (
            self.heading +
            (desired_heading - self.heading) * 0.15
        ).get_normalised()
        accel = self.heading * self.acceleration
        self.apply_movement(accel, delta)
        return True
    
    def update_debug_buffers(self):
        # clear old buffer visuals
        if not hasattr(self, "debug_buffers"):
            self.debug_buffers = []
        for rect in self.debug_buffers:
            rect.delete()
        self.debug_buffers.clear()
        for agent in self.world.agents:
            if agent is self.world.player:
                continue
            ax, ay, aw, ah = agent.get_buffer_aabb()
            rect = Rectangle(
                ax,
                ay,
                aw,
                ah,
                color=(200, 80, 80),  # red = AI danger zone
                batch=window.get_batch("info")
            )
            rect.opacity = 40  # make it translucent
            rect.anchor_x = 0
            rect.anchor_y = 0
            self.debug_buffers.append(rect)

    def update_debug_ray(self):
        for line in self.debug_lines:
            line.delete()
        self.debug_lines.clear()
        direction = self.turret_direction().get_normalised()
        origin = self.get_muzzle_position()
        path = self.simulate_bullet_path(origin, direction, max_bounces=1)
        unsafe = not self.is_shot_safe(direction)
        colour = (255, 60, 60, 255) if unsafe else (80, 220, 120, 255)
        for start, end in path:
            line = Line(
                start.x, start.y,
                end.x, end.y,
                color=colour,
                batch=window.get_batch("info")
            )
            line.width = 2
            self.debug_lines.append(line)
            
    def render_path_debug(self):
        if not hasattr(self, "debug_path_lines"):
            self.debug_path_lines = []
        # clear old
        for line in self.debug_path_lines:
            line.delete()
        self.debug_path_lines.clear()
        path = getattr(self, "path", None)
        if not path or len(path) < 2:
            return
        for i in range(len(path) - 1):
            a = path[i]
            b = path[i + 1]
            line = Line(
                a.x, a.y,
                b.x, b.y,
                color=(80, 160, 255, 255),  # blue = navigation path
                batch=window.get_batch("info")
            )
            line.width = 2
            self.debug_path_lines.append(line)