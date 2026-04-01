# Unified Sensor System for Raspberry Pi (Refactored)
import time
import serial
import board
import adafruit_dht
import requests 
from gpiozero import DigitalInputDevice
import busio
import adafruit_sgp30
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


class SGP30Sensor(Sensor): #TVOC and CO2 sensor using I2C communication.
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)

        while not i2c.try_lock():
            pass
        i2c.unlock()

        time.sleep(1)

        for _ in range(3):
            try:
                self.sensor = adafruit_sgp30.Adafruit_SGP30(i2c)
                self.sensor.iaq_init()
                time.sleep(1)
                break
            except OSError:
                time.sleep(1)

    def read(self):
        try:
            return {
                "tvoc_i2c": self.sensor.TVOC,
                "co2": self.sensor.eCO2
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
        self.sensor = DigitalInputDevice(23, pull_up=False)

    def read(self):
        return {"co": self.sensor.is_active}

# Sensor Manager

class SensorManager:
    """Manages multiple sensors and aggregates their data."""

    def __init__(self):
        self.sensors = [] # List of Sensor instances

    def add_sensor(self, sensor: Sensor):
        self.sensors.append(sensor)

    def read_all(self): 
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
