import argparse
import serial
import signal
import sys
from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO
from upnp import UPnPPortMapper

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)

class CommandDeck:
    def __init__(self, serial_device=None):
        self.smartport = None
        if serial_device is not None:
            self.smartport = serial.Serial(serial_device, 115200, timeout=1)
            print(f"Connected to SmartPort device at {serial_device}")
        else:
            print("No SmartPort device specified, will only print commands for debugging")

    def send_command(self, action, controller, value):
        if self.smartport is not None:
            self.smartport.write(bytes([action, controller, value]))
        else:
            print(f"DEBUG - Action: {action} Controller: {controller} Value: {value}")

testing_controller = 4 # VIRTUAL_CONTROLLER_1

rok_action = {
  "press": 0,
  "release": 1,
  "edit": 2,
  "enable": 3,
  "disable": 4,
  "reset": 5
}

button_map = {
    0: {'name': 'a', 'rok_cmd': 8},
    1: {'name': 'b', 'rok_cmd': 9}
}

@socketio.on('gamepad')
def handle_gamepad(data):
    button_index = data['button']
    pressed = data['pressed']
    
    if button_index in button_map:
        btn = button_map[button_index]
        action = "press" if pressed else "release"
        command_deck.send_command(rok_action[action], testing_controller, btn['rok_cmd'])

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/control.js')
def script():
    return send_from_directory('static', 'control.js')

@app.route('/press', methods=['POST'])
def press():
    data = request.json
    command_deck.send_command(rok_action["press"], data['controller'], data['button'])
    return "OK"

@app.route('/release', methods=['POST'])
def release():
    data = request.json
    command_deck.send_command(rok_action["release"], data['controller'], data['button'])
    return "OK"

@app.route('/edit', methods=['POST'])
def edit():
    data = request.json
    command_deck.send_command(rok_action["edit"], data['controller'], data['selection'])
    return "OK"

@app.route('/enable', methods=['POST'])
def enable():
    command_deck.send_command(rok_action["enable"], request.json['controller'], 0)
    return "OK"

@app.route('/disable', methods=['POST'])
def disable():
    command_deck.send_command(rok_action["disable"], request.json['controller'], 0)
    return "OK"

@app.route('/reset', methods=['POST'])
def reset():
    command_deck.send_command(rok_action["reset"], 0, 0)
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
    
    args = parser.parse_args()
    
    command_deck = CommandDeck(serial_device=args.device)

    if args.upnp == "enable":
        print("Trying to open port via UPnP")
        upnp_mapper = UPnPPortMapper(args.port, args.port, args.ip, "SmartPort Web Server")
    socketio.run(app.run(host=args.ip, port=args.port))
