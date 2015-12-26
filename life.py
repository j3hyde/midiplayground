import pypm, time, random, copy

# Concept of views
# There is one root view which may delegate to sub-views.
# E.g. a view for the top and side buttons with another for the grid.
# The controller could then swap out/activate other views for the grid

class LifeView(object):
  '''Views basically listen to model changes and issue MIDI events to represent them.  Input is also taken from MIDI, interpreted a bit, and emitted as events by the View.'''
  def setitem(self, o, i, v):
    '''Listen for LifeModel changes.'''
    pass

class PrintingLifeView(LifeView):
  def setitem(self, o, i, v):
    print(o, i, v)

class MidiLifeView(LifeView):
  def __init__(self, out_device):
    '''Takes a MIDI input device to be used for displaying life.'''
    self.out_device = out_device

  def setitem(self, o, i, v):
    index = self.map_item_to_midi(i[0], i[1])
    data = [[[144, index, v * 127, 0], pypm.Time()]]

    self.out_device.Write(data)

  def map_item_to_midi(self, col, row):
    '''Maps Game of Life coordinates to MIDI note index.
    
    >>> view = MidiLifeView(None)
    >>> view.map_item_to_midi(5, 5)
    85
    '''
    return row * 16 + col


class LifeModel(object):
  def __init__(self, width, height, data=None):
    '''
    >>> m = LifeModel(5, 5)
    >>> m[0, 0]
    0
    >>> m = LifeModel(5, 5, ( \
        (1, 0, 0, 0, 0), \
        (0, 0, 0, 0, 0), \
        (1, 0, 0, 0, 0), \
        (0, 0, 0, 0, 0), \
        (0, 0, 0, 0, 0)))
    >>> m[0, 0]
    1
    >>> m[1, 0]
    0
    >>> m[0, 2]
    1
    '''
    self.width = width
    self.height = height
    if data is None:
      self.model = [[0 for c in range(width)] for r in range(height)]
    else:
      self.model = [[data[r][c] for c in range(width)] for r in range(height)]

  def __getitem__(self, i):
    '''Enables two-dimensional access to the model.  The first index is the column, the second is the row.
    
    >>> m = LifeModel(5, 5)
    >>> m[2, 2]
    0
    >>> m[4, 0] = 1
    >>> m[-1, 0]
    1
    >>> m[-10, 0]
    Traceback (most recent call last):
        ...
    IndexError: Index out of range.
    >>> m[5]
    Traceback (most recent call last):
        ...
    TypeError: Expected a 2-tuple but got a <type 'int'> instead.
    >>> m[2, 2, 2]
    Traceback (most recent call last):
        ...
    TypeError: Expected a 2-tuple but got a 3-tuple instead.
    >>> m[1:2,2]
    Traceback (most recent call last):
        ...
    ValueError: Only int-value indices are supported.
    >>> m[5, 5]
    Traceback (most recent call last):
        ...
    IndexError: Index out of range.
    >>> m[4, 5]
    Traceback (most recent call last):
        ...
    IndexError: Index out of range.
    >>> m[5, 4]
    Traceback (most recent call last):
        ...
    IndexError: Index out of range.

    '''
    if not type(i) is tuple:
      raise TypeError("Expected a 2-tuple but got a {0} instead.".format(type(i)))

    if not len(i) is 2:
      raise TypeError("Expected a 2-tuple but got a {0}-tuple instead.".format(len(i)))

    col = i[0]
    row = i[1]

    if type(col) != int or type(row) != int:
      raise ValueError("Only int-value indices are supported.")

    if col < 0:
      col += self.width
    if row < 0:
      row += self.height

    if col < 0 or col >= self.width or row < 0 or row >= self.height:
      raise IndexError("Index out of range.")

    return self.model[row][col]
        
  def __setitem__(self, i, value):
    '''Enables two-dimensional access to the model.  The first index is the column, the second is the row.
    
    >>> m = LifeModel(5, 5)
    >>> m[2, 2] = 1
    >>> m[2, 2]
    1
    >>> m[4, 0]
    0
    >>> m[-1, 0] = 1
    >>> m[4, 0]
    1
    >>> m[-10, 0] = 1
    Traceback (most recent call last):
        ...
    IndexError: Index out of range.
    >>> m[5] = 1
    Traceback (most recent call last):
        ...
    TypeError: Expected a 2-tuple but got a <type 'int'> instead.
    >>> m[2, 2, 2] = 1
    Traceback (most recent call last):
        ...
    TypeError: Expected a 2-tuple but got a 3-tuple instead.
    >>> m[1:2,2] = 1
    Traceback (most recent call last):
        ...
    ValueError: Only int-value indices are supported.
    >>> m[5, 5] = 1
    Traceback (most recent call last):
        ...
    IndexError: Index out of range.
    >>> m[4, 5] = 1
    Traceback (most recent call last):
        ...
    IndexError: Index out of range.
    >>> m[5, 4] = 1
    Traceback (most recent call last):
        ...
    IndexError: Index out of range.
    '''
    if not type(i) is tuple:
      raise TypeError("Expected a 2-tuple but got a {0} instead.".format(type(i)))

    if not len(i) is 2:
      raise TypeError("Expected a 2-tuple but got a {0}-tuple instead.".format(len(i)))

    col = i[0]
    row = i[1]

    if type(col) != int or type(row) != int:
      raise ValueError("Only int-value indices are supported.")

    if col < 0:
      col += self.width
    if row < 0:
      row += self.height

    if col < 0 or col >= self.width or row < 0 or row >= self.height:
      raise IndexError("Index out of range.")

    self.model[row][col] = value

  def perturb(self, count=10):
    rand = random.Random()
    coords = set()
    while len(coords) < count:
      r = rand.randint(0, self.height-1)
      c = rand.randint(0, self.width-1)
      coords.add((c, r))
    for c in coords:
      self[c[0], c[1]] = 1



  def count_neighbors(self, col, row, data=None):
    '''Returns the number of neighboring cells with non-zero values.
    
    >>> m = LifeModel(5, 5, ( \
        (1, 1, 0, 0, 0), \
        (0, 0, 1, 0, 0), \
        (0, 0, 0, 0, 0), \
        (0, 0, 0, 0, 0), \
        (0, 0, 0, 0, 1)))
    >>> m.count_neighbors(1, 1)
    3
    >>> m.count_neighbors(0, 0)
    1
    >>> m.count_neighbors(0, 4)
    0
    >>> m.count_neighbors(4, 4)
    0
    >>> m.count_neighbors(3, 4)
    1
    >>> m.count_neighbors(4, 3)
    1
    >>> m = LifeModel(5, 5, ( \
        (1, 0, 1, 1, 1), \
        (1, 0, 0, 0, 1), \
        (0, 0, 0, 0, 0), \
        (0, 0, 0, 1, 1), \
        (0, 0, 0, 1, 1)))
    >>> m.count_neighbors(0, 0)
    1
    >>> m.count_neighbors(0, 1)
    1
    >>> m.count_neighbors(0, 2)
    1
    >>> m.count_neighbors(0, 3)
    0
    >>> m.count_neighbors(0, 4)
    0
    >>> m.count_neighbors(1, 0)
    3
    >>> m.count_neighbors(1, 1)
    3
    >>> m.count_neighbors(1, 2)
    1
    >>> m.count_neighbors(1, 3)
    0
    >>> m.count_neighbors(1, 4)
    0
    >>> m.count_neighbors(2, 0)
    1
    >>> m.count_neighbors(2, 1)
    2
    >>> m.count_neighbors(2, 2)
    1
    >>> m.count_neighbors(2, 3)
    2
    >>> m.count_neighbors(2, 4)
    2
    >>> m.count_neighbors(3, 0)
    3
    >>> m.count_neighbors(3, 1)
    4
    >>> m.count_neighbors(3, 2)
    3
    >>> m.count_neighbors(3, 3)
    3
    >>> m.count_neighbors(3, 4)
    3
    >>> m.count_neighbors(4, 0)
    2
    >>> m.count_neighbors(4, 1)
    2
    >>> m.count_neighbors(4, 2)
    3
    >>> m.count_neighbors(4, 3)
    3
    >>> m.count_neighbors(4, 4)
    3
    
    '''
    if data is None:
      data = self.model
    candidates = set()
    for r in range(row-1, row+2):
      for c in range(col-1, col+2):
        if r < self.height and r >= 0 and c < self.width and c >= 0:
          candidates.add((c, r))
    candidates.remove((col, row))

    return sum([data[c[1]][c[0]] for c in candidates])

  def __eq__(self, other):
    '''Checks that each element of two LifeModels is equal.

    >>> m1 = LifeModel(5, 5)
    >>> m2 = LifeModel(4, 4)
    >>> m1 == m2
    False
    >>> m2 = LifeModel(5, 5)
    >>> m1 == m2
    True
    >>> m1 = LifeModel(5, 5, ( \
        (1, 1, 0, 0, 0), \
        (0, 0, 1, 1, 1), \
        (0, 0, 0, 0, 1), \
        (0, 0, 0, 0, 1), \
        (0, 0, 0, 1, 1)))
    >>> m2 = LifeModel(5, 5, ( \
        (0, 1, 0, 0, 0), \
        (0, 0, 1, 1, 1), \
        (0, 0, 0, 0, 1), \
        (0, 0, 0, 0, 1), \
        (0, 0, 0, 1, 1)))
    >>> m2[0, 0] = 1
    >>> m1 == m2
    True
    '''
    if self.width != other.width or self.height != other.height:
      return False

    for c in range(self.width):
      for r in range(self.height):
        if self[c, r] != other[c, r]:
          return False
    return True

  def tick(self):
    '''Applies the rules of Life to the model, returning a new model in the process.

    >>> m = LifeModel(5, 5, ( \
        (1, 1, 1, 1, 1), \
        (1, 1, 0, 0, 1), \
        (0, 0, 0, 0, 0), \
        (0, 0, 0, 0, 1), \
        (1, 1, 0, 1, 1)))
    >>> print str(m) # 0
    ((1, 1, 1, 1, 1),
     (1, 1, 0, 0, 1),
     (0, 0, 0, 0, 0),
     (0, 0, 0, 0, 1),
     (1, 1, 0, 1, 1))
    >>> m.count_neighbors(0, 2)
    2
    >>> m.count_neighbors(0, 3)
    2
    >>> m.count_neighbors(0, 4)
    1
    >>> m.tick()
    >>> print str(m) # 1
    ((1, 0, 1, 1, 1),
     (1, 0, 0, 0, 1),
     (0, 0, 0, 0, 0),
     (0, 0, 0, 1, 1),
     (0, 0, 0, 1, 1))
    >>> m.tick()
    >>> print str(m) # 2
    ((0, 1, 0, 1, 1),
     (0, 1, 0, 0, 1),
     (0, 0, 0, 1, 1),
     (0, 0, 0, 1, 1),
     (0, 0, 0, 1, 1))
    >>> m.tick()
    >>> print str(m) # 3
    ((0, 0, 1, 1, 1),
     (0, 0, 0, 0, 0),
     (0, 0, 1, 0, 0),
     (0, 0, 1, 0, 0),
     (0, 0, 0, 1, 1))
    '''
    last_model = copy.deepcopy(self.model)
    for row in range(self.height):
      for col in range(self.width):
        neighbors = self.count_neighbors(col, row, data=last_model)
        if last_model[row][col] == 1:
          if neighbors < 2: # underpopulated; die off
            self[col, row] = 0
          elif neighbors <= 3: # just right - stay alive
            self[col, row] = 1
            pass
          else: # overpopulated; die off
            self[col, row] = 0
        else:
          if neighbors == 3: # reproduction
            self[col, row] = 1
          else: # stay dead
            self[col, row] = 0
            pass

  def __str__(self):
    return "({0})".format(",\n ".join(["({0})".format(", ".join([str(c) for c in row])) for row in self.model] ))


class ItemBindingMixin(object):
  def __init__(self, *args, **kwargs):
    super(ItemBindingMixin, self).__init__(*args, **kwargs)
    self._binding_listeners = []

  def add_listener(self, listener):
    '''Addes a callable to the list of listeners.  The callable should take three arguments: the object emitting the message, the __setitem__ index, and the new value.'''
    self._binding_listeners.append(listener)

  def __setitem__(self, i, value):
    super(ItemBindingMixin, self).__setitem__(i, value)
    for l in self._binding_listeners:
      l(self, i, value)

class BoundLifeModel(ItemBindingMixin, LifeModel):
  pass

class Life(object):
  def __init__(self, out_device, width=8, height=8):
  #def __init__(self, width=8, height=8):
    self.out_device = out_device
    self.model = BoundLifeModel(width, height)
    #self.model.add_listener(PrintingLifeView().setitem)
    self.model.add_listener(MidiLifeView(self.out_device).setitem)
    self.model.perturb(30)

  def run(self, speed=1):
    '''Runs a Life simulation and displays it in a view.'''
    # Link a View to our data model
    # Loop, ticking the simulation each second
    while True:
      self.model.tick()
      print(self.model)
      print
      time.sleep(speed)

def find_device():
  n = pypm.CountDevices()
  for i in range(n):
    info = pypm.GetDeviceInfo(i)
    if info[1] == 'Launchpad Mini' and info[3] == 1:
      return i
  return None


def test():
  import unittest, doctest
  doctest.testmod()

def clear(out_device):
  for i in range(9*16):
    out_device.Write([[[144, i, 0, 0], pypm.Time()]])


if __name__ == '__main__':
  test()
  pypm.Initialize()
  d = find_device()
  if d:
    out_device = pypm.Output(d)
    try:
        time.sleep(2)
        Life(out_device).run(1)
    finally:
      clear(out_device)
      out_device.Close()
      pypm.Terminate()
  else:
    print 'No output device found.  Exiting.'
