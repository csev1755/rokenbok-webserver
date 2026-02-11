import serial
from abc import ABC, abstractmethod

class Controller:
    """
    A single logical controller assigned to a client.

    Attributes:
        deck (VirtualCommandDeck): Parent command deck instance.
        controller_id (int): Controller identifier.
        selection (int): Current vehicle selection.
        player_id (str): Socket.IO session identifier.
    """

    def __init__(self, command_deck, controller_id):
        """
        Initializes a controller instance.

        Args:
            command_deck (VirtualCommandDeck): Parent command deck.
            controller_id (int): Controller identifier.
        """
        self.deck = command_deck
        self.selection = None
        self.player_name = None
        self.player_id = None
        self.controller_id = controller_id
        self.buttons = set()

    def handle_input(self, input):
        """Processes input from a gamepad.

        Args:
            input (dict): A dictionary containing a button (int) and its state (string).

        Sends:
            A command to the `VirtualCommandDeck` to either press or release a button.
        """
        if input['pressed']:
            if input['button'] in ("SELECT_UP", "SELECT_DOWN"):
                delta = 1 if input['button'] == "SELECT_UP" else -1

                if self.selection is None:
                    self.selection = 1 if delta == 1 else self.deck.vehicle_count
                elif ((self.selection + delta) < 1) or ((self.selection + delta) > self.deck.vehicle_count):
                    self.selection = None
                else:
                    self.selection += delta
            else:
                self.buttons.add(input['button'])
        else:
            self.buttons.discard(input['button'])

        vehicle = self.deck.get_vehicle(self.selection) or None

        if vehicle:
            vehicle.control(self)

class Vehicle(ABC):
    """Exposes methods to control a vehicle

    Attributes:
        id: The numeric unique id for seleciton
        name: The name of the vehicle
        type: The name of the control device
    """

    type = None
    vehicle_types = {}

    def __init_subclass__(cls):
        super().__init_subclass__()
        Vehicle.vehicle_types[cls.type] = cls

    def __init__(self, config, id, name):
        self.id = id
        self.name = name
        self.config = config

    @classmethod
    def configure(cls, type, config, id, name):
        try:
            device = cls.vehicle_types[type]
        except KeyError:
            raise ValueError(f"Unknown vehicle type: {type}")

        print(f"Configured <{type}> vehicle <{name}> with id <{id}>")
        return device(config, id, name)

    @abstractmethod
    def control(self):
        """Vehicle controls"""
        pass

class SmartPortArduino(Vehicle):
    type = "smartport_arduino"
    serial = None

    def __init__(self, config, id, name):
        super().__init__(config, id, name)
        if SmartPortArduino.serial is None:
            SmartPortArduino.serial = serial.Serial(config['serial_port'], 1000000)
            print(f"Connected to serial at {config['serial_port']}")
    
    def control(self, controller):   
        for button in controller.buttons:
            print(button)

    def encode_controller_state(self, buttons):
        up    = 'DPAD_UP' in buttons
        down  = 'DPAD_DOWN' in buttons
        right = 'DPAD_RIGHT' in buttons
        left  = 'DPAD_LEFT' in buttons

        b_a = 'A_BUTTON' in buttons
        b_b = 'B_BUTTON' in buttons
        b_x = 'X_BUTTON' in buttons
        b_y = 'Y_BUTTON' in buttons

        b_rt = int('LEFT_TRIGGER' in buttons or 'RIGHT_TRIGGER' in buttons)

        byte1 = (up << 3) | (down << 2) | (right << 1) | left
        byte2 = (b_a << 4) | (b_b << 3) | (b_x << 2) | (b_y << 1) | b_rt

        return byte1, byte2