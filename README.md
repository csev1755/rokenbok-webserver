# rokenbok-webserver
A Python Flask application to control Rokenbok over the internet
## [web.py](/web.py)
A Flask webserver that emulates Command Deck functions with input over WebSockets

## [rokenbok_device.py](/rokenbok_device.py)
A module called by the webserver to control a Rokenbok device like a SmartPort adapter ([smartport-arduino](/smartport-arduino))

## [upnp.py](/upnp.py)
A module that can be used by the webserver to open its port on a router via UPnP
