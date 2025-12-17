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

    class ControllerIdentifier(Enum):
        """Enum representing identifiers for physical and virtual controllers."""
        PHYSICAL_CONTROLLER_1 = 0
        PHYSICAL_CONTROLLER_2 = 1
        PHYSICAL_CONTROLLER_3 = 2
        PHYSICAL_CONTROLLER_4 = 3
        VIRTUAL_CONTROLLER_1 = 4
        VIRTUAL_CONTROLLER_2 = 5
        VIRTUAL_CONTROLLER_3 = 6
        VIRTUAL_CONTROLLER_4 = 7

    class VehicleKey(Enum):
        """Enum representing vehicles for selection."""
        SELECT_KEY_1 = 0
        SELECT_KEY_2 = 1
        SELECT_KEY_3 = 2
        SELECT_KEY_4 = 3
        SELECT_KEY_5 = 4
        SELECT_KEY_6 = 5
        SELECT_KEY_7 = 6
        SELECT_KEY_8 = 7
        SELECT_KEY_9 = 8
        SELECT_KEY_10 = 9
        SELECT_KEY_11 = 10
        SELECT_KEY_12 = 11
        SELECT_KEY_13 = 12
        SELECT_KEY_14 = 13
        SELECT_KEY_15 = 14
        NO_SELECTION = 15

class SmartPortArduino:
    """A class that provides methods to communicate with an
        Arduino with the `smartport-arduino` sketch installed
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
        byte2 = controller.index.value if controller else 0
        byte3 = value.value if value else 0

        self.arduino.write(bytes([byte1, byte2, byte3]))
