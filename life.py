# MidiPlayground - Conway's Game of Life
# 
# Latest version available at: https://github.com/j3hyde/midiplayground
# 
# Copyright (c) 2015 Jeffrey Kyllo
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR
# ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import pypm, time, random, copy, argparse, sys, traceback

# Concept of views
# There is one root view which may delegate to sub-views.
# E.g. a view for the top and side buttons with another for the grid.
# The controller could then swap out/activate other views for the grid

class LifeView(object):
  '''Views basically listen to model changes and issue MIDI events to represent them.  Input is also taken from MIDI, interpreted a bit, and emitted as events by the View.'''
  def __init__(self, width=8, height=8, left=0, top=0):
    self.listeners = []
    self.width = width
    self.height = height
    self.left = left
    self.top = top

  def setitem(self, o, i, v):
    '''Listen for LifeModel changes.'''
    pass

  def handle_input(self):
    pass

  def add_listener(self, listener):
    self.listeners.append(listener)

class PrintingLifeView(LifeView):
  def setitem(self, o, i, v):
    print(o, i, v)

class UIDriver(object):
  def close(self):
    pass

  def get(self):
    return []

  def set(self, col, row, value):
    pass

  def clear(self, col=None, row=None):
    pass

  def commit(self):
    pass

  def close(self):
    pass

class UIInputEvent(object):
  '''Represents a UI event in "app space" meaning that coordinates are converted away from the raw device coordinates (i.e. in grid-space, not MIDI-space).  The value currently represents the value from the input device, however, until I define a suitable grid-space value domain.'''
  def __init__(self, col, row, value):
    self.col = col
    self.row = row
    self.value = value

class DebugDriver(UIDriver):
  def __init__(self, inner):
    self.inner = inner

  def get(self):
    self.log('get')
    if self.inner:
      return self.inner.get()
    else:
      return []

  def set(self, col, row, value):
    self.log('set({0}, {1}, {2})'.format(col, row, value))
    if self.inner:
      return self.inner.set(col, row, value)

  def clear(self, col=None, row=None):
    self.log('clear({0}, {1})'.format(col, row))
    if self.inner:
      return self.inner.clear()

  def commit(self):
    self.log('commit')
    if self.inner:
      return self.inner.commit()

  def close(self):
    self.log('close')
    if self.inner:
      return self.inner.close()

  def log(self, message):
    print(message)

class MidiDriver(UIDriver):
  '''Drives UI interactions with a MIDI device.  Currently implemented with the Novation Launchpad Mini grid controller.  Ideally more mappings would be supported.'''
  def __init__(self, in_device_id, out_device_id):
    print "Opening devices:"

    self.in_device = pypm.Input(in_device_id)
    print "\tin: {0}, {1}".format(in_device_id, self.in_device)

    self.out_device = pypm.Output(out_device_id)
    print "\tin: {0}, {1}".format(out_device_id, self.out_device)
    self.write_queue = []

  @classmethod
  def list_devices(cls):
    '''Queries the MIDI API for available devices.'''
    ret = []
    for i in range(pypm.CountDevices()):
      ret.append(pypm.GetDeviceInfo(i))
    return ret

  def get(self):
    '''Gets any available UIInputEvents from the attached MIDI device.'''
    events = []
    while self.in_device.Poll():
      for e in self.in_device.Read(1):
        coords = self.map_midi_to_ui(e[0][1])
        events.append(UIInputEvent(coords[0], coords[1], e[0][2]))
    return events

  def set(self, col, row, velocity=127):
    '''Sets the value of a light in the MIDI device's grid.'''
    index = self.map_ui_to_midi(col, row)
    self.write_queue.append([[144, index, velocity, 0], pypm.Time()])

  def clear(self, col=None, row=None):
    '''Clears the value of a light in the MIDI device's grid.'''
    if col is None and row is None:
      t = pypm.Time()
      self.write_queue += [ [[144, index, 0, 0], t] for index in range(8*16) ]
    else:
      index = self.map_ui_to_midi(col, row)
      self.write_queue.append([[144, index, 0, 0], pypm.Time()])

  def commit(self):
    '''Writes out the MIDI commands set up in set() and clear().  This must be called for those methods to take any actual effect.'''
    self.out_device.Write(self.write_queue)
    del self.write_queue[:]

  def close(self):
    self.in_device.Close()
    self.out_device.Close()

  @classmethod
  def map_ui_to_midi(cls, col, row):
    '''Maps Game of Life coordinates to MIDI note index.
    
    >>> MidiDriver.map_ui_to_midi(5, 5)
    85
    >>> MidiDriver.map_ui_to_midi(8, 0)
    8
    '''
    return row * 16 + col

  @classmethod
  def map_midi_to_ui(cls, note):
    '''Maps Game of Life coordinates to MIDI note index.
    
    >>> MidiDriver.map_midi_to_ui(85)
    (5, 5)
    >>> MidiDriver.map_midi_to_ui(84)
    (4, 5)
    >>> MidiDriver.map_midi_to_ui(80)
    (0, 5)
    >>> MidiDriver.map_midi_to_ui(64)
    (0, 4)
    >>> MidiDriver.map_midi_to_ui(65)
    (1, 4)
    '''
    return (note % 16, int(note / 16))


class MidiLifeView(LifeView):
  def __init__(self, *args, **kwargs):
    '''Takes a MIDI device to be used for displaying life.'''
    if kwargs.has_key('ui_driver'):
      ui_driver = kwargs.pop('ui_driver', None)
    elif len(args) > 0:
      ui_driver = args[0]
      args = args[1:]
    self.ui_driver = ui_driver

    super(MidiLifeView, self).__init__(*args, **kwargs)

  def setitem(self, o, i, v):
    if type(i) is str and i == 'paused':
      self.ui_driver.set(8, 0, 127 if bool(v) else 1)
    elif type(i) is tuple:
      self.ui_driver.set(i[0], i[1], v)

    self.ui_driver.commit()

  def handle_input(self):
    for event in self.ui_driver.get():
      for listener in self.listeners:
        listener(self, event)

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

    self._paused = False

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
    if type(i) is str and i == 'paused':
      return self._paused

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
    if type(i) is str:
      if i == 'paused':
        self._paused = bool(value)
      else:
        print 'got unexpected key: {0}'.format(i)
      return

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
    for listener in self._binding_listeners:
      listener(self, i, value)

class BoundLifeModel(ItemBindingMixin, LifeModel):
  pass

class Life(object):
  def __init__(self, uidriver, width=8, height=8):
    self.model = BoundLifeModel(width, height)
    #self.model.add_listener(PrintingLifeView().setitem)
    self.view = MidiLifeView(uidriver)
    self.view.add_listener(self.input_handler)
    self.model.add_listener(self.view.setitem)
    self.model.perturb(30)

  def run(self, speed=1):
    '''Runs a Life simulation and displays it in a view.'''
    # Link a View to our data model
    # Loop, ticking the simulation each second
    print 'running'
    next_tick = time.time()
    while True:
      now = time.time()
      if now >= next_tick and not self.model['paused']:
        next_tick = now + speed
        self.model.tick()
        print(self.model)
        print

      self.view.handle_input()
      time.sleep(0.1)

  def input_handler(self, source, uievent):
    if uievent.value == 0:
      return

    if uievent.row < 8 and uievent.col < 8 and uievent.row >= 0 and uievent.col >= 0:
      print('input: {0}, {1}, {2}'.format(uievent.col, uievent.row, uievent.value))
      v = self.model[uievent.col, uievent.row]
      self.model[uievent.col, uievent.row] = 1 if v == 0 else 0
    elif uievent.col == 8 and uievent.row == 0:
      self.model['paused'] = not self.model['paused']


def find_device(dev_name):
  n = pypm.CountDevices()
  in_device = None
  out_device = None
  for i in range(n):
    info = pypm.GetDeviceInfo(i)
    if info[1] == dev_name and info[2] == True:
      in_device = i
    if info[1] == dev_name and info[3] == True:
      out_device = i
  return (in_device, out_device)


def test():
  import unittest, doctest
  doctest.testmod()

def clear(out_device):
  for i in range(9*16):
    out_device.Write([[[144, i, 0, 0], pypm.Time()]])

def get_argparser():
  parser = argparse.ArgumentParser()
  parser.add_argument('--test', default=False, action='store_true')
  parser.add_argument('--list', action='store_true')
  parser.add_argument('--device')
  parser.add_argument('--indevice', type=int)
  parser.add_argument('--outdevice', type=int)
  parser.add_argument('--verbose', '-v', action='store_true')
  return parser

def get_config():
  return get_argparser().parse_args()

def print_help():
  get_argparser().print_help()

def main(config):
  pypm.Initialize()
  if config.device:
    d = find_device(config.device)
  else:
    d = (config.indevice, config.outdevice)
  if not d is None or not (d[0] is None or d[1] is None):
#    try:
#      in_device = pypm.Input(d[0])
#    except:
#      print("Error: Could not open input device.")
#      pypm.Terminate()
#      return
#
#    try:
#      out_device = pypm.Output(d[1])
#    except:
#      print("Error: Could not open output device.")
#      pypm.Terminate()
#      return
    print d
    uidriver = MidiDriver(d[0], d[1])
    if config.verbose:
      uidriver = DebugDriver(uidriver)

    try:
      time.sleep(2)
      print 'Life()'
      life = Life(uidriver)
      print 'run()'
      life.run(1)
      print 'Done.'
    except Exception as e:
      traceback.print_exc()
    finally:
      uidriver.clear()
      uidriver.close()
      pypm.Terminate()
      return
  else:
    print 'No input/output device found.  Exiting.'


if __name__ == '__main__':
  config = get_config()

  if config.test:
    test()
  elif config.list:
    devs = MidiDriver.list_devices()
    i = 0
    for dev in devs:
      print('{0} (id: {1}, in: {2}, out: {3})'.format(dev[1], i, dev[2] == 1, dev[3] == 1))
      i += 1
  elif not config.device is None or not (config.indevice is None or config.outdevice is None):
    main(config)
  else:
    print_help()
