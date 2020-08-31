# Sentinel Robot Controller Board
Python libraries for the Sentinel robot controller board for the Raspberry Pi and micro controller boards running Circuit Python

## Installation

These libraries are intended to be Python 3.6+ and Circuit Python compatible. They require the Adafruit Blinka libraries to run on a Raspberry Pi computer along with Adafruit libraries for low level access to the i2c hardware features. This code is still in active development and may change before the first release of the hardware boards it is being written for.

### Install Blinka
See https://learn.adafruit.com/circuitpython-on-raspberrypi-linux for the latest guide from Adafruit.

For a quick guide, at time of writing, run the following:
```bash
sudo apt-get update
sudo apt-get upgrade
```

```bash
pip3 install --upgrade setuptools
```

If above doesn't work try this to install pip for python 3 first:
```bash
sudo apt-get install python3-pip
```

Now install/upgrade the libraries using pip3 (for Python3):
```bash
pip3 install --upgrade RPI.GPIO adafruit_blinka  adafruit-circuitpython-pca9685 adafruit-circuitpython-mcp230xx
```
Before running the examples, it is recommended to ensure you have the latest versions of the hardware support libraries.

Once this library is complete it should be possible to install the library and all dependencies using pip. But for now while it is in a pre-release state you will need to install from the source as follows:

Open a terminal window in the 'library' folder and run the following script:
```bash
python3 setup.py install
```

You should now be able to import the library into your python modules:
```bash
import sentinelboard

sb = sentinelboard.SentinelBoard()
```

See the examples folder in this repository for usage.

