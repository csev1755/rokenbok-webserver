import argparse
import signal
import sys
from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO
from rokenbok_device import Commands as Rokenbok
from rokenbok_device import SmartPortArduino
from upnp import UPnPPortMapper

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/control.js')
def script():
    return send_from_directory('static', 'control.js')

@socketio.on("connect")
def handle_connect():
    command_deck.assign_controller(request.sid)

@socketio.on("disconnect")
def handle_disconnect():
    command_deck.release_controller(request.sid)

@socketio.on("controller")
def handle_controller(data):
    controller = command_deck.get_controller(request.sid)
    controller.send_input(data) if controller else None

class CommandDeck:
    """Represents a Command Deck and provides methods to communicate with it.

    Attributes:
        debug (bool): Enables debug output when True.
        device: The underlying hardware device interface, if configured.
        controllers (dict): Mapping of controller identifiers to Controller instances.
        selection_count (int): Number of selectable vehicles.
    """

    def __init__(self, **kwargs):
        """
        Initializes the CommandDeck and connects to a specified hardware device.

        Keyword Args:
            device_name (str): Identifier for the control device type.
            serial_device (str): Serial port path for the control device.
            debug (bool): Enables debug output.
        """
        self.debug = kwargs['debug']
        self.device = None

        if kwargs['device_name'] == "smartport-arduino":
            self.device = SmartPortArduino(kwargs['serial_device'])
        else:
            print("Invalid device or no device specified, will only print commands for debugging")

        self.controllers: dict[Rokenbok.ControllerIdentifier, CommandDeck.Controller] = {}
        self.selection_count = 16

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
                controller.enable()
                return controller
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
                controller.disable()
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
        return [
            {
                "controller": controller.index.name,
                "player_id": controller.player_id,
                "selection": controller.selection.name,
            }
            for controller in self.controllers.values()
        ]

    class Controller:
        """
        A single logical controller assigned to a client.

        Attributes:
            deck (CommandDeck): Parent command deck instance.
            index (ControllerIdentifier): Controller identifier.
            selection (VehicleKey): Current vehicle selection.
            player_id (str): Socket.IO session identifier.
            button_map (dict): Mapping of gamepad buttons to controller commands.
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
            self.player_id = None

            # Mapping from a JavaScript gamepad device to Rokenbok controller buttons
            self.button_map = {
                0:  Rokenbok.ControllerCommand.A,
                1:  Rokenbok.ControllerCommand.B,
                3:  Rokenbok.ControllerCommand.X,
                2:  Rokenbok.ControllerCommand.Y,
                4:  Rokenbok.ControllerCommand.LEFT_TRIGGER,
                5:  Rokenbok.ControllerCommand.RIGHT_TRIGGER,
                12: Rokenbok.ControllerCommand.DPAD_UP,
                13: Rokenbok.ControllerCommand.DPAD_DOWN,
                14: Rokenbok.ControllerCommand.DPAD_LEFT,
                15: Rokenbok.ControllerCommand.DPAD_RIGHT,
                9:  Rokenbok.ControllerCommand.SELECT_UP,
                8:  Rokenbok.ControllerCommand.SELECT_DOWN
            }

        def select(self, vehicle: Rokenbok.VehicleKey):
            """Changes the controller's selection.

            Args:
                vehicle (VehicleKey)

            Sends:
                A command to the `CommandDeck` to edit the controller's selection.
            """
            self.selection = vehicle
            self.deck.send_command(Rokenbok.DeviceCommand.EDIT, self, self.selection)

        def disable(self):
            """Disables the controller.

            Sends:
                A command to the `CommandDeck` to disable the controller.
            """
            self.deck.send_command(Rokenbok.DeviceCommand.DISABLE, self)
        
        def enable(self):
            """Enables the controller.

            Sends:
                A command to the `CommandDeck` to enable the controller.
            """
            self.deck.send_command(Rokenbok.DeviceCommand.ENABLE, self)

        def send_input(self, input):
            """Processes input from a gamepad.

            Args:
                input (dict): A dictionary containing a button (int) and its state (string).

            Sends:
                A command to the `CommandDeck` to either press or release a button.
            """
            if input['button'] in self.button_map:
                button = self.button_map[input['button']]

                if button in (Rokenbok.ControllerCommand.SELECT_UP, Rokenbok.ControllerCommand.SELECT_DOWN):
                    if input['pressed']:
                        delta = 1 if button == Rokenbok.ControllerCommand.SELECT_UP else -1
                        next_selection = (self.selection.value + delta) % self.deck.selection_count
                        self.select(Rokenbok.VehicleKey(next_selection))
                
                else:
                    command = Rokenbok.DeviceCommand.PRESS if input['pressed'] else Rokenbok.DeviceCommand.RELEASE
                    self.deck.send_command(command, self, self.button_map[input['button']])

            socketio.emit("players", {"players": self.deck.get_players()})

    def send_command(self, command, controller=None, value=None):
        """Sends a command to the connected device.

        Args:
            command (DeviceCommand): The command to send.
            controller (Controller, optional): The controller that triggered the command.
            value (optional): An optional value associated with the command.

        Sends:
            A command to the connected device or prints the command in debugging mode if no device is connected.
        """
        if self.device is not None:
            self.device.send_command(command, controller, value)
        if self.debug:
            print(f"DEBUG - {command} - {controller.index.name if controller is not None else None} - {value}")

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

    socketio.run(app, host=args.ip, port=args.port)
