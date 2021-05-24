#!/usr/bin/env python3
""" Example for the Footleg Robotics Sentinel robot controller board
    Reads the voltage of the motor power supply
"""

from sentinelboard import SentinelBoard

sb = SentinelBoard()

#Get motor voltage using default calibration
motorV = sb.sbHardware.motor_voltage
print(f"Motor supply voltage: {motorV:.2f}")

#Adjust calibration for your specific board
sb.sbHardware.voltage_floor = 0.195
sb.sbHardware.voltage_multiplier = 1.11
motorV = sb.sbHardware.motor_voltage
print(f"Motor supply voltage: {motorV:.2f}")