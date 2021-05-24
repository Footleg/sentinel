#!/usr/bin/env python3
""" PWM outputs test for the Footleg Robotics Sentinel robot controller board
    Cycles a bank of 4 PWM outputs through various duty cycles.
    Uses the low level hardware interface class directly, so have to
    send pulses watchdog pin to keep pwm alive.
"""

import sys
from time import sleep
import digitalio
from sentinelboard import SentinelHardware

if len(sys.argv) > 1:
    bank = int(sys.argv[1])
else:
    #Set bank of pwm outsputs to test (0 - 2)
    bank = 0

sh = SentinelHardware()

watchdogPin = 7


#Configure IO for watchdog pin
p = sh.mcp23017.get_pin(watchdogPin)
p.direction = digitalio.Direction.OUTPUT
p.value = False

# Cycle bank of pwm outputs from 0 to 100 duty cycle in turn
for c in range( (bank*4), (bank*4 + 4) ):
    print(f"Channel {c}")
    for p in range (0,100,5):
        # Keep watchdog alive by briefly pulsing input high
        sh.mcp23017.get_pin(watchdogPin).value = True
        sleep(0.01)
        sh.mcp23017.get_pin(watchdogPin).value = False

        #Set duty cycle
        sh.setPercentageOn(c,p)
        sleep(0.1)

    sh.setPercentageOn(c,0)

# Turn off all outputs
sh.allOff()
sleep(0.5)

# Test watchdog disables pwm outputs if not kept alive
for c in range( (bank*4), (bank*4 + 4) ):
    sh.setConstantOn(c)

for i in range(5):
    # Keep watchdog alive by briefly pulsing input high
    sh.mcp23017.get_pin(watchdogPin).value = True
    sleep(0.01)
    sh.mcp23017.get_pin(watchdogPin).value = False
    # Sleep a short enough time that watchdog does not disable outputs
    print("Sleeping <1s so watchdog stays alive")
    sleep(0.8)

for i in range(5):
    # Keep watchdog alive by briefly pulsing input high
    sh.mcp23017.get_pin(watchdogPin).value = True
    sleep(0.01)
    sh.mcp23017.get_pin(watchdogPin).value = False
    # Sleep a long enough time that watchdog does disable outputs
    print("Sleeping >1s so watchdog disables pwm outputs")
    sleep(1.5)

# Turn off all outputs
sh.allOff()