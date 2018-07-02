#!/usr/bin/python
from gpiozero import InputDevice
import time

print "Start"

redLED = InputDevice(19)
powerlow=0
while True:
        if redLED.is_active:
                print "POWER dipped below 4.63v"
                powerlow += 1
        else:
                print "OK"
                powerlow =0
        if (powerlow  > 3):
                print "Low power for " + str(powerlow) + " seconds"
        time.sleep(1)
