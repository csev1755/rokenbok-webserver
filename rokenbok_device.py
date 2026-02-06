import serial
from enum import Enum

class Commands:
    class DeviceCommand(Enum):
        """Enum representing commands associated with a Rokenbok device."""
        PRESS = 0
        RELEASE = 1
        EDIT = 2
        ENABLE = 3
        DISABLE = 4
        RESET = 5

    class ControllerCommand(Enum):
        """Enum representing functions associated with a controller."""
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
        SELECT_UP = 13
        SELECT_DOWN = 14

class SmartPortArduino:
    """A class that provides methods to communicate with an
        Arduino with the `smartport_arduino` sketch installed
        via command Enums.
    """
    def __init__(self, serial_device=None):
        """Connects to the Arduino via serial.

        Args:
            serial_device (str, optional): The name of the serial device to connect to.

        Prints:
            A message indicating whether a connection to the Arduino was established.
        """
        self.arduino = None

        if serial_device is not None:
            self.arduino = serial.Serial(serial_device, 115200, timeout=1)
            print(f"Connected to SmartPort Arduino via serial at {serial_device}")

    def send_command(self, command, controller=0, value=0):
        """Sends a command to the SmartPort device.

            This command is sent via serial as 3 bytes that represent
            the type of command, an associated controller, and a
            value specific to the command taken from Enum values

        Args:
            command (int)
            controller (int)
            value (int)
        """

        byte1 = command.value
        byte2 = controller.controller_id
        byte3 = value.value or value

        self.arduino.write(bytes([byte1, byte2, byte3]))
