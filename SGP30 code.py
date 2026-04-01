# Ai helper code for SGP30 sensor integration - this is a test file to experiment with the SGP30 sensor code before integrating it into the main all_sensors.py file.
class SGP30Sensor(Sensor):
    def __init__(self):
        import busio
        import adafruit_sgp30
        import board
        import time

        i2c = busio.I2C(board.SCL, board.SDA)

        # Wait for I2C to be ready
        while not i2c.try_lock():
            time.sleep(0.1)
        i2c.unlock()

        time.sleep(2)  # 🔥 longer delay (important)

        self.sensor = None

        # Retry init multiple times
        for attempt in range(5):
            try:
                self.sensor = adafruit_sgp30.Adafruit_SGP30(i2c)
                self.sensor.iaq_init()
                time.sleep(1)
                print("SGP30 initialised")
                break
            except Exception as e:
                print(f"SGP30 init failed (attempt {attempt+1}): {e}")
                time.sleep(2)

        if self.sensor is None:
            print("SGP30 failed to initialise")

    def read(self):
        if self.sensor is None:
            return {"tvoc_i2c": None, "co2": None}

        try:
            return {
                "tvoc_i2c": self.sensor.TVOC,
                "co2": self.sensor.eCO2
            }
        except Exception:
            return {"tvoc_i2c": None, "co2": None}