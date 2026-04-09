# Unified Sensor System for Raspberry Pi (Refactored)
# This program has been refactored by CoPilot and myself. Fixing a few secuity issues and improving code structure. 
import time
import serial
import board
import adafruit_dht
import requests 
from gpiozero import DigitalInputDevice
import busio
import adafruit_sgp30
from typing import Optional
import paho.mqtt.client as mqtt
import json
import os


# Run the following commands in terminal to set MQTT environment variables before running the program:
"""
export MQTT_BROKER=192.168.1.10
export MQTT_PORT=1883
export MQTT_TOPIC=sensors/air_quality
""" 


# MQTT Publisher Class: This is the publisher part of the server 
class MQTTPublisher:
    def __init__(self):
        self.broker = os.getenv("MQTT_BROKER", "192.168.1.100")
        self.port = int(os.getenv("MQTT_PORT", 1883))
        self.topic = os.getenv("MQTT_TOPIC", "sensors/air_quality")

        self.client = mqtt.Client()
        self.client.connect(self.broker, self.port, 60)

    def publish(self, payload: dict) -> None:  # Type hints for parameters
        """Publish sensor data to MQTT broker."""
        try:
            self.client.publish(self.topic, json.dumps(payload))
            print("Published to MQTT")
        except Exception as e:
            print(f"MQTT error: {e}")


# Base Sensor Class
class Sensor:
    """Base class for all sensors."""

    def read(self) -> dict:
        """Return sensor data as a dictionary."""
        raise NotImplementedError


def get_overall_status(issues: dict) -> str:  # Type hints
    """Convert issues dict into a single status string."""
    if not issues:
        return "GOOD"
    if "CRITICAL" in issues.values():
        return "CRITICAL"
    return "POOR"


# Sensor Implementations

class TVOCSensor(Sensor):
    """TVOC sensor using UART communication."""

    def __init__(self, port: str = "/dev/ttyAMA0"):
        self.port = port
        self.serial: Optional[serial.Serial] = None  # # Type hint for serial port 
        self.command = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x01, 0x84, 0x0A])
        self.value: Optional[int] = None

    def read(self) -> dict:
        """Read TVOC value from sensor via UART. Returns dict with 'tvoc_uart' key or None."""
        try:
            # Lazy initialization - only open port when needed
            if self.serial is None or not self.serial.is_open:
                self.serial = serial.Serial(self.port, 9600, timeout=1)
            
            self.serial.write(self.command)
            time.sleep(0.1)
            data = self.serial.read(7)

            if len(data) == 7:
                self.value = (data[3] << 8) | data[4]
            else:
                self.value = None

        except serial.SerialException as e:  # More specific error handling
            print(f"TVOC sensor error: {e}")
            self.value = None
            if self.serial:  # Close on error to free port
                self.serial.close()
                self.serial = None  # Reset so it retries next time

        return {"tvoc_uart": self.value}
    
    def __del__(self): # Destructor to ensure serial port is closed
        """Ensure serial port is closed on cleanup."""
        if self.serial and self.serial.is_open: # Check if serial port is open before trying to close
            self.serial.close()


class SGP30Sensor(Sensor):
    """TVOC and CO2 sensor using I2C communication."""
    
    def __init__(self):
        import time
        self.sensor: Optional[adafruit_sgp30.Adafruit_SGP30] = None
        
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            
            while not i2c.try_lock():
                time.sleep(0.1)
            i2c.unlock()
            
            time.sleep(2)
            
            # Try to initialize sensor up to 5 times
            for attempt in range(5):
                try:
                    self.sensor = adafruit_sgp30.Adafruit_SGP30(i2c)
                    self.sensor.iaq_init()
                    time.sleep(1)
                    print("SGP30 sensor initialised successfully")
                    break
                except Exception as e:
                    print(f"SGP30 init attempt {attempt + 1}/5 failed: {e}")
                    time.sleep(2)
                    
            if self.sensor is None:
                print("WARNING: SGP30 sensor failed to initialize after 5 attempts")
                
        except Exception as e:
            print(f"CRITICAL: Failed to initialize I2C bus for SGP30: {e}")
            self.sensor = None

    def read(self) -> dict:
        """Read TVOC and CO2 from sensor. Returns dict with 'tvoc_i2c' and 'co2' keys."""
        if self.sensor is None:
            # Sensor failed to initialize (logged in __init__)
            return {"tvoc_i2c": None, "co2": None}

        try:
            return {
                "tvoc_i2c": self.sensor.TVOC,
                "co2": self.sensor.eCO2
            }
        except Exception as e:  # Log the actual error
            print(f"SGP30 read error: {e}")
            return {"tvoc_i2c": None, "co2": None}


class DHT22Sensor(Sensor):
    """Temperature and Humidity Sensor."""

    def __init__(self):
        self.sensor = adafruit_dht.DHT22(board.D17)

    def read(self) -> dict:  # Type hint for return
        """Read temperature and humidity. Returns dict with sensor readings or None values."""
        try:
            return {
                "Temperature": self.sensor.Temperature,
                "Humidity": self.sensor.humidity
            }
        except RuntimeError as e:
            print(f"DHT22 read error: {e}")
            return {"Temperature": None, "Humidity": None}


class MQ7Sensor(Sensor):
    """Carbon Monoxide Sensor (Digital Output)."""

    def __init__(self):
        self.sensor = DigitalInputDevice(23, pull_up=False) # GPIO pin 23 

    def read(self) -> dict:  # Type hint for return
        """Read CO sensor status. Returns dict with 'co' key (True if gas detected)."""
        return {"co": self.sensor.is_active}

# Sensor Manager

class SensorManager:
    """Manages multiple sensors and aggregates their data."""

    def __init__(self):
        self.sensors: list = [] # List of Sensor instances

    def add_sensor(self, sensor: Sensor) -> None:  # Type hints
        """Add a sensor to the manager."""
        self.sensors.append(sensor)

    def read_all(self) -> dict:  # Type hints with return type
        """Read all sensors and aggregate data into single dictionary."""
        readings = {} # Aggregate all sensor readings into a single dictionary

        for sensor in self.sensors:
            data = sensor.read()
            readings.update(data)  # Merge sensor data

        return readings

# Air Quality Logic

class AirSensor:
    """Evaluates air quality based on sensor data. [1][2][3][4]"""

    def __init__(self):
        self.tvoc_poor = 300
        self.tvoc_critical = 600

        self.co2_poor = 1000
        self.co2_critical = 2000

        self.temp_poor = 25
        self.temp_critical = 30

        self.hum_poor = 60
        self.hum_critical = 75

    def check_air_quality(self, data: dict) -> dict:  # Type hints for parameter and return
        """Check air quality and return dictionary of issues found."""
        issues = {}

        # Carbon Monoxide overrides everything
        if data.get("co") is True:
            return {"co": "CRITICAL"}

        tvoc = data.get("tvoc_i2c") or data.get("tvoc_uart")
        co2 = data.get("co2")
        temp = data.get("Temperature")
        hum = data.get("Humidity")

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
                issues["Temperature"] = "CRITICAL"
            elif temp > self.temp_poor:
                issues["Temperature"] = "POOR"

        if hum is not None:
            if hum > self.hum_critical:
                issues["Humidity"] = "CRITICAL"
            elif hum > self.hum_poor:
                issues["Humidity"] = "POOR"

        return issues



# Main Program

if __name__ == "__main__":
    try:
        mqtt_client = MQTTPublisher()  # Initialie MQTT Publisher
        manager = SensorManager() # Create Sensor Manager and add all sensors

        manager.add_sensor(TVOCSensor()) # TVOC sensor using UART
        manager.add_sensor(DHT22Sensor()) # Temperature and Humidity sensor
        manager.add_sensor(MQ7Sensor()) # Carbon Monoxide sensor (digital output)
        manager.add_sensor(SGP30Sensor()) # TVOC and CO2 sensor using I2C

        air_sensor = AirSensor() # Air quality evaluation logic
        previous_issues = {} # Track previous issues to avoid redundant alerts 

        print("Starting Sensor System")

        while True:
            readings = manager.read_all()
            issues = air_sensor.check_air_quality(readings)
            status = get_overall_status(issues)

            # Prepare payload for Flask
            payload = {
                "Pi_ID": 1,
                "Temperature": readings.get("Temperature"),
                "Humidity": readings.get("Humidity"),
                "co2": readings.get("co2"),
                "co": readings.get("co"),
                "tvoc": readings.get("tvoc_i2c") or readings.get("tvoc_uart"),
                "status": status,
                "issues": issues,
            }


            
            #Send to MQTT 
            mqtt_client.publish(payload) 

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
            
    except KeyboardInterrupt:
        print("\nSensor system stopped by user")
    except Exception as e:
        print(f"Fatal error in sensor system: {e}")
        raise


# References:
# TVOC Sensor(Organic Compounds):
# [1] https://gpmoldinspection.com/article/what-is-tvoc-air-quality/ 

# Carbon Dioxide:
# [2] https://www.co2meter.com/en-uk/blogs/news/carbon-dioxide-indoor-levels-chart?srsltid=AfmBOoq-kpY_efXM7PtXR0MuDu-OECYW_o4m7gRn0sAuLZ85KX_KnLT1

# Temperature and Humidity:
# [3] https://www.hse.gov.uk/temperature/employer/managing.htm

# [4] https://www.hse.gov.uk/foi/internalops/ocs/300-399/oc311_2.htm


# Things to do:
# Check over co and co2 naming consistency between sensors and Flask app. 