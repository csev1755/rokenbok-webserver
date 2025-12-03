/* SMART PORT ARDUINO DEMO CODE
 * AUTHORS: STEPSTOOLS, CSEV1755
 * DATE: 2 DEC 25
 * ROKENBOK DISCORD: https://discord.gg/pmbbAsq
 */

//---------------------------------------------------------------------------------------------
// THIS SECTION IS FOR SMART PORT DEFINES - USE CAUTION WHEN MAKING CHANGES
//---------------------------------------------------------------------------------------------

#define slaveReadyPin 8

#define enable_attrib_byte   0x0D
#define disable_attrib_byte  0x00
#define send_no_sel_to       0x00

#define NO_SERIES           0
#define SYNC_SERIES         1
#define EDIT_TPADS_SERIES   2
#define EDIT_SELECT_SERIES  3

#define PHYSICAL_CONTROLLER_1  0
#define PHYSICAL_CONTROLLER_2  1
#define PHYSICAL_CONTROLLER_3  2
#define PHYSICAL_CONTROLLER_4  3
#define VIRTUAL_CONTROLLER_1   4
#define VIRTUAL_CONTROLLER_2   5
#define VIRTUAL_CONTROLLER_3   6
#define VIRTUAL_CONTROLLER_4   7

#define SELECT_KEY_1    0
#define SELECT_KEY_2    1
#define SELECT_KEY_3    2
#define SELECT_KEY_4    3
#define SELECT_KEY_5    4
#define SELECT_KEY_6    5
#define SELECT_KEY_7    6
#define SELECT_KEY_8    7
#define SELECT_KEY_9    8
#define SELECT_KEY_10   9
#define SELECT_KEY_11   10
#define SELECT_KEY_12   11
#define SELECT_KEY_13   12
#define SELECT_KEY_14   13
#define SELECT_KEY_15   14
#define NO_SELECTION    15

#define SELECT_BUTTON         0
#define LEFT_TRIGGER          1
#define SHARE_SWITCH          2
#define IS16SEL_CONTROLLER    3
#define DPAD_UP               4
#define DPAD_DOWN             5
#define DPAD_RIGHT            6
#define DPAD_LEFT             7
#define A_BUTTON              8
#define B_BUTTON              9
#define X_BUTTON              10
#define Y_BUTTON              11
#define RIGHT_TRIGGER         12

//---------------------------------------------------------------------------------------------
// THIS SECTION IS FOR SMART PORT VARIABLES - USE CAUTION WHEN MAKING CHANGES
//---------------------------------------------------------------------------------------------

bool smart_port_status = false;

int current_series = 0;  // 0 = Not In Series, 1 = Sync, 2 = Edit T-Pads, 3 = Edit Select
int series_count = 0;

byte rec_byte = 0;
byte send_byte = 0;

int p1_control, p2_control, p3_control, p4_control;
int enabled_controllers;

int* control_map[] = {
  &p1_control,   // PHYSICAL_CONTROLLER_1
  &p2_control,   // PHYSICAL_CONTROLLER_2
  &p3_control,   // PHYSICAL_CONTROLLER_3
  &p4_control    // PHYSICAL_CONTROLLER_4
};

uint8_t controller_masks[] = {
  0b00000001,    // PHYSICAL_CONTROLLER_1
  0b00000010,    // PHYSICAL_CONTROLLER_2
  0b00000100,    // PHYSICAL_CONTROLLER_3
  0b00001000     // PHYSICAL_CONTROLLER_4
};

int p1_select, p2_select, p3_select, p4_select;
int v1_select, v2_select, v3_select, v4_select;

int* controller_map[] = {
  &p1_select, &p2_select, &p3_select, &p4_select,
  &v1_select, &v2_select, &v3_select, &v4_select
};

int sel_button, lt, share, is16SEL;
int up, down, right, left;
int a, b, x, y, rt;
int priority_byte;

int* button_map[] = {
  &sel_button,   // SELECT_BUTTON
  &lt,            // LEFT_TRIGGER
  &share,        // SHARE_SWITCH
  &is16SEL,      // IS16SEL_CONTROLLER
  &up,           // DPAD_UP
  &down,         // DPAD_DOWN
  &right,        // DPAD_RIGHT
  &left,         // DPAD_LEFT
  &a,            // A_BUTTON
  &b,            // B_BUTTON
  &x,            // X_BUTTON
  &y,            // Y_BUTTON
  &rt            // RIGHT_TRIGGER
};

//---------------------------------------------------------------------------------------------
// THIS SECTION IS FOR SMART PORT USER CALLABLE FUNCTIONS - USE CAUTION WHEN MAKING CHANGES
//---------------------------------------------------------------------------------------------

void edit_select(int controller, int selection) {
  if (controller >= 0 && controller < 8) {
    *controller_map[controller] = selection;
  }
}

void press_button(int controller, int button) {
  if (button >= 0 && button < (sizeof(button_map) / sizeof(button_map[0]))) {
    *button_map[button] |= (1 << controller);
    priority_byte |= (1 << controller);
  }
}

void release_button(int controller, int button) {
  // Make sure button index is valid
  if (button >= 0 && button < (sizeof(button_map) / sizeof(button_map[0]))) {
    *button_map[button] &= ~(1 << controller);   // clear bit
    priority_byte |= (1 << controller);          // same as before
  }
}

void enable_physical_controller(int controller) {
  if (controller >= 0 && controller < 4) {
    *control_map[controller] = 1;
    enabled_controllers &= ~controller_masks[controller]; // clear that bit
  }
}

void disable_physical_controller(int controller) {
  if (controller >= 0 && controller < 4) {
    *control_map[controller] = 0;
    enabled_controllers |= controller_masks[controller];  // set that bit
  }
}

void begin_smart_port(int slave_ready_pin) {
  pinMode(MISO, OUTPUT);  // have to send on master in, *slave out*
  pinMode(MOSI, INPUT);
  pinMode(SCK, INPUT);
  pinMode(slave_ready_pin, OUTPUT);

  pinMode(2, OUTPUT);

  SPCR |= _BV(SPE);  // Enable SPI (Slave Mode)
  SPCR |= _BV(SPIE); // Enable SPI Interrupt
  SPDR = 0x00; // Zero Out SPI Register

  TCCR1A = 0;
  TCCR1B = 0;

  TCNT1 = 0;
  TCCR1B |= (1 << CS10);    // 64 prescaler 
  TCCR1B |= (1 << CS11);    // 64 prescaler 
  TIMSK1 |= (1 << TOIE1);   // enable timer overflow interrupt
  
  digitalWrite(slaveReadyPin, HIGH); // Ready for the first byte.
}

//---------------------------------------------------------------------------------------------
// RECEIVE COMMANDS VIA SERIAL
//---------------------------------------------------------------------------------------------

void setup() {
  Serial.begin(115200); 
  begin_smart_port(slaveReadyPin);
}

void receive_command(String cmd) {
  cmd.trim();  // Remove whitespace/newlines

  if (cmd.startsWith("PRESS,")) {
    int controller = cmd.substring(6, cmd.indexOf(',', 6)).toInt();
    int button = cmd.substring(cmd.lastIndexOf(',') + 1).toInt();
    press_button(controller, button);

  } else if (cmd.startsWith("RELEASE,")) {
    int controller = cmd.substring(8, cmd.indexOf(',', 8)).toInt();
    int button = cmd.substring(cmd.lastIndexOf(',') + 1).toInt();
    release_button(controller, button);

  } else if (cmd.startsWith("EDIT,")) {
    int controller = cmd.substring(5, cmd.indexOf(',', 5)).toInt();
    int selection = cmd.substring(cmd.lastIndexOf(',') + 1).toInt();
    edit_select(controller, selection);

  } else if (cmd.startsWith("ENABLE,")) {
    int controller = cmd.substring(7).toInt();
    enable_physical_controller(controller);

  } else if (cmd.startsWith("DISABLE,")) {
    int controller = cmd.substring(8).toInt();
    disable_physical_controller(controller);

  } else {
    true;
  }
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    receive_command(cmd);
  }
}

//---------------------------------------------------------------------------------------------
// THIS SECTION IS FOR SMART PORT INTERRUPTS - USE CAUTION WHEN MAKING CHANGES
//---------------------------------------------------------------------------------------------

ISR (SPI_STC_vect) {
  digitalWrite(slaveReadyPin, HIGH); // We are NOT ready for a new byte.

  rec_byte = SPDR;
  //Serial.println(rec_data, HEX);

  // NO SERIES
  if (current_series == NO_SERIES) {
    if (rec_byte == 0xC6) {
      current_series = SYNC_SERIES;
      series_count = 1;
      send_byte = 0x81;

    } else if (rec_byte == 0xC3) {
      current_series = EDIT_TPADS_SERIES;
      series_count = 1;
      send_byte = 0x80;

    } else if (rec_byte == 0xC4) {
      current_series = EDIT_SELECT_SERIES;
      series_count = 1;
      send_byte = 0x80;

    } else {
      current_series = NO_SERIES;
      series_count = 0;
      send_byte = 0x00;
    }

    // SYNC SERIES
  } else if (current_series == SYNC_SERIES) {
    if (series_count == 1) {
      series_count = 2;
      send_byte = enable_attrib_byte;
    } else if (series_count == 2) {
      current_series = NO_SERIES;
      series_count = 0;
      send_byte = send_no_sel_to;

      TCNT1 = 0; // Reset timer.
      digitalWrite(8, HIGH);
      smart_port_status = true;
    } else {
      current_series = NO_SERIES;
      series_count = 0;
      send_byte = 0x00;
    }

    // EDIT TPADS SERIES
  } else if (current_series == EDIT_TPADS_SERIES) {
    if (series_count == 1) {
      series_count = 2;
      send_byte = (rec_byte & enabled_controllers) | sel_button; // Select Button

    } else if (series_count == 2) {
      series_count = 3;
      send_byte = (rec_byte & enabled_controllers) | lt; // Left Trigger (Last Select)

    } else if (series_count == 3) {
      series_count = 4;
      send_byte = (rec_byte & enabled_controllers) | share; // Sharing Mode (1 = Allow Sharing)

    } else if (series_count == 4) {
      series_count = 5;
      send_byte = rec_byte; // RESERVED

    } else if (series_count == 5) {
      series_count = 6;
      send_byte = (rec_byte & enabled_controllers) | is16SEL; // IS16SEL

    } else if (series_count == 6) {
      series_count = 7;
      send_byte = (rec_byte & enabled_controllers) | up; // D Pad Up

    } else if (series_count == 7) {
      series_count = 8;
      send_byte = (rec_byte & enabled_controllers) | down; // D Pad Down

    } else if (series_count == 8) {
      series_count = 9;
      send_byte = (rec_byte & enabled_controllers) | right; // D Pad Right

    } else if (series_count == 9) {
      series_count = 10;
      send_byte = (rec_byte & enabled_controllers) | left; // D Pad Left

    } else if (series_count == 10) {
      series_count = 11;
      send_byte = (rec_byte & enabled_controllers) | a; // A

    } else if (series_count == 11) {
      series_count = 12;
      send_byte = (rec_byte & enabled_controllers) | b; // B

    } else if (series_count == 12) {
      series_count = 13;
      send_byte = (rec_byte & enabled_controllers) | x; // X

    } else if (series_count == 13) {
      series_count = 14;
      send_byte = (rec_byte & enabled_controllers) | y; // Y

    } else if (series_count == 14) {
      series_count = 15;
      send_byte = !enabled_controllers; // RESERVED (This Line Somehow Helps Physical Controllers)

    } else if (series_count == 15) {
      series_count = 16;
      send_byte = !enabled_controllers; // RESERVED (This Line Somehow Helps Physical Controllers)

    } else if (series_count == 16) {
      series_count = 17;
      send_byte = (rec_byte & enabled_controllers) | rt; // Right Trigger (Slow)

    } else if (series_count == 17) {
      series_count = 18;
      send_byte = rec_byte; // Spare

    } else if (series_count == 18) {
      current_series = NO_SERIES;
      series_count = 0;
      send_byte = rec_byte | priority_byte; // Priority Byte
      priority_byte = 0x00;

    } else {
      current_series = NO_SERIES;
      series_count = 0;
      send_byte = 0x00;
    }

    // EDIT SELECT SERIES
  } else if (current_series == EDIT_SELECT_SERIES) {
    if (series_count == 1) {
      series_count = 2;
      //spi_rec_select[0] = rec_byte;
      if (p1_control) {
        send_byte = p1_select;
      } else {
        send_byte = rec_byte;
      }

    } else if (series_count == 2) {
      series_count = 3;
      //spi_rec_select[1] = rec_byte;
      if (p2_control) {
        send_byte = p2_select;
      } else {
        send_byte = rec_byte;
      }

    } else if (series_count == 3) {
      series_count = 4;
      //spi_rec_select[2] = rec_byte;
      if (p3_control) {
        send_byte = p3_select;
      } else {
        send_byte = rec_byte;
      }

    } else if (series_count == 4) {
      series_count = 5;
      //spi_rec_select[3] = rec_byte;
      if (p4_control) {
        send_byte = p4_select;
      } else {
        send_byte = rec_byte;
      }

    } else if (series_count == 5) {
      series_count = 6;
      //spi_rec_select[4] = rec_byte;
      send_byte = v1_select;

    } else if (series_count == 6) {
      series_count = 7;
      //spi_rec_select[5] = rec_byte;
      send_byte = v2_select;

    } else if (series_count == 7) {
      series_count = 8;
      //spi_rec_select[6] = rec_byte;
      send_byte = v3_select;

    } else if (series_count == 8) {
      series_count = 9;
      //spi_rec_select[7] = rec_byte;
      send_byte = v4_select;

    } else if (series_count == 9) {
      current_series = NO_SERIES;
      series_count = 0;
      send_byte = 0x00;
      // Timer Value Received, Send Null

    } else {
      current_series = NO_SERIES;
      series_count = 0;
      send_byte = 0x00;
    }

    // CATCH ALL
  } else {
    current_series = NO_SERIES;
    series_count = 0;
    send_byte = 0x00;
  }

  SPDR = send_byte;

  digitalWrite(slaveReadyPin, LOW); // We are ready for a new byte.
}

ISR(TIMER1_OVF_vect) {
  SPCR = 0;
  current_series = 0;
  series_count = 0;
  SPCR |= _BV(SPE);  // Enable SPI (Slave Mode)
  SPCR |= _BV(SPIE); // Enable SPI Interrupt
  
  smart_port_status = false;
  digitalWrite(8, LOW);
}
