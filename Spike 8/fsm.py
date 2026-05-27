from time import time
import pyglet
from vector2d import Vector2D, Point2D
from graphics import COLOUR_NAMES, PolyLine, window, ArrowLine
from math import sin, cos, radians
from random import random, randrange, uniform
from path import Path
from matrix33 import Matrix33

class State:
    """Base class for all FSM states."""

    def enter(self, agent):
        pass

    def exit(self, agent):
        pass

    def update(self, agent, delta):
        pass


class AgentFSM:
    """Top-level state controller."""

    def __init__(self, agent):
        self.agent = agent
        self.current_state = PatrolState()
        self.current_state.enter(agent)

    def change_state(self, new_state):
        self.current_state.exit(self.agent)
        self.current_state = new_state
        self.current_state.enter(self.agent)

    def update(self, delta):
        self.current_state.update(self.agent, delta)

    def get_full_state(self, agent):
        agent_state = self.current_state.__class__.__name__.replace("State", "")

        movement = agent.movement_fsm.current_state.__class__.__name__.replace("State", "")
        combat = agent.combat_fsm.current_state.__class__.__name__.replace("State", "") if agent.combat_fsm else "None"

        return f"{agent_state} | {movement} | {combat}"

class MovementFSM:
    def __init__(self, agent):
        self.agent = agent
        self.current_state = SeekState()
        self.current_state.enter(agent)

    def change_state(self, new_state):
        self.current_state.exit(self.agent)
        self.current_state = new_state
        self.current_state.enter(self.agent)

    def update(self, delta):
        return self.current_state.update(self.agent, delta)

class CombatFSM:
    def __init__(self, agent):
        self.agent = agent
        self.current_state = ShootingState()
        self.current_state.enter(agent)

    def change_state(self, new_state):
        self.current_state.exit(self.agent)
        self.current_state = new_state
        self.current_state.enter(self.agent)

    def update(self, delta):
        self.current_state.update(self.agent, delta)

class PatrolState(State):
    def enter(self, agent):
        pass

    def update(self, agent, delta):
        # Protect against None type if FSMs are not initialized
        if agent.movement_fsm is None:
            agent.movement_fsm = MovementFSM(agent)

        # High-level transition
        if agent.can_see_target():
            agent.fsm.change_state(AttackState())
            return

        # Low-level movement update
        agent.movement_fsm.update(delta)

        # waypoint switching logic (shared responsibility)
        current = agent.path.current_pt()
        if (current - agent.pos).length() < agent.waypoint_threshold:
            agent.path.inc_current_pt()

            # optional: switch movement behaviour
            # Seek keeps momentum, Arrive slows near waypoint
            agent.movement_fsm.change_state(ArriveState())
        else:
            agent.movement_fsm.change_state(SeekState())

class AttackState(State):
    def enter(self, agent):
        agent.combat_fsm = CombatFSM(agent)

        # Used for circular patrol (center of orbit)
        if not hasattr(agent, "orbit_center"):
            agent.orbit_center = agent.path.current_pt().copy()

    def exit(self, agent):
        agent.movement_locked = False

    def update(self, agent, delta):

        target = agent.world.target_agent

        if target is None or not agent.can_see_target() or not target.alive:
            agent.movement_fsm.change_state(StopState())  # optional safety stop
            agent.fsm.change_state(PatrolState())
            return

        weapon = agent.weapon

        to_target = target.pos - agent.pos
        dist = to_target.length()

        # -------------------------
        # RIFLE
        # -------------------------
        if weapon.weapon_type == "rifle":

            # hard lock movement
            agent.movement_fsm.change_state(StopState())

            # aim only
            weapon.set_aim(agent.get_aim_direction(target))

            agent.combat_fsm.update(delta)
            return

        # -------------------------
        # HANDGUN
        # -------------------------
        if weapon.weapon_type == "handgun":

            shoot_range = 400
            flee_range = 600

            # VERY CLOSE: FLEE + SHOOT
            if dist < shoot_range:
                agent.movement_fsm.change_state(FleeState())
                weapon.set_aim(agent.get_aim_direction(target))
                agent.combat_fsm.update(delta)
                return

            # CLOSE: FLEE
            if dist < flee_range:
                agent.movement_fsm.change_state(FleeState())
                agent.combat_fsm.update(delta)
                return

            # FAR: ORBIT
            center = agent.orbit_center
            to_center = agent.pos - center

            if to_center.lengthSq() < 1e-6:
                to_center = Vector2D(1, 0)

            tangent = Vector2D(-to_center.y, to_center.x).normalise()

            agent.movement_fsm.change_state(StrafeState(target.pos, tangent))

            weapon.set_aim(agent.get_aim_direction(target))
            agent.combat_fsm.update(delta)
            return

        # -------------------------
        # SHOTGUN
        # -------------------------
        if weapon.weapon_type == "shotgun":

            to_target = target.pos - agent.pos
            dist = to_target.length()

            weapon.set_aim(agent.get_aim_direction(target))

            # FAR: RUSH
            if dist > 350:
                agent.seek_target = target.pos
                agent.movement_fsm.change_state(SeekState())
                agent.combat_fsm.update(delta)
                return

            # MID: STRAFE + RUSH
            elif dist > 180:

                tangent = Vector2D(-to_target.y, to_target.x).normalise()

                agent.movement_fsm.change_state(
                    StrafeState(target.pos, tangent)
                )

                agent.combat_fsm.update(delta)
                return

            # CLOSE: PURE STRAFE
            else:
                tangent = Vector2D(-to_target.y, to_target.x).normalise()

                agent.movement_fsm.change_state(
                    StrafeState(target.pos, tangent)
                )

                agent.combat_fsm.update(delta)
                return

        # -------------------------
        # ROCKET
        # -------------------------
        if weapon.weapon_type == "rocket":

            weapon.set_aim(agent.get_aim_direction(target))

            # CLOSE -> FLEE
            if dist < 600:
                agent.movement_fsm.change_state(FleeState())
                agent.rocket_aim_timer = 0.0
                return

            # LONG -> STOP + AIM + FIRE
            else:
                agent.movement_fsm.change_state(StopState())

                if not hasattr(agent, "rocket_aim_timer"):
                    agent.rocket_aim_timer = 0.0

                agent.rocket_aim_timer += delta

                if agent.rocket_aim_timer >= 4.0:
                    agent.combat_fsm.update(delta)
                    agent.rocket_aim_timer = 0.0

                return

        # -------------------------
        # GRENADE
        # -------------------------
        if weapon.weapon_type == "grenade":

            weapon.set_aim(agent.get_aim_direction(target))

            ideal_min = 350
            ideal_max = 550

            # TOO CLOSE -> FLEE
            if dist < ideal_min:
                agent.movement_fsm.change_state(FleeState())
                agent.combat_fsm.update(delta)
                return

            # IDEAL -> STRAFE
            elif dist < ideal_max:
                tangent = Vector2D(-to_target.y, to_target.x).normalise()
                agent.movement_fsm.change_state(StrafeState(target.pos, tangent))
                agent.combat_fsm.update(delta)
                return

            # TOO FAR -> SEEK
            else:
                agent.seek_target = target.pos
                agent.movement_fsm.change_state(SeekState())
                agent.combat_fsm.update(delta)
                return

        # -------------------------
        # DEFAULT
        # -------------------------
        agent.combat_fsm.update(delta)

class CombatState:
    def enter(self, agent): pass
    def exit(self, agent): pass
    def update(self, agent, delta): pass

class MovementState:
    def enter(self, agent): pass
    def exit(self, agent): pass
    def update(self, agent, delta): 
        return Vector2D()

class ShootingState(CombatState):

    def update(self, agent, delta):

        target = agent.world.target_agent

        if target is None:
            return

        weapon = agent.weapon

        # EMPTY MAGAZINE -> RELOAD
        if weapon.ammo <= 0:
            agent.combat_fsm.change_state(ReloadingState())
            return

        # AIM
        aim_dir = agent.get_aim_direction(target)

        weapon.set_aim(aim_dir)

        # FIRE
        if weapon.can_fire():

            shots = weapon.fire(aim_dir)

            # weapon may refuse if empty
            if shots:
                agent.world.spawn_projectiles(weapon, shots)

        # AFTER SHOT CHECK
        if weapon.ammo <= 0:
            agent.combat_fsm.change_state(ReloadingState())

class ReloadingState(CombatState):

    def enter(self, agent):

        weapon = agent.weapon

        # weapon-specific reload speeds
        reload_times = {
            "rifle": 2.0,
            "handgun": 1.4,
            "shotgun": 3.0,
            "rocket": 1.0,  # placeholder. reloads each shot, no full reload time
            "grenade": 3.5,
        }

        self.reload_timer = reload_times.get(
            weapon.weapon_type,
            2.0
        )

    def update(self, agent, delta):

        self.reload_timer -= delta

        if self.reload_timer <= 0:

            weapon = agent.weapon

            if weapon.magazine_size is None:
                # infinite ammo (e.g. rockets) -> just reset cooldown
                weapon._last_fire_time = 0.0

            # refill magazine
            weapon.ammo = weapon.magazine_size

            # back to combat
            agent.combat_fsm.change_state(ShootingState())

class TakingCoverState(CombatState):
    def update(self, agent, delta):
        # No obstacles yet -> fallback to shooting
        agent.combat_fsm.change_state(ShootingState())

class SeekState(MovementState):
    def update(self, agent, delta):
        target = getattr(agent, "seek_target", agent.path.current_pt())
        return agent.seek(target)
    
class StopState(MovementState):
    def enter(self, agent):
        agent.vel = Vector2D()
        agent.accel = Vector2D()

    def update(self, agent, delta):
        return Vector2D()

class StrafeState(MovementState):
    def __init__(self, target, tangent):
        self.target = target
        self.tangent = tangent

    def update(self, agent, delta):
        rush = agent.seek(self.target)
        strafe = self.tangent * agent.max_speed

        return (rush * 0.6) + (strafe * 0.8)

class FleeState(MovementState):
    def update(self, agent, delta):
        target = agent.world.target_agent
        if target is None:
            return Vector2D()

        return agent.flee(target.pos)

class ArriveState(MovementState):
    def update(self, agent, delta):
        target = agent.path.current_pt()
        return agent.arrive(target, 'normal')



