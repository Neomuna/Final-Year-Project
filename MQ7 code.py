"""
from gpiozero import DigitalInputDevice
from signal import pause

# 'pull_up=True' and 'active_state=False' 
# tells the Pi that 0V means "Active/Alarm"
sensor = DigitalInputDevice(17, pull_up=True, active_state=False)

def gas_detected():
    print("Warning! Carbon monoxide detected!")

def gas_cleared():
    print("Air is clear. You're safe!")

#Set up event handlers for the sensor
sensor.when_activated = gas_detected
sensor.when_deactivated = gas_cleared

print("MQ-7 Monitoring Active. Press Ctrl+C to stop.")
pause()
"""

import RPi.GPIO as GPIO # This now uses rpi-lgpio under the hood
import time

# Use BCM numbering (GPIO 17)
GPIO.setmode(GPIO.BCM)

SENSOR_PIN = 17
# Set as input. We often use a pull-up to keep the signal steady.
GPIO.setup(SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("MQ-7 Sensor Initialized. Waiting for stable reading...")

try:
    while True:
        if GPIO.input(SENSOR_PIN) == GPIO.LOW:
            print("CO Detected!")
        else:
            print("All clear")
            
        time.sleep(1) 

except KeyboardInterrupt:
    print("\nCleaning up...")
    GPIO.cleanup()
