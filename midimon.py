# MidiPlayground - MIDI Monitor
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


import pypm, time

def find_device():
  count = pypm.CountDevices()
  print 'Found {0} devices'.format(count)
  in_dev, out_dev = (None, None)
  for i in range(count):
    info = pypm.GetDeviceInfo(i)
    print info
    if info[1] == 'Launchpad Mini':
      if info[2] == 1:
        print 'Opening input {0}'.format(i)
        in_dev = pypm.Input(i)
      if info[3] == 1:
        print 'Opening output {0}'.format(i)
        out_dev = pypm.Output(i)
  return (in_dev, out_dev)

if __name__ == '__main__':
  pypm.Initialize()

  in_dev, out_dev = find_device()
  print in_dev, out_dev
  print 'Ready to read inputs.'
  if in_dev and out_dev:
    try:
      while True:
        while in_dev.Poll():
          events = in_dev.Read(50)
          print [(e[0][1], e[0][2]) for e in events]
          out_dev.Write(events)
        time.sleep(0.1)
    finally:
      pypm.Terminate()
  else:
    print "Couldn't find suitable device.  Exiting."
