import serial
import time

ser = serial.Serial('COM3', 115200)
time.sleep(2)

# enabled_controllers
ser.write(bytes([0x01, 0b11101111]))

# selects[0] = 0x06
ser.write(bytes([0x02, 0x00, 0x06]))

# sp_up = 0x10
ser.write(bytes([0x03, 0x10]))
