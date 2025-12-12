import argparse
import signal
import sys
from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO
from upnp import UPnPPortMapper
from smartport_arduino import CommandDeck

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)

@socketio.on('gamepad')
def handle_gamepad(data):
    controller.send_input(data)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/control.js')
def script():
    return send_from_directory('static', 'control.js')

@app.route('/press', methods=['POST'])
def press():
    data = request.json
    command_deck.send_command(command_deck.Command.PRESS, data['controller'], data['button'])
    return "OK"

@app.route('/release', methods=['POST'])
def release():
    data = request.json
    command_deck.send_command(command_deck.Command.RELEASE, data['controller'], data['button'])
    return "OK"

@app.route('/edit', methods=['POST'])
def edit():
    data = request.json
    command_deck.send_command(command_deck.Command.EDIT, data['controller'], data['selection'])
    return "OK"

@app.route('/enable', methods=['POST'])
def enable():
    command_deck.send_command(command_deck.Command.ENABLE, request.json['controller'])
    return "OK"

@app.route('/disable', methods=['POST'])
def disable():
    command_deck.send_command(command_deck.Command.DISABLE, request.json['controller'])
    return "OK"

@app.route('/reset', methods=['POST'])
def reset():
    command_deck.send_command(command_deck.Command.RESET)
    return "OK"

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
    parser.add_argument('-c', '--controller', help='Override controller used by webserver', default=4)

    args = parser.parse_args()
    
    command_deck = CommandDeck(serial_device=args.device)
    controller = command_deck.Controller(command_deck, 4, 6)

    if args.upnp == "enable":
        print("Trying to open port via UPnP")
        upnp_mapper = UPnPPortMapper(args.port, args.port, args.ip, "SmartPort Web Server")
    socketio.run(app.run(host=args.ip, port=args.port))
