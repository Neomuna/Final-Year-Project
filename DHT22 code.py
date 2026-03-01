# DHT22 code for Raspberry Pi

# pip these packages before running the code:
#pip install adafruit-circuitpython-dht



import time
import board
import adafruit_dht

dht = adafruit_dht.DHT22(board.D4)

while True:
    try:
        print("Temp:", dht.temperature)
        print("Humidity:", dht.humidity)
    except RuntimeError:
        pass
    time.sleep(2)
    