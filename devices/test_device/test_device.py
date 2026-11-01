from devices.vehicle import Vehicle


class TestDevice(Vehicle):
    """
    Test device type that prints all controls to console for testing purposes.
    """

    type = "test_device"

    def __init__(self, config, id, name, logger):
        super().__init__(self, config, id, name, logger)

    def control(self, player, play_manager):
        """
        Prints player inputs for players that have this vehicle selected.
        """
        print(
            f"Player {player.player_id} controlled test_vehicle {player.selection} with input {player.buttons if len(player.buttons) > 0 else {''}}"
        )
