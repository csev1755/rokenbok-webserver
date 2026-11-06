import serial
import serial.tools.list_ports

from devices.vehicle import Vehicle


class SmartPortSerial(Vehicle):
    """
    Device type/vehicle class for Smart Port devices that are controlled over serial.
    https://github.com/stepstools/Rokenbok-Smart-Port-Arduino
    https://github.com/stepstools/Rokenbok-Smart-Port-WiFi
    """

    type = "smartport_serial"
    serial = None

    def __init__(self, play_manager, config, id, name, logger):
        super().__init__(play_manager, config, id, name, logger)

    def connect_serial(self):
        """
        Establishes a serial connection to the Smart Port serial device if not already connected.
        Sends the configuration packet using send_configuration() once the connection is established.
        """
        if SmartPortSerial.serial is None:
            try:
                if self.config["serial_port"] == "auto":
                    device_found = False
                    for port in serial.tools.list_ports.comports():
                        if port.vid in [0x2341, 0x1A86, 0x239A, 0x1B4F, 0x303A]:  # Common Arduino and ESP32 VIDs.
                            SmartPortSerial.serial = serial.Serial(port.device, 1000000)
                            print(f" * Auto detected and connected to SmartPort serial device at '{port.device}'")
                            device_found = True
                            break
                    if not device_found:
                        self.logger.error("Failed to auto detect SmartPort serial device")
                        return False
                else:
                    SmartPortSerial.serial = serial.Serial(self.config["serial_port"], 1000000)
                    print(f" * Connected to SmartPort serial device at '{self.config['serial_port']}'")
                self.send_configuration()
                return True
            except serial.SerialException as e:
                self.logger.error(f"Cannot connect to SmartPort serial device at '{self.config['serial_port']}'")
                self.logger.debug(e)
                return False
        else:
            return True

    def send_configuration(self):
        """
        Sends configuration bytes to the serial device.
        """
        if not self.connect_serial():
            return

        try:
            if SmartPortSerial.serial is not None:
                packet = bytearray(
                    [
                        253,
                        int(self.play_manager.allow_share),
                        int(sum(1 for v in self.play_manager.vehicles.values() if v.type == "smartport_serial") > 8),
                        int(self.config.getboolean("enable_wifi")),
                        0,  # Reserved for future use.
                        255,
                    ]
                )
                SmartPortSerial.serial.write(packet)
                self.logger.debug(f"SmartPortSerial - Sent Config: {packet}")
            else:
                self.logger.error("Connection to SmartPort serial device is not established")

        except serial.SerialException as e:
            self.logger.debug(e)
            self.logger.error(f"Cannot connect to SmartPort serial device at '{self.config['serial_port']}'")
            SmartPortSerial.serial = None

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
        to the serial device and receives data representing the command deck's state.
        """
        packet = bytearray([254])
        for p in play_manager.players.values():
            if p.socket_id and p.selection and play_manager.get_vehicle_from_id(p.selection).type == "smartport_serial":
                p_id = p.player_id + 1 or 0
                v_sel = p.selection - 1
                byte1, byte2 = self.encode_player_state(p) if p.selection is not None else (0, 0)
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
            if SmartPortSerial.serial is not None:
                SmartPortSerial.serial.write(packet)
                self.logger.debug(f"SmartPortSerial - Sent: {packet}")

                if SmartPortSerial.serial.in_waiting >= 27:
                    raw = SmartPortSerial.serial.read(SmartPortSerial.serial.in_waiting)
                    start = raw.rfind(254)

                    if start != -1 and len(raw) >= start + 27 and raw[start + 26] == 255:
                        frame = raw[start : start + 27]
                        if not frame[1]:
                            self.logger.warning("SmartPortSerial - SmartPort Connection to Command Deck Not Established")

                        self.logger.debug(f"SmartPortSerial Player IDs - {[int(x) for x in frame[2:14]]}")
                        self.logger.debug(f"SmartPortSerial Selections - {[None if x == 15 else x + 1 for x in frame[14:26]]}")

                    else:
                        self.logger.debug(f"SmartPortSerial - Invalid Response: {raw}")
                        self.logger.warning("SmartPortSerial - SmartPort Communication Error")

                else:
                    self.logger.debug("SmartPortSerial - No Response Received")
            else:
                self.logger.error("Connection to SmartPort serial device is not established")

        except serial.SerialException as e:
            self.logger.debug(e)
            self.logger.error(f"Cannot connect to SmartPort serial device at '{self.config['serial_port']}'")
            SmartPortSerial.serial = None
