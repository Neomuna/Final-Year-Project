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
