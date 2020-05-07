#!/usr/bin/env python3
from time import sleep
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_mcp230xx.mcp23017 import MCP23017
from digitalio import Direction

# PWM board configuration values.
freqPWM = 50    # Frequency of PWM pulses (default is 50 Hz)

# Set servo min and max pulse length for the range of rotation of the servo model being used
servoMin = 1680   # Min pulse length (105 out of 4096) * 16 for 16 bit values in Circuit Python
servoMax = 8000   # Max pulse length (475-500 out of 4096) * 16 for 16 bit values in Circuit Python
servoRange = 180  # Rotation range in degrees of the servos being used

motorPowerLimiting = 50  # Default limits motors to 50 power
maxPulseLength = 0xffff  # Length of an always on pulse for the pwm board (circuit python library takes 16 bit value but hardware resolution is only 12 bit)
channelPulseLengths = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # Store pulse lengths sent to each channel (for debug info)

# Hardware fixed PWM channel numbers used for motor drivers
motorAChannel1 = 12
motorAChannel2 = 13
motorBChannel1 = 15
motorBChannel2 = 14

# Initialise the i2c bus to communicate with devices
i2c = busio.I2C(SCL, SDA)

# Initialise the PWM device using the default address

pwm = PCA9685(i2c, address=0x40)

# Set frequency to 50 Hz
pwm.frequency = freqPWM

# Initialise MCP 16 channel io
mcp = MCP23017(i2c, address=0x20)

def setPWMpulseLength(channel, pulse):
    """ Helper method used to set any PWM channel.
        All code setting PWM outputs should use this method so the hardware interface
        code only occurs once in the library, including storing what values each channel
        is set to.
    """
    global channelPulseLengths

    # Set PWM hardware output
    active_channel = pwm.channels[channel]
    active_channel.duty_cycle = pulse
    # Store setting in array for reading back what values have been set
    channelPulseLengths[channel] = pulse


def setServoPosition(channel, position):
    """ Sets the position of a servo in degrees
    """
    # Convert position in degrees to value in range min-max
    pulse = int( ( (servoMax - servoMin) * position / servoRange ) + servoMin)

    if (pulse < servoMin) or (pulse > servoMax):
        print("Calculated servo pulse {} is outside supported range of {} to {}".format(pulse, servoMin, servoMax) )
    elif (channel < 0) or (channel > 11):
        print("Attempt to set servo position using an invalid channel {}".format(channel) )
    else:
        print("Setting servo {} pulse to {}".format(channel, pulse) )
        # pwm.setPWM(channel, 0, pulse)
        setPWMpulseLength(channel, pulse)


def setMotorPowerLimiting(percentage):
    """ Sets limit to maximum motor power (as a percentage of motor board input voltage)
        Used to limit the maximum voltage the motors receive via PWM limiting.
        e.g. Setting this to 50% will mean when the motor percent on method is sent a value
        of 100%, the motors will only actually be send a PWM pulse which is on 50% of the time.
    """
    global motorPowerLimiting

    if percentage > 0:
        if percentage > 100:
            motorPowerLimiting = 100
        else:
            motorPowerLimiting = percentage
    else:
        motorPowerLimiting = 0


def setPercentageOn(channel, percent):
    """ Sets the percentage of time a channel is on per cycle.
        For use with PWM motor speed control.
    """
    # Scale down fully on pulse using percentage power limiting global variable value
    maxPulse = maxPulseLength * motorPowerLimiting / 100

    # Convert percentage to pulse length
    pulse = int( percent * maxPulse / 100 )

    # Limit pulse length to between zero and maximum
    if (percent < 0):
        pulse = 0
    elif (percent > 100):
        pulse = maxPulse

    print("Setting motor PWM channel {} pulse to {}".format(channel,pulse) )
    setPWMpulseLength(channel, pulse)


def setConstantOn(channel):
    """ Sets a channel to completely on (for logical high).
    """
    setPWMpulseLength(channel, maxPulseLength)


def allOff():
    """ Sets all outputs off """
    global channelPulseLengths

    pwm.reset()
    channelPulseLengths = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


def setMotorsPower(leftPower, rightPower):
    lPowerChannel = motorAChannel1
    lZeroChannel = motorAChannel2
    rPowerChannel = motorBChannel1
    rZeroChannel = motorBChannel2

    if leftPower < 0:
        setPercentageOn(motorAChannel2,0)
        setPercentageOn(motorAChannel1,-leftPower)
    else:
        setPercentageOn(motorAChannel1,0)
        setPercentageOn(motorAChannel2,leftPower)

    if rightPower < 0:
        setPercentageOn(motorBChannel2,0)
        setPercentageOn(motorBChannel1,-rightPower)
    else:
        setPercentageOn(motorBChannel1,0)
        setPercentageOn(motorBChannel2,rightPower)


def pulseWatchdog(duration, pin=7):
    mcp.get_pin(pin).value = 0
    sleep(duration)
    mcp.get_pin(pin).value = 0


def main():
    """ Test function for servos and motors
    """

    # Initialise watchdog pin
    wdpin = 15
    mcp.get_pin(wdpin).direction = Direction.OUTPUT
    mcp.get_pin(wdpin).value = 0
    pulseWatchdog(0.1,wdpin)
    sleep(0.1)

    #Servo on channel 0
    testChannel = 0
    print("Setting servo on channel {} to 0 degrees position.".format(testChannel))
    setServoPosition(testChannel, 0)
    pulseWatchdog(0.1,wdpin)
    sleep(0.4)
    print("Setting servo on channel {} to 180 degrees position.".format(testChannel))
    setServoPosition(testChannel, 180)
    pulseWatchdog(0.1,wdpin)
    sleep(0.4)
    print("Setting servo on channel {} to 90 degrees position.".format(testChannel))
    setServoPosition(testChannel, 90)
    pulseWatchdog(0.1,wdpin)
    sleep(0.4)

    #Motor A
    print("Setting motor A to power 50 forwards.")
    setPercentageOn(motorAChannel1,0)
    setPercentageOn(motorAChannel2,50)
    pulseWatchdog(0.1,wdpin)
    sleep(0.4)
    print("Setting motor A to power 0.")
    setPercentageOn(motorAChannel2,0)
    pulseWatchdog(0.1,wdpin)
    sleep(0.4)
    print("Setting motor A to power 50 reverse.")
    setPercentageOn(motorAChannel1,50)
    pulseWatchdog(0.1,wdpin)
    sleep(0.4)
    print("Setting motor A to power 0.")
    setPercentageOn(motorAChannel1,0)

    #Motor B
    print("Setting motor B to power 50 forwards.")
    setPercentageOn(motorBChannel1,0)
    setPercentageOn(motorBChannel2,50)
    pulseWatchdog(0.1,wdpin)
    sleep(0.4)
    print("Setting motor B to power 0.")
    setPercentageOn(motorBChannel2,0)
    pulseWatchdog(0.1,wdpin)
    sleep(0.4)
    print("Setting motor B to power 50 reverse.")
    setPercentageOn(motorBChannel1,50)
    pulseWatchdog(0.1,wdpin)
    sleep(0.4)
    print("Setting motor B to power 0.")
    setPercentageOn(motorBChannel1,0)

    #Test one PWM output
    setConstantOn(11)
    pulseWatchdog(0.1,wdpin)
    sleep(0.4)

    #Test one IO
    ioPin = 0

    pin = mcp.get_pin(ioPin)
    pin.direction = Direction.OUTPUT
    pin.value = True
    pulseWatchdog(0.1,wdpin)
    sleep(0.4)
    pin.value = False

    #mcp.config(ioPin, mcp.OUTPUT)
    #mcp.output(ioPin, 1)  # Pin High
    #mcp.output(ioPin, 0)  # Pin Low


    #All Off
    print("Turning off all PWM channels.")
    allOff()


if __name__ == '__main__':
    main()