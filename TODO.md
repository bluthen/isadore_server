# About

This file is a document of things that are needed for both [isadore_server](https://github.com/bluthen/isadore_server) and [isadore_electronics](https://github.com/bluthen/isadore_electronics).

General Overview:
* Better troubleshooting/configuration from the isadore server web interface
* Reliability improvements to the electronics (circuit protections and connector change)
* Update software from python2 to python3 for better support on newer operating systems and databases, the longer it goes the harder it will be to run.

# Server Software
  1. Port [isadore_server](https://github.com/bluthen/isadore_server) to python3 and use Flask instead of bottle. -- Currently the server software is written in Python 2. Python 2 [support has been dropped](https://www.python.org/doc/sunset-python-2/) since January 1st, 2020. The future is Python 3, it will get harder and harder to run Python 2 on modern operating systems, harder to get the required older modules, harder for the database driver to connect to updated database software. There has been work done to use python3 in the [python3_flask](https://github.com/bluthen/isadore_server/tree/python3_flask) branch but it is not complete or tested.
  2. Troubleshooting/Calibration tools
     1. Troubleshooting - It can be very time consuming to troubleshoot failed units. Every failed unit adds time between pulling sensor unit information. There needs to be a way to halt the round of pulls and just ask to pull specific units as you replace them. A interface needs to be added to do this, and the MID software needs to be modified to do this as well. 
     2. Calibration - There is convert formula and bias, but other than that there is no automated calibration tools that can be done from the web interface. It currently can only be done using command line tools on the MID. It should be possible to do this from the web interface, this is especially important for pressure sensors.
  3. Alarms
     1. A interface to indicate harvest has started/ended so enable/disable the alarms. Have the alarm system more integrated with the server software instead of it being it's own process. 
     2. Interface to set up SMS account keys linked with your account - Right now this has to be done modifying a config file on the server.
     3. Interface to set up which outgoing email server to use to help better to not have isadore alert emails go to spam server.


# MID

The MID is the box that sits in the dryer and pulls sensor info from the sensor units and reports it back to the server.

  1. Port to python3 - The main pulling software is writting in python 2, it needs to be updated to python3, see Server Software #1
  2. Troubleshooting/Calibration tools - See Server Software #2. The MID part of these needs to be done
  3. Read-only file system - Despite using industrial SD Cards, constant power cycling when the dryer loses power and writting system logs to the sd card wear it out or causes corruption. If a read-only file system with a ram-only write layer were in places, it could lower the chances of sdcard failures.
  4. General Troubleshooting indicators - At a minimum have a few different color LED for troubleshooting. Suggestion below:
     1. Red - Has power
     2. Yellow - Operating system up and running
     3. Blue - Has a connection to local network
     4. Green - Has internet
     5. White - Is able to communicate with Isadore Server
  5. Port Troubleshooting indicators
     1. Red - Has not been able to read from any sensor units on the port
     2. Yellow - Can read from some sensor units on the port, but some have errored
     3. Green - All sensor units on the power have been able to be read from
  6. Sensor Units relay - Power off sensor units while keeping MID up - Many people keep the MID and sensor units running year round even though they only use it during harvest. Having a manual process to unplug the MID seems to be forgotten when harvest is over. If there was a way to power down the sensor unit network through the isadore server web interface, it could prevent transitory causes of sensor unit damage that happen in off season.


# Sensor Units and other MID electronics

  1. Better electronics protection - When there is a wiring error or connector issue (maybe the main reason a sensor unit fails)  
     1. RS485 transceivers with over/under voltage protection (Something like the LTC2862, LTC2863, LTC2864, or LTC2865)
     2. Sensor unit needs reverse polarity protection on its power input
  2. replace RJ45 connectors - The RJ45 connectors are too unreliable and a big reasons for sensor unit destruction or being unable to communicate. They are not very weather resistant and in some conditions cause shorts or other wiring issues.
     1. Screw terminals could be more reliable but for ease of installation I suggest moving to half duplex communication so there are only 4 conductors in a cable (power, com+, com-, ground). This though would make them uncompatible with current units and MID. Make sure com+, com- are still twisted pair.
  3. Sensor units could have more protected coating over them
  4. Improved sensor units for previously support sensor types (thermocouple, tachometer, multipoint)

# Documentation

There could be better setup and troubleshooting documentation for the whole project.
