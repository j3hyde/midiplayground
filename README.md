MidiPlayground
==============
This repo is a small collection of tools/toys to exercise python-portmidi with the Novation Launchpad Mini.  They are essentially works in progress but they do work.

I built them using the Launchpad Mini but I imagine they should work without modification (or very little) on the Launchpad and Launchpad Pro.  Other grid controllers are in the 'totally unknown' category but hopefully wouldn't be too hard to support.  I'd like to add a mapping mechanism to easily add new devices.

Checker
-------
The first toy displays an alternating checker pattern on the main grid.  This was the first test of "real" output on the device.  Run:

    python checker.py

Note that it is currently set with static MIDI device numbers from my system.  It should work given that you only have one Launchpad connected but a simple code change will let you use others.

MIDI Monitor
------------
This tool simply monitors a MIDI device and prints incoming events to the console.  It first prints a list of all the connected devices.  You have to edit the code file to change what device ID gets opened though.  Run:

    python midimon.py

Conway's Game of Life
---------------------
After writing to the device in Checker and reading from it in MIDI Monitor this toy combines the two and starts into a sort of MVC pattern with the MIDI device as the primary user interface.

Run `python life.py --help` to see a list of options.  If you are using a Launchpad Mini you can do `python life.py --device 'Launchpad Mini'` to use that device.

`life.py` runs an instance of Conway's Game of Life in an eight-by-eight grid.  This is displayed on the grid controller.  You can press any of the grid's buttons to toggle the value of that square.  Press the top-right button (Labeled 'A') to pause the simulation.  That makes it much easier to edit the simulation itself.

Installation/Environment
------------------------
I found it less than trivial to get my environment up and going, unfortunately.  It seems that although pyportmidi appears to be the most used it doesn't install on Windows with a simple `pip install pyportmidi`.

To ease this process I include instructions for building pyportmidi below.  However, [here]() is a pre-built Python wheel you can use instead.  You can download that and install using `pip install pyPortMidi-0.0.7-cp27-none-win32.whl` and it should *Just Work*.

Building PyPortMidi
-------------------
1. Download the PortMidi and PyPortMidi source
  * PortMidi is part of the PortMedia project.  The PortMidi downloads [are here](http://sourceforge.net/projects/portmedia/files/portmidi/) and the latest download as of this writing [is here](http://sourceforge.net/projects/portmedia/files/portmidi/217/portmidi-src-217.zip/download)
  * The original PyPortMedia by John Harrison [is here](http://alumni.media.mit.edu/~harrison/code.html) but Alexandre Quessy's "friendly fork" seems slightly more up-to-date with patches from the PyGame fork.  Downloads [are here](https://bitbucket.org/aalex/pyportmidi/downloads) and the latest download as of this writing [is here](https://bitbucket.org/aalex/pyportmidi/downloads/python-portmidi-0.0.7.tar.gz).

2. Build PortMidi
  * In my case I was building the PyPortMidi extension for Python 2.7 for some other library support reasons.  To build for Python 2.7 you need Microsoft Visual C++ 2008 (Express is okay) installed.  2008 can be a bit tricky to find - search for it or try [downloading here](https://www.microsoft.com/en-us/download/details.aspx?id=10986).
  * Moving right along, once you have the PortMidi source unpacked, look for and open the *portmidi.sln* solution.  You could build the whole thing but we just need the *portmidi-dynamic* project.  Set your build configuration to *Release* and build platform to *Win32*, right-click on the portmidi-dynamic project, and click *Build*.
  * We also need to build *porttime* but this isn't present in the solution.  Browse the source tree, open the *porttime* directory, then open the porttime project (*porttime.vcproj*).  Set the configuration and build to *Release* and *Win32* respectively then build.
  * Collect *portmidi.lib*, *portmidi.dll*, and *porttime.lib* files from the Release and porttime/Release directories and keep them handy for the next step.

3. Build PyPortMidi
  * Unpack the PyPortMidi source
  * Copy the *portmidi.lib*, *portmidi.dll*, and *porttime.lib* files from the last step into the PyPortMidi source directory
  * Install Pyrex (PyPortMidi is a native extension built using Pyrex)
  * Run `python setup.py build`

4. Install PyPortMidi
  The last step is to actually install PyPortMidi.  You could do this in a virtualenv or into your main Python installation.  Either way, from that point on you can use `import pypm` from your own projects.
