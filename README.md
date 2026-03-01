# rokenbok-webserver

A Python Flask application for hosting a Rokenbok multiplayer web interface.

Configuration is done entirely within the [rokenbok_webserver.ini](/rokenbok_webserver.ini) file the server reads on startup. All available options are noted there.

## Supported Devices

Currently, the server supports the first generation Rokenbok CommandDeck with the SmartPort adapter. An Arduino is used to connect to that SmartPort and receive commands from the server over Serial/USB to control the connected vehicles. See the [smartport_arduino](/smartport_arduino) for the Arduino code and information on connecting it.

### Extending device support

This server was designed to support mulitple types of vehicles behind multiple different control devices all at the same time. Vehicle functionality is exposed via the `Vehicle` abstract class within [rokenbok_device.py](/rokenbok_device.py). See `SmartPortArduino` as an example of implementing the base class methods along with device specific ones.
