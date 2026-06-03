"""
D-LEVEL CUSTOM PROJECT - Map Loader Module
This module defines the MapLoader class, which is responsible for loading map data from text files.
The map files use a simple character-based format to define player spawn points, enemy spawns, walls, and holes.
"""

class MapData:
    def __init__(self):
        self.player_spawn = None
        self.enemy_spawns = []   # (pos, type)
        self.walls = []
        self.holes = []
        self.air = []


class MapLoader:
    ENEMY_TYPES = {
        "B": "brown",
        "G": "grey",
        "T": "teal",
        "Y": "yellow",
        "R": "red",
        "N": "green",
        "P": "purple",
        "W": "white",
        "K": "black",
    }

    def load(self, filename, tile_size=40):
        map_data = MapData()

        with open(filename, "r") as f:
            lines = [line.rstrip("\n") for line in f]

        height = len(lines)

        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                world_x = x * tile_size
                world_y = (height - y - 1) * tile_size

                pos = (world_x, world_y)
                agent_pos = (world_x + tile_size / 2, world_y + tile_size / 2)

                if char == "*":
                    map_data.player_spawn = agent_pos

                elif char in self.ENEMY_TYPES:
                    map_data.enemy_spawns.append((agent_pos, char))

                elif char == "/":
                    map_data.walls.append(pos)

                elif char == "H":
                    map_data.holes.append(pos)

                elif char == ".":
                    map_data.air.append(pos)

        return map_data