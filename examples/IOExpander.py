#!/usr/bin/env python3
""" Example for the Footleg Robotics Sentinel robot controller board
    Configures the IO expander pins
"""

from time import sleep
from sentinelboard import SentinelBoard

sb = SentinelBoard()

# Set pin 0 as an output, setting it LOW
sb.configureIOE(0, True, False)
sleep(1)

for i in range(10):
    sb.setOutput(0,True)
    sleep(0.2)
    sb.setOutput(0,False)
    sleep(0.8)
