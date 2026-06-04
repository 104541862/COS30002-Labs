"""
D-LEVEL CUSTOM PROJECT - Behavior Tree Module
This module defines a simple behavior tree implementation with Node, Selector, and Sequence classes.
The Node class is an abstract base class for all behavior tree nodes, while Selector and Sequence are composite nodes that control the flow of execution based on their children.
"""

import math 
import random
from vector2d import Vector2D

class Node:
    def run(self, agent, delta):
        raise NotImplementedError

class Selector(Node):
    def __init__(self, children):
        self.children = children

    def run(self, agent, delta):
        for c in self.children:
            if c.run(agent, delta):
                return True
        return False

class Action:
    def __init__(self, func):
        self.func = func

    def run(self, agent, delta):
        self.func(agent, delta)
        return True
    
class Condition:
    def __init__(self, func):
        self.func = func

    def run(self, agent, delta):
        return bool(self.func(agent))

class Sequence(Node):
    def __init__(self, children):
        self.children = children

    def run(self, agent, delta):
        for c in self.children:
            if not c.run(agent, delta):
                return False
        return True
    
class RandomChance(Node):
    def __init__(self, chance):
        self.chance = chance

    def run(self, agent, delta):
        return random.random() < self.chance


class CanShoot(Node):
    def run(self, agent, delta):
        return agent.can_shoot()


class HasLineOfSight(Node):
    def __init__(self, target_func):
        self.target_func = target_func

    def run(self, agent, delta):
        target = self.target_func(agent)
        if not target:
            return False

        return agent.world.has_clear_line(agent.pos, target.pos)

class AimAt(Node):
    def __init__(self, target_func, noise=0.0, smooth=0.1):
        self.target_func = target_func
        self.noise = noise
        self.smooth = smooth

    def run(self, agent, delta):
        target = self.target_func(agent)
        if not target:
            return False

        to_target = target.pos - agent.pos

        angle = math.degrees(math.atan2(to_target.y, to_target.x))
        angle += random.uniform(-self.noise, self.noise)

        # IMPORTANT: match turret_direction convention
        desired = -angle

        agent.turret.rotation += (desired - agent.turret.rotation) * self.smooth
        return True

class Shoot(Node):
    def run(self, agent, delta):
        direction = agent.turret_direction()
        agent.shoot_override_direction(direction)
        return True

class KeepDistance:
    def __init__(self, target_fn, min_dist, max_dist, speed_scale=1.0):
        self.target_fn = target_fn
        self.min_dist = min_dist
        self.max_dist = max_dist
        self.speed_scale = speed_scale

    def run(self, agent, delta):
        target = self.target_fn(agent)

        to_target = target.pos - agent.pos
        dist = to_target.length()

        if dist < 1:
            return True

        direction = to_target.get_normalised()

        accel = Vector2D()

        # too close → move away
        if dist < self.min_dist:
            accel = -direction * agent.acceleration * self.speed_scale

        # too far → slightly approach (optional soft cap)
        elif dist > self.max_dist:
            accel = direction * agent.acceleration * self.speed_scale

        agent.apply_movement(accel, delta)
        return True