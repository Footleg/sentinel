from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="sentinel-board",
    version="0.1.0",
    packages=find_packages(),
    
    install_requires=[
		"adafruit_blinka>=5.0.0",
		"RPi.GPIO>=0.7.0",
		"adafruit-circuitpython-pca9685>=3.3.1",
		"adafruit-circuitpython-mcp230xx>=2.3.1"
	],
    
    # metadata to display on PyPI
    author="Paul 'Footleg' Fretwell",
    author_email="drfootleg@gmail.com",
    description="Python library for the Footleg Robotics Sentinel robot controller board.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="Sentinel Raspberry Pi Robotics",
    url="https://github.com/Footleg/sentinel/",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    python_requires='>=3.6',
)