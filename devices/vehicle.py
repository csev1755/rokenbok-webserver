from abc import ABC, abstractmethod

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
