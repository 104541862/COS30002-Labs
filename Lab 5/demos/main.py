"""Deceptive PlanetWars Simulation — entry point and CLI.

This module handles command-line argument parsing, game-state loading (from map
or replay JSON files), and bootstraps the simulation by either launching the
graphical (pyglet) window or running a headless game loop.

Created by
    Michael Jensen (2011)
    Clinton Woodward (2012)
    James Bonner (2023/4)
    contact: jbonner@swin.edu.au

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""

from planet_wars import PlanetWarsGame

import argparse
import json
import pathlib
import uuid
import collections
import datetime

if __name__ == "__main__":
	# ---- CLI argument definitions ----
	parser = argparse.ArgumentParser(
		prog="PlanetWars",
		description=""" 
				Deceptive PlanetWars Simulation

					Created by 
					Michael Jensen (2011)
					Clinton Woodward (2012)
					James Bonner (2023/4)
					contact: jbonner@swin.edu.au""",
		formatter_class=argparse.RawDescriptionHelpFormatter,
	)
	parser.add_argument(
		"-p",
		"--players",
		nargs="*",
		help="Players in this run. Should be the name (no extension) of file found in /bots. Ignored if the map or replay has players hardcoded.",
	)
	parser.add_argument(
		"-m",
		"--map",
		help="Filename (no extension) of map to play on. If not supplied, a random map is generated for play.",
	)
	# parser.add_argument(
	# 	"-g",
	# 	"--generate",
	# 	help="Generate a new random map. Outputs the json for the map to the filename provided.",
	# )
	parser.add_argument(
		"-r",
		"--replay",
		help="Filename (no extension) of replay to run. Does nothing without either --gui or --logscript being provided",
	)
	parser.add_argument(
		"--gui", help="Runs with the graphical output", action="store_true"
	)
	parser.add_argument(
		"--logscript",
		help="Adds a log output script. Could be used to make game ticks/actions human readable or to print statistics about the game states.",
	)
	parser.add_argument(
		"--save-replay",
		nargs="?",
		default=argparse.SUPPRESS,
		help="Saves a replay. Optional: filename (no extension) to save the replay to. If not provided, the replay is saved to the replays directory with a UUID filename.",
	)
	parser.add_argument(
		"--max-ticks",
		type=int,
		default=10000,
		help="Maximum number of game ticks before the simulation ends.",
	)
	args = parser.parse_args()

	# ---- Validate mutually exclusive source options ----
	if args.map and args.replay:
		print("Cannot use both --map and --replay")
		exit()

	# ---- Load the game state from a map or replay JSON file ----
	if args.map or args.replay:
		filename = args.map or args.replay
		if args.map:
			filename = pathlib.PurePath().joinpath('maps').joinpath(filename + ".json")
		if args.replay:
			filename = pathlib.PurePath().joinpath('replays').joinpath(filename + ".json")
		f = open(filename, "r+")
		gamestate = json.loads(f.read())
	else:
		# No map or replay was provided — cannot continue without one.
		# TODO: generate a random map here in future.
		print(
			"No map or replay specified. Use -m <map_name> or -r <replay_name>."
		)
		exit()

	# ---- Ensure players are specified (either in the file or via CLI) ----
	if not "players" in gamestate:
		if not args.players:
			print(
				"Players not specified in the map/replay, or on the command line. To run with this map/replay, specify the players using -p."
			)
			exit()
		gamestate["players"] = []
		for player in args.players:
			gamestate["players"].append({"ID": str(uuid.uuid1()), "name": player})

	if(args.max_ticks):
		gamestate["max_ticks"] = args.max_ticks

	# ---- Optional replay recording ----
	replay_object = None
	if not args.replay and hasattr(args, "save_replay"):
		replay_object = collections.defaultdict(list)
		

	# ---- Create the game instance ----
	game = PlanetWarsGame(gamestate, args.logscript, replay_object)

	def write_replay():
		"""Write the recorded replay data to a JSON file.

		The replay filename is determined by priority:
		  a) --save-replay was not passed at all → no replay to save
		  b) --save-replay <name> → save to that filename
		  c) --save-replay (no value) → auto-name from players + timestamp
		"""
		if replay_object:
			try:
				if args.save_replay:
					replay_file = open(pathlib.PurePath().joinpath('replays').joinpath(args.save_replay + ".json"), "w")
				else:
					filename = "".join(gamestate["players"])+str(datetime.datetime.now())+".json"
					replay_file = open(pathlib.PurePath().joinpath('replays').joinpath(filename), "w")
				replay_file.write(json.dumps(replay_object))
			except:
				pass

	# ---- Run with GUI or headless ----
	if args.gui:
		from planet_wars_draw import PlanetWarsWindow
		window = PlanetWarsWindow(game)
	else:
		game.paused = False
		while game.is_alive() and game.tick < game.max_ticks:
			game.update()
	write_replay()
