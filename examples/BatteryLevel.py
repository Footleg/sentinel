#!/usr/bin/env python3
""" Example for the Footleg Robotics Sentinel robot controller board
    Reads the voltage of the motor power supply
"""

from sentinelboard import SentinelBoard

sb = SentinelBoard()

motorV = sb.motor_voltage
print(f"Motor supply voltage: {motorV:.2f}")

sb.voltageAdjustMultiplier = 1.1
motorV = sb.motor_voltage
print(f"Motor supply voltage: {motorV:.2f}")
