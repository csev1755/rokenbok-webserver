import time
from devices.vehicle import Vehicle
from server.player import Player


class PlayManager:
    """
    Manages player and vehicle states.

    Attributes:
        players (dict[int, Player]): Mapping of player IDs to Player instances.
        player_count (int): Max number of players (default: 12).
        vehicles (dict[int, Vehicle]): Mapping of vehicle IDs to Vehicle instances.
        vehicle_count (int): Number of selectable vehicles.
    """

    def __init__(self, config, logger):
        """
        Initializes the PlayManager and Player obects.

        Reads vehicle/device configurations from the config file and creates vehicle instances.
        """
        self.logger = logger
        self.config = config

        self.players: dict[int, Player] = {}
        self.player_count = 12

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
                        type=device_name, config=device_config, id=int(vehicle_id), name=vehicle_name, logger=self.logger
                    )

        for player_id in range(1, self.player_count + 1):
            self.players[player_id] = Player(self, player_id, self.logger)

    def player_join(self, socket_id):
        """
        Assigns an available Player object to a client session.

        Args:
            socket_id (str): Socket.IO session identifier.

        Returns:
            Player or None: The assigned Player object.
        """
        for player in self.players.values():
            if player.socket_id is None:
                player.socket_id = socket_id
                player.selection = None
                self.logger.info(f"Assigned Player object {player.player_id} to player {socket_id}")
                return player
        self.logger.warning(f"No Player object available for player {socket_id}")
        return None

    def player_quit(self, socket_id):
        """
        Releases the Player object associated with a client session.

        Args:
            socket_id (str): Socket.IO session identifier.

        Returns:
            Player or None: The released Player object.
        """
        for player in self.players.values():
            if player.socket_id == socket_id:
                player.socket_id = None
                player.player_name = None
                self.logger.info(f"Released Player object {player.player_id} from player {socket_id}")
                return player
        return None

    def get_player_from_socket_id(self, socket_id):
        """
        Retrieves the Player object associated with a client session.

        Args:
            socket_id (str): Socket.IO session identifier.

        Returns:
            Player or None: The matching Player object.
        """
        for player in self.players.values():
            if player.socket_id == socket_id:
                return player
        return None

    def get_vehicle_from_id(self, vehicle_id=None):
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

    def get_player_info(self):
        """
        Retrieves data about all connected players and times out selections if needed.

        Returns:
            list[dict]: A list of player metadata dictionaries:
                - 'player_name' (str or None): Player display name
                - 'selection' (int or None): Currently selected vehicle ID
                - 'selection_name' (str or None): Name of the selected vehicle
        """
        players = []

        for player in self.players.values():
            if player.socket_id:
                if player.selection and time.time() - player.last_activity > self.config.getint("webserver", "player_timeout"):
                    player.selection = None

                player_vehicle = self.get_vehicle_from_id(player.selection) if player.selection else None
                players.append(
                    {
                        "player_name": player.player_name,
                        "selection": player.selection,
                        "selection_name": player_vehicle.name if player_vehicle else None,
                    }
                )

        return players
