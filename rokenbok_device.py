import serial

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
