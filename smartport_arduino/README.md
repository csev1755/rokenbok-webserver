# smartport_arduino
An Arduino sketch that listens to commands from its USB serial interface to perform commands via the SmartPort protocol

## SmartPort pinout

![SmartPort diagram](./mini_din_6.jpg)

| SmartPort | Arduino | Function |
|---|---|---|
| 1 | 13 | Serial Clock |
| 2 | 12 | MISO |
| 3 | 11 | MOSI |
| 4 | - | Frame End |
| 5 | 8 | Slave Ready |
| 6 | GND | Ground |
| - | 9 * | Slave Ready (Virtual) |
| - | 10 * | Slave Select |

*\* Pins 9 and 10 connect to eachother instead of the SmartPort*

## Other projects

### https://github.com/stepstools/Rokenbok-Smart-Port-WiFi
Custom ESP32 controller with web interface

### https://github.com/jordan-woyak/rokenbok-smart-port
Arduino controller

### https://github.com/rgill02/rokenbok
Arduino controller with Python client, server, and hub
