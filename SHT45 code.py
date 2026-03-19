#SHT 45 code
import time
import board
import adafruit_sht4x

# Create the I2C bus interface
i2c = board.I2C()  # uses board.SCL and board.SDA

# Initialize the SHT45 sensor
# The SHT45 uses the same driver as the SHT45 series
sht = adafruit_sht4x.SHT45(i2c)

print("Found the sensor!")

# Setting the precision of the sensor: HIGH, MEDIUM, LOW. This affects the measurement time and power consumption.
sht.mode = adafruit_sht4x.Mode.HIGH

while True:
    # Get temperature and humidity readings
    temperature = sht.temperature
    humidity = sht.relative_humidity

    # Print the values formatted to two decimal places
    print(f"Temperature: {temperature:.2f} °C")
    print(f"Humidity: {humidity:.2f} %")
    print("-" * 25)

    time.sleep(1)