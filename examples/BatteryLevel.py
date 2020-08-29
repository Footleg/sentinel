#!/usr/bin/env python3
""" Example for the Footleg Robotics Sentinel robot controller board
    Reads the voltage of the motor power supply
"""

from sentinelboard import SentinelBoard

sb = SentinelBoard()

motorV = sb.motorVoltage()

print("Motor supply voltage: {}".format(motorV) )