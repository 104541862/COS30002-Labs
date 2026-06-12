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

def teal_escape_goal(agent):
    player = agent.world.player
    grid = agent.world.grid

    best_node = None
    best_score = float("inf")

    for node in grid.nodes.values():

        if not node.walkable:
            continue

        world_pos = grid.world_from_node((node.x, node.y))

        dist = (world_pos - player.pos).length()

        # prefer FARTHER than current distance
        ideal = 650.0

        score = abs(dist - ideal)

        # extra weight: avoid direct line-of-fire lanes
        direction_to_player = (player.pos - world_pos).get_normalised()
        alignment = direction_to_player.dot((player.pos - agent.pos).get_normalised())

        score += alignment * 50  # punish exposed forward positions

        if score < best_score:
            best_score = score
            best_node = world_pos

    return best_node


def teal_escape_path(agent):
    goal = teal_escape_goal(agent)
    if not goal:
        return []

    start = agent.pos + agent.heading * (agent.size * 0.5)

    return astar(agent.world.grid, start, goal)

def red_charge_goal(agent):
    player = agent.world.player
    grid = agent.world.grid

    # just pick a node closest to player (no distance balancing)
    best_node = None
    best_score = float("inf")

    for node in grid.nodes.values():

        if not node.walkable:
            continue

        world_pos = grid.world_from_node((node.x, node.y))

        score = (world_pos - player.pos).length()

        if score < best_score:
            best_score = score
            best_node = world_pos

    return best_node

def red_charge_path(agent):
    goal = red_charge_goal(agent)
    if not goal:
        return []

    start = agent.pos + agent.heading * (agent.size * 0.5)

    return astar(agent.world.grid, start, goal)

def red_direct_charge(agent):
    player = agent.world.player

    to_player = (player.pos - agent.pos).get_normalised()

    # aggressive acceleration override
    accel = to_player * agent.acceleration * 1.2

    agent.apply_movement(accel, agent.world.delta_time)

def purple_cover_goal(agent):
    player = agent.world.player
    grid = agent.world.grid

    best_node = None
    best_score = float("inf")

    for node in grid.nodes.values():

        if not node.walkable:
            continue

        world_pos = grid.world_from_node((node.x, node.y))

        dist_to_player = (world_pos - player.pos).length()

        score = abs(dist_to_player - 450.0)

        # strong preference for wall adjacency
        for wall in agent.world.wall_rects:

            closest_x = max(wall.x, min(world_pos.x, wall.x + wall.width))
            closest_y = max(wall.y, min(world_pos.y, wall.y + wall.height))

            cover_dist = (world_pos - Vector2D(closest_x, closest_y)).length()

            if cover_dist < 100:
                score -= 35  # strong anchor bonus

        if score < best_score:
            best_score = score
            best_node = world_pos

    return best_node

def purple_cover_path(agent):
    goal = purple_cover_goal(agent)
    if not goal:
        return []

    start = agent.pos + agent.heading * (agent.size * 0.5)

    return astar(agent.world.grid, start, goal)

def black_peek_movement(agent):
    """
    Black tank behaviour:
    - stays near cover (walls)
    - peeks when player is visible
    - repositions aggressively when exposed
    - uses pathfinding like GREY
    """

    player = agent.world.player

    # --- 1. If no path or timer expired, recalc ---
    if not hasattr(agent, "path_timer"):
        agent.path_timer = 0.0

    agent.path_timer -= 1  # tick-based (NOT delta)

    need_new_path = (
        agent.path_timer <= 0 or
        not getattr(agent, "path", None)
    )

    # --- 2. Choose a "peek cover" goal ---
    def find_cover_point():
        grid = agent.world.grid

        best_node = None
        best_score = float("inf")

        for node in grid.nodes.values():
            if not node.walkable:
                continue

            world_pos = grid.world_from_node((node.x, node.y))

            # distance to player (prefer mid-range)
            dist = (world_pos - player.pos).length()
            ideal = 350.0
            score = abs(dist - ideal)

            # prefer cover heavily
            for wall in agent.world.wall_rects:
                closest_x = max(wall.x, min(world_pos.x, wall.x + wall.width))
                closest_y = max(wall.y, min(world_pos.y, wall.y + wall.height))

                cover_dist = (world_pos - Vector2D(closest_x, closest_y)).length()

                if cover_dist < 140:
                    score -= 40  # strong cover bias

            # avoid direct exposure
            if agent.world.has_clear_line(world_pos, player.pos):
                score += 80  # punish exposed nodes

            if score < best_score:
                best_score = score
                best_node = world_pos

        return best_node

    # --- 3. Repath if needed ---
    if need_new_path:
        goal = find_cover_point()

        if goal:
            start = agent.pos + agent.heading * (agent.size * 0.5)
            agent.path = astar(agent.world.grid, start, goal)

        agent.path_timer = 2.5  # repath interval

    # --- 4. If no path, just sway defensively ---
    if not agent.path:
        agent.update_turret_sway(0.016)
        return

    # --- 5. Movement logic (NO delta usage here) ---
    # follow_path already handles steering + acceleration properly
    agent.follow_path(agent.path, delta=0.016)

    # --- 6. Behavioural twist: peek logic ---
    # If player has line of sight, strafe aggressively
    if agent.world.has_clear_line(agent.pos, player.pos):
        offset = (agent.pos - player.pos).get_normalised()

        # sideways peek movement (adds unpredictability)
        strafe = offset.perp()

        accel = (agent.heading + strafe * 0.8).get_normalised() * agent.acceleration
        agent.apply_movement(accel, 0.016)

    return True

def black_reposition_path(agent):
    player = agent.world.player
    grid = agent.world.grid

    best_node = None
    best_score = float("inf")

    for node in grid.nodes.values():

        if not node.walkable:
            continue

        world_pos = grid.world_from_node((node.x, node.y))

        dist = (world_pos - player.pos).length()
        score = abs(dist - 300.0)

        for wall in agent.world.wall_rects:
            closest_x = max(wall.x, min(world_pos.x, wall.x + wall.width))
            closest_y = max(wall.y, min(world_pos.y, wall.y + wall.height))

            cover_dist = (world_pos - Vector2D(closest_x, closest_y)).length()

            if cover_dist < 80:
                score -= 10

        if score < best_score:
            best_score = score
            best_node = world_pos

    return [best_node] if best_node is not None else []

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
        # if player gets too close → immediate reposition
        Condition(lambda a: player_too_close(a)),

        Action(lambda a, d: setattr(a, "path_timer", 0.0))
    ]),

    Sequence([
        RandomChance(0.05),

        Action(lambda a, d: setattr(
            a,
            "path",
            teal_escape_path(a)
        )),

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
            smooth=0.4,
            noise=0.15
        ),

        CanShoot(),

        RandomChance(0.15),

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
        CanPlaceMine(),
        RandomChance(0.001),   # occasional trap laying
        PlaceMine()
    ]),

    Sequence([
        HasLineOfSight(lambda a: a.world.player),

        AimAt(
            lambda a: a.world.player,
            smooth=0.2,
            noise=0.05
        ),

        CanShoot(),
        RandomChance(0.2),
        Shoot()
    ]),

    Action(lambda a, d: a.update_turret_sway(d))
])

RED_MOVEMENT_TREE = Selector([

    Sequence([
        HasLineOfSight(lambda a: a.world.player),

        Action(lambda a, d: red_direct_charge(a))
    ]),

    Sequence([
        RandomChance(0.02),

        Action(lambda a, d: setattr(
            a,
            "path",
            red_charge_path(a)
        )),

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

        Action(lambda a, d: setattr(
            a.turret,
            "rotation",
            -math.degrees(
                math.atan2(
                    a.world.player.pos.y - a.pos.y,
                    a.world.player.pos.x - a.pos.x
                )
            )
        )),

        Action(lambda a, d: setattr(
            a,
            "_green_shot_dir",
            a.find_bounce_shot()
        )),

        Condition(lambda a: getattr(a, "_green_shot_dir", None) is not None),

        CanShoot(),

        RandomChance(0.35),

        Shoot()
    ]),

    # fallback: no randomness wandering aim
    Action(lambda a, d: a.update_turret_sway(d))
])

PURPLE_MOVEMENT_TREE = Selector([

    Sequence([
        RandomChance(0.04),

        Action(lambda a, d: setattr(
            a,
            "path",
            purple_cover_path(a)
        )),

        Action(lambda a, d: setattr(a, "path_timer", 2.5)),
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
            smooth=0.45,
            noise=0.25
        ),

        CanShoot(),

        RandomChance(0.05),

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
        HasLineOfSight(lambda a: a.world.player),

        Action(lambda a, d: black_peek_movement(a))
    ]),

    Sequence([
        RandomChance(0.03),

        Action(lambda a, d: setattr(
            a,
            "path",
            black_reposition_path(a)
        )),

        Action(lambda a, d: setattr(a, "path_timer", 1.2)),
    ]),

    Sequence([
        Action(lambda a, d: a.follow_path(a.path, d))
    ])
])

BLACK_COMBAT_TREE = Selector([
    Sequence([
        CanPlaceMine(),
        RandomChance(0.04),
        PlaceMine()
    ]),

    Sequence([
        HasLineOfSight(lambda a: a.world.player),

        AimAt(
            lambda a: a.world.player,
            smooth=0.5,
            noise=0.03
        ),

        CanShoot(),

        RandomChance(0.55),

        Shoot()
    ]),

    Action(lambda a, d: a.update_turret_sway(d))
])