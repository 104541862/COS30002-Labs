"""Game entities for the PlanetWars world.

There are two game entity classes: ``Planet`` and ``Fleet``. Both are derived
from an ``Entity`` base class. Conceptually both planets and fleets contain
"ships" and are given a unique game ID.

Planets are either "owned" by a player or neutral. When occupied by a player,
planets create new ships (based on their ``growth`` rate).

Fleets are launched from a planet (or fleet) and sent to a target planet.
Fleets are always owned by one of the players.

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""
import math
import uuid

NEUTRAL_ID = '0'
FLEET_SPEED = 20
SCALE_FACTOR = 1000

class Entity():
	"""Abstract base class representing entities in the 2-D game world.

	Provides shared state (position, ships, owner) and utility methods
	(distance calculation, ship management) used by both Planet and Fleet.
	"""

	def __init__(self, x, y, ID=None, owner=None, ships=0):
		if ID:
			self.ID = ID
		else:
			self.ID = str(uuid.uuid1())

		self.x = x*SCALE_FACTOR
		self.y = y*SCALE_FACTOR
		self.ships = ships
		if owner:
			self.owner = owner
		else:
			self.owner = NEUTRAL_ID
		self.vision_age = 0
		# self._name = "%s:%s" % (type(self).__name__, str(id))

	def distance_to(self, other=None, x=None, y=None, sqrt=False):
		"""Calculate the squared distance to another entity or point.

		Returns the *squared* Euclidean distance by default because square-root
		is unnecessary when only comparing relative magnitudes. Pass
		``sqrt=True`` if you need the precise (non-squared) distance.

		Args:
			other: Another Entity instance (optional).
			x, y:  Raw coordinates — used when the target is not an Entity.
			sqrt:  If True, return the true Euclidean distance.
		"""
		if other:
			if self.ID == other.ID:
				return 0.0
			dx = self.x - other.x
			dy = self.y - other.y
		else:
			dx = self.x - x
			dy = self.y - y
		if sqrt:
			return math.sqrt(dx * dx + dy * dy)
		else:
			return dx * dx + dy * dy

	def remove_ships(self, ships):
		"""Remove the specified number of ships from this entity.

		Raises ValueError if the request is invalid (zero/negative count or
		more ships than available).
		"""
		if ships <= 0:
			raise ValueError("%s (owner %s) tried to send %d ships (of %d)." %
							 (self.ID, self.owner, ships, self.ships))
		if self.ships < ships:
			raise ValueError("%s (owner %s) can't remove more ships (%d) then it has (%d)!" %
							 (self.ID, self.owner, ships, self.ships))
		self.ships -= ships

	def add_ships(self, ships):
		"""Add the specified number of ships to this entity."""
		if ships < 0:
			raise ValueError("Cannot add a negative number of ships...")
		self.ships += ships

	def update(self):
		raise NotImplementedError("This method cannot be called on this 'abstract' class")

	def is_in_vision(self):
		"""Return True if this entity was observed on the current tick."""
		return self.vision_age == 0

	def in_range(self, entities):
		"""Return a list of entity IDs that are within vision range of this entity."""
		limit = self.vision_range()
		return [p.ID for p in entities if self.distance_to(p) <= limit]

	def __str__(self):
		return "%s, owner: %s, ships: %d" % (self.ID, self.owner, self.ships)

	def serialise(self):
		"""Return a JSON-compatible dictionary of this entity's state."""
		return {
			'ID': self.ID,
			'owner': self.owner,
			'ships': self.ships,
			'x': self.x/SCALE_FACTOR,
			'y': self.y/SCALE_FACTOR
		}


class Planet(Entity):
	"""A planet in the game world.

	When occupied by a player the planet creates new ships each time step
	(when ``update`` is called). Each planet also has a ``vision_range``
	which is partially proportional to its growth rate (size).
	"""

	def __init__(self, x, y, ID=None, owner=None, ships=None, growth=1):
		super().__init__(x, y, ID, owner, ships)
		self.growth = growth

	def update(self):
		"""If the planet is owned (non-neutral), grow the number of ships."""
		if self.owner != NEUTRAL_ID:
			self.add_ships(self.growth)

	def vision_range(self):
		"""Return the vision range based on planet growth and garrison."""
		return 100+50*self.growth+self.ships
	
	def serialise(self):
		"""Return a JSON-compatible dictionary including growth rate."""
		serial = super().serialise()
		serial['growth'] = self.growth
		return serial

class Fleet(Entity):
	"""A fleet in the game world.

	Each fleet is owned by a player and launched from either a planet or
	another fleet (mid-flight). All fleets move at the same constant speed
	each game step.

	Fleet ID values are deliberately obscure (using UUID) to prevent enemy
	players from gleaning information from predictable identifiers.
	"""

	def __init__(self, ID=None, owner=None, ships=None, src=None, dest=None, x=None, y=None):
		super().__init__(
			x or src.x/SCALE_FACTOR,
			y or src.y/SCALE_FACTOR,
			ID, owner, ships)
		self.dest = dest
		# Cache the heading angle since it is unlikely to change tick-to-tick.
		self.heading = math.atan2((self.dest.y-self.y),(self.dest.x-self.x))

	# def in_range(self, entities, ignoredest=True):
	# 	result = super(Fleet, self).in_range(entities)
	# 	if (not ignoredest) and (self.turns_remaining == 1) and (self.dest not in result):
	# 		result.append(self.dest)
	# 	return result

	def vision_range(self):
		"""Return the vision range based on fleet ship count."""
		return 50+self.ships*2.5

	def update(self):
		"""Move the fleet forward by one game time step."""
		self.x += math.cos(self.heading) * FLEET_SPEED
		self.y += math.sin(self.heading) * FLEET_SPEED

	def serialise(self):
		"""Return a JSON-compatible dictionary of the fleet's state."""
		return super().serialise()