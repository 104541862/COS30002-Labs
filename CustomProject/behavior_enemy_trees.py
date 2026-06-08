"""
D-LEVEL CUSTOM PROJECT - Enemy Trees Behavior Module
This module defines behavior trees for enemy agents in the game. 
It uses the behavior tree implementation from behavior_tree.py to create specific behaviors for enemy tanks.
"""


from behavior_tree import *
from vector2d import Vector2D
from pathfinding import astar

def player_too_close(agent):
    return (
        agent.world.player.pos -
        agent.pos
    ).length() < 500

def grey_path(agent):

    goal = grey_goal(agent)

    if goal is None:
        return []

    start = agent.pos + agent.heading * (agent.size * 0.5)

    return astar(
        agent.world.grid,
        start,
        goal
    )

def grey_goal(agent):

    player = agent.world.player
    grid = agent.world.grid

    best_node = None
    best_score = float("inf")

    for node in grid.nodes.values():

        if not node.walkable:
            continue

        world_pos = grid.world_from_node((node.x, node.y))

        dist = (world_pos - player.pos).length()

        ideal_dist = 400.0

        score = abs(dist - ideal_dist)

        # cover preference
        for wall in agent.world.wall_rects:

            closest_x = max(
                wall.x,
                min(world_pos.x, wall.x + wall.width)
            )

            closest_y = max(
                wall.y,
                min(world_pos.y, wall.y + wall.height)
            )

            cover_dist = (
                world_pos -
                Vector2D(closest_x, closest_y)
            ).length()

            if cover_dist < 120:
                score -= 20

        if score < best_score:
            best_score = score
            best_node = world_pos

    return best_node

BROWN_COMBAT_TREE = Selector([
    Sequence([
        Action(lambda a, d: a.update_turret_sway(d)),
        RandomChance(0.005),
        Condition(lambda a: a.is_shot_safe(a.turret_direction())),
        CanShoot(),
        Shoot()
    ]),
    Action(lambda a, d: a.update_turret_sway(d))
])

GREY_MOVEMENT_TREE = Selector([

    Sequence([
        Condition(player_too_close),

        Action(lambda a, d: setattr(
            a,
            "path_timer",
            max(0.0, a.path_timer - d)
        )),

        Condition(lambda a: a.path_timer <= 0),

        Action(lambda a, d: setattr(a, "path", grey_path(a))),
        Action(lambda a, d: setattr(a, "path_timer", 2.0)),
    ]),

    Sequence([
        Condition(player_too_close),
        Action(lambda a, d: a.follow_path(a.path, d))
    ])
])

GREY_COMBAT_TREE = Selector([

    Sequence([
        HasLineOfSight(lambda a: a.world.player),

        AimAt(
            lambda a: a.world.player,
            smooth=0.25   # reduce jitter
        ),

        CanShoot(),

        RandomChance(0.08),  # slightly more natural pacing
        Shoot()
    ]),

    # fallback idle aiming
    Action(lambda a, d: a.update_turret_sway(d))
])

TEAL_MOVEMENT_TREE = Selector([
    Sequence([
        # Teal repositions occasionally even when not pressured
        RandomChance(0.02),
        Action(lambda a, d: setattr(a, "path", grey_path(a))),
        Action(lambda a, d: setattr(a, "path_timer", 2.0)),
    ]),

    Sequence([
        Action(lambda a, d: a.follow_path(a.path, d))
    ])
])

TEAL_COMBAT_TREE = Selector([
    Sequence([
        HasLineOfSight(lambda a: a.world.player),

        AimAt(
            lambda a: a.world.player,
            smooth=0.35,   # tighter aim than grey
            noise=0.1
        ),

        CanShoot(),
        RandomChance(0.12),
        Shoot()
    ]),

    Action(lambda a, d: a.update_turret_sway(d))
])

YELLOW_MOVEMENT_TREE = Selector([
    Sequence([
        RandomChance(0.03),
        Action(lambda a, d: setattr(a, "path", grey_path(a))),
        Action(lambda a, d: setattr(a, "path_timer", 2.0)),
    ]),

    Sequence([
        Action(lambda a, d: a.follow_path(a.path, d))
    ])
])

YELLOW_COMBAT_TREE = Selector([
    Sequence([
        HasLineOfSight(lambda a: a.world.player),

        AimAt(
            lambda a: a.world.player,
            smooth=0.2,
            noise=0.05
        ),

        CanShoot(),
        RandomChance(0.2),   # more aggressive than grey/teal
        Shoot()
    ]),

    Action(lambda a, d: a.update_turret_sway(d))
])

RED_MOVEMENT_TREE = Selector([
    Sequence([
        # red rarely repositions
        RandomChance(0.01),
        Action(lambda a, d: setattr(a, "path", grey_path(a))),
        Action(lambda a, d: setattr(a, "path_timer", 2.0)),
    ]),

    Sequence([
        Action(lambda a, d: a.follow_path(a.path, d))
    ])
])

RED_COMBAT_TREE = Selector([
    Sequence([
        HasLineOfSight(lambda a: a.world.player),

        AimAt(
            lambda a: a.world.player,
            smooth=0.3,
            noise=0.15
        ),

        CanShoot(),

        RandomChance(0.35),  # high aggression
        Shoot()
    ]),

    Action(lambda a, d: a.update_turret_sway(d))
])

GREEN_COMBAT_TREE = Selector([
    Sequence([
        HasLineOfSight(lambda a: a.world.player),

        AimAt(
            lambda a: a.world.player,
            smooth=0.15,
            noise=0.4   # intentionally messy aim
        ),

        CanShoot(),

        RandomChance(0.25),
        Shoot()
    ]),

    Action(lambda a, d: a.update_turret_sway(d))
])

PURPLE_MOVEMENT_TREE = Selector([
    Sequence([
        # purple repositions more defensively
        RandomChance(0.05),
        Action(lambda a, d: setattr(a, "path", grey_path(a))),
        Action(lambda a, d: setattr(a, "path_timer", 2.0)),
    ]),

    Sequence([
        Action(lambda a, d: a.follow_path(a.path, d))
    ])
])

PURPLE_COMBAT_TREE = Selector([
    Sequence([
        HasLineOfSight(lambda a: a.world.player),

        AimAt(
            lambda a: a.world.player,
            smooth=0.4,
            noise=0.2
        ),

        CanShoot(),
        RandomChance(0.06),  # cautious firing
        Shoot()
    ]),

    Action(lambda a, d: a.update_turret_sway(d))
])

WHITE_MOVEMENT_TREE = Selector([
    # WHITE tanks: minimal movement logic (mostly hold position / slight repositioning later)
    Sequence([
        Condition(player_too_close),

        # simple evasive drift instead of full pathfinding (placeholder behaviour)
        Action(lambda a, d: setattr(
            a,
            "path_timer",
            max(0.0, a.path_timer - d)
        )),

        Condition(lambda a: a.path_timer <= 0),

        # placeholder: could later be replaced with "find cover node" or "reposition slightly"
        Action(lambda a, d: setattr(
            a,
            "path",
            grey_path(a)   # reuse grey logic for now as fallback
        )),

        Action(lambda a, d: setattr(a, "path_timer", 2.0)),
    ]),

    Sequence([
        Condition(player_too_close),
        Action(lambda a, d: a.follow_path(a.path, d))
    ]),

    # idle (hold position if nothing else is happening)
    Action(lambda a, d: None)
])


WHITE_COMBAT_TREE = Selector([

    Sequence([
        HasLineOfSight(lambda a: a.world.player),

        # WHITE tanks: very precise, low-noise aiming
        AimAt(
            lambda a: a.world.player,
            noise=0.05,   # extremely stable aim
            smooth=0.35   # slow, deliberate tracking
        ),

        CanShoot(),

        # low fire rate = “calculated sniper shots”
        RandomChance(0.03),

        Shoot()
    ]),

    # fallback: very subtle sway (almost static)
    Action(lambda a, d: a.update_turret_sway(d))
])

BLACK_MOVEMENT_TREE = Selector([
    Sequence([
        RandomChance(0.01),
        Action(lambda a, d: setattr(a, "path", grey_path(a))),
        Action(lambda a, d: setattr(a, "path_timer", 2.0)),
    ]),

    Sequence([
        Action(lambda a, d: a.follow_path(a.path, d))
    ])
])

BLACK_COMBAT_TREE = Selector([
    Sequence([
        HasLineOfSight(lambda a: a.world.player),

        AimAt(
            lambda a: a.world.player,
            smooth=0.45,   # very stable aim
            noise=0.02
        ),

        CanShoot(),
        RandomChance(0.5),  # deadly when LOS exists
        Shoot()
    ]),

    Action(lambda a, d: a.update_turret_sway(d))
])