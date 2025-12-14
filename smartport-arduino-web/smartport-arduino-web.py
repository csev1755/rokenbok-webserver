import argparse
import signal
import sys
from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO
from upnp import UPnPPortMapper
from smartport_arduino import CommandDeck

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
    controller = command_deck.Controller(command_deck, request.json['controller'])
    controller.release(request.json['value'])
    return "OK"

@app.route('/release', methods=['POST'])
def release():
    controller = command_deck.Controller(command_deck, request.json['controller'])
    controller.press(request.json['value'])
    return "OK"

@app.route('/edit', methods=['POST'])
def edit():
    controller = command_deck.Controller(command_deck, request.json['controller'])
    controller.select(request.json['value'])
    return "OK"

@app.route('/enable', methods=['POST'])
def enable():
    controller = command_deck.Controller(command_deck, request.json['controller'])
    controller.enable()
    return "OK"

@app.route('/disable', methods=['POST'])
def disable():
    controller = command_deck.Controller(command_deck, request.json['controller'])
    controller.disable()
    return "OK"

@app.route('/reset', methods=['POST'])
def reset():
    command_deck.send_command(command_deck.Command.RESET)
    return "OK"

@socketio.on('gamepad')
def handle_gamepad(data):
    controller = command_deck.Controller(command_deck, data['controller'])
    controller.send_input(data)

def handle_exit(signal, frame):
    print("Program interrupted, performing cleanup...")
    if args.upnp == "enable":
        upnp_mapper.remove_port_mapping()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts the Arduino SmartPort web controller')
    
    parser.add_argument('-d', '--device', help='The serial device name of your Arduino', default=None)
    parser.add_argument('-i', '--ip', help='What IP the server will listen on', default='')
    parser.add_argument('-p', '--port', help='What port the server will listen on', default=5000)
    parser.add_argument('-u', '--upnp', help='Enable UPnP for auto port forwarding', default='')

    args = parser.parse_args()
    
    command_deck = CommandDeck(serial_device=args.device)

    if args.upnp == "enable":
        print("Trying to open port via UPnP")
        upnp_mapper = UPnPPortMapper(args.port, args.port, args.ip, "SmartPort Web Server")
    socketio.run(app.run(host=args.ip, port=args.port))
