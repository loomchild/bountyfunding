from itertools import ifilter

class Enum:

	@classmethod
	def items(cls):
		return dict(ifilter(lambda (k,v) : not k.startswith('__'), 
				vars(cls).iteritems()))
 
	@classmethod
	def values(cls):
		return sorted(cls.items().itervalues())
	
	@classmethod
	def keys(cls):
		return sorted(cls.items().iterkeys())

	@classmethod
	def to_string(cls, val):
		for k,v in vars(cls).iteritems():
			if v==val:
				return k

	@classmethod
	def from_string(cls, str):
		if str != None:
			return getattr(cls, str.upper(), None)
		else:
			return None

