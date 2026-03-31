"""
# Unified Sensor System for Raspberry Pi
import time
import serial
import board
import adafruit_dht
import adafruit_sht4x
import requests 
from gpiozero import DigitalInputDevice
from sgp30 import SGP30
from smbus import SMBus
from typing import Optional 

"""Features following Python style guide and includes docstrings for all classes and methods.
This code is designed to be modular and extensible, allowing for easy addition of new sensors in the future."""
class Sensor: # Base class for all sensors
    """Base class for all sensors."""

    def read(self) -> None: # Read data from the sensor
        """Read data from the sensor."""
        raise NotImplementedError

    def display(self) -> None: # Display the sensor data in a human-readable format 
        """Display sensor data."""
        raise NotImplementedError


class TVOCSensor(Sensor): # TVOC Sensor using UART communication
    """TVOC sensor using UART communication."""

    def __init__(self, port: str = "/dev/ttyAMA0") -> None: # Initialise serial connection to TVOC sensor
        self.serial = serial.Serial( 
            port = port, # UART port for TVOC sensor 
            baudrate = 9600, # Standard baud rate for many UART devices
            bytesize = 8, # 8 data bits
            parity = "N", # No parity
            stopbits = 1, # 1 stop bit
            timeout = 1, # 1 second timeout for reading data
        )
        self.command = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x01, 0x84, 0x0A]) # Command to request TVOC reading from sensor 
        self.value: Optional[int] = None # Store the latest TVOC value in parts per billion (ppb)

    def read(self) -> None: # Read TVOC value from sensor
        """Fetch TVOC value from sensor."""
        try:
            self.serial.write(self.command) # Send command to sensor to request TVOC reading
            time.sleep(0.1) # Short delay to allow sensor to process command and prepare data

            data = self.serial.read(7) # Read 7 bytes of data from sensor (expected response length for TVOC reading)
            if len(data) == 7: # Check if we received the expected number of bytes
                self.value = (data[3] << 8) | data[4] # Combine the two bytes of TVOC data into a single integer value (ppb)
            else:
                self.value = None # If we didn't receive the expected data, set value to None to indicate an error

        except serial.SerialException: # Handle serial communication errors gracefully
            self.value = None # Set value to None if there was an error communicating with the sensor 
    def display(self) -> None: # Display the TVOC value in a human-readable format
        # Print TVOC reading.
        if self.value is not None: 
            print(f"TVOC: {self.value} ppb") # Display TVOC value in parts per billion (ppb) if we have a valid reading, otherwise indicate that there is no data
        else:
            print("TVOC: No data")

class DHT22Sensor(Sensor): # DHT22 Temperature and Humidity Sensor
    def __init__(self):
        self.sensor = adafruit_dht.DHT22(board.D17) # Initialise DHT22 sensor on GPIO4
        self.temp = None # Store the latest temperature value
        self.hum = None # Store the latest humidity value

    def read(self): # Read temperature and humidity from DHT22 sensor
        try:
            self.temp = self.sensor.temperature # Read temperature in Celsius
            self.hum = self.sensor.humidity # Read relative humidity in percentage
        except RuntimeError:
            self.temp, self.hum = None, None # Handle read errors gracefully

    def display(self): # Display the temperature and humidity values
        if self.temp is not None:
            print(f"DHT22 Temp: {self.temp:.2f} °C | Humidity: {self.hum:.2f}%") # Display temperature and humidity with 2 decimal places
        else:
            print("DHT22: Error") 


class MQ7Sensor(Sensor): # MQ-7 Carbon Monoxide Sensor (Digital Output) - I don't have access to a ADC converter. This is mentioned in the report. 
    def __init__(self):
        self.sensor = DigitalInputDevice(23, pull_up=True, active_state=False)  # Initialise MQ-7 sensor on GPIO17 with pull-up resistor and active low signal
        self.detected = False

    def read(self):
        self.detected = self.sensor.is_active # Read the digital output from MQ-7 sensor (True if CO detected, False if air is safe)

    def display(self): # Display the status of carbon monoxide detection
        if self.detected:
            print("Carbon Monoxide Detected!")
        else:
            print("MQ-7: Air safe")


class SGP30Sensor(Sensor): # SGP30 Air Quality Sensor (I2C)
    def __init__(self): # Initialise I2C connection and SGP30 sensor
        self.bus = SMBus(1) # Use I2C bus 1 on Raspberry Pi
        self.sensor = SGP30(self.bus) # Initialize SGP30 sensor
        self.voc = None # Store the latest VOC value in parts per billion
        self.co2 = None # Store the latest CO2 value in parts per million

    def read(self): # Read VOC and CO2 values from SGP30 sensor
        try:
            aq = self.sensor.air_quality() # Get air quality readings (VOC in ppb and CO2 in ppm)
            self.voc = aq.voc_ppb # Store VOC value in parts per billion
            self.co2 = aq.co2_ppm # Store CO2 value in parts per million
        except:
            self.voc, self.co2 = None, None # Handle read errors gracefully

    def display(self): # Display the VOC and CO2 values from SGP30 sensor
        if self.voc is not None:
            print(f"SGP30 VOC: {self.voc} ppb | CO2: {self.co2} ppm") # Display VOC in parts per billion and CO2 in parts per million
        else:
            print("SGP30: Error")



# The SHT45 Sensor lacks sufficent connectors for the Pi, so I've removed it from the manager. I have left the code here for reference and future use if I can find a way to connect it.
"""
class SHT45Sensor(Sensor): # SHT45 Temperature and Humidity Sensor (I2C)
    def __init__(self): # Initialise I2C connection and SHT45 sensor
        self.i2c = board.I2C() # Use default I2C bus on Raspberry Pi
        self.sensor = adafruit_sht4x.SHT45(self.i2c) # Initialise SHT45 sensor
        self.sensor.mode = adafruit_sht4x.Mode.HIGH # Set SHT45 to high precision mode
        self.temp = None
        self.hum = None

    def read(self):
        try:
            self.temp = self.sensor.temperature # Read temperature in Celsius from SHT45 sensor
            self.hum = self.sensor.relative_humidity # Read relative humidity in percentage from SHT45 sensor
        except:
            self.temp, self.hum = None, None # Handle read errors gracefully

    def display(self): # Display the temperature and humidity values from SHT45 sensor
        if self.temp is not None:
            print(f"SHT45 Temp: {self.temp:.2f} °C | Humidity: {self.hum:.2f}%") # Display temperature and humidity with 2 decimal places
        else:
            print("SHT45: Error")
"""


class SensorManager:
    """Manages multiple sensors and coordinates reading their data."""

    def __init__(self):
        self.sensors = []

    def add_sensor(self, sensor):
        self.sensors.append(sensor)

    def read_all(self):
        """Read all sensors and return structured data."""
        readings = {}

        for sensor in self.sensors:
            sensor.read()

            if isinstance(sensor, TVOCSensor):
                readings["tvoc_uart"] = sensor.value

            elif isinstance(sensor, SGP30Sensor):
                readings["tvoc_i2c"] = sensor.voc
                readings["co2"] = sensor.co2

            elif isinstance(sensor, DHT22Sensor):
                readings["temperature"] = sensor.temp
                readings["humidity"] = sensor.hum

        # SHT45 Code
            #elif isinstance(sensor, SHT45Sensor):
              #  readings["temperature"] = sensor.temp
               # readings["humidity"] = sensor.hum

            elif isinstance(sensor, MQ7Sensor):
                readings["co"] = sensor.detected 


        return readings
def run(self):
    print("Starting Sensor System")

    air_sensor = AirSensor()
    previous_issues = {}

    while True:
        readings = self.read_all()

        issues = air_sensor.check_air_quality(
            readings.get("tvoc"),
            readings.get("co2"),
            readings.get("temp"),
            readings.get("hum"), 
            readings.get("co")
         )

        if issues != previous_issues:
            if issues:
                print("Air Quality Issues Detected:")
                for k, v in issues.items():
                    print(f"{k}: {v}")
            else:
                print("Air quality is good")

            previous_issues = issues

        print("-" * 40)
        time.sleep(2)


class AirSensor: # Class to check air quality based on sensor readings and predefined thresholds [1],[2] 
   def __init__(self): 
        # Define thresholds c
        self.tvoc_poor = 300
        self.tvoc_critical = 600

        self.co2_poor = 1000
        self.co2_critical = 2000 

        self.temp_poor = 17
        self.temp_critical = 30

        self.hum_poor = 61
        self.hum_critical = 75

   def check_air_quality(self, tvoc, co2, temp, hum, co_detected): # Check air quality based on sensor readings and return any issues detected
        issues = {}
        if tvoc is not None:
            if tvoc > self.tvoc_critical:
                issues["tvoc"] = "Critical"
            elif tvoc > self.tvoc_poor:
                issues["tvoc"] = "Poor"

        if co2 is not None:
            if co2 > self.co2_critical:
                issues["co2"] = "Critical"
            elif co2 > self.co2_poor:
                issues["co2"] = "Poor"

        if temp is not None:
            if temp > self.temp_critical:
                issues["temperature"] = "Critical"
            elif temp > self.temp_poor:
                issues["temperature"] = "Poor"

        if hum is not None:
            if hum > self.hum_critical:
                issues["humidity"] = "Critical"
            elif hum > self.hum_poor:
                issues["humidity"] = "Poor"
        
        if co_detected:
            issues["co"] = "CRITICAL"

        return issues
   
   import requests


# Main Program

if __name__ == "__main__": # Create sensor manager and add all sensors to it, then run the program
    manager = SensorManager()

    manager.add_sensor(TVOCSensor())
    manager.add_sensor(DHT22Sensor())
    manager.add_sensor(MQ7Sensor())
    manager.add_sensor(SGP30Sensor())

    manager.run() 


# Reference:
# TVOC Sensor(Organic Compounds):
# [1] https://gpmoldinspection.com/article/what-is-tvoc-air-quality/ 

# Carbon Dioxide:
# [2] https://www.co2meter.com/en-uk/blogs/news/carbon-dioxide-indoor-levels-chart?srsltid=AfmBOoq-kpY_efXM7PtXR0MuDu-OECYW_o4m7gRn0sAuLZ85KX_KnLT1

# Temperature and Humidity:
# [3] https://www.hse.gov.uk/temperature/employer/managing.htm

# [4] https://www.hse.gov.uk/foi/internalops/ocs/300-399/oc311_2.htm

"""


# Unified Sensor System for Raspberry Pi (Refactored)

import time
import serial
import board
import adafruit_dht
import requests 
from gpiozero import DigitalInputDevice
from sgp30 import SGP30
from smbus import SMBus
from typing import Optional


# Base Sensor Class


class Sensor:
    """Base class for all sensors."""

    def read(self) -> dict:
        """Return sensor data as a dictionary."""
        raise NotImplementedError



# Flask Server Communication with app.py 
SERVER_URL = "http://86.17.112.152:5000/api/upload/sensor"


def get_overall_status(issues):
    """Convert issues dict into a single status."""
    if not issues:
        return "GOOD"
    if "CRITICAL" in issues.values():
        return "CRITICAL"
    return "POOR"


def send_to_server(payload):
    """Send sensor data to Flask server."""
    try:
        response = requests.post(SERVER_URL, json=payload, timeout=5)

        if response.status_code == 201:
            print("Data sent to server")
        else:
            print(f"Server error: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to connect: {e}")

# Sensor Implementations

class TVOCSensor(Sensor):
    """TVOC sensor using UART communication."""

    def __init__(self, port: str = "/dev/ttyAMA0"):
        self.serial = serial.Serial(port, 9600, timeout=1)
        self.command = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x01, 0x84, 0x0A])
        self.value: Optional[int] = None

    def read(self):
        try:
            self.serial.write(self.command)
            time.sleep(0.1)
            data = self.serial.read(7)

            if len(data) == 7:
                self.value = (data[3] << 8) | data[4]
            else:
                self.value = None

        except serial.SerialException:
            self.value = None

        return {"tvoc_uart": self.value}


class SGP30Sensor(Sensor):
    """SGP30 Air Quality Sensor (VOC + CO2)."""

    def __init__(self):
        self.bus = SMBus(1)
        self.sensor = SGP30(self.bus)

    def read(self):
        try:
            aq = self.sensor.air_quality()
            return {
                "tvoc_i2c": aq.voc_ppb,
                "co2": aq.co2_ppm
            }
        except Exception:
            return {"tvoc_i2c": None, "co2": None}


class DHT22Sensor(Sensor):
    """Temperature and Humidity Sensor."""

    def __init__(self):
        self.sensor = adafruit_dht.DHT22(board.D17)

    def read(self):
        try:
            return {
                "temperature": self.sensor.temperature,
                "humidity": self.sensor.humidity
            }
        except RuntimeError:
            return {"temperature": None, "humidity": None}


class MQ7Sensor(Sensor):
    """Carbon Monoxide Sensor (Digital Output)."""

    def __init__(self):
        self.sensor = DigitalInputDevice(23, pull_up=True, active_state=False)

    def read(self):
        return {"co": self.sensor.is_active}



# Sensor Manager

class SensorManager:
    """Manages multiple sensors and aggregates their data."""

    def __init__(self):
        self.sensors = []

    def add_sensor(self, sensor: Sensor):
        self.sensors.append(sensor)

    def read_all(self):
        readings = {}

        for sensor in self.sensors:
            data = sensor.read()
            readings.update(data)  # Merge sensor data

        return readings

# Air Quality Logic

class AirSensor:
    """Evaluates air quality based on sensor data."""

    def __init__(self):
        self.tvoc_poor = 300
        self.tvoc_critical = 600

        self.co2_poor = 1000
        self.co2_critical = 2000

        self.temp_poor = 25
        self.temp_critical = 30

        self.hum_poor = 60
        self.hum_critical = 75

    def check_air_quality(self, data: dict):
        issues = {}

        # Carbon Monoxide overrides everything
        if data.get("co"):
            return {"co": "CRITICAL"}

        tvoc = data.get("tvoc_i2c") or data.get("tvoc_uart")
        co2 = data.get("co2")
        temp = data.get("temperature")
        hum = data.get("humidity")

        if tvoc is not None:
            if tvoc > self.tvoc_critical:
                issues["tvoc"] = "CRITICAL"
            elif tvoc > self.tvoc_poor:
                issues["tvoc"] = "POOR"

        if co2 is not None:
            if co2 > self.co2_critical:
                issues["co2"] = "CRITICAL"
            elif co2 > self.co2_poor:
                issues["co2"] = "POOR"

        if temp is not None:
            if temp > self.temp_critical:
                issues["temperature"] = "CRITICAL"
            elif temp > self.temp_poor:
                issues["temperature"] = "POOR"

        if hum is not None:
            if hum > self.hum_critical:
                issues["humidity"] = "CRITICAL"
            elif hum > self.hum_poor:
                issues["humidity"] = "POOR"

        return issues



# Main Program

if __name__ == "__main__":
    manager = SensorManager()

    manager.add_sensor(TVOCSensor())
    manager.add_sensor(DHT22Sensor())
    manager.add_sensor(MQ7Sensor())
    manager.add_sensor(SGP30Sensor())

    air_sensor = AirSensor()
    previous_issues = {}

    print("Starting Sensor System")

    while True:
        readings = manager.read_all()
        issues = air_sensor.check_air_quality(readings)
        status = get_overall_status(issues)

        # Prepare payload for Flask
        payload = {
            "Pi_ID": 1,
            "temperature": readings.get("temperature"),
            "humidity": readings.get("humidity"),
            "co2": readings.get("co2"),
            "co": readings.get("co"),
            "tvoc": readings.get("tvoc_i2c") or readings.get("tvoc_uart"),
            "status": status,
            "issues": issues,
        }

        # Send to server
        send_to_server(payload)

        # Local alert (optional)
        if issues != previous_issues:
            if issues:
                print("Air Quality Issues Detected:")
                for k, v in issues.items():
                    print(f"{k}: {v}")
            else:
                print("Air quality is GOOD")

            previous_issues = issues

        print("-" * 40)
        time.sleep(5)


# References:
# TVOC Sensor(Organic Compounds):
# [1] https://gpmoldinspection.com/article/what-is-tvoc-air-quality/ 

# Carbon Dioxide:
# [2] https://www.co2meter.com/en-uk/blogs/news/carbon-dioxide-indoor-levels-chart?srsltid=AfmBOoq-kpY_efXM7PtXR0MuDu-OECYW_o4m7gRn0sAuLZ85KX_KnLT1

# Temperature and Humidity:
# [3] https://www.hse.gov.uk/temperature/employer/managing.htm

# [4] https://www.hse.gov.uk/foi/internalops/ocs/300-399/oc311_2.htm
