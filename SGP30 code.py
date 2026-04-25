class SGP30Sensor(Sensor):
    """TVOC and CO2 sensor using I2C communication."""

    def __init__(self): # Initializes the SGP30 sensor by setting up the I2C communication and initializing the sensor itself. It also handles any exceptions that may occur during initialization and sets the sensor to None if it fails.
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA) # Attempt to acquire the I2C lock. This is necessary to ensure that the bus is not being used by another process or thread. If the lock cannot be acquired, it will keep trying until it succeeds. 
            while not self.i2c.try_lock(): 
                pass 
            print("I2C scan:", self.i2c.scan()) # Scans for I2c as conformation of acquisition
            self.i2c.unlock() # Releases the I2C lock after scanning. This allows other processes or threads to use the I2C bus if needed.
            time.sleep(2) 

            self.sensor = adafruit_sgp30.Adafruit_SGP30(self.i2c) # Initialises the SGP30 sensor using the I2C interface. This creates an instance of the Adafruit_SGP30 class, which provides methods for interacting with the sensor.
            self.sensor.iaq_init() # Initializes the Indoor Air Quality (IAQ) algorithm of the SGP30 sensor. This is necessary to start measuring TVOC and CO2 levels accurately.

            print("SGP30 initialised")

        except Exception as e:
            print(f"SGP30 init failed: {e}") 
            self.sensor = None

    def read(self): #Reading the TVOC and CO2 levels from sensor
        if self.sensor is None:
            return {"tvoc_i2c": None, "co2": None} # If the sensor was not initialized successfully, it returns a dictionary with None values for TVOC and CO2.
        try:
            self.sensor.iaq_measure() # Measures the current TVOC and CO2 levels using the SGP30 sensor. This method updates the internal state of the sensor object with the latest readings.
            return {
                "tvoc_i2c": self.sensor.TVOC, #
                "co2": self.sensor.eCO2
            }

        except Exception as e:
            print(f"SGP30 read error: {e}")
            return {"tvoc_i2c": None, "co2": None}