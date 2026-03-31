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

    def cycle_vehicle_select(self, delta):
        """
        Cycles through available vehicles.

        Args:
            delta (int): A positive or negative integer that determines the direction and length of each step in the cycle
        """
        new_selection = self.selection if self.selection is not None else 0
        occupied_selections = {
            player["selection"]
            for player in self.command_deck.get_players()
            if player["selection"] is not None
        }

        for _selection in range(self.command_deck.vehicle_count):
            new_selection = (new_selection + delta) % (self.command_deck.vehicle_count + 1)
            if new_selection == 0:
                self.selection = None
                return
            if new_selection not in occupied_selections:
                self.selection = new_selection
                return      

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
                delta = 1 if input['button'] == "SELECT_UP" else -1
                self.cycle_vehicle_select(delta)
            self.buttons.add(input['button'])
        else:
            self.buttons.discard(input['button'])
        
        self.logger.debug(f"Session {self.player_id} - {self.buttons if len(self.buttons) > 0 else {''}} - {self.selection}")

        vehicle = self.command_deck.get_vehicle(self.selection) or None
        if vehicle:
            vehicle.control(self, self.command_deck)
