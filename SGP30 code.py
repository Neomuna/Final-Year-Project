class SGP30Sensor(Sensor):
    """TVOC and CO2 sensor using I2C communication."""
    
    i2c = busio.I2C(board.SCL, board.SDA)

    # Wait for I2C to be ready
    while not i2c.try_lock():
        pass

    print("I2C scan:", i2c.scan())
    i2c.unlock()

    # Give sensor time to stabilise
    time.sleep(5)

    sensor = adafruit_sgp30.Adafruit_SGP30(i2c)
    sensor.iaq_init()

    print("SGP30 initialised")

    def read(self):
        if self.sensor is None:
            return {"tvoc_i2c": None, "co2": None}

        try:
            self.sensor.iaq_measure()   

            return {
                "tvoc_i2c": self.sensor.TVOC,
                "co2": self.sensor.eCO2
            }
        except Exception as e:
            print(f"SGP30 read error: {e}")
            return {"tvoc_i2c": None, "co2": None}

