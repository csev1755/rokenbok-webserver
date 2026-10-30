from abc import ABC, abstractmethod


class Vehicle(ABC):
    """
    Abstract base class for controllable vehicles.

    Attributes:
        id (int): The numeric identifier for selection.
        name (str): The display name of the vehicle.
        type (str or None): The unique name of the control device type.
        play_manager (PlayManager): Reference to the parent PlayManager class.
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

    def __init__(self, play_manager, config, id, name, logger):
        """
        Initializes a vehicle instance.

        Args:
            play_manager (PlayManager): Parent PlayManager instance.
            config (dict): Configuration parameters for this vehicle.
            id (int): Unique numeric identifier for vehicle selection.
            name (str): Display name of the vehicle.
        """
        self.play_manager = play_manager
        self.id = id
        self.name = name
        self.config = config
        self.logger = logger

    @classmethod
    def configure(cls, type, config, id, name, logger):
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
    def control(self, player, play_manager):
        """
        Abstract method to control the vehicle based on player input.

        Args:
            player (Player): The player issuing commands.
            play_manager (PlayManager): The parent command deck instance.
        """
        pass
