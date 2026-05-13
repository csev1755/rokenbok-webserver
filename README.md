# rokenbok-webserver 

[![Download Latest](https://img.shields.io/github/v/release/csev1755/rokenbok-webserver?style=for-the-badge&label=download%20latest&color=green)](https://github.com/csev1755/rokenbok-webserver/releases/latest)

A Python Flask application that serves a Rokenbok multiplayer web interface with optional live video. Download and extract, edit [rokenbok_webserver.ini,](/rokenbok_webserver.ini) and run the executable!

## Supported Devices

Currently, the server supports the first generation Rokenbok CommandDeck with the SmartPort adapter. An Arduino is used to connect to that SmartPort and receive commands from the server over Serial/USB to control the connected vehicles. See [smartport_arduino](/devices/smartport_arduino) for the Arduino code and information on connecting it.

### Extending device support

This server was designed to support mulitple types of vehicles behind multiple different control devices all at the same time. Functionality is exposed via the [Vehicle](/devices/vehicle.py) abstract class.
