# DHT22 code for Raspberry Pi

# pip these packages before running the code:
#pip install adafruit-circuitpython-dht
#sudo apt install libgpiod2


import time
import board
import adafruit_dht

# GPIO4 = BCM 4
dhtDevice = adafruit_dht.DHT22(board.D4)

while True:
    try:
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity

        print(f"Temperature: {temperature}°C  Humidity: {humidity}%")

    except RuntimeError as error:
        # DHT sensors are an issue, this should resolve itself
        print(f"Reading error: {error}")

    time.sleep(1)