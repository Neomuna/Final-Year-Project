# Unified Sensor System for Raspberry Pi (Refactored)
# This program has been refactored by CoPilot and myself. Fixing a few secuity issues, improving code structure and error handling. 
# I've removed TVOCs from the UART sensor as it was unreliable and not essential. 
# Unused imports have been left for MQTT and Flask integration
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
        # MQTT connection details from environment variables 
        self.broker = os.environ["MQTT_BROKER"]
        self.client.username_pw_set(
            os.environ["MQTT_USERNAME"], # Left blank for security
            os.environ["MQTT_PASSWORD"]  # Left blank for security
        )
        
  # Left blank for security
        self.port = 8883                  
        self.topic = "sensors/air_quality" 

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)


        # Enable TLS for secure connection
        self.client.tls_set()

        try:
            self.client.connect(self.broker, self.port, 60)
            print(f"Connected to HiveMQ broker at {self.broker}")
        except Exception as e:
            print(f"MQTT connection failed: {e}")
        
    def publish(self, payload: dict):
        try:
            self.client.publish(self.topic, json.dumps(payload))
            print("Published:", payload)
        except Exception as e:
            print(f"Publish failed: {e}")

# Base Sensor Class
class Sensor:
    """Base class for all sensors."""

    def read(self) -> dict[str, float]:
        """Return sensor data as a dictionary."""
        raise NotImplementedError


# Air Quality Evaluation Logic 
def get_overall_status(issues: dict) -> list[str]:  # Type hints
    """Convert issues dict into a single status string."""
    if not issues:
        return ["GOOD"]
    if "CRITICAL" in issues.values():
        return ["CRITICAL"]
    return ["POOR"]
 
# Sensor Implementations

class SGP30Sensor(Sensor):
    """TVOC and CO2 sensor using I2C communication."""
    
    def __init__(self):
        import time
        self.sensor: Optional[adafruit_sgp30.Adafruit_SGP30] = None
        
        try:
            i2c = busio.I2C(board.SCL, board.SDA) # Initialize I2C bus
            
            while not i2c.try_lock(): # Wait for I2C bus to be available
                time.sleep(0.1)
            i2c.unlock() # Release the bus after checking
            
            time.sleep(2)
            
            # Try to initialize sensor up to 5 times
            for attempt in range(5):
                try:
                    self.sensor = adafruit_sgp30.Adafruit_SGP30(i2c) # Attempt to initialize sensor
                    self.sensor.iaq_init() # Initialize IAQ algorithm
                    time.sleep(1)
                    print("SGP30 sensor initialised successfully")
                    break
                except Exception as e: 
                    print(f"SGP30 init attempt {attempt + 1}/5 failed: {e}") # Log the actual error for debugging
                    time.sleep(2)
                    
            if self.sensor is None:
                print("WARNING: SGP30 sensor failed to initialise after 5 attempts")
                
        except Exception as e:
            print(f"CRITICAL: Failed to initialise I2C bus for SGP30: {e}")
            self.sensor = None

    def read(self) -> dict[str, float]:  # Type hint for return type
        """Read TVOC and CO2 from sensor. Returns dict with 'tvoc_i2c' and 'co2' keys."""
        if self.sensor is None:
            # Sensor failed to initialise (logged in __init__)
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
    def __init__(self):
        self.sensor = adafruit_dht.DHT22(board.D4)

    def read(self) -> dict[str, float]:  # Type hint for return type
        try:
            temperature = self.sensor.temperature
            humidity = self.sensor.humidity

            return {
                "Temperature": round(temperature, 2) if temperature else None, # Round to 2 decimal places for consistency
                "Humidity": round(humidity, 2) if humidity else None # Round to 2 decimal places for consistency
            }

        except RuntimeError as e:
            print(f"DHT22 read error: {e}")
            return {"Temperature": None, "Humidity": None}

class MQ7Sensor(Sensor):
    """Carbon Monoxide Sensor (Digital Output)."""

    def __init__(self):
        self.sensor = DigitalInputDevice(23, pull_up=False) # GPIO pin 23 

    def read(self) -> dict[str, bool]:  # Type hint for return type
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

    def read_all(self) -> dict[str, float]:  # Type hints with return type
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
        self.tvoc_poor = 300 # Poor air quality threshold for TVOC
        self.tvoc_critical = 600 # Critical air quality threshold for TVOC

        self.co2_poor = 1000 # Poor air quality threshold for CO2
        self.co2_critical = 2000 # Critical air quality threshold for CO2

        self.temp_poor = 25 # Poor air quality threshold for temperature (°C)
        self.temp_critical = 30 # Critical air quality threshold for temperature (°C)

        self.hum_poor = 60 # Poor air quality threshold for humidity (%)
        self.hum_critical = 75 # Critical air quality threshold for humidity (%)

    def check_air_quality(self, data: dict) -> dict[str,]:  # Type hints for parameter and return
        """Check air quality and return dictionary of issues found."""
        issues = {}

        # Carbon Monoxide overrides everything
        if data.get("co") is True: # If CO sensor detects gas, it's considerd critical regardless of other readings
            return {"co": "CRITICAL"}

        tvoc = data.get("tvoc_i2c") # TVOC reading from I2C sensor
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
                "CO2_reading": readings.get("co2"),
                "CO_Reading": 1 if readings.get("co") else 0,
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
# Add TVOC to database  