# Unified Sensor System for Raspberry Pi
import time
import serial
import board
import adafruit_dht
import adafruit_sht4x
from gpiozero import DigitalInputDevice
from sgp30 import SGP30
from smbus import SMBus

# SETUP

# UART (TVOC)
ser = serial.Serial(
    port='/dev/serial10',
    baudrate=9600,
    bytesize=8,
    parity='N',
    stopbits=1,
    timeout=1
)

READ_TVOC = bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x01, 0x84, 0x0A]) 

# DHT22
dht = adafruit_dht.DHT22(board.D4)

# MQ-7 (Digital)
mq7 = DigitalInputDevice(17, pull_up=True, active_state=False)

# SGP30
i2c_bus = SMBus(1)
sgp30 = SGP30(i2c_bus)

# SHT45
i2c = board.I2C()
sht = adafruit_sht4x.SHT45(i2c)
sht.mode = adafruit_sht4x.Mode.HIGH


# SENSOR FUNCTIONS

def read_tvoc():
    try:
        ser.write(READ_TVOC)
        time.sleep(0.1)
        data = ser.read(7)

        if len(data) != 7:
            return None

        tvoc = (data[3] << 8) | data[4]
        return tvoc
    except:
        return None


def read_dht22():
    try:
        return dht.temperature, dht.humidity
    except RuntimeError:
        return None, None


def read_mq7():
    return mq7.is_active  # True = gas detected


def read_sgp30():
    try:
        aq = sgp30.air_quality()
        return aq.voc_ppb, aq.co2_ppm
    except:
        return None, None


def read_sht45():
    try:
        return sht.temperature, sht.relative_humidity
    except:
        return None, None


# MAIN LOOP

print("Starting unified sensor system...\n")

while True:
    # TVOC
    tvoc = read_tvoc()
    if tvoc is not None:
        print(f"TVOC: {tvoc} ppb")
    else:
        print("TVOC: No data")

    # DHT22
    temp, hum = read_dht22()
    if temp is not None:
        print(f"DHT22 Temp: {temp:.2f} °C | Humidity: {hum:.2f}%")
    else:
        print("DHT22: Error reading")

    # MQ-7
    if read_mq7():
        print("Carbon Monoxide Detected!")
    else:
        print("Air safe")

    # SGP30 
    voc, co2 = read_sgp30()
    if voc is not None:
        print(f"SGP30 VOC: {voc} ppb | CO2: {co2} ppm")
    else:
        print("SGP30: Error")

    # SHT45 
    t2, h2 = read_sht45()
    if t2 is not None:
        print(f"SHT45 Temp: {t2:.2f} °C | Humidity: {h2:.2f}%")
    else:
        print("SHT45: Error")

    print("-" * 40)

    time.sleep(2)