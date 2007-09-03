
from graphication.css import hex_to_rgba


class OrderedDict(object):
	
	def __init__(self, pairs):
		self.dict = {}
		self.ordered = []
		for key, value in pairs:
			self.dict[key] = value
			self.ordered.append(key)
	
	def order(self):
		self.ordered = self.dict.keys()
		self.ordered.order()
	
	def keys(self):
		return self.ordered
	
	def values(self):
		return [self.dict[x] for x in self.ordered]
	
	def items(self):
		return [(x, self.dict[x]) for x in self.ordered]
	
	def __getitem__(self, key):
		return self.dict[key]
	
	def __setitem__(self, key, value):
		self.dict[key] = value
		if key not in self.dict:
			self.ordered.append(key)



class Series(object):
	
	"""Holds one set of data, with keys, values and a title."""
	
	def __init__(self, title, data, color="#000000ff"):
		self.title = title
		self.data = data
		self.color = color.replace("#", "")
	
	
	def color_as_rgba(self):
		return hex_to_rgba(self.color)
	
	
	def keys(self):
		return map(lambda (x,y): x, self.items())
	
	
	def values(self):
		return map(lambda (x,y): y, self.items())
	
	
	def items(self):
		items = self.data.items()
		items.sort()
		return items
	
	
	def key_range(self):
		keys = self.data.keys()
		return min(keys), max(keys)
	
	
	def value_range(self):
		values = self.data.values()
		return min(values), max(values)
	
	
	def __iter__(self):
		return iter(self.data)
	
	
	def __getitem__(self, key):
		return self.values[key]
	
	
	def __len__(self):
		return len(self.values)
	
	
	def interpolate(self, key):
		"""
		Returns the value at 'key', with linear interpolation, and
		constant extrapolation.
		"""
		
		keys = self.keys()
		
		if not keys:
			raise ValueError("No values to interpolate between.")
		
		if key in keys:
			return self.data[key]
		
		pre = keys[0]
		post = None
		
		# Check to see if it needs to be extrapolated below.
		if key < pre:
			return self.data[pre]
		
		# Get the two values above and below it
		for a_key in keys:
			if a_key > key:
				post = a_key
				break
			else:
				pre = a_key
		
		# Extrapolate above?
		if post is None:
			return self.data[pre]
		
		# Interpolate
		range = post - pre
		pc = (key - pre) / float(range)
		
		bottom = self.data[pre]
		top = self.data[post]
		vrange = top - bottom
		return top + (vrange * pc)



class SeriesSet(object):
	
	"""
	SeriesSets hold zero or more Series.
	They have useful operations such as overall maxima, minima, etc.
	Iterating over one will yield the series one-by-one.
	"""
	
	def __init__(self, series=[]):
		self.series = series
	
	
	def __iter__(self):
		return iter(self.series)
	
	
	def add_series(self, series):
		self.series.append(series)
	
	
	def key_range(self):
		mins, maxs = zip(*[series.key_range() for series in self.series])
		return min(mins), max(maxs)
	
	
	def value_range(self):
		mins, maxs = zip(*[series.value_range() for series in self.series])
		return min(mins), max(maxs)
	
	
	def keys(self, with_series=False):
		"""
		Returns all possible keys, in order.
		If 'with_series' is true, returns them as tuples, with the second element being the list
		of series they appear in.
		"""
		
		# TODO: This could be made a bit more efficient.
		
		keys = {}
		for series in self.series:
			for key in series.keys():
				keys[key] = keys.get(key, []) + [series]
		
		if with_series:
			keys = keys.items()
		else:
			keys = keys.keys()
		keys.sort()
		return keys
	
	
	def stack(self, key):
		"""Returns a list of (series, value-at-key) tuples for the series."""
		
		return map(lambda x:(x,x.interpolate(key)), self.series)
	
	
	def stacks(self):
		"""Returns a list of (key, stack) for each possible key."""
		
		return map(lambda x:(x, self.stack(x)), self.keys())
	
	
	def totals(self):
		"""Generates a list of (key, total-at-key) tuples, in key order."""
		
		for key in self.keys():
			yield key, sum(map(lambda x:x.interpolate(key), self.series))



class MultiSeries(object):
	
	"""A MultiSeries holds one or more sets of data points, 
	which all share common key values."""
	
	def __init__(self, keys):
		
		"""Constructor. Creates a MultiSeries, which you can add series to using add_series.
		
		@param keys: The key values for these series
		@type keys: list
		"""
		
		assert self.distinct(keys), "You must pass a list of keys which has distinct values."
		
		try:
			self.keys = map(float, keys)
		except ValueError:
			raise ValueError("All keys must be numeric")
		
		self.keys.sort()
		self.series = []
	
	
	def distinct(self, list):
		for i in range(len(list)):
			if list.index(list[i]) != i:
				return False
		return True
	
	
	def add_series(self, series):
		assert len(series) == len(self.keys), "You must pass the right size SubSeries for the number of keys."
		self.series.append(series)
	
	
	def items(self):
		
		"""Generator, which yields tuples of (key, [value, ...])"""
		
		for i in range(len(self.keys)):
			key = self.keys[i]
			values = []
			for serie in self.series:
				values.append(serie[i])
			yield (key, values)
	
	
	def get(self, key):
		
		"""Returns a list of values for the given key."""
		
		i = self.keys.index(key)
		
		return [serie[i] for serie in self.series]
	
	
	def get_series(self, index):
		
		"""Returns the series at the given index."""
		
		return self.series[index]
	
	
	def totals(self):
		
		"""Returns a list of sums of each key's values"""
		
		totals = []
		for (key, values) in self.items():
			totals.append(sum(values))
		return totals
	
	
	def titles(self):
		
		"""Returns an iterable of series titles, in order."""
		
		for serie in self.series:
			yield serie.title



class Node(object):
	
	"""
	Represents a node in a structure diagram.
	Has a single value, as well as attributes like title and color.
	"""
	
	def __init__(self, value, title="Node", color="#036"):
		
		self.value = value
		self.title = title
		self.color = color



class NodeLink(object):
	
	"""
	Represents a link between to Nodes.
	"""
	
	def __init__(self, start, end, weight=1, color="#600"):
		
		self.start = start
		self.end = end
		self.weight = weight
		self.color = color


class NodeSet(object):
	
	"""
	Contains many Nodes, as well as the relationships that link them together.
	"""
	
	def __init__(self):
		
		self.nodes = []
		self.links = []
	
	
	def add_node(self, node):
		"""Adds the given Node to the NodeSet."""
		self.nodes.append(node)
	
	
	def add_link(self, link):
		"""Links the first node to the second. Note that in some graphs, order might matter."""
		assert isinstance(link, NodeLink), "You must pass in a NodeLink"
		assert link.start in self.nodes, "The first node is not in this NodeSet."
		assert link.end in self.nodes, "The second node is not in this NodeSet."
		self.links.append(link)
	
	
	def adjacent_to(self, node, both=True):
		"""Returns a generator of all (othernode, link) tuples that are linked to this Node.
		
		@param node: The node to return nodes adjacent to.
		@param both: If we should use links in either direction (True) or only ones away (False)."""
		
		for link in self.links:
			if link.start == node:
				yield link.end, link
			elif link.end == node and both:
				yield link.start, link
	
	
	def value_range(self):
		"""Returns a tuple of (min, max, range) for the set of value values."""
		values = [node.value for node in self.nodes]
		this_max = max(values)
		this_min = min(values)
		return (this_min, this_max, this_max-this_min)
	
	
	def __iter__(self):
		return iter(self.nodes)
	
	
	def __getitem__(self, key):
		return self.nodes[key]