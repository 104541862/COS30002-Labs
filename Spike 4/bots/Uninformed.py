from random import choice

class Uninformed(object):
    def update(self, gameinfo):

        my_planets = gameinfo._my_planets()
        neutral_planets = gameinfo._neutral_planets()
        enemy_planets = gameinfo._enemy_planets()

        # Game over man, game over!
        if not my_planets:
            return

        # Always send from the strongest planet
        src = max(my_planets.values(), key=lambda p: p.ships)

        # Don't send ships if there are less than 10
        if src.ships <= 10:
            return

        # Simply expand to the nearest neutral planet
        if neutral_planets:
            # Expand safely to the closest neutral planet
            dest = min(neutral_planets.values(), key=lambda p: src.distance_to(p))

            send_amount = int(src.ships * 0.5)

        # Attack enemies afterwards and only the weakest ones
        elif enemy_planets:
            dest = min(
                enemy_planets.values(),
                key=lambda p: p.ships
            )

            # Only attack if we are much stronger
            if src.ships <= dest.ships * 1.5:
                return

            send_amount = int(src.ships * 0.4)

        else:
            return

        # Minimum amount, just in case
        send_amount = min(send_amount, src.ships - 5)

        if send_amount > 0:
            gameinfo.planet_order(src, dest, send_amount)