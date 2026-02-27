
# TVOC sensor (SGP40)
import time
import board
import busio
import adafruit_sgp40
import adafruit_dht

# I2C setup
i2c = busio.I2C(board.SCL, board.SDA)
sgp = adafruit_sgp40.SGP40(i2c)

# DHT22 setup
dht = adafruit_dht.DHT22(board.D4)

while True:
    try:
        temperature = dht.temperature
        humidity = dht.humidity

        voc_index = sgp.measure_index(temperature=temperature, relative_humidity=humidity)

        print("Temperature:", temperature)
        print("Humidity:", humidity)
        print("VOC Index:", voc_index)
        print("------------------")

    except RuntimeError:
        pass

    time.sleep(2)