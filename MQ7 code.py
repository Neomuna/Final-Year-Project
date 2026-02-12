# MQ7 code

# pip installs below 
"""
sudo apt update
sudo apt install python3-lgpio
""" 


import lgpio
import time

# Pi 5 GPIO 17
PIN = 17
h = lgpio.gpiochip_open(0)

# Input and ensure the Pi's internal pull-up is off since we are providing the voltage via the sensor
lgpio.gpio_claim_input(h, PIN)

try:
    print("Pi 5 Monitoring MQ-7...")
    while True:
        level = lgpio.gpio_read(h, PIN)
        if level == 0:
            print("CO Detected!")
        time.sleep(0.5)
finally:
    lgpio.gpiochip_close(h)