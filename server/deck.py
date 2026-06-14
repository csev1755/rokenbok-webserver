import time
from devices.vehicle import Vehicle
from server.controller import Controller

class VirtualCommandDeck:
    """
    Manages controllers and vehicles and handles player assignments and
    vehicle control routing.

    Attributes:
        controllers (dict[int, Controller]): Mapping of controller IDs to Controller instances.
        controller_count (int): Number of usable controllers (default: 12).
        vehicles (dict[int, Vehicle]): Mapping of vehicle IDs to Vehicle instances.
        vehicle_count (int): Number of selectable vehicles.
    """

    def __init__(self, config, logger):
        """
        Initializes the virtual command deck and controllers.

        Reads vehicle/device configurations from the config file and creates vehicle instances.
        """
        self.logger = logger
        self.config = config

        self.controllers: dict[int, Controller] = {}
        self.controller_count = 12

        self.vehicles: dict[int, Vehicle] = {}
        self.vehicle_count = 0

        for section in config.sections():
            if section.endswith(".vehicles"):
                device_vehicles = config[section].items()
                device_name = section.replace(".vehicles", "")
                device_config = config[device_name]
                
                for vehicle_id, vehicle_name in device_vehicles:
                    self.vehicle_count += 1
                    self.vehicles[int(vehicle_id)] = Vehicle.configure(
                        type=device_name,
                        config=device_config,
                        id=int(vehicle_id),
                        name=vehicle_name,
                        logger=self.logger
                    )

        for controller_id in range(1, self.controller_count + 1):
            self.controllers[controller_id] = Controller(self, controller_id, self.logger)

    def assign_controller(self, player_id):
        """
        Assigns an available controller to a client session.

        Args:
            player_id (str): Socket.IO session identifier.

        Returns:
            Controller or None: The assigned controller.
        """
        for controller in self.controllers.values():
            if controller.player_id is None:
                controller.player_id = player_id
                controller.selection = None
                self.logger.info(f"Assigned controller {controller.controller_id} to player {player_id}")
                return controller
        self.logger.warning(f"No controller available for player {player_id}")
        return None

    def release_controller(self, player_id):
        """
        Releases the controller associated with a client session.

        Args:
            player_id (str): Socket.IO session identifier.

        Returns:
            Controller or None: The released controller.
        """
        for controller in self.controllers.values():
            if controller.player_id == player_id:
                controller.player_id = None
                controller.player_name = None
                self.logger.info(f"Released controller {controller.controller_id} from player {player_id}")
                return controller
        return None

    def get_controller(self, player_id):
        """
        Retrieves the controller associated with a client session.

        Args:
            player_id (str): Socket.IO session identifier.

        Returns:
            Controller or None: The matching controller.
        """
        for controller in self.controllers.values():
            if controller.player_id == player_id:
                return controller
        return None

    def get_vehicle(self, vehicle_id=None):
        """
        Retrieves a vehicle by its ID.

        Args:
            vehicle_id (int or None): The vehicle identifier.

        Returns:
            Vehicle or None: The matching vehicle.
        """
        for vehicle in self.vehicles.values():
            if vehicle.id == vehicle_id:
                return vehicle
        return None

    def get_players(self):
        """
        Retrieves data about all connected players and times out selections if needed.

        Returns:
            list[dict]: A list of player metadata dictionaries:
                - 'player_name' (str or None): Player display name
                - 'selection' (int or None): Currently selected vehicle ID
                - 'selection_name' (str or None): Name of the selected vehicle
        """
        players = []

        for controller in self.controllers.values():
            if controller.player_id:

                if controller.selection and time.time() - controller.last_activity > self.config.getint('webserver', 'player_timeout'):
                    controller.selection = None
                
                player_vehicle = self.get_vehicle(controller.selection) if controller.selection else None
                
                players.append({
                    "player_name": controller.player_name,
                    "selection": controller.selection,
                    "selection_name": player_vehicle.name if player_vehicle else None
                })

        return players
