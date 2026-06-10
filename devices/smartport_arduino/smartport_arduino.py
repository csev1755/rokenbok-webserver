import serial
from devices.vehicle import Vehicle

class SmartPortArduino(Vehicle):
    """
    Device type/vehicle class for the smartport_arduino sketch
    """
    type = "smartport_arduino"
    serial = None

    def __init__(self, config, id, name, logger=None):
        super().__init__(self, config, id, name, logger)

    def connect_serial(self):
        """
        Establishes a serial connection to the SmartPort Arduino if not already connected.
        """
        if not SmartPortArduino.serial:
            try:
                SmartPortArduino.serial = serial.Serial(self.config['serial_port'], 1000000)
                print(f" * Connected to SmartPort Arduino at '{self.config['serial_port']}'")
                return True
            except Exception as e:
                self.logger.error(f"Cannot connect to SmartPort Arduino at '{self.config['serial_port']}'")
                self.logger.debug(e)
                return False
        else:
            return True

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
        if not self.connect_serial():
            return

        try:
            SmartPortArduino.serial.write(packet)

            if SmartPortArduino.serial.in_waiting >= 27:
                raw = SmartPortArduino.serial.read(SmartPortArduino.serial.in_waiting)
                start = raw.rfind(254)

                if start != -1 and len(raw) >= start + 27 and raw[start + 26] == 255:
                    frame = raw[start:start + 27]
                    if not frame[1]:
                        self.logger.debug(f"SmartPortArduino - Invalid packet: {raw}")
                        self.logger.warning(f"SmartPortArduino - SmartPort communication error")

                    self.logger.debug(f"SmartPortArduino Selections - {[None if x == 15 else x + 1 for x in frame[14:26]]}")
                
                else:
                    self.logger.debug(f"SmartPortArduino - Invalid packet: {raw}")
                    self.logger.warning(f"SmartPortArduino - SmartPort communication error")
            
            else:
                self.logger.debug(f"SmartPortArduino - No packet received")

        except Exception as e:
            self.logger.debug(e)
            self.logger.error(f"Cannot connect to SmartPort Arduino at '{self.config['serial_port']}'")
            SmartPortArduino.serial = None
