import time


class Player:
    """
    A single Player object assigned to a client.

    Attributes:
        play_manager (PlayManager): Parent PlayManager instance.
        player_id (int): Player object identifier.
        selection (int or None): Current vehicle selection (1-indexed), or None if no vehicle selected.
        player_name (str or None): Display name of the player.
        socket_id (str or None): Socket.IO session identifier for the connected player.
        buttons (set): Set of currently pressed button identifiers.
        last_activity (float): Timestamp of the last input.
    """

    def __init__(self, play_manager, player_id, logger):
        """
        Initializes a Player instance.

        Args:
            play_manager (PlayManager): Parent PlayManager.
            player_id (int): Player identifier.
        """
        self.play_manager = play_manager
        self.selection = None
        self.player_name = None
        self.socket_id = None
        self.player_id = player_id
        self.buttons = set()
        self.last_activity = time.time()
        self.logger = logger

    def cycle_vehicle_select(self, delta):
        """
        Cycles through available vehicles.

        Args:
            delta (int): A positive or negative integer that determines the direction and length of each step in the cycle
        """
        new_selection = self.selection if self.selection is not None else 0
        occupied_selections = {player["selection"] for player in self.play_manager.get_player_info() if player["selection"] is not None}

        for _selection in range(self.play_manager.vehicle_count):
            new_selection = (new_selection + delta) % (self.play_manager.vehicle_count + 1)
            if new_selection == 0:
                self.selection = None
                return
            if new_selection not in occupied_selections:
                self.selection = new_selection
                return

    def handle_input(self, input):
        """
        Processes player input, updates button states, and controls a selected vehicle.

        Args:
            input (dict): A dictionary containing:
                - 'button' (str): Button identifier
                - 'pressed' (bool): True if button is pressed, False if released
        """
        if input["pressed"]:
            if input["button"] in ("SELECT_UP", "SELECT_DOWN"):
                old_vehicle = self.play_manager.get_vehicle_from_id(self.selection) or None
                delta = 1 if input["button"] == "SELECT_UP" else -1
                self.cycle_vehicle_select(delta)
                if old_vehicle:
                    old_vehicle.control(self, self.play_manager)  # Old vehicle must be controlled to release inputs.
            self.buttons.add(input["button"])
        else:
            self.buttons.discard(input["button"])

        self.logger.debug(f"Session {self.socket_id} - {self.buttons if len(self.buttons) > 0 else {''}} - {self.selection}")

        vehicle = self.play_manager.get_vehicle_from_id(self.selection) or None
        if vehicle:
            vehicle.control(self, self.play_manager)
            self.last_activity = time.time()
