import serial
from enum import Enum

class CommandDeck:
    def __init__(self, serial_device=None):
        self.smartport = None
        if serial_device is not None:
            self.smartport = serial.Serial(serial_device, 115200, timeout=1)
            print(f"Connected to SmartPort device at {serial_device}")
        else:
            print("No SmartPort device specified, will only print commands for debugging")
    
    class Command(Enum):
        PRESS = 0
        RELEASE = 1
        EDIT = 2
        ENABLE = 3
        DISABLE = 4
        RESET = 5

    def send_command(self, command: Command, controller=None, value=0):
        if self.smartport is not None:
            self.smartport.write(bytes([command.value, controller.index, value]))
        else:
            print(f"DEBUG - Action: {command.value} Controller: {controller.index if controller else 0} Value: {value}")

    class Controller:
        def __init__(self, command_deck, index, vehicle=None): 
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
            self.command.send_command(self.command.Command.PRESS, self, button)
        
        def release(self, button: Command):
            self.command.send_command(self.command.Command.RELEASE, self, button)

        def select(self, vehicle):
            self.selection = vehicle
            self.command.send_command(self.command.Command.EDIT, self, self.selection)

        def disable(self):
            self.command.send_command(self.command.Command.DISABLE, self)
        
        def enable(self):
            self.command.send_command(self.command.Command.ENABLE, self)

        def send_input(self, input):
            if input['button'] in self.button_map:
                command = self.command.Command.PRESS if input['pressed'] else self.command.Command.RELEASE
                button = self.button_map[input['button']]
                self.command.send_command(command, self, button.value)
