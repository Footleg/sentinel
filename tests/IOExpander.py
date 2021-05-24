#!/usr/bin/env python3
""" Test case for the Footleg Robotics Sentinel robot controller board
    Pulses all IO expander pins configured as outputs
"""

from time import sleep
import digitalio
from sentinelboard import SentinelHardware

sh = SentinelHardware()

# Set all pins as outputs, setting them LOW
for pin in range(16):
    p = sh.mcp23017.get_pin(pin)
    p.direction = digitalio.Direction.OUTPUT
    p.value = False

# Pulse each pin twice in turn
for pin in range(16):
    p = sh.mcp23017.get_pin(pin)

    for i in range(2):
        p.value = True
        sleep(0.15)
        p.value = False
        sleep(0.3)