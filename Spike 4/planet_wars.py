"""PlanetWars core game engine.

This module contains the ``PlanetWarsGame`` class — the authoritative source
of truth for the entire simulation. It manages the game loop phases
(player orders → growth → fleet movement → combat resolution → façade sync),
enforces all rules, and maintains the canonical state of every planet and
fleet.

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""

import copy
import collections
from entities import Planet, Fleet, NEUTRAL_ID
from players import Player
from planet_wars_draw import PLANET_RADIUS_FACTOR
import uuid


class PlanetWarsGame():
	"""Core simulation engine for PlanetWars.

	Orchestrates a multi-phase game loop each tick:
	  0. Player controllers issue orders.
	  1. Orders are validated and executed (fleet creation).
	  2. Planets grow ships (advancement).
	  3. Fleets move towards their destinations.
	  4. Fleet arrivals trigger combat resolution.
	  5. Tick counter advances.
	  6. Fog-of-war façades are re-synced for every player.
	"""

	def __init__(self, gamestate_json, logger=None, replay_object=None):
		"""Initialise the game from a parsed JSON game-state dictionary.

		Args:
			gamestate_json: dict containing 'planets', optionally 'fleets',
				'orders', 'players', and 'max_ticks'.
			logger: Optional name (string) of a logscript module in
				``logscripts/`` to use for turn logging.
			replay_object: Optional defaultdict(list) to record replay data
				into. Pass None to disable replay recording.
		"""
		# ---- Build planet registry from JSON ----
		self.planets = {}
		for p in gamestate_json['planets']:
			p = Planet(
				p['x'],
				p['y'],
				p.get('ID'),
				p.get('owner'),
				p.get('ships'),
				p.get('growth')
			)
			self.planets[p.ID] = p

		# ---- Build fleet registry from JSON (if any) ----
		self.fleets = {}
		if 'fleets' in gamestate_json:
			for f in gamestate_json['fleets']:
				f = Fleet(f)
				self.fleets[f.ID] = f

		# ---- Load pre-recorded orders (typically from a replay) ----
		# Replay orders are executed before control is handed over to players;
		# they are plain JSON objects keyed by the tick they execute on.
		self.orders = collections.defaultdict(list)
		if 'orders' in gamestate_json:
			for order in gamestate_json['orders']:
				self.orders[order['tick']].append(order)

		# ---- Create player objects (including a Neutral placeholder) ----
		if 'players' in gamestate_json:
			self.players = {}
			self.players[NEUTRAL_ID] = Player(NEUTRAL_ID, "Neutral")
			for p in gamestate_json['players']:
				self.players[p["ID"]] = Player(p["ID"], p["name"])

		# ---- Optional logscript loader ----
		if logger:
			logger = logger.replace('.py', '')
			# Dynamic import: logscript/<logger>.py → class <logger>
			module = __import__('logscript.'+logger)
			module = getattr(module, logger)  # ... then the bot mod (file)
			cls = getattr(module, logger)		# ... the class
			self.turn_log = cls().log

		# ---- Game-state bookkeeping ----
		self.tick = 0
		self.max_ticks = gamestate_json.get('max_ticks')
		self.winner = None
		self.dirty = True   # flag for the renderer to know when to re-sync
		self.paused = True

		# ---- Assign unowned players to starting planets ----
		self.spawn_players()

		# ---- Build the initial fog-of-war façade for each player ----
		for player in self.players.values():
			if player.ID != NEUTRAL_ID:
				self.update_facade(player)

		# ---- Replay recording (optional) ----
		self.replay_object = replay_object
		if self.replay_object is not None:
			self.replay_object["orders"] = []
			self.serialise_to_replay()

	def serialise_to_replay(self):
		"""Snapshot the initial game state into the replay object."""
		for planet in self.planets.values():
			self.replay_object["planets"].append(planet.serialise())
		for fleet in self.fleets.values():
			self.replay_object["fleets"].append(fleet.serialise())
		for player in self.players.values():
			self.replay_object["players"].append(player.serialise())
		

	def spawn_players(self):
		"""Assign starting planets to players that do not yet own any.

		Uses a furthest-from-centroid heuristic so that players spawn as
		far apart as possible on the map.
		"""
		players_to_be_spawned = []
		# should we keep this on self as a speedy cache and just move planets around when they change hands?
		planets_by_player = collections.defaultdict(list)
		centroid_of_owned_planets = [0, 0]
		sum_of_owned_planets = [0, 0]
		sum_of_planets = [0, 0]
		count_of_owned_planets = 0
		for player in self.players.values():
			for planet in self.planets.values():
				sum_of_planets[0] += planet.x
				sum_of_planets[1] += planet.y
				if planet.owner == player.ID:
					planets_by_player[player.ID].append(planet)
					sum_of_owned_planets[0] += planet.x
					sum_of_owned_planets[1] += planet.y
					count_of_owned_planets += 1
			if not player.ID in planets_by_player.keys():
				players_to_be_spawned.append(player.ID)
		unowned_planets = planets_by_player.pop(NEUTRAL_ID)
		# Quick check that we have enough planets for players
		if len(players_to_be_spawned) > len(unowned_planets):
			raise ValueError("Not enough planets for players to spawn")
		for playerID in players_to_be_spawned:
			if count_of_owned_planets == 0:
				centroid_of_owned_planets[0] = sum_of_planets[0] / \
					count_of_owned_planets
				centroid_of_owned_planets[1] = sum_of_planets[0] / \
					count_of_owned_planets
			else:
				centroid_of_owned_planets[0] = sum_of_owned_planets[0] / \
					count_of_owned_planets
				centroid_of_owned_planets[1] = sum_of_owned_planets[1] / \
					count_of_owned_planets
			dist = 0
			candidate = None
			for planet in unowned_planets:
				_dist = planet.distance_to(
					x=centroid_of_owned_planets[0],
					y=centroid_of_owned_planets[1]
				)
				if _dist > dist:
					candidate = planet
					dist = _dist
			candidate.owner = playerID
			unowned_planets.remove(candidate)
			sum_of_owned_planets[0] += candidate.x
			sum_of_owned_planets[1] += candidate.y
			count_of_owned_planets += 1
			# if we use planets_by_player again, be sure to set it up here

	def add_to_vision_list(self, src, target, entity_dict, force=False, update=True, shallowcpy=False):
		"""Conditionally add a target entity to a vision-filtered dict.

		Adds a (deep) copy of *target* into *entity_dict* if it is within
		the vision range of *src*.

		Does **not** add if:
		  - They share the same owner (unless *force* is True).
		  - Target already exists in *entity_dict* (unless *update* is True).

		Returns True if the entity was added, False otherwise.
		"""
		if shallowcpy:
			_copy = copy.copy
		else:
			_copy = copy.deepcopy
		# An entity can always see other entities owned by the same player.
		if src.owner == target.owner:
			if force:
				entity_dict[target.ID] = _copy(target)
				return True
			return False

		# Skip planets that have already been seen by something else
		if force or update or target.ID not in entity_dict.facade.planets:
			# Check vision range and add if visible
			if src.distance_to(target) < src.vision_range()**2:
				entity_dict[target.ID] = copy.deepcopy(target)
				return True

	def update_facade(self, player):
		"""Refresh the fog-of-war façade for a given player.

		Iterates over all the player's owned planets and fleets, determining
		which other entities fall within their vision range. The player's
		``planets`` and ``fleets`` dicts are updated accordingly.
		"""
		player.fleets = {}  # no memory of fleets' last locations
		player.tick = self.tick
		if len(player.planets) == 0:
			# Player starts the game with knowledge of the initial state of
			# all planets.
			# TODO: this shouldn't be the case if the game is loaded from a
			# later state
			player.planets = copy.deepcopy(self.planets)
		else:
			for planet in self.planets.values():
				if planet.owner == player.ID:
					# You can see a planet if you own it
					player.planets[planet.ID] = copy.deepcopy(planet)
					# Check what other planets this planet can see
					for other in self.planets.values():
						if self.add_to_vision_list(planet, other, player.planets):
							player.planets[other.ID].vision_age = 0
						else:
							player.planets[other.ID].vision_age += 1
					# Same logic, but for fleets
					for other in self.fleets.values():
						if self.add_to_vision_list(planet, other, player.fleets):
							player.fleets[other.ID].vision_age = 0

		for fleet in self.fleets.values():
			if fleet.owner == player.ID:
				# You can see a fleet if you own it
				player.fleets[fleet.ID] = copy.deepcopy(fleet)
				# Check what other planets this fleet can see
				for other in self.planets.values():
					if self.add_to_vision_list(fleet, other, player.planets):
						player.planets[planet.ID].vision_age = 0
					else:
						player.planets[planet.ID].vision_age += 1

				# Same logic, but for fleets
				for other in self.fleets.values():
					if self.add_to_vision_list(fleet, other, player.fleets):
						player.fleets[other.ID].vision_age = 0

	def update(self, t=None, manual=False):
		"""Advance the game simulation by one tick.

		This method implements the full game loop across six phases:
		  0. Player controllers issue orders (skipped during replay).
		  1. Orders are validated and executed.
		  2. Planets grow ships.
		  3. Fleets advance towards their destinations.
		  4. Arriving fleets trigger combat resolution.
		  5. Tick counter increments.
		  6. Façades are re-synced for each player.

		Args:
			t: Unused (reserved for future use / scheduler delta).
			manual: If True, runs even when the game is paused (for
				single-step debugging via the 'N' key).
		"""
		if self.paused and not manual:
			return
		# Phase 0: Give each player (controller) a chance to create new fleets.
		# Skipped if there are pre-recorded orders remaining (replay mode).
		if len(self.orders.keys()) == 0:
			for player in self.players.values():
				if player.ID != NEUTRAL_ID:
					player.update()
			# Phase 1: Retrieve and process all pending orders from each player
			for player in self.players.values():
				if player.ID != NEUTRAL_ID:
					self._process_orders(player.orders, player)
					player.orders = []
		else:
			self._process_orders(self.orders[self.tick])
			del self.orders[self.tick]
		# Phase 2: Planet ship number growth (advancement)
		for planet in self.planets.values():
			planet.update()
		# Phase 3: Update fleets, check for arrivals
		arrivals = collections.defaultdict(list)
		for f in self.fleets.values():
			f.update()
			if f.distance_to(f.dest) <= ((f.dest.growth+1) * PLANET_RADIUS_FACTOR)**2:
				arrivals[f.dest].append(f)
		# Phase 4: Collate fleet arrivals and planet forces by owner
		for p, fleets in arrivals.items():
			forces = collections.defaultdict(int)
			# Add the current occupier of the planet
			forces[p.owner] = p.ships
			# Add arriving fleets
			for f in fleets:
				self.fleets.pop(f.ID)
				forces[f.owner] += f.ships
			# No battle — just reinforce
			if len(forces) == 1:
				self.turn_log(
					"{0:4d}: Player {1} reinforced planet {2}".format(self.tick, p.owner, p.ID))
				p.ships = forces[p.owner]
			else:
				# Battle!
				# There are at least 2 forces, maybe more. Biggest force wins.
				# Gap between 1st and 2nd is the remaining force size.
				result = sorted([(v, k)
								for k, v in forces.items()], reverse=True)
				winner = result[0][1]
				gap_size = result[0][0] - result[1][0]
				if gap_size == 0:
					winner = p.owner  # if the planet ends up on 0, it stays with the current owner
				# If meaningful outcome, log it
				if winner == p.owner:
					self.turn_log(
						"{0:4d}: Player {1} defended planet {2}".format(self.tick, winner, p.ID))
				else:
					self.turn_log(
						"{0:4d}: Player {1} now owns planet {2}".format(self.tick, winner, p.ID))
				# Set the new owner
				p.owner = winner
				p.ships = gap_size
			# Either a planet changed hands or was defended/reinforced
			# — either way fleets/planets rendering needs to be updated
			self.dirty = True
		# Phase 5: Update the game tick count.
		self.tick += 1
		# Phase 6: Re-sync the fog-of-war façade for each player
		for player in self.players.values():
			if player.ID != NEUTRAL_ID:
				self.update_facade(player)

	def _process_orders(self, orders, player=None):
		"""Process all pending orders, then clear them.

		An order sends ships from a player-owned fleet or planet to a
		destination planet.

		Checks for valid order conditions:
		  - Valid source (planet or fleet)
		  - Valid destination (planet only)
		  - Source is owned by player
		  - Source has ships to launch (> 0)
		  - Limits number of ships to number available

		Invalid orders are modified (ship number limit) or ignored.
		"""
		for order in orders:
			try:
				# Order is a dict (JSON-sourced)
				player = self.players[order["owner"]]
				o_type = order['type']
				src_id = order['source']
				new_id = order['new_fleet_id']
				ships = order['ships']
				dest_id = order['destination']
			except TypeError:
				# TODO: update player orders to use some nice JSON
				o_type, src_id, new_id, ships, dest_id = order
			# Check for valid fleet or planet id?
			if src_id not in (self.planets.keys() | self.fleets.keys()):
				self.turn_log("Invalid order ignored - not a valid source.")
			# Check for valid planet destination?
			# TODO: allow destination to be a fleet or an x,y coord
			elif dest_id not in self.planets:
				self.turn_log(
					"Invalid order ignored - not a valid destination.")
			else:
				# Extract and use the src and dest details
				src = self.fleets[src_id] if o_type == 'fleet' else self.planets[src_id]
				dest = self.planets[dest_id]
				# Check that player owns the source of ships!
				if src.owner is not player.ID:
					self.turn_log(
						"Invalid order ignored - player does not own source!")
				# Is the number of ships requested valid?
				if ships > src.ships:
					self.turn_log(
						"Invalid order modified - not enough ships. Max used.")
					ships = src.ships
				# Still ships to launch? Do it ...
				if ships > 0:
					fleet = Fleet(new_id, player.ID, ships, src, dest)
					src.remove_ships(ships)
					# Old empty fleet removal
					if o_type == 'fleet' and src.ships == 0:
						del self.fleets[src.ID]
					# Keep new fleet
					self.fleets[new_id] = fleet
					msg = "{0:4d}: Player {1} launched {2} (left {3}) ships from {4} {5} to planet {6}".format(
						self.tick, player.ID, ships, src.ships, o_type, src.ID, dest.ID)
					self.turn_log(msg)
					# player.log(msg)
					self.dirty = True
				else:
					self.turn_log(
						"Invalid order ignored - no ships to launch.")

				if self.replay_object:
					# Save the orders to the replay file
					for order in player.orders:
						self.replay_object["orders"].append(
							{
								"ID": uuid.uuid1().__str__(),
								"owner": player.ID,
								"tick": self.tick,
								"name": order[0],
								"type": order[0],
								"source": order[1],
								"destination": order[4],
								"ships": order[3],
								"new_fleet_id": order[2].__str__()
							}
						)


	def is_alive(self):
		"""Return True if two or more players are still alive.

		A player is considered alive if they own at least one planet or
		have at least one fleet in transit.
		"""
		living_players = []
		for planet in self.planets.values():
			if planet.owner != NEUTRAL_ID and planet.owner not in living_players:
				living_players.append(planet.owner)
				if len(living_players) > 1:
					return True
		for fleet in self.fleets.values():
			if fleet.owner != NEUTRAL_ID and fleet.owner not in living_players:
				living_players.append(fleet.owner)
				if len(living_players) > 1:
					return True
		return False

	def turn_log(self, msg):
		"""Default no-op logger; replaced if a logscript is provided."""
		pass
