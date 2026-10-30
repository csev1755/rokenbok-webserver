import serial
from devices.vehicle import Vehicle


class SmartPortArduino(Vehicle):
    """
    Device type/vehicle class for the smart_port_arduino sketch.
    https://github.com/stepstools/Rokenbok-Smart-Port-Arduino
    """

    type = "smartport_arduino"
    serial = None

    def __init__(self, config, id, name, logger):
        super().__init__(self, config, id, name, logger)

    def connect_serial(self):
        """
        Establishes a serial connection to the SmartPort Arduino if not already connected.
        """
        if SmartPortArduino.serial is None:
            try:
                SmartPortArduino.serial = serial.Serial(self.config["serial_port"], 1000000)
                print(f" * Connected to SmartPort Arduino at '{self.config['serial_port']}'")
                return True
            except Exception as e:
                self.logger.error(f"Cannot connect to SmartPort Arduino at '{self.config['serial_port']}'")
                self.logger.debug(e)
                return False
        else:
            return True

    def encode_player_state(self, player):
        """
        Encodes player button states into two bytes for serial transmission.

        Byte 1: D-pad directions (up, down, right, left)
        Byte 2: Action buttons (A, B, X, Y) and triggers

        Args:
            player (Player): A player object.

        Returns:
            tuple[int, int]: Two bytes representing the player state.
        """
        up = "DPAD_UP" in player.buttons
        down = "DPAD_DOWN" in player.buttons
        right = "DPAD_RIGHT" in player.buttons
        left = "DPAD_LEFT" in player.buttons

        b_a = "A_BUTTON" in player.buttons
        b_b = "B_BUTTON" in player.buttons
        b_x = "X_BUTTON" in player.buttons
        b_y = "Y_BUTTON" in player.buttons

        b_rt = int("LEFT_TRIGGER" in player.buttons or "RIGHT_TRIGGER" in player.buttons)

        byte1 = (up << 3) | (down << 2) | (right << 1) | left
        byte2 = (b_a << 4) | (b_b << 3) | (b_x << 2) | (b_y << 1) | b_rt

        return byte1, byte2

    def control(self, player, play_manager):
        """
        Constructs and transmits a packet containing the state of all players
        to the Arduino and receives data representing the command deck's state.
        """
        packet = bytearray([254])
        for player in play_manager.players.values():
            p_id = player.player_id + 10 or 0
            v_sel = 15 if player.selection is None else player.selection - 1
            byte1, byte2 = self.encode_player_state(player) if player.selection is not None else (0, 0)
            packet.extend([p_id, v_sel, byte1, byte2])
        packet.append(255)
        self.send_and_receive_packet(packet)

    def send_and_receive_packet(self, packet):
        """
        Sends a packet via serial and processes any incoming response.

        Args:
            packet (bytearray): The packet to transmit.
        """
        if not self.connect_serial():
            return

        try:
            if SmartPortArduino.serial is not None:
                SmartPortArduino.serial.write(packet)

                if SmartPortArduino.serial.in_waiting >= 27:
                    raw = SmartPortArduino.serial.read(SmartPortArduino.serial.in_waiting)
                    start = raw.rfind(254)

                    if start != -1 and len(raw) >= start + 27 and raw[start + 26] == 255:
                        frame = raw[start : start + 27]
                        if not frame[1]:
                            self.logger.debug(f"SmartPortArduino - Invalid packet: {raw}")
                            self.logger.warning(f"SmartPortArduino - SmartPort communication error")

                        self.logger.debug(f"SmartPortArduino Selections - {[None if x == 15 else x + 1 for x in frame[14:26]]}")

                    else:
                        self.logger.debug(f"SmartPortArduino - Invalid packet: {raw}")
                        self.logger.warning(f"SmartPortArduino - SmartPort communication error")

                else:
                    self.logger.debug(f"SmartPortArduino - No packet received")
            else:
                self.logger.error(f"Serial connection to SmartPort Arduino is not established")

        except Exception as e:
            self.logger.debug(e)
            self.logger.error(f"Cannot connect to SmartPort Arduino at '{self.config['serial_port']}'")
            SmartPortArduino.serial = None
