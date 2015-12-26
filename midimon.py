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
