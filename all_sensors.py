import time
import lgpio
import board
import busio
import adafruit_sgp40
import adafruit_sgp30
import adafruit_dht

# Intialize sensors
# MQ-7 CO sensor setup
MQ7_PIN = 17

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h, MQ7_PIN)

# I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# SGP40 TVOC sensor
sgp40 = adafruit_sgp40.SGP40(i2c)

# SGP30 air quality sensor
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)
sgp30.iaq_init()

# DHT22 temperature/humidity
dht = adafruit_dht.DHT22(board.D4)

# Main loop to read sensors
while True:

    try:
        # DHT22
        temperature = dht.temperature
        humidity = dht.humidity

        # SGP30
        eco2 = sgp30.eCO2
        tvoc_sgp30 = sgp30.TVOC

        # SGP40
        tvoc_raw = sgp40.raw

        # MQ7 digital detection
        gas_detected = lgpio.gpio_read(h, MQ7_PIN)

        if gas_detected == 0:
            mq7_status = "CO Detected!"
        else:
            mq7_status = "No CO detected, happy days!"

        print(" Sensor Readings ")
        print(f"Temperature: {temperature} C")
        print(f"Humidity: {humidity} %")
        print(f"eCO2: {eco2} ppm")
        print(f"TVOC (SGP30): {tvoc_sgp30} ppb")
        print(f"TVOC Raw (SGP40): {tvoc_raw}")
        print(f"CO (MQ-7): {mq7_status}")

    except RuntimeError as error:
        print("Sensor error:", error)

    except Exception as error:
        print("Unexpected error:", error)

    time.sleep(2)