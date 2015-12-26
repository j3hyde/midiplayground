import pypm
import time
import random

class Checker(object):
  def __init__(self, wait=1, in_device_id=1, out_device_id=3):
    self.wait = wait
    self.in_device_id = in_device_id
    self.out_device_id = out_device_id

  def run(self):
    self.running = True
    pypm.Initialize()
    self.in_device = pypm.Input(self.in_device_id)
    self.out_device = pypm.Output(self.out_device_id)

    self.clear()

#    try:
#      while self.running:
#        self.read_buttons()
#    finally:
#      print("Shutting down.")
#      self.in_device.Close()
#      self.out_device.Close()
#      pypm.Terminate()
#
#    return

    try:
      while self.running:
        self.set_pattern(0)
        time.sleep(self.wait)
        self.set_pattern(1)
        time.sleep(self.wait)

    finally:
      print("Shutting down.")
      self.clear()
      self.in_device.Close()
      self.out_device.Close()
      pypm.Terminate()

  def read_buttons(self):
    while self.in_device.Poll():
      events = self.in_device.Read(50)
      for e in events:
        print e

      self.out_device.Write(events)


  def set_pattern(self, on):
    t = pypm.Time()
    data = []
    for r in range(0, 113, 16): 
      even = 127 if bool(on) else 0
      odd = 0 if bool(on) else 127
      on = not on
      for n in range(r, r+8, 2):
        data.append([[144, n, even, 0], t])
        data.append([[144, n+1, odd, 0], t])
    random.shuffle(data)
    self.out_device.Write(data)

  def set_all(self, value):
    t = pypm.Time()
    data = []
    for n in range(0, 136):
      data.append([[144, n, value, 0], t])
    self.out_device.Write(data)

  def clear(self):
    self.set_all(0)

  def stop(self):
    self.running = False


if __name__ == '__main__':
  Checker().run()
