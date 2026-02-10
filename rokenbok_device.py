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

    def handle_input(self, input):
        """Processes input from a gamepad.

        Args:
            input (dict): A dictionary containing a button (int) and its state (string).

        Sends:
            A command to the `VirtualCommandDeck` to either press or release a button.
        """

        if input['button'] in ("SELECT_UP", "SELECT_DOWN"):
            if input['pressed']:
                delta = 1 if input['button'] == "SELECT_UP" else -1

                if self.selection is None:
                    self.selection = 1 if delta == 1 else self.deck.vehicle_count
                elif ((self.selection + delta) < 1) or ((self.selection + delta) > self.deck.vehicle_count):
                    self.selection = None
                else:
                    self.selection += delta

        button_state = "pressed" if input['pressed'] else "release"
        vehicle = self.deck.get_vehicle(self.selection) or None
        controller_state = self.player_id, input['button'], button_state
        if vehicle:
            vehicle.control(controller_state)

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
    
    def control(self, controller_state):
        print(controller_state)
