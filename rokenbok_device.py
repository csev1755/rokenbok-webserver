from abc import ABC, abstractmethod
from rokenbok_webserver import VirtualCommandDeck

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

    def get_input(self, input):
        """Processes input from a gamepad.

        Args:
            input (dict): A dictionary containing a button (int) and its state (string).

        Sends:
            A command to the `VirtualCommandDeck` to either press or release a button.
        """
        button = input['button']

        if button in ("SELECT_UP", "SELECT_DOWN"):
            if input['pressed']:
                delta = 1 if button == "SELECT_UP" else -1

                if self.selection is None:
                    self.selection = 1 if delta == 1 else self.deck.vehicle_count

                elif ((self.selection + delta) < 1) or ((self.selection + delta) > self.deck.vehicle_count):
                    self.selection = None

                else:
                    self.selection += delta

                return [button, self.selection]
        else:
            state = "pressed" if input['pressed'] else "release"
            return [button, state]

class Vehicle(ABC):
    """Exposes methods to control a vehicle

    Attributes:
        device: The control device dependency
        id: The numeric unique id for seleciton
        name: The name of the vehicle
    """

    vehicle_types = {}
    vehicle_type = None

    def __init_subclass__(cls):
        super().__init_subclass__()
        Vehicle.vehicle_types[cls.vehicle_type] = cls

    def __init__(self, device, id, name):
        self.device = device
        self.id = id
        self.name = name

    @classmethod
    def configure(cls, vehicle_type, device, id, name):
        try:
            vehicle_cls = cls.vehicle_types[vehicle_type]
        except KeyError:
            raise ValueError(f"Unknown vehicle type: {vehicle_type}")

        print(f"Configured vehicle <{name}> with id <{id}> and device type <{vehicle_type}>")
        return vehicle_cls(device, id, name)

    @abstractmethod
    def control(self):
        """Vehicle controls"""
        pass

class SmartPortArduino(Vehicle):
    vehicle_type = "smartport_arduino"

    def __init__(self, device, id, name):
        super().__init__(device, id, name)
    
    def control(self):
        print(f"vehicle={self.id} action")
