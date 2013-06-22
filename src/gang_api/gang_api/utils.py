class Enum:

  @classmethod
  def to_string(cls, val):
    for k,v in vars(cls).iteritems():
        if v==val:
            return k

  @classmethod
  def from_string(cls, str):
      return getattr(cls, str.upper(), None)	
