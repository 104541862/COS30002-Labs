from random import choice

class BestWorst(object):
    def update(self, gameinfo):
        # Check if we should attack
        if gameinfo._my_planets() and gameinfo._not_my_planets():
            # Find the source planet with the MAXIMUM number of ships
            src = max(gameinfo._my_planets().values(), key=lambda p: p.ships)

            # Find a target planet with the MINIMUM number of ships
            dest = min(gameinfo._not_my_planets().values(), key=lambda p: p.ships)

            # Launch new fleet if there's enough ships
            if src.ships > 10:
                gameinfo.planet_order(src, dest, int(src.ships * 0.75))