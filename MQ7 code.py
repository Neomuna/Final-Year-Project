# MQ7 code

# pip installs below 
"""
sudo apt update
sudo apt install python3-lgpio
""" 


import lgpio
import time

# Configuration change this as needed 
CHIP = 0          # Default GPIO chip
SENSOR_PIN = 17   # GPIO pin connected to DO
SLEEP_TIME = 1    # Check every second

# Initialize the GPIO chip
h = lgpio.gpiochip_open(CHIP)

# Set the pin as an input
try:
    lgpio.gpio_claim_input(h, SENSOR_PIN)
    
    print("MQ-7 Sensor Warming Up... (Wait ~30s)")
    time.sleep(2) # Short delay for script start
    print("Monitoring for CO...")

    while True:
        # Read the digital state
        # Note: Most MQ modules are 'Active Low' (0 = Gas Detected)
        state = lgpio.gpio_read(h, SENSOR_PIN)

        if state == 0:
            print("Carbon Monoxide Detected!")
        else:
            print("System Clear: No significant CO levels.")

        time.sleep(SLEEP_TIME)

except KeyboardInterrupt:
    print("\nStopping sensor monitor...")

finally:
    # Clean up and release the GPIO
    if 'h' in locals():
        lgpio.gpiochip_close(h)