import configparser
import logging
import os
import signal
import sys
from flask import Flask, request, send_from_directory, render_template
from flask_socketio import SocketIO
from rokenbok_device import Commands as Rokenbok
from rokenbok_device import SmartPortArduino
from upnp import UPnPPortMapper

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    app_dir = os.path.abspath(os.path.dirname(sys.executable))
else:
    app_dir = "."

web_dir = "web"

log = logging.getLogger()
app = Flask(__name__, static_folder=web_dir, template_folder=web_dir)
config = configparser.ConfigParser()
config.optionxform = str
config_file = f"{app_dir}/rokenbok_webserver.ini"
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('player.html', enable_video=config['webserver'].getboolean('enable_video'), video_streams=config['video_streams'])

@app.route('/player.js')
def script():
    return send_from_directory('web', 'player.js')

@socketio.on("connect")
def handle_connect():
    command_deck.assign_controller(request.sid)
    socketio.emit("players", {"players": command_deck.get_players()})

@socketio.on("disconnect")
def handle_disconnect():
    command_deck.release_controller(request.sid)
    socketio.emit("players", {"players": command_deck.get_players()})

@socketio.on("controller")
def handle_controller(data):
    controller = command_deck.get_controller(request.sid)
    if controller:
        controller.player_name = data['player_name']
        controller.send_input(data)

class CommandDeck:
    """Represents a Command Deck and provides methods to communicate with it.

    Attributes:
        device: The underlying hardware device interface, if configured.
        controllers (dict): Mapping of controller identifiers to Controller instances.
        vehicle_count (int): Number of selectable vehicles.
    """

    def __init__(self, **kwargs):
        """
        Initializes the CommandDeck and connects to a specified hardware device.

        Keyword Args:
            device_name (str): Identifier for the control device type.
            serial_device (str): Serial port path for the control device.
        """
        self.device = None

        if kwargs['device_name'] == "smartport-arduino":
            self.device = SmartPortArduino(kwargs['serial_device'])
        else:
            app.logger.warning("Invalid device or no device specified")

        self.controllers: dict[Rokenbok.ControllerIdentifier, CommandDeck.Controller] = {}
        self.vehicle_count = 15

        for cid in Rokenbok.ControllerIdentifier:
            self.controllers[cid] = self.Controller(self, cid)

    def assign_controller(self, player_id):
        """
        Assigns an available controller to a client session.

        Args:
            player_id (str): Socket.IO session identifier.

        Returns:
            Controller or None: The assigned controller, or None if none are available.
        """
        for controller in self.controllers.values():
            if controller.player_id is None:
                controller.player_id = player_id
                app.logger.info(f"Assigned {controller.index} to {player_id}")
                return controller
        app.logger.warning(f"No controller available for {player_id}")
        return None

    def release_controller(self, player_id):
        """
        Releases the controller associated with a client session.

        Args:
            player_id (str): Socket.IO session identifier.

        Returns:
            Controller or None: The released controller, or None if not found.
        """
        for controller in self.controllers.values():
            if controller.player_id == player_id:
                controller.player_id = None
                controller.player_name = None
                app.logger.info(f"Released {controller.index} from {player_id}")
                return controller
        return None

    def get_controller(self, player_id):
        """
        Retrieves the controller associated with a client session.

        Args:
            player_id (str): Socket.IO session identifier.

        Returns:
            Controller or None: The matching controller, or None if not found.
        """
        for controller in self.controllers.values():
            if controller.player_id == player_id:
                return controller
        return None

    def get_players(self):
        """
        Returns:
            list[dict]: A list of player metadata dictionaries.
        """
        players = []

        for controller in self.controllers.values():
            if controller.player_id is not None:
                if controller.selection is not Rokenbok.VehicleKey.NO_SELECTION:
                    selection = controller.selection.value + 1
                    vehicle_name = config["vehicle_names"][str(selection)]
                else:
                    selection = "None"
                    vehicle_name = ""
    
                players.append({
                    "player_name": controller.player_name,
                    "selection": selection,
                    "selection_name": vehicle_name
                })

        return players

    class Controller:
        """
        A single logical controller assigned to a client.

        Attributes:
            deck (CommandDeck): Parent command deck instance.
            index (ControllerIdentifier): Controller identifier.
            selection (VehicleKey): Current vehicle selection.
            player_id (str): Socket.IO session identifier.
        """

        def __init__(self, command_deck, index: Rokenbok.ControllerIdentifier):
            """
            Initializes a controller instance.

            Args:
                command_deck (CommandDeck): Parent command deck.
                index (ControllerIdentifier): Controller identifier.
            """
            self.deck = command_deck
            self.index = index
            self.selection = Rokenbok.VehicleKey.NO_SELECTION
            self.player_name = None
            self.player_id = None

        def select(self, vehicle: Rokenbok.VehicleKey):
            """Changes the controller's selection.

            Args:
                vehicle (VehicleKey)

            Sends:
                A command to the `CommandDeck` to edit the controller's selection.
            """
            self.selection = vehicle
            self.deck.send_command(Rokenbok.DeviceCommand.EDIT, self, self.selection)

        def send_input(self, input):
            """Processes input from a gamepad.

            Args:
                input (dict): A dictionary containing a button (int) and its state (string).

            Sends:
                A command to the `CommandDeck` to either press or release a button.
            """
            button = Rokenbok.ControllerCommand(input['button'])

            if button in (Rokenbok.ControllerCommand.SELECT_UP, Rokenbok.ControllerCommand.SELECT_DOWN):
                if input['pressed']:
                    delta = 1 if button == Rokenbok.ControllerCommand.SELECT_UP else -1
                    next_selection = (self.selection.value + delta) % (self.deck.vehicle_count - 1)
                    self.select(Rokenbok.VehicleKey(next_selection))
            
            else:
                command = Rokenbok.DeviceCommand.PRESS if input['pressed'] else Rokenbok.DeviceCommand.RELEASE
                self.deck.send_command(command, self, button)

            socketio.emit("players", {"players": self.deck.get_players()})

    def send_command(self, command, controller=None, value=None):
        """Sends a command to the connected device.

        Args:
            command (DeviceCommand): The command to send.
            controller (Controller, optional): The controller that triggered the command.
            value (optional): An optional value associated with the command.

        Sends:
            A command to the connected device.
        """
        if self.device is not None:
            self.device.send_command(command, controller, value)
        
        app.logger.debug(f"{command} - {controller.index.name if controller is not None else None} - {value}")

def handle_exit(signal, frame):
    print("Program interrupted, performing cleanup...")
    if config['webserver'].getboolean('upnp'):
        upnp_mapper.remove_port_mapping()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

if __name__ == '__main__':

    if not os.path.exists(config_file):
        print(f"Creating new config file: {config_file}")

        config['webserver'] = {
            'listen_ip': '0.0.0.0',
            'listen_port': '5000',
            'upnp': 'false',
            'log_level': 'WARNING',
            'flask_logs': 'false',
            'enable_video': 'false'
        }

        config['smartport_arduino'] = {
            'enabled': 'false',
            'serial_port': ''
        }

        config['vehicle_names'] = {
            '1': '',
            '2': '',
            '3': '',
            '4': '',
            '5': '',
            '6': '',
            '7': '',
            '8': '',
            '9': '',
            '10': '',
            '11': '',
            '12': '',
            '13': '',
            '14': '',
            '15': ''
        }

        config['video_streams'] = {
            'Camera 1': '',
            'Camera 2': ''
        }

        with open(f'{app_dir}/rokenbok_webserver.ini', 'w') as configfile:
            config.write(configfile)
    
    config.read(config_file)

    log.setLevel(config['webserver']['log_level'])
    if not config['webserver'].getboolean('flask_logs'):
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
    
    if config['smartport_arduino'].getboolean('enabled'):
        device_name = "smartport-arduino"
    else:
        device_name = None
    
    command_deck = CommandDeck(device_name=device_name, serial_device=config['smartport_arduino']['serial_port'])

    if config['webserver'].getboolean('upnp'):
        print("Trying to open port via UPnP")
        upnp_mapper = UPnPPortMapper(config['webserver']['listen_port'], config['webserver']['listen_port'], config['webserver']['listen_ip'], "SmartPort Web Server")

    socketio.run(app, host=config['webserver']['listen_ip'], port=config['webserver']['listen_port'])
