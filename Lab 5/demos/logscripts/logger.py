"""PlanetWars logger — writes match data to log files.

During game play log calls are stored in memory. When ``flush()`` is called
any data logged is written to one of the following log files:

- ``results``   — contains the match result (win/loss score)
- ``turns``     — contains turn-by-turn details
- ``errors``    — contains any errors logged during the match
- ``player_id`` — player log details, one file for each player

If messages have not been logged the corresponding file is not created.

Comments and code refactored by Enrique Ketterer <ekettererortiz@swin.edu.au>
- S1 2026

For class use only. Do not publicly share or post this code without permission.
"""

from collections import defaultdict


class Logger(object):
	"""File-based logger for PlanetWars match data."""

	def __init__(self, filename_pattern):
		"""Create a logger that writes to files matching the pattern.

		Args:
			filename_pattern: Must contain one ``%s`` which will be replaced
				with the name of each log file (e.g. 'results', 'turns').
		"""
		self._pattern = filename_pattern
		self._results = []
		self._turns = []
		self._errors = []
		self._players = defaultdict(list)

	def flush(self):
		"""Write all accumulated log data to their respective files."""

		def flushit(name, data):
			if data:
				f = open(self._pattern % name, 'w')
				f.writelines(data)
				f.close()

		flushit('results', self._results)
		flushit('turns', self._turns)
		flushit('errors', self._errors)

		for k, v in self._players.items():
			flushit('player' + str(k), v)

	def _append_message(self, log, message):
		"""Ensure messages are newline-terminated and append to the log."""
		if message[-1] != "\n":
			message = message + "\n"
		log.append(message)

	def result(self, message):
		"""Log a match result message."""
		self._append_message(self._results, message)

	def turn(self, message):
		"""Log a turn result message."""
		self._append_message(self._turns, message)

	def player(self, player_id, message):
		"""Log a player-specific message."""
		self._append_message(self._players[player_id], message)

	def get_player_logger(self, player_id):
		"""Return a closure that logs messages for a specific player.

		This wraps (decorates) the ``player()`` method with a fixed
		player_id, so callers don't need to pass it each time.
		"""
		def player_log(message):
			self.player(player_id, message)
		return player_log

	def error(self, message):
		"""Log an error message."""
		self._append_message(self._errors, message)
