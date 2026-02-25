import pigpio
import DHT22
import time

pi = pigpio.pi()
sensor = DHT22.sensor(pi, 4)  # GPIO4

while True:
    sensor.trigger()
    print(f"Temperature: {sensor.temperature()}°C  Humidity: {sensor.humidity()}%")
    time.sleep(1)
