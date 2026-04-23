"""Player and bot-controller integration for PlanetWars.

The ``Player`` class acts as both the game's internal player representation
and the *façade* through which bot controllers interact with the simulation.

Each game step the ``PlanetWars`` game updates the information held by the
player, taking into account the entities the player is actually aware of.
The Player then passes itself to the bot controller, which issues orders
(via the Player order methods). The orders may be ignored if they are invalid.

The Player façade represents a "fog-of-war" view of the true game
environment. A player bot can only "see" what is in range of its own
occupied planets or fleets in transit across the map. This creates an
incentive for bots to exploit scouting details.

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""

import uuid
from entities import NEUTRAL_ID

class Player(object):
	"""Represents a player in the game, wrapping their bot controller.

	This class is used by the ``PlanetWarsGame`` instance to manage each
	player. It dynamically loads the bot controller module from the
	``bots/`` directory based on the player's ``name``, then delegates
	per-tick decision-making to that controller's ``update`` method.

	The Player also provides a range of helper functions for providing
	useful filtered views on the façade data (e.g. only your planets,
	only enemy fleets).
	"""

	def __init__(self, ID, name):
		self.ID = ID  # as allocated by the game
		self.name = name.replace('.py', '')  # accept both "Dumbo" or "Dumbo.py"
		#self.log = log or (lambda *p, **kw: None)
		self.orders = []
		self.ships = 0
		self._alive = True
		self.planets = {}	# façade-visible planets (fog-of-war filtered)
		self.fleets = {}	# façade-visible fleets  (fog-of-war filtered)

		if self.ID != NEUTRAL_ID:
			# Dynamically import the bot controller from ./bots/<name>.py
			# The class name inside the file MUST match the filename exactly.
			mod = __import__('bots.' + name)  # ... the top level bots mod (dir)
			mod = getattr(mod, name)	   # ... then the bot mod (file)
			cls = getattr(mod, name)	  # ... the class (eg DumBo.py contains DumBo class)
			self.controller = cls()

	def __str__(self):
		return "%s(id=%s)" % (self.name, str(self.ID))
	
	def serialise(self):
		"""Return a JSON-compatible dictionary of the player's identity."""
		return {
			'ID': self.ID,
			'name': self.name
		}

	def update(self):
		"""Delegate decision-making to the bot controller.

		Assumes the façade details (planets, fleets) have already been
		refreshed by the game before this method is called.
		"""
		if self.ID != NEUTRAL_ID:
			self.controller.update(self)

	def fleet_order(self, src_fleet, dest, ships):
		"""Order a fleet to divert (some/all) ships to a destination planet.

		Note: this is just a *request* — the game decides and enforces the
		rules. The returned fleet ID is your reference if the order is
		fulfilled, but there is no guarantee.
		"""
		# If splitting the source fleet we need a new fleet ID; otherwise
		# reuse the existing one.
		fleetid = uuid.uuid4() if ships < src_fleet.ships else src_fleet.ID
		self.orders.append(('fleet', src_fleet.ID, fleetid, ships, dest.ID))
		return fleetid

	def planet_order(self, src_planet, dest, ships):
		"""Order a planet to launch a new fleet to a destination planet.

		Note: this is just a *request* — the game decides and enforces the
		rules. The returned fleet ID is your reference if the order is
		fulfilled, but there is no guarantee.
		"""
		fleetid = uuid.uuid4()
		self.orders.append(('planet', src_planet.ID, fleetid, ships, dest.ID))
		return fleetid

	# ---- Helper / convenience filters ----
	# It is strongly recommended that you cache the results of these function
	# calls. Multiple calls within the same game tick will produce the same
	# results.
	def _my_planets(self):
		"""Return a dict of planets owned by this player."""
		return dict([(k, p) for k, p in self.planets.items() if p.owner == self.ID])

	def _enemy_planets(self):
		"""Return a dict of planets owned by enemy players (excludes neutral)."""
		return dict([(k, p) for k, p in self.planets.items() if p.owner not in (NEUTRAL_ID, self.ID)])

	def _not_my_planets(self):
		"""Return a dict of all planets NOT owned by this player."""
		return dict([(k, p) for k, p in self.planets.items() if p.owner != self.ID])

	def _neutral_planets(self):
		"""Return a dict of neutral (unowned) planets."""
		return dict([(k, p) for k, p in self.planets.items() if p.owner == NEUTRAL_ID])

	def _my_fleets(self):
		"""Return a dict of fleets owned by this player."""
		return dict([(k, f) for k, f in self.fleets.items() if f.owner == self.ID])

	def _enemy_fleets(self):
		"""Return a dict of fleets owned by enemy players."""
		return dict([(k, f) for k, f in self.fleets.items() if f.owner != self.ID])
