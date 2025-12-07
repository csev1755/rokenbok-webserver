import argparse
import serial
from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)

class CommandDeck:
    def __init__(self, serial_device):
        self.smartport = serial.Serial(serial_device, 115200, timeout=1)

    def send_command(self, action, controller, value):
        self.smartport.write(bytes([action, controller, value]))

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts the Arduino SmartPort web controller')
    
    parser.add_argument('serial_device', help='The serial device name of your Arduino')
    parser.add_argument('-i', '--ip', help='What IP the server will listen on', default='0.0.0.0')
    parser.add_argument('-p', '--port', help='What port the server will listen on', default='5000')
    
    args = parser.parse_args()
    
    command_deck = CommandDeck(serial_device=args.serial_device)
    app.run(host=args.ip, port=args.port)
    socketio.run(app)
