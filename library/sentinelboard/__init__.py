#!/usr/bin/env python3
""" Library for the Footleg Robotics Sentinel robot controller board

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
    https://github.com/Footleg/sentinel

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
import digitalio
from adafruit_bus_device.i2c_device import I2CDevice

# Hardware fixed PWM channel numbers used for motor drivers
motor1ChannelA = 12
motor1ChannelB = 13
motor2ChannelA = 14
motor2ChannelB = 15

# Length of an always on pulse for the pwm board (circuit python library
# takes a 16 bit value but hardware resolution is only 12 bit)
maxPulseLength = 0xffff

class SentinelBoard:
    """ Control class to represent a Footleg Robotics Sentinel robot controller board
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
        self._mcp23017 = MCP23017(i2c, address=addressIOE)

        # Initialise watchdog signal pin (if set)
        if 0 <= self.watchdogPin < 16:
            p = self._mcp23017.get_pin(self.watchdogPin)
            p.direction = digitalio.Direction.OUTPUT
            p.value = False

        # Initialise adc for voltage reading
        self._voltageAdjustMultiplier = 1.1
        self._voltageFloor = 0.24
        self.adc = I2CDevice(i2c, 0x4D)


    def configureIOE(self, pin, out=True, pullUp=False):
        """ Enables any pin on the IO expander to be configured
            as either an input (set out=False) or output (default
            if out argument is omitted, or out=True). If a pin is
            configured as an output, the pullUp argument is used
            to initialise it to HIGH or LOW (default). If set as
            and input the pullUp argument determines if internal
            pull-up resistor is set (pullUp=True), or input is left
            floating (deafult).
        """
        p = self._mcp23017.get_pin(pin)
        if (out):
            p.direction = digitalio.Direction.OUTPUT
            p.value = pullUp
        else:
            p.direction = digitalio.Direction.INPUT
            if (pullUp):
                p.pull = digitalio.Pull.UP
            else:
                # Note hardware does not have built in pull down
                # so this is just setting to floating input
                p.pull = digitalio.Pull.DOWN


    def readIOPin(self, pin):
        """ Returns the logic state of any IO pin whether configured as
            an input or output.
        """
        return self._mcp23017.get_pin(pin).value


    def setOutput(self, pin, value):
        """ Sets the logic state of any IO pin configured as
            an output.
        """
        self._mcp23017.get_pin(pin).value = value


    @property
    def mcp23017(self):
        """ Direct access to the MCP23017 object for lower level digital
            IO control. This enables you to configure interupts for input
            pins and read, set or configure the groups of IO pins all at once
            via the chip registers.
            See the Adafruit documentation for this object at
            https://circuitpython.readthedocs.io/projects/mcp230xx/en/latest/api.html#mcp23017
        """
        return self._mcp23017


    @property
    def voltage_multiplier(self):
        """ The voltage_multiplier property is used to compensate for
            the difference in ADC calculated voltage and measured voltage.
        """
        return self._voltageAdjustMultiplier


    @voltage_multiplier.setter
    def voltage_multiplier(self,value):
        """ Set the voltage_multiplier to a non-default value.
        """
        self._voltageAdjustMultiplier = value


    @property
    def voltage_floor(self):
        return self._voltageAdjustMultiplier


    @voltage_floor.setter
    def voltage_floor(self,value):
        self._voltageFloor = value


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
        #self.pwm.reset() #Does not set channels to off!
        #self.channelPulseLengths = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for i in range(0,16):
            self.setPWMpulseLength(i, 0)


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
        scaledPower = percentPower * self.motorPowerLimiting / 100

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
        self.setPercentageOn(powerChannel, abs(scaledPower) )


    def setMotorsPower(self, motor1Power, motor2Power):
        """ Helper method to update the speeds of both motors in one call """
        self.setMotorPower(1, motor1Power)
        self.setMotorPower(2, motor2Power)


    def pulseWatchdog(self, duration=0.001):
        """ Sends a pulse of a set duration (default 1 ms) to the watchdog
            to keep the PWM power alive. This only applies when one of the
            IO expander pins has been configured (and wired) to be the
            watchdog circuit input.
        """
        self._mcp23017.get_pin(self.watchdogPin).value = True
        sleep(duration)
        self._mcp23017.get_pin(self.watchdogPin).value = False

    @property
    def motor_voltage(self):
        readbuf = bytearray(2)
        piVolts = 5.2

        self.adc.readinto(readbuf)
        # Combine 2 bytes into word
        adcVal = 0x100 * readbuf[0] + readbuf[1]
        # Convert reading to voltage based on ratio of Pi power supply voltage
        adcVoltage = piVolts * adcVal / 0xFFF
        # Convert to motor supply voltage based on resistor divider 1.24K / 10K
        # multiplied by correction mulitpler (compensates for imprecision of resistor values)
        motorSupplyVoltage = (adcVoltage*8.0645 - self._voltageFloor)*self._voltageAdjustMultiplier

        return motorSupplyVoltage

    def watchdogPause(self, duration = 1):
        """ Method to pause code execution while keeping the watchdog pulses
            running so the board PWM output remains active
        """
        highDuration = 0.001
        pauseLen = duration
        if duration > 0.25:
            # Break pause into 0.25s cycles
            pauseLen = 0.25

        lowDuration = pauseLen - highDuration
        cycles = int(duration / pauseLen)
        remainder = duration - highDuration - cycles*pauseLen

        for i in range(cycles):
            self.pulseWatchdog(highDuration)
            sleep(lowDuration)

        self.pulseWatchdog(highDuration)
        if remainder > 0:
            sleep(remainder)

def main():
    """ Test function for servos and motors
    """
    from time import perf_counter


    # Initialise board
    rrb = SentinelBoard()

    # Grab start time for measuring duration of tests
    startt = perf_counter()

    # Activate PWM via watchdog
    rrb.pulseWatchdog()

    # Servo on channel x
    testChannel = 0
    minDeg = 65
    maxDeg = 155
    for i in range(3):
        if i == 0:
            deg = minDeg
        elif i == 1:
            deg = maxDeg
        else:
            deg = minDeg + (maxDeg - minDeg) / 2

        print("Time {}: Setting servo on channel {} to {} degrees position.".format(perf_counter() - startt, testChannel, deg))
        rrb.setServoPosition(testChannel, deg)
        watchdogPause()

    for motor in range(1,3):
        #Ramp up motor power
        for pwr in range (0, 101, 5):
            rrb.setMotorPower(motor, pwr)
            print("Time {}: Motor {} +{}".format(perf_counter() - startt, motor, pwr))
            watchdogPause(0.1)

        #Stop motor
        rrb.setMotorPower(motor,0)
        watchdogPause()

        #Reverse motor
        rrb.setMotorPower(motor,-50)
        print("Time {}: Motor {} -50%".format(perf_counter() - startt, motor))
        watchdogPause()
        print("Time {}: Motor {} -100%".format(perf_counter() - startt, motor))
        rrb.setMotorPower(motor,-100)
        watchdogPause()
        #Stop motor
        rrb.setMotorPower(motor,0)

    # Restart both motors
    print("Time {}: Starting both motors and sending watchdog keep-alive pulse".format(perf_counter() - startt))
    rrb.setMotorsPower(50,-50)
    watchdogPause()

    print("Time {}: Letting watchdog time out".format(perf_counter() - startt))
    for i in range(3):
        sleep(1)
        print("Time {}".format(perf_counter() - startt))
    """

    #Test one PWM output
    setConstantOn(11)
    pulseWatchdog(0.1,wdpin)
    sleep(0.4)

    #Test one IO
    ioPin = 7

    pin = mcp23017.get_pin(ioPin)
    pin.direction = Direction.OUTPUT
    for i in range(50):
        pin.value = True
        sleep(0.1)
        pin.value = False
        sleep(0.1)
    """

    #All Off
    print("Turning off all PWM channels.")
    rrb.allOff()

    print("Reactivate watchdog for 1 second.") #Servo and motor should remain inactive now
    watchdogPause()

if __name__ == '__main__':
    main()