#!/usr/bin/env python3
""" Example for the Footleg Robotics Sentinel robot controller board
    Powers up motors on the two motor drivers at various speeds
    with the watchdog circuit active.
"""

from time import perf_counter, sleep
from sentinelboard import SentinelBoard

sb = SentinelBoard()

# Activate PWM via watchdog
print("Activate watchdog")
sb.pulseWatchdog()

# Grab start time for measuring duration of tests
startt = perf_counter()


for motor in range(1,3):
    #Ramp up motor power
    for pwr in range (0, 101, 5):
        sb.setMotorPower(motor, pwr)
        print(f"Time {perf_counter() - startt:.2f}: Motor {motor} +{pwr}")
        sb.watchdogPause(0.1)

    #Stop motor
    sb.setMotorPower(motor,0)
    sb.watchdogPause()

    #Reverse motor
    sb.setMotorPower(motor,-50)
    print(f"Time {perf_counter() - startt:.2f}: Motor {motor} -50%")
    sb.watchdogPause()
    print(f"Time {perf_counter() - startt:.2f}: Motor {motor} -100%")
    sb.setMotorPower(motor,-100)
    sb.watchdogPause()

    #Stop motor
    sb.setMotorPower(motor,0)

# Restart both motors
print(f"Time {perf_counter() - startt:.2f}: Starting both motors and sending watchdog keep-alive pulse")
sb.setMotorsPower(50,-50)
sb.watchdogPause()

print(f"Time {perf_counter() - startt:.2f}: Letting watchdog time out")
for i in range(12):
    sleep(0.25)
    print(f"Time {perf_counter() - startt:.2f}: No watchdog keep alive pulses")

print("Activate watchdog")
sb.pulseWatchdog()

print(f"Time {perf_counter() - startt:.2f}: Letting watchdog time out")
for i in range(12):
    sleep(0.25)
    print(f"Time {perf_counter() - startt:.2f}: No watchdog keep alive pulses")

#Stop both motors
sb.setMotorsPower(0,0)