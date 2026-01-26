import serial
import sys
import time

key7 = 0x06
controller_bit = 0b00010000 # V4|V3|V2|V1|P4|P3|P2|P1
enabled_controllers = 0b11101111 # V4|V3|V2|V1|P4|P3|P2|P1 // 0 = Enabled, 1 = Disabled
controller_id = 0 # array position: V1, V2, V3, V4, P1, P2, P3, P4, D1, D2, D3, D4

controller_status_cmd = 0x01
select_cmd = 0x02
button = 0x03

delay = 3

ser = serial.Serial(sys.argv[1], 115200)
time.sleep(2) # breaks without this

ser.write(bytes([controller_status_cmd, enabled_controllers]))

ser.write(bytes([select_cmd, controller_id, key7]))

while True:
    ser.write(
        bytes([button, 0x00, 0x00, 0x00, 0x00, controller_bit, 0x00, 0x00, 0x00, 0x00]))

    time.sleep(delay)

    ser.write(
        bytes([button, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))

    time.sleep(delay)