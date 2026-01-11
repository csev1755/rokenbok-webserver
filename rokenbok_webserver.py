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

@socketio.on('controller')
def handle_controller(data):
    controller = command_deck.get_controller(Rokenbok.ControllerIdentifier(data['controller']))
    controller.send_input(data)

class CommandDeck:
    """Represents a Command Deck and provides methods to communicate with it.

    Attributes:
        device: A device used to control Rokenbok
        controllers: A dictionary of controller instances keyed by index
    """
    
    def __init__(self, **kwargs):
        """Initializes the `CommandDeck` class and establishes communication with
            a control device.

        Args:
            type (str, optional): The type control device to connect to.
                If not provided, only the commands will be printed for debugging.

        Prints:
            A message indicating whether a connection to a device was established 
            or if it is in debugging mode without a device.
        """
        self.debug = kwargs['debug']
        self.device = None
        self.controllers = {}
        self.selection_count = 16
        
        if kwargs['device_name'] == "smartport-arduino":
            self.device = SmartPortArduino(kwargs['serial_device'])
        else:
            print("Invalid device or no device specified, will only print commands for debugging")
    
    def get_controller(self, index: Rokenbok.ControllerIdentifier):
        """Gets or creates a controller instance.

        Args:
            index (ControllerIdentifier): The controller identifier
            vehicle (VehicleKey, optional): Initial vehicle selection

        Returns:
            Controller: The controller instance
        """
        if index not in self.controllers:
            self.controllers[index] = self.Controller(self, index)
        return self.controllers[index]
    
    class Controller:
        """Represents a controller connected to the Command Deck.

        Attributes:
            command (CommandDeck): The parent `CommandDeck` instance for communication.
            index (int): The controller number.
            selection (int, optional): A vehicle or selection tied to the controller.
            button_map (dict): A mapping from button integer values to controller command enums.
        """

        def __init__(self, command_deck, index: Rokenbok.ControllerIdentifier=None): 
            """Initializes a controller instance.

            Args:
                command_deck (CommandDeck)
                index (ControllerIdentifier, optional)
                vehicle (VehicleKey, optional)
            """
            self.deck = command_deck
            self.index = index
            self.selection = Rokenbok.VehicleKey.NO_SELECTION
            self.enable()

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

        def press(self, button: Rokenbok.ControllerCommand):
            """Presses a button on the controller.

            Args:
                button (ControllerCommand)

            Sends:
                A command to the `CommandDeck` to perform a press action on the specified button.
            """
            self.deck.send_command(Rokenbok.DeviceCommand.PRESS, self, button)
        
        def release(self, button: Rokenbok.ControllerCommand):
            """Releases a button on the controller.

            Args:
                button (ControllerCommand)

            Sends:
                A command to the `CommandDeck` to perform a release action on the specified button.
            """
            self.deck.send_command(Rokenbok.DeviceCommand.RELEASE, self, button)

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

    socketio.run(app.run(host=args.ip, port=args.port))
