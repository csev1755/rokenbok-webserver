import serial
from enum import Enum

class CommandDeck:
    """Represents a Command Deck and provides methods to communicate with it.

    This class manages communication with the Command Deck
    by sending commands to a SmartPort device via serial connection.

    Attributes:
        smartport (serial.Serial): The serial connection to the SmartPort device.
    """
    
    def __init__(self, serial_device=None):
        """Initializes the `CommandDeck` class and connects to a SmartPort device.

        Args:
            serial_device (str, optional): The name of the serial device to connect to.
                If not provided, the device will not be connected and only commands will be printed.

        Prints:
            A message indicating whether a connection to the SmartPort device was established 
            or if it is in debugging mode without a device.
        """
        self.smartport = None
        if serial_device is not None:
            self.smartport = serial.Serial(serial_device, 115200, timeout=1)
            print(f"Connected to SmartPort device at {serial_device}")
        else:
            print("No SmartPort device specified, will only print commands for debugging")
    
    class Command(Enum):
        """Enum representing types of commands that can be sent to the SmartPort device."""
        PRESS = 0
        RELEASE = 1
        EDIT = 2
        ENABLE = 3
        DISABLE = 4
        RESET = 5

    def send_command(self, command: Command, controller=None, value=0):
        """Sends a command to the SmartPort device or prints a debug message if no device is connected.

            This command is sent via serial as 3 bytes that represent
            the type of command, an associated controller, and a
            value specific to the command.

        Args:
            command (Command): The type of command to send.
            controller (Controller, optional): A controller object.
            value (int, optional): A command specific value.

        Prints:
            A debug message if no SmartPort device is connected, otherwise sends the command 
            over the serial connection.
        """
        if self.smartport is not None:
            self.smartport.write(bytes([command.value, controller.index, value]))
        else:
            print(f"DEBUG - Action: {command.value} Controller: {controller.index if controller else 0} Value: {value}")

    class Controller:
        """Represents a controller connected to the Command Deck.

        Attributes:
            command (CommandDeck): The parent `CommandDeck` instance for communication.
            index (int): The controller number.
            selection (int, optional): A vehicle or selection tied to the controller.
            button_map (dict): A mapping from button integer values to controller command enums.
        """

        def __init__(self, command_deck, index, vehicle=None): 
            """Initializes a controller instance.

            Args:
                command_deck (CommandDeck): The `CommandDeck` instance for communication.
                index (int): The index of the controller (e.g., 0 for the first controller).
                vehicle (int, optional): A vehicle selected by the controller.
            """
            self.command = command_deck
            self.index = index
            self.selection = vehicle
            self.button_map = {
                0:  self.Command.A,
                1:  self.Command.B,
                3:  self.Command.X,
                2:  self.Command.Y,
                4:  self.Command.LEFT_TRIGGER,
                5:  self.Command.RIGHT_TRIGGER,
                12: self.Command.DPAD_UP,
                13: self.Command.DPAD_DOWN,
                14: self.Command.DPAD_LEFT,
                15: self.Command.DPAD_RIGHT
            }

        class Command(Enum):
            """Enum representing the values available for controller commands."""
            SELECT = 0
            LEFT_TRIGGER = 1
            SHARE_SWITCH = 2
            IS_16_SEL = 3
            DPAD_UP = 4
            DPAD_DOWN = 5
            DPAD_RIGHT = 6
            DPAD_LEFT = 7
            A = 8
            B = 9
            X = 10
            Y = 11
            RIGHT_TRIGGER = 12

        def press(self, button: Command):
            """Presses a button on the controller.

            Args:
                button (Command): The button to press, represented by a `Command` enum.

            Sends:
                A command to the `CommandDeck` to perform a press action on the specified button.
            """
            self.command.send_command(self.command.Command.PRESS, self, button)
        
        def release(self, button: Command):
            """Releases a button on the controller.

            Args:
                button (Command): The button to release, represented by a `Command` enum.

            Sends:
                A command to the `CommandDeck` to perform a release action on the specified button.
            """
            self.command.send_command(self.command.Command.RELEASE, self, button)

        def select(self, vehicle):
            """Changes the controller's selection.

            Args:
                vehicle (int): The vehicle to select.

            Sends:
                A command to the `CommandDeck` to edit the controller's selection.
            """
            self.selection = vehicle
            self.command.send_command(self.command.Command.EDIT, self, self.selection)

        def disable(self):
            """Disables the controller.

            Sends:
                A command to the `CommandDeck` to disable the controller.
                This only works with the physical controllers 0-3.
            """
            self.command.send_command(self.command.Command.DISABLE, self)
        
        def enable(self):
            """Enables the controller.

            Sends:
                A command to the `CommandDeck` to disable the controller.
                This only works with the physical controllers 0-3.
            """
            self.command.send_command(self.command.Command.ENABLE, self)

        def send_input(self, input):
            """Processes input from a gamepad.

            Args:
                input (dict): A dictionary containing a button (int) and it's state (string).

            Sends:
                A command to the `CommandDeck` to either press or release a button.
            """
            if input['button'] in self.button_map:
                command = self.command.Command.PRESS if input['pressed'] else self.command.Command.RELEASE
                button = self.button_map[input['button']]
                self.command.send_command(command, self, button.value)
