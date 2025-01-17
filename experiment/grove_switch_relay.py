#!/usr/bin/env python
#
# GrovePi Example for using the Grove Switch and the Grove Relay
#
# Modules:
# 	http://www.seeedstudio.com/wiki/Grove_-_Switch(P)
# 	http://www.seeedstudio.com/wiki/Grove_-_Relay
#
# The GrovePi connects the Raspberry Pi and Grove sensors.  You can learn more about GrovePi here:  http://www.dexterindustries.com/GrovePi
#
# Have a question about this example?  Ask on the forums here:  http://forum.dexterindustries.com/c/grovepi
#

'''
## License

The MIT License (MIT)

GrovePi for the Raspberry Pi: an open source platform for connecting Grove Sensors to the Raspberry Pi.
Copyright (C) 2017  Dexter Industries

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import os
import sys
sys.path.append(os.path.abspath('..'))

from utils.is_on_raspi import is_raspberry_pi

if not is_raspberry_pi():
    print('Warning: Only Raspberry Pi is supported!')
    exit(-1)

import time
import grovepi

# Connect the Grove Switch to digital port D3
# SIG,NC,VCC,GND
switch = 3

# Connect the Grove Relay to digital port D4
# SIG,NC,VCC,GND
relay = 4

grovepi.pinMode(switch, 'INPUT')
grovepi.pinMode(relay, 'OUTPUT')

print('Starting read loop...')

while True:
    try:
        if grovepi.digitalRead(switch):
            grovepi.digitalWrite(relay, 1)
            print('Relay on!')
        else:
            grovepi.digitalWrite(relay, 0)
            print('Relay off!')

        time.sleep(.01)

    except KeyboardInterrupt:
        grovepi.digitalWrite(relay, 0)
        print('Stopping read loop...')
        break
    except IOError as ioex:
        print(f'Error: {ex}')
