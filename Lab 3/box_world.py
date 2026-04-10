import math
from math import hypot
from enum import Enum
from graphics import COLOUR_NAMES, window
import pyglet
from point2d import Point2D
from graph import SparseGraph, Node, Edge
from searches import SEARCHES

box_types = {
	"CLEAR":{"symbol":'.', "cost":{"CLEAR":1, "MUD":2,"WATER":5}, "colour":"WHITE"},
	"MUD":{"symbol":'m', "cost":{"CLEAR":2, "MUD":4,"WATER":9}, "colour":"BROWN"},
	"WATER":{"symbol":'~', "cost":{"CLEAR":5, "MUD":9,"WATER":10}, "colour":"AQUA"},
	"WALL":{"symbol":'X', "colour":"GREY"},
}

# This value can be changed to match the scale of the box world if necessary
min_edge_cost = 1.0 

''' def edge_cost(k1, k2):
	k1 = box_type.index(k1)
	k2 = box_type.index(k2)
	return edge_cost_matrix[k1][k2] '''

search_modes = list(SEARCHES.keys())

class Box(object):
	# This class describes a box in the world and what it does

	def __init__(self,index, x, y, width, height, type='.'):

		self.x = x
		self.y = y
		self.index = index
		self.width = width
		self.height = height
		for key, value in box_types.items():
			if value['symbol'] == type:
				self.type = key

		def create_hexagon(cx, cy, radius):
			points = []
			for i in range(6):
				angle = math.radians(60 * i)
				x = cx + radius * math.cos(angle)
				y = cy + radius * math.sin(angle)
				points.append((x, y))
			return points
		
		hex_points = create_hexagon(self.x, self.y, self.width//2)

		# Draw hexagon
		self.box = pyglet.shapes.Polygon(
			*hex_points,
			color=COLOUR_NAMES[box_types[self.type]["colour"]], 
			#border_color=COLOUR_NAMES["GREY"],
			batch=window.get_batch()
		)

		# The label describes and shows the box's index
		self.label = pyglet.text.Label(
			str(index),
			font_name='Times New Roman',
			font_size=12,
			x=self.x, y=self.y,
			anchor_x='center', anchor_y='center',
			color=COLOUR_NAMES["BLACK"],
			batch=window.get_batch("numbers")
		)
		
		# Marker at the center
		self.center_marker = pyglet.shapes.Circle(
			self.x, self.y,
			radius=3,
			color=COLOUR_NAMES["BLACK"],
			batch=window.get_batch("centers")
		)
		
		# nav graph node
		self.node = None

	def set_type(self, type):
		# Function-in-function here for readability
		def update_box(type):
			self.type = type
			self.box.color = COLOUR_NAMES[box_types[self.type]["colour"]]
		if type in box_types:
			update_box(type)
			return
		else:
			for key, value in box_types.items():
				if value['symbol'] == type:
					update_box(key)
					return
		print('not a known tile type "%s"' % type)
	
	def center(self):
		return Point2D(self.x, self.y)
	
	def contains_point(self, px, py):
		points = self.box._coordinates
		inside = False

		j = len(points) - 1
		for i in range(len(points)):
			xi, yi = points[i]
			xj, yj = points[j]

			if ((yi > py) != (yj > py)) and \
			(px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi):
				inside = not inside

			j = i

		return inside

class BoxWorld(object):
	# This class describes the entire box world

	def __init__(self, x_boxes, y_boxes, window_width, window_height):
		self.boxes = [None]*x_boxes*y_boxes
		self.x_boxes= x_boxes 
		self.y_boxes= y_boxes 
		box_width = window_width // x_boxes
		box_height = window_height // y_boxes
		self.wx = (window_width-1) // self.x_boxes
		self.wy = (window_height-1) // self.y_boxes 

		HEX_SIZE = box_width / 2
		HEX_WIDTH = HEX_SIZE * 2
		HEX_HEIGHT = math.sqrt(3) * HEX_SIZE

		grid_width = (x_boxes - 1) * (HEX_WIDTH * 0.75) + HEX_WIDTH
		grid_height = y_boxes * HEX_HEIGHT + (HEX_HEIGHT / 2)

		offset_x = (window_width - grid_width) / 2
		offset_y = (window_height - grid_height) / 2

		for i in range(len(self.boxes)):
			col = i % x_boxes
			row = i // x_boxes

			x = col * (HEX_WIDTH * 0.75)
			y = row * HEX_HEIGHT

			if col % 2 == 1:
				y += HEX_HEIGHT / 2

			# Apply centering offset
			x += offset_x
			y += offset_y

			self.boxes[i] = Box(
				i,
				x,
				y,
				box_width,
				box_height
			)
		
		pyglet.shapes.Rectangle(
		offset_x,
		offset_y,
		grid_width,
		grid_height,
		color=(255, 0, 0),
		batch=window.get_batch()
		)

		# create nav_graph
		self.path = None
		self.graph = None
		
		self.start = self.boxes[1]
		self.start_marker = pyglet.shapes.Arc(
			self.boxes[1].center().x,
			self.boxes[1].center().y,
			15, segments=30,
			color=COLOUR_NAMES["RED"],
			batch=window.get_batch("path"),
			thickness=4
		)

		self.target = self.boxes[2]
		self.target_marker = pyglet.shapes.Arc(
			self.boxes[2].center().x,
			self.boxes[2].center().y,
			15, segments=30,
			color=COLOUR_NAMES["GREEN"],
			batch=window.get_batch("path"),
			thickness=4
		)

		#lists used to store the primitives that render out our various pathfinding data
		self.render_path = []
		self.render_tree = []
		self.render_open_nodes = []
		self.render_graph = []

		self.reset_navgraph()

	def get_box_by_xy(self, ix, iy):
		idx = (self.x_boxes * iy) + ix
		return self.boxes[idx] if idx < len(self.boxes) else None

	def get_box_by_pos(self, x, y):
		for box in self.boxes:
			if box.contains_point(x, y):
				return box
		return None

	def _add_edge(self, from_idx, to_idx, distance=1.0):
		b = self.boxes
		if "cost" in box_types[b[from_idx].type] and b[to_idx].type in box_types[b[from_idx].type]["cost"]:
			cost = box_types[b[from_idx].type]["cost"][b[to_idx].type]
			self.graph.add_edge(Edge(from_idx, to_idx, cost*distance))

	# Heuristic functions for calculation - Manhattan, Euclidean and Chebyshev
	def _manhattan(self, idx1, idx2):
		# Return the Manhattan cost for two points.
		x1, y1 = self.boxes[idx1].pos
		x2, y2 = self.boxes[idx2].pos
		return (abs(x1-x2) + abs(y1-y2)) * min_edge_cost

	def _hypot(self, idx1, idx2):
		# Return the Euclidean cost for two points.
		x1, y1 = self.boxes[idx1].pos
		x2, y2 = self.boxes[idx2].pos
		return hypot(x1-x2, y1-y2) * min_edge_cost

	def _max(self, idx1, idx2):
		# Return the Chebyshev cost for two points.
		x1, y1 = self.boxes[idx1].pos
		x2, y2 = self.boxes[idx2].pos
		return max(abs(x1-x2),abs(y1-y2)) * min_edge_cost


	def reset_navgraph(self):
		# Store the current boxworld config as a navgraph
		self.path = None # invalid so remove if present
		self.graph = SparseGraph()
		# Set a heuristic cost function for the search to use
		#self.graph.cost_h = self._manhattan
		self.graph.cost_h = self._hypot
		#self.graph.cost_h = self._max

		nx, ny = self.x_boxes, self.y_boxes
		# add all the nodes required
		for i, box in enumerate(self.boxes):
			box.pos = (i % nx, i // nx) #tuple position
			box.node = self.graph.add_node(Node(idx=i))

		for i, box in enumerate(self.boxes):
			if "cost" not in box_types[box.type]:
				continue

			col = i % nx
			row = i // nx

			# Odd-q vertical layout neighbors
			if col % 2 == 0:
				neighbors = [
					(col+1, row),     # right
					(col-1, row),     # left
					(col, row+1),     # up
					(col, row-1),     # down
					(col+1, row-1),   # upper-right
					(col-1, row-1),   # upper-left
				]
			else:
				neighbors = [
					(col+1, row),     # right
					(col-1, row),     # left
					(col, row+1),     # up
					(col, row-1),     # down
					(col+1, row+1),   # lower-right
					(col-1, row+1),   # lower-left
				]

			# Add valid edges
			for ncol, nrow in neighbors:
				if 0 <= ncol < nx and 0 <= nrow < ny:
					j = nrow * nx + ncol
					self._add_edge(i, j)
		
		# add the graph to the render_graph
		for line in self.render_graph:
			try:
				line.delete() #pyglets Line.delete method is slightly broken
			except:
				pass
		for start, edge in self.graph.edgelist.items():
			for target in edge.keys():
				self.render_graph.append(
					pyglet.shapes.Line(
						self.boxes[start].center().x, 
						self.boxes[start].center().y,
						self.boxes[target].center().x,
						self.boxes[target].center().y,
						thickness=1.0, 
						color=COLOUR_NAMES['PURPLE'],
						batch=window.get_batch("edges")
					)
				)

	def set_start(self, idx):
		'''Set the start box based on its index idx value. '''
		# remove any existing start node, set new start node
		if self.target == self.boxes[idx]:
			print("Can't have the same start and end boxes!")
			return
		self.start = self.boxes[idx]
		self.start_marker.x = self.start.center().x
		self.start_marker.y = self.start.center().y

	def set_target(self, idx):
		'''Set the target box based on its index idx value. '''
		# remove any existing target node, set new target node
		if self.start == self.boxes[idx]:
			print("Can't have the same start and end boxes!")
			return
		self.target = self.boxes[idx]
		self.target_marker.x = self.target.center().x
		self.target_marker.y = self.target.center().y

	def plan_path(self, search, limit):
		'''Conduct a nav-graph search from the current world start node to the
		current target node, using a search method that matches the string
		specified in `search`.
		'''
		cls = SEARCHES[search]
		self.path = cls(self.graph, self.start.index, self.target.index, limit)
		# print the path details
		print(self.path.report())
		#then add them to the renderer
		#render the final path
		for line in self.render_path:
			try:
				line.delete() #pyglets Line.delete method is slightly broken
			except:
				pass
		p = self.path.path # alias to save us some typing
		if(len(p) > 1):
			for idx in range(len(p)-1):
				self.render_path.append(
					pyglet.shapes.Line(
						self.boxes[p[idx]].center().x, 
						self.boxes[p[idx]].center().y,
						self.boxes[p[idx+1]].center().x,
						self.boxes[p[idx+1]].center().y,
						thickness=3, 
						color=COLOUR_NAMES['BLUE'],
						batch=window.get_batch("path")
					)
				)
		for line in self.render_tree:
			try:
				line.delete() #pyglets Line.delete method is slightly broken
			except:
				pass
		#render the search tree
		t = self.path.route # alias to save us some typing
		if(len(t) > 1):
			for start, end in t.items():
				self.render_tree.append(
					pyglet.shapes.Line(
						self.boxes[start].center().x, 
						self.boxes[start].center().y,
						self.boxes[end].center().x,
						self.boxes[end].center().y,
						thickness=2, 
						color=COLOUR_NAMES['PINK'],
						batch=window.get_batch("tree")
					)
				)
		for circle in self.render_open_nodes:
			try:
				circle.delete() #pyglets Line.delete method is slightly broken
			except:
				pass
		#render the nodes that were still on the search stack when the search ended
		o = self.path.open # alias to save us some typing
		if(len(o) > 0):
			for idx in o:
				self.render_open_nodes.append(
					pyglet.shapes.Circle(
						self.boxes[idx].center().x, 
						self.boxes[idx].center().y,
						5, 
						color=COLOUR_NAMES['ORANGE'],
						batch=window.get_batch("tree")
					)
				)


	@classmethod
	def FromFile(cls, filename ):
		'''Support a the construction of a BoxWorld map from a simple text file.
		See the module doc details at the top of this file for format details.
		'''
		# open and read the file
		f = open(filename)
		lines = []
		for line in f.readlines():
			line = line.strip()
			if line and not line.startswith('#'):
				lines.append(line)
		f.close()
		# first line is the number of boxes width, height
		nx, ny = [int(bit) for bit in lines.pop(0).split()]
		# Create a new BoxWorld to store all the new boxes in...
		world = BoxWorld(nx, ny, window.width, window.height)
		# Get and set the Start and Target tiles
		s_idx, t_idx = [int(bit) for bit in lines.pop(0).split()]
		world.set_start(s_idx)
		world.set_target(t_idx)
		# Ready to process each line
		assert len(lines) == ny, "Number of rows doesn't match data."
		# read each line
		idx = 0
		for line in reversed(lines): # in reverse order
			bits = line.split()
			assert len(bits) == nx, "Number of columns doesn't match data."
			for bit in bits:
				bit = bit.strip()
				world.boxes[idx].set_type(bit)
				idx += 1
		world.reset_navgraph()
		return world