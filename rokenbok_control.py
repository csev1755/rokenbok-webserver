from rokenbok_device import SmartPortArduino
from rokenbok_device import Commands as Rokenbok

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
        
        if kwargs['device_name'] == "smartport-arduino":
            self.device = SmartPortArduino(kwargs['serial_device'])
        else:
            print("Invalid device or no device specified, will only print commands for debugging")
    
    def get_controller(self, index: Rokenbok.ControllerIdentifier, vehicle: Rokenbok.VehicleKey=None):
        """Gets or creates a controller instance.

        Args:
            index (ControllerIdentifier): The controller identifier
            vehicle (VehicleKey, optional): Initial vehicle selection

        Returns:
            Controller: The controller instance
        """
        if index not in self.controllers:
            self.controllers[index] = self.Controller(self, index, vehicle)
        return self.controllers[index]
    
    class Controller:
        """Represents a controller connected to the Command Deck.

        Attributes:
            command (CommandDeck): The parent `CommandDeck` instance for communication.
            index (int): The controller number.
            selection (int, optional): A vehicle or selection tied to the controller.
            button_map (dict): A mapping from button integer values to controller command enums.
        """

        def __init__(self, command_deck, index: Rokenbok.ControllerIdentifier=None, vehicle: Rokenbok.VehicleKey=None): 
            """Initializes a controller instance.

            Args:
                command_deck (CommandDeck)
                index (ControllerIdentifier, optional)
                vehicle (VehicleKey, optional)
            """
            self.deck = command_deck
            self.index = index
            self.selection = vehicle

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
                15: Rokenbok.ControllerCommand.DPAD_RIGHT
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
                command = Rokenbok.DeviceCommand.PRESS if input['pressed'] else Rokenbok.DeviceCommand.RELEASE
                button = self.button_map[input['button']]
                self.deck.send_command(command, self, Rokenbok.ControllerCommand(button.value))

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
