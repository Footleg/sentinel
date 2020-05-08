#!/usr/bin/env python3
""" Library for the Footleg Robotics Rocky Rover robot control board
    Supports board revision 1.2

    Dependencies
    ------------
    This library requires the following Adafruit libraries to be installed:
    - RPI.GPIO
    - adafruit_blinka
    - adafruit-circuitpython-pca9685
    - adafruit-circuitpython-mcp230xx

    These can be installed/upgraded to the latest using the following command:
    pip3 install --upgrade RPI.GPIO adafruit_blinka  adafruit-circuitpython-pca9685 adafruit-circuitpython-mcp230xx

    For full installation guide, see:
    https://github.com/Footleg/rocky-rover-board

    MIT License

    (c) Paul 'Footleg' Fretwell 2020

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

from time import sleep
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_mcp230xx.mcp23017 import MCP23017
from digitalio import Direction

# Hardware fixed PWM channel numbers used for motor drivers
motor1ChannelA = 12
motor1ChannelB = 13
motor2ChannelA = 15
motor2ChannelB = 14

# Length of an always on pulse for the pwm board (circuit python library
# takes a 16 bit value but hardware resolution is only 12 bit)
maxPulseLength = 0xffff

class RockyRoverBoard:
    """ Control class to represent a Footleg Robotics Rocky Rover robot control board
        Supports board revision 1.2
    """
    def __init__(self, addressPWM=0x40, addressIOE=0x20, freqPWM=50,
                 servoMinPulse=1680, servoMaxPulse=8000, servoRange=180,
                 watchdogPin=7
                 ):

        # Set servo min and max pulse length for the range of rotation of the servo model being used
        # Min pulse length (105 out of 4096) * 16 for 16 bit values in Circuit Python
        self.servoMinPulse = servoMinPulse
        # Max pulse length (475-500 out of 4096) * 16 for 16 bit values in Circuit Python
        self.servoMaxPulse = servoMaxPulse
        # Rotation range in degrees of the servos being used
        self.servoRange = servoRange

        # Store which IO expander pin is being used to send the watchdog keep alive signal
        self.watchdogPin = watchdogPin

        # Limits motors max power to a percentage of supplied voltage
        self.motorPowerLimiting = 100

        # Initialise pulse lengths store for each PWM channel (for reading back what they were set to)
        self.channelPulseLengths = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        # Initialise the i2c bus to communicate with devices
        i2c = busio.I2C(SCL, SDA)

        # Initialise the PWM device using the default address
        self.pwm = PCA9685(i2c, address=addressPWM)

        # Set frequency of PWM pulses (default is 50 Hz)
        self.pwm.frequency = freqPWM

        # Initialise MCP 16 channel io
        self.mcp = MCP23017(i2c, address=addressIOE)

        # Initialise watchdog signal pin (if set)
        if 0 <= self.watchdogPin < 16:
            p = self.mcp.get_pin(self.watchdogPin)
            p.direction = Direction.OUTPUT
            p.value = 0


    def setPWMpulseLength(self, channel, pulse):
        """ Helper method used to set any PWM channel.
            All code setting PWM outputs should use this method so the hardware interface
            code only occurs once in the library, including storing what values each channel
            is set to.
        """
        # Set PWM hardware output
        active_channel = self.pwm.channels[channel]
        active_channel.duty_cycle = pulse
        # Store setting in array for reading back what values have been set
        self.channelPulseLengths[channel] = pulse


    def setPercentageOn(self, channel, percent):
        """ Sets the percentage of time a PWM channel is on per duty cycle.
        """
        # Limit pulse length to between zero and maximum
        if (percent < 0):
            pulse = 0
        elif (percent > 100):
            pulse = maxPulseLength
        else:
            # Convert percentage to pulse length
            pulse = int( percent * maxPulseLength / 100 )

        self.setPWMpulseLength(channel, pulse)


    def setConstantOn(self, channel):
        """ Sets a channel to completely on (for logical high).
        """
        self.setPWMpulseLength(channel, maxPulseLength)


    def allOff(self):
        """ Sets all outputs off """
        self.pwm.reset()
        self.channelPulseLengths = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


    def setServoPosition(self, channel, position):
        """ Sets the position of a servo in degrees
        """
        minp = self.servoMinPulse
        maxp = self.servoMaxPulse
        srange = self.servoRange

        # Convert position in degrees to value in range min-max
        pulse = int( ( (maxp - minp) * position / srange ) + minp)

        if (pulse < minp) or (pulse > maxp):
            print("Calculated servo pulse {} is outside supported range of {} to {}".format(pulse, minp, maxp) )
        elif (channel < 0) or (channel > 11):
            print("Attempt to set servo position using an invalid channel {}".format(channel) )
        else:
            print("Setting servo {} pulse to {}".format(channel, pulse) )
            # pwm.setPWM(channel, 0, pulse)
            self.setPWMpulseLength(channel, pulse)


    def setMotorPowerLimiting(self, percentage):
        """ Sets limit to maximum motor power (as a percentage of motor board input voltage)
            Used to limit the maximum voltage the motors receive via PWM limiting.
            e.g. Setting this to 50% will mean when the motor power method is sent a value
            of 100%, the motors will only actually be sent a PWM pulse which is on 50% of the time.
            Useful for speed limiting motors for fine control, and to protect motors when
            over-volting motors (powering with above their rated maximum voltage).
        """
        if percentage > 0:
            if percentage > 100:
                self.motorPowerLimiting = 100
            else:
                self.motorPowerLimiting = percentage
        else:
            self.motorPowerLimiting = 0


    def setMotorPower(self, motor, percentPower):
        """ Sets the direction and power of a motor in the range -100 to +100
            The motor power is scaled down using the motor power limiting setting
            in place at the time the method is called.
        """
        # Scale down power using percentage power limiting value
        scaledPower = percentPower * self.motorPowerLimiting

        if motor == 1:
            if scaledPower < 0:
                powerChannel = motor1ChannelA
                zeroChannel = motor1ChannelB
            else:
                powerChannel = motor1ChannelB
                zeroChannel = motor1ChannelA
        elif motor == 2:
            if scaledPower < 0:
                powerChannel = motor2ChannelA
                zeroChannel = motor2ChannelB
            else:
                powerChannel = motor2ChannelB
                zeroChannel = motor2ChannelA

        self.setPercentageOn(zeroChannel, 0)
        self.setPercentageOn(powerChannel, scaledPower)


    def setMotorsPower(self, motor1Power, motor2Power):
        """ Helper method to update the speeds of both motors in one call """
        self.setMotorPower(1, motor1Power)
        self.setMotorPower(2, motor2Power)


    def pulseWatchdog(self, duration=0.1):
        """ Sends a pulse of a set duration (default 0.1 seconds) to the watchdog
            to keep the PWM power alive
        """
        self.mcp.get_pin(self.watchdogPin).value = True
        sleep(duration)
        self.mcp.get_pin(self.watchdogPin).value = False


def main():
    """ Test function for servos and motors
    """

    # Initialise board
    rrb = RockyRoverBoard(watchdogPin=0)

    # Servo on channel 0
    testChannel = 0
    print("Setting servo on channel {} to 0 degrees position.".format(testChannel))
    rrb.setServoPosition(testChannel, 0)
    for i in range(10):
        rrb.pulseWatchdog()
        sleep(0.1)
    print("Setting servo on channel {} to 180 degrees position.".format(testChannel))
    rrb.setServoPosition(testChannel, 180)
    for i in range(10):
        rrb.pulseWatchdog()
        sleep(0.1)
    print("Setting servo on channel {} to 90 degrees position.".format(testChannel))
    rrb.setServoPosition(testChannel, 90)
    for i in range(10):
        rrb.pulseWatchdog()
        sleep(0.1)
    """

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
    ioPin = 7

    pin = mcp.get_pin(ioPin)
    pin.direction = Direction.OUTPUT
    for i in range(50):
        pin.value = True
        sleep(0.1)
        pin.value = False
        sleep(0.1)
    """

    #mcp.config(ioPin, mcp.OUTPUT)
    #mcp.output(ioPin, 1)  # Pin High
    #mcp.output(ioPin, 0)  # Pin Low

    #All Off
    print("Turning off all PWM channels.")
    rrb.allOff()


if __name__ == '__main__':
    main()