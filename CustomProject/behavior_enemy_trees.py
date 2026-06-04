"""
D-LEVEL CUSTOM PROJECT - Enemy Trees Behavior Module
This module defines behavior trees for enemy agents in the game. 
It uses the behavior tree implementation from behavior_tree.py to create specific behaviors for enemy tanks.
"""


from behavior_tree import *
from vector2d import Vector2D
from pathfinding import astar

def ai_path(agent):
    start = agent.pos + agent.heading * (agent.size * 0.5)
    goal = agent.world.player.pos
    return astar(agent.world.grid, start, goal)

BROWN_TREE = Selector([
    Sequence([
        Action(lambda a, d: a.update_turret_sway(d)),
        RandomChance(0.005),
        Condition(lambda a: a.is_shot_safe(a.turret_direction())),
        CanShoot(),
        Shoot()
    ]),
    Action(lambda a, d: a.update_turret_sway(d))
])

GREY_TREE = Selector([
    Sequence([
        Action(lambda a, d: setattr(
            a,
            "path_timer",
            max(0.0, a.path_timer - d)
        )),

        Condition(lambda a: a.path_timer <= 0),

        Action(lambda a, d: setattr(a, "path", ai_path(a))),
        Action(lambda a, d: setattr(a, "path_timer", 1.0)),
    ]),

    Sequence([
        Action(lambda a, d: a.follow_path(a.path, d)),

        HasLineOfSight(lambda a: a.world.player),
        AimAt(lambda a: a.world.player, noise=0.3, smooth=0.05),

        CanShoot(),
        RandomChance(0.02),
        Shoot()
    ])
])

TEAL_TREE = Selector([
    Sequence([
        HasLineOfSight(lambda a: a.world.player),
        AimAt(lambda a: a.world.player, noise=0.15, smooth=0.08),
        CanShoot(),
        RandomChance(0.03),
        Shoot()
    ])
])

YELLOW_TREE = Selector([
    Sequence([
        HasLineOfSight(lambda a: a.world.player),
        AimAt(lambda a: a.world.player, noise=0.05, smooth=0.15),
        CanShoot(),
        RandomChance(0.05),
        Shoot()
    ])
])

RED_TREE = Selector([
    Sequence([
        HasLineOfSight(lambda a: a.world.player),
        AimAt(lambda a: a.world.player, noise=0.1, smooth=0.2),
        CanShoot(),
        RandomChance(0.08),
        Shoot()
    ])
])

GREEN_TREE = Selector([
    Sequence([
        RandomChance(0.5),  # often "does something"
        HasLineOfSight(lambda a: a.world.player),
        AimAt(lambda a: a.world.player, noise=0.2, smooth=0.1),
        CanShoot(),
        RandomChance(0.03),
        Shoot()
    ])
])

PURPLE_TREE = Selector([
    Sequence([
        RandomChance(0.5),
        HasLineOfSight(lambda a: a.world.player),
        AimAt(lambda a: a.world.player, noise=0.4, smooth=0.05),
        CanShoot(),
        RandomChance(0.04),
        Shoot()
    ])
])

WHITE_TREE = Selector([
    Sequence([
        HasLineOfSight(lambda a: a.world.player),
        AimAt(lambda a: a.world.player, noise=0.25, smooth=0.03),
        CanShoot(),
        RandomChance(0.01),
        Shoot()
    ])
])

BLACK_TREE = Selector([
    Sequence([
        HasLineOfSight(lambda a: a.world.player),
        AimAt(lambda a: a.world.player, noise=0.05, smooth=0.25),
        CanShoot(),
        RandomChance(0.1),
        Shoot()
    ])
])