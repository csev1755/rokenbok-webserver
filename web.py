import argparse
import signal
import sys
from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO
from rokenbok_control import CommandDeck
from rokenbok_device import Commands as Rokenbok
from upnp import UPnPPortMapper

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/control.js')
def script():
    return send_from_directory('static', 'control.js')

@app.route('/press', methods=['POST'])
def press():
    controller = command_deck.get_controller(Rokenbok.ControllerIdentifier(request.json['controller']))
    controller.press(Rokenbok.ControllerCommand(request.json['value']))
    return "OK"

@app.route('/release', methods=['POST'])
def release():
    controller = command_deck.get_controller(Rokenbok.ControllerIdentifier(request.json['controller']))
    controller.release(Rokenbok.ControllerCommand(request.json['value']))
    return "OK"

@app.route('/edit', methods=['POST'])
def edit():
    controller = command_deck.get_controller(Rokenbok.ControllerIdentifier(request.json['controller']))
    controller.select(Rokenbok.VehicleKey(request.json['value']))
    return "OK"

@app.route('/enable', methods=['POST'])
def enable():
    controller = command_deck.get_controller(Rokenbok.ControllerIdentifier(request.json['controller']))
    controller.enable()
    return "OK"

@app.route('/disable', methods=['POST'])
def disable():
    controller = command_deck.get_controller(Rokenbok.ControllerIdentifier(request.json['controller']))
    controller.disable()
    return "OK"

@app.route('/reset', methods=['POST'])
def reset():
    command_deck.send_command(Rokenbok.DeviceCommand.RESET)
    return "OK"

@socketio.on('gamepad')
def handle_gamepad(data):
    controller = command_deck.get_controller(Rokenbok.ControllerIdentifier(data['controller']))
    controller.send_input(data)

def handle_exit(signal, frame):
    print("Program interrupted, performing cleanup...")
    if args.upnp == "enable":
        upnp_mapper.remove_port_mapping()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts the Arduino SmartPort web controller')
    
    parser.add_argument('-d', '--device', help='The type of Rokenbok control device', default=None)
    parser.add_argument('-s', '--serial', help='The serial device name of the control device', default=None)
    parser.add_argument('-i', '--ip', help='What IP the server will listen on', default='')
    parser.add_argument('-p', '--port', help='What port the server will listen on', default=5000)
    parser.add_argument('-u', '--upnp', help='Enable UPnP for auto port forwarding', default='')
    parser.add_argument('-b', '--debug', help='Enable debug output', default='')

    args = parser.parse_args()
    
    command_deck = CommandDeck(device_name=args.device, serial_device=args.serial, debug=args.debug)

    if args.upnp == "enable":
        print("Trying to open port via UPnP")
        upnp_mapper = UPnPPortMapper(args.port, args.port, args.ip, "SmartPort Web Server")

    socketio.run(app.run(host=args.ip, port=args.port))
