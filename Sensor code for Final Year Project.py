# Sensor code for Final Year Project

# When on Pi download and install the following libraries via terminal:
"""
sudo apt update
sudo apt install -y python3-pip python3-dev
pip3 install adafruit-circuitpython-dht
pip3 install adafruit-circuitpython-sgp30
pip3 install adafruit-circuitpython-mcp3xxx
pip3 install RPI.GPIO
pip3 install adafruit-blinka
"""

# Then: sudo raspi-config
# Go to Interfacing Options and enable I2C and SPI

import time
import board
import busio
import adafruit_dht
import digitalio
import adafruit_sgp30

from adafruit_mcp3xxx.mcp3008 import MCP3008
from adafruit_mcp3xxx.analog_in import AnalogIn

# GPiO pin for DH22 sensor
DHT_PIN =  board.D4
dht22 = adafruit_dht.DHT22(DHT_PIN)

# SGP30 sensor setup
i2c = busio.I2C(board.SCL, board.SDA)
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

# MQ7 sensor setup
spi = busio.SPI(board.SCK, board.MOSI, board.MISO) 
cs = digitalio.DigitalInOut(board.D5)   
mcp = MCP3008(spi, cs)
mq7_channel = AnalogIn(mcp, 0)

# Reading the sensors

# DHT22 sensor 
def read_dht22():
    temperature = dht22.temperature
    humidity = dht22.humidity
    return temperature, humidity
   
# SGP30 sensor   
def read_sgp30():
    co2 = sgp30.eCO2
    tvoc = sgp30.TVOC
    
    return co2, tvoc

# MQ7 sensor
def read_mq7():
    mq7_value = mq7_channel.value
    return mq7_value






