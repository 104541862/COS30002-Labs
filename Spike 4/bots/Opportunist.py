from random import choice
from entities import NEUTRAL_ID

class Opportunist(object):
    def __init__(self):
        # Phase thresholds
        self.EARLY_LIMIT = 150
        self.LATE_LIMIT = 400

        # Behaviour tuning
        self.expansion_ratio = 0.5
        self.attack_ratio = 0.7
        self.defence_ratio = 0.6
        self.min_send = 5

    # Creates a list of threatening fleets for the bot to defend against.
    def threatened_planets(self, gameinfo):
        threats = {}

        for fleet in gameinfo.fleets.values():
            if fleet.owner != gameinfo.ID:  # enemy fleet
                dest = fleet.dest

                if dest.owner == gameinfo.ID:
                    if dest.ID not in threats:
                        threats[dest.ID] = 0
                    threats[dest.ID] += fleet.ships
        return threats

    # Update loop
    def update(self, gameinfo):
        
        # Updates the list of all planets, including both the bot's and the enemy's and neutral planets
        my_planets = list(gameinfo._my_planets().values())
        enemy_planets = list(gameinfo._enemy_planets().values())
        neutral_planets = list(gameinfo._neutral_planets().values())

        # Game over man, game over!
        if not my_planets:
            return
        
        # Takes the size of the bot's entire armada
        my_size = sum(p.ships for p in my_planets)
        # The source of all attacks is the bot's greatest planet
        src = max(my_planets, key=lambda p: p.ships)

        threats = self.threatened_planets(gameinfo)

        # Reinforce threatened planets
        for planet in my_planets:
            if planet.ID in threats:

                incoming = threats[planet.ID]

                # Only defend if we are likely to lose it
                if incoming > planet.ships:

                    # Find nearest reinforcement source
                    src_def = min(
                        my_planets,
                        key=lambda s: s.distance_to(planet) if s.ID != planet.ID else float('inf')
                    )

                    if src_def.ships > self.min_send:
                        gameinfo.planet_order(
                            src_def,
                            planet,
                            int(src_def.ships * self.defence_ratio)
                        )
                    return  # stop all other actions this tick

        # Early expansion and scouting logic
        if my_size < self.EARLY_LIMIT and neutral_planets:

            dest = min(neutral_planets, key=lambda p: p.ships)

            if src.ships > self.min_send:
                gameinfo.planet_order(
                    src,
                    dest,
                    int(src.ships * self.expansion_ratio)
                )
            return

        # Cleanup neutral planets
        if my_size < self.LATE_LIMIT and neutral_planets:

            dest = min(neutral_planets, key=lambda p: src.distance_to(p))

            if src.ships > self.min_send:
                gameinfo.planet_order(
                    src,
                    dest,
                    int(src.ships * 0.4)
                )
            return

        # Attacking enemy planet logic
        if enemy_planets:

            dest = min(enemy_planets, key=lambda p: p.ships)

            if src.ships > self.min_send:
                gameinfo.planet_order(
                    src,
                    dest,
                    int(src.ships * self.attack_ratio)
                )