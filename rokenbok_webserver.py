import configparser
import logging
import os
import signal
import sys
import rokenbok_device as RokenbokDevice
from flask import Flask, request, send_from_directory, render_template
from flask_socketio import SocketIO
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
    """
    Returns:
        str: Rendered HTML template with video configuration.
    """
    return render_template('player.html', enable_video=config['webserver'].getboolean('enable_video'), video_streams=config['video_streams'])

@app.route('/player.js')
def script():
    """
    Returns:
        Response: The player.js file from the web directory.
    """
    return send_from_directory('web', 'player.js')

@socketio.on("connect")
def handle_connect():
    """
    Assigns a controller to the connecting player and broadcasts
    the updated player list to all clients.
    """
    command_deck.assign_controller(request.sid)
    socketio.emit("players", {"players": command_deck.get_players()})

@socketio.on("disconnect")
def handle_disconnect():
    """
    Releases the controller from the disconnecting player and broadcasts
    the updated player list to all clients.
    """
    command_deck.release_controller(request.sid)
    socketio.emit("players", {"players": command_deck.get_players()})

@socketio.on("controller")
def handle_controller(data):
    """
    Updates the player name and processes controller input, then broadcasts
    the updated player list to all clients.

    Args:
        data (dict): Controller data containing:
            - 'player_name' (str): Display name of the player
            - 'button' (str): Button identifier
            - 'pressed' (bool): Button state
    """
    controller = command_deck.get_controller(request.sid)
    if controller:
        controller.player_name = data['player_name']
        controller.handle_input(data)
        socketio.emit("players", {"players": command_deck.get_players()})

class VirtualCommandDeck:
    """
    Manages controllers and vehicles and handles player assignments and
    vehicle control routing.

    Attributes:
        controllers (dict[int, RokenbokDevice.Controller]): Mapping of controller IDs to Controller instances.
        controller_count (int): Number of usable controllers (default: 12).
        vehicles (dict[int, RokenbokDevice.Vehicle]): Mapping of vehicle IDs to Vehicle instances.
        vehicle_count (int): Number of selectable vehicles.
    """

    def __init__(self):
        """
        Initializes the virtual command deck and controllers.

        Reads vehicle/device configurations from the config file and creates vehicle instances.
        """

        self.controllers: dict[int, RokenbokDevice.Controller] = {}
        self.controller_count = 12

        self.vehicles: dict[int, RokenbokDevice.Vehicle] = {}
        self.vehicle_count = 0

        for section in config.sections():
            if section.endswith(".vehicles"):
                device_vehicles = config[section].items()
                device_name = section.replace(".vehicles", "")
                device_config = config[device_name]
                
                for vehicle_id, vehicle_name in device_vehicles:
                    self.vehicle_count += 1
                    self.vehicles[int(vehicle_id)] = RokenbokDevice.Vehicle.configure(
                        type=device_name,
                        config=device_config,
                        id=int(vehicle_id),
                        name=vehicle_name
                    )

        for controller_id in range(1, self.controller_count + 1):
            self.controllers[controller_id] = RokenbokDevice.Controller(self, controller_id)

    def assign_controller(self, player_id):
        """
        Assigns an available controller to a client session.

        Args:
            player_id (str): Socket.IO session identifier.

        Returns:
            RokenbokDevice.Controller or None: The assigned controller.
        """
        for controller in self.controllers.values():
            if controller.player_id is None:
                controller.player_id = player_id
                controller.selection = None
                app.logger.info(f"Assigned controller {controller.controller_id} to player {player_id}")
                return controller
        app.logger.warning(f"No controller available for player {player_id}")
        return None

    def release_controller(self, player_id):
        """
        Releases the controller associated with a client session.

        Args:
            player_id (str): Socket.IO session identifier.

        Returns:
            RokenbokDevice.Controller or None: The released controller.
        """
        for controller in self.controllers.values():
            if controller.player_id == player_id:
                controller.player_id = None
                controller.player_name = None
                app.logger.info(f"Released controller {controller.controller_id} from player {player_id}")
                return controller
        return None

    def get_controller(self, player_id):
        """
        Retrieves the controller associated with a client session.

        Args:
            player_id (str): Socket.IO session identifier.

        Returns:
            RokenbokDevice.Controller or None: The matching controller.
        """
        for controller in self.controllers.values():
            if controller.player_id == player_id:
                return controller
        return None

    def get_vehicle(self, vehicle_id=None):
        """
        Retrieves a vehicle by its ID.

        Args:
            vehicle_id (int or None): The vehicle identifier.

        Returns:
            RokenbokDevice.Vehicle or None: The matching vehicle.
        """
        for vehicle in self.vehicles.values():
            if vehicle.id == vehicle_id:
                return vehicle
        return None

    def get_players(self):
        """
        Returns:
            list[dict]: A list of player metadata dictionaries:
                - 'player_name' (str or None): Player display name
                - 'selection' (int or None): Currently selected vehicle ID
                - 'selection_name' (str or None): Name of the selected vehicle
        """
        players = []

        for controller in self.controllers.values():
            if controller.player_id:
                players.append({
                    "player_name": controller.player_name,
                    "selection": controller.selection,
                    "selection_name": self.get_vehicle(controller.selection).name if controller.selection else None
                })

        return players

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
            'serial_port': ''
        }

        config['smartport_arduino.vehicles'] = {
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
    
    command_deck = VirtualCommandDeck()

    if config['webserver'].getboolean('upnp'):
        print("Trying to open port via UPnP")
        upnp_mapper = UPnPPortMapper(config['webserver']['listen_port'], config['webserver']['listen_port'], config['webserver']['listen_ip'], "SmartPort Web Server")

    socketio.run(app, host=config['webserver']['listen_ip'], port=config['webserver']['listen_port'])
