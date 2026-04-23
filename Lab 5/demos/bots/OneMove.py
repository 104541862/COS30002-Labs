"""OneMove bot — sends all ships from the first owned planet to the first
enemy/neutral planet every tick.

This is a minimal demonstration bot. Students should study it to understand
how the game façade works before building their own bots.

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026
"""

class OneMove(object):

	def update(self, gameinfo):

		if gameinfo._my_planets() and gameinfo._not_my_planets():
			# print(gameinfo._my_planets())
			src = list(gameinfo._my_planets().values())[0]
			dest = list(gameinfo._not_my_planets().values())[0]
			gameinfo.planet_order(src, dest, src.ships)
