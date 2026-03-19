import serial
import time

# Open UART port on Pi 
ser = serial.Serial(
    port = '/dev/serial10',
    baudrate = 9600,
    bytesize = 8,
    parity = 'N',
    stopbits = 1,
    timeout = 1 
)

# Waveshare TVOC UART query
READ_TVOC =bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x01, 0x84, 0x0A])

def read_tvoc():
    ser.write(READ_TVOC)
    time.sleep(0.1)
    data = ser.read(7) # Expect exactly 7 bytes

    if len(data) !=7:
        return None

    # Parse response 
    high = data[3]
    low = data[4]
    tvoc = (high << 8) | low
    return tvoc 

while True:
    value = read_tvoc()
    if value is not None:
        print("TVOC:", value, "ppb")
    else: 
        print("No data is being received")
    time.sleep(1) 
