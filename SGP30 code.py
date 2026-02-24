# SGP30 code
import time
from sgp30 import SGP30
from smbus import SMBus 
ssmbus = SMBus(1) # I2C bus 1


with SGP30(ssmbus) as sgp30:
    while True:
        aq = sgp30.air_quality()
        V = aq.voc_ppb 
        C = aq.co2_ppm

        print(V,C)
        time.sleep(1) 


