import serial
from abc import ABC, abstractmethod

class Controller:
    """
    A single logical controller assigned to a client.

    Attributes:
        command_deck (VirtualCommandDeck): Parent command deck instance.
        controller_id (int): Controller identifier.
        selection (int or None): Current vehicle selection (1-indexed), or None if no vehicle selected.
        player_name (str or None): Display name of the player using this controller.
        player_id (str or None): Socket.IO session identifier for the connected player.
        buttons (set): Set of currently pressed button identifiers.
    """

    def __init__(self, command_deck, controller_id, logger=None):
        """
        Initializes a controller instance.

        Args:
            command_deck (VirtualCommandDeck): Parent command deck.
            controller_id (int): Controller identifier.
        """
        self.command_deck = command_deck
        self.selection = None
        self.player_name = None
        self.player_id = None
        self.controller_id = controller_id
        self.buttons = set()
        self.logger = logger

    def handle_input(self, input):
        """
        Processes input from a gamepad and updates controller state.

        Args:
            input (dict): A dictionary containing:
                - 'button' (str): Button identifier
                - 'pressed' (bool): True if button is pressed, False if released
        """
        if input['pressed']:
            if input['button'] in ("SELECT_UP", "SELECT_DOWN"):
                self.logger.debug(f"Session {self.player_id} - Event {input['button']}")
                delta = 1 if input['button'] == "SELECT_UP" else -1

                if self.selection is None:
                    self.selection = 1 if delta == 1 else self.command_deck.vehicle_count
                elif ((self.selection + delta) < 1) or ((self.selection + delta) > self.command_deck.vehicle_count):
                    self.selection = None
                else:
                    self.selection += delta
            else:
                self.buttons.add(input['button'])
                self.logger.debug(f"Session {self.player_id} - Event {self.buttons}")
        else:
            self.buttons.discard(input['button'])

        vehicle = self.command_deck.get_vehicle(self.selection) or None

        if vehicle:
            vehicle.control(self, self.command_deck)

class Vehicle(ABC):
    """
    Abstract base class for controllable vehicles.

    Attributes:
        id (int): The numeric identifier for selection.
        name (str): The display name of the vehicle.
        type (str or None): The unique name of the control device type.
        command_deck (VirtualCommandDeck): Reference to the parent command deck class.
        config (dict): Configuration for the vehicle's device type.
        vehicle_types (dict): Mapping of type names to device-specific vehicle classes.
    """

    type = None
    vehicle_types = {}

    def __init_subclass__(cls):
        """
        Registers vehicle subclasses in the vehicle_types registry.
        """
        super().__init_subclass__()
        Vehicle.vehicle_types[cls.type] = cls

    def __init__(self, command_deck, config, id, name, logger=None):
        """
        Initializes a vehicle instance.

        Args:
            command_deck (VirtualCommandDeck): Parent command deck instance.
            config (dict): Configuration parameters for this vehicle.
            id (int): Unique numeric identifier for vehicle selection.
            name (str): Display name of the vehicle.
        """
        self.command_deck = command_deck
        self.id = id
        self.name = name
        self.config = config
        self.logger = logger

    @classmethod
    def configure(cls, type, config, id, name, logger=None):
        """
        Factory method to create a vehicle instance of the specified type.

        Args:
            type (str): Vehicle type identifier.
            config (dict): Configuration parameters for the vehicle's contrtol device.
            id (int): Unique numeric identifier for vehicle selection.
            name (str): Display name of the vehicle.

        Returns:
            Vehicle: Instance of the appropriate vehicle subclass.

        Raises:
            ValueError: If the specified vehicle type is not registered.
        """
        try:
            device = cls.vehicle_types[type]
        except KeyError:
            raise ValueError(f"Unknown vehicle type: {type}")

        logger.info(f"Configured <{type}> vehicle <{name}> with id <{id}>")
        return device(config, id, name, logger)

    @abstractmethod
    def control(self, controller, command_deck):
        """
        Abstract method to control the vehicle based on controller input.

        Args:
            controller (Controller): The controller issuing commands.
            command_deck (VirtualCommandDeck): The parent command deck instance.
        """
        pass

class SmartPortArduino(Vehicle):
    """
    Device type/vehicle class for the smartport_arduino sketch
    """
    type = "smartport_arduino"
    serial = None

    def __init__(self, config, id, name, logger=None):
        super().__init__(self, config, id, name, logger)
        if SmartPortArduino.serial is None:
            SmartPortArduino.serial = serial.Serial(config['serial_port'], 1000000)
        self.logger.info(f"Connected to serial at {config['serial_port']}")
    
    @classmethod
    def encode_controller_state(self, controller):
        """
        Encodes controller button states into two bytes for serial transmission.

        Byte 1: D-pad directions (up, down, right, left)
        Byte 2: Action buttons (A, B, X, Y) and triggers

        Args:
            controller (Controller): A controller object.

        Returns:
            tuple[int, int]: Two bytes representing the controller state.
        """
        up    = 'DPAD_UP' in controller.buttons
        down  = 'DPAD_DOWN' in controller.buttons
        right = 'DPAD_RIGHT' in controller.buttons
        left  = 'DPAD_LEFT' in controller.buttons

        b_a = 'A_BUTTON' in controller.buttons
        b_b = 'B_BUTTON' in controller.buttons
        b_x = 'X_BUTTON' in controller.buttons
        b_y = 'Y_BUTTON' in controller.buttons

        b_rt = int('LEFT_TRIGGER' in controller.buttons or 'RIGHT_TRIGGER' in controller.buttons)

        byte1 = (up << 3) | (down << 2) | (right << 1) | left
        byte2 = (b_a << 4) | (b_b << 3) | (b_x << 2) | (b_y << 1) | b_rt

        return byte1, byte2

    def control(self, controller, command_deck):
        """
        Constructs and transmits a packet containing the state of all controllers
        to the Arduino and receives data representing the command deck's state
        """
        packet = bytearray([254])
        for controller in command_deck.controllers.values():
            p_id = controller.controller_id + 10 or 0
            v_sel = 15 if controller.selection is None else controller.selection - 1
            byte1, byte2 = self.encode_controller_state(controller)
            packet.extend([p_id, v_sel, byte1, byte2])
        packet.append(255)
        self.send_and_receive_packet(packet)

    def send_and_receive_packet(self, packet):
        """
        Sends a packet via serial and processes any incoming response.

        Args:
            packet (bytearray): The packet to transmit.
        """
        SmartPortArduino.serial.write(packet)
        if SmartPortArduino.serial.in_waiting >= 27:
            raw = SmartPortArduino.serial.read(SmartPortArduino.serial.in_waiting)
            start = raw.rfind(254)

            if start != -1 and len(raw) >= start + 27 and raw[start + 26] == 255:
                frame = raw[start:start + 27]
                self.logger.debug(f"SmartPortArduino Controllers - {[x == 1 for x in frame[2:14]]}")
                self.logger.debug(f"SmartPortArduino Selections - {[None if x == 15 else x + 1 for x in frame[14:26]]}")
