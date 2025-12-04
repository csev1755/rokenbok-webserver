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

//---------------------------------------------------------------------------------------------
// THIS SECTION IS FOR SMART PORT VARIABLES - USE CAUTION WHEN MAKING CHANGES
//---------------------------------------------------------------------------------------------

bool smart_port_status = false;

int current_series = 0;
int series_count = 0;

byte rec_byte = 0;
byte send_byte = 0;

int p1_control, p2_control, p3_control, p4_control;
int enabled_controllers;

int* control_map[] = {
  &p1_control,
  &p2_control,
  &p3_control,
  &p4_control
};

uint8_t controller_masks[] = {
  0b00000001,
  0b00000010,
  0b00000100,
  0b00001000
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
  &sel_button,
  &lt,
  &share,
  &is16SEL,
  &up,
  &down,
  &right,
  &left,
  &a,
  &b,
  &x,
  &y,
  &rt
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
  if (button >= 0 && button < (sizeof(button_map) / sizeof(button_map[0]))) {
    *button_map[button] &= ~(1 << controller);
    priority_byte |= (1 << controller);
  }
}

void enable_physical_controller(int controller) {
  if (controller >= 0 && controller < 4) {
    *control_map[controller] = 1;
    enabled_controllers &= ~controller_masks[controller];
  }
}

void disable_physical_controller(int controller) {
  if (controller >= 0 && controller < 4) {
    *control_map[controller] = 0;
    enabled_controllers |= controller_masks[controller];
  }
}

void begin_smart_port(int slave_ready_pin) {
  pinMode(MISO, OUTPUT);
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

  switch (current_series) {

    case NO_SERIES:
      switch (rec_byte) {
        case 0xC6:
          current_series = SYNC_SERIES;
          series_count = 1;
          send_byte = 0x81;
          break;

        case 0xC3:
          current_series = EDIT_TPADS_SERIES;
          series_count = 1;
          send_byte = 0x80;
          break;

        case 0xC4:
          current_series = EDIT_SELECT_SERIES;
          series_count = 1;
          send_byte = 0x80;
          break;

        default:
          current_series = NO_SERIES;
          series_count = 0;
          send_byte = 0x00;
          break;
      }
      break;

      
    case SYNC_SERIES:
      switch (series_count) {
        case 1:
          series_count = 2;
          send_byte = enable_attrib_byte;
          break;

        case 2:
          current_series = NO_SERIES;
          series_count = 0;
          send_byte = send_no_sel_to;

          TCNT1 = 0; // Reset timer.
          digitalWrite(8, HIGH);
          smart_port_status = true;
          break;

        default:
          current_series = NO_SERIES;
          series_count = 0;
          send_byte = 0x00;
          break;
      }
      break;


    case EDIT_TPADS_SERIES:
      switch (series_count) {

        case 1:  series_count = 2;  send_byte = (rec_byte & enabled_controllers) | sel_button;     break;
        case 2:  series_count = 3;  send_byte = (rec_byte & enabled_controllers) | lt;             break;
        case 3:  series_count = 4;  send_byte = (rec_byte & enabled_controllers) | share;          break;
        case 4:  series_count = 5;  send_byte = rec_byte;                                          break; // RESERVED
        case 5:  series_count = 6;  send_byte = (rec_byte & enabled_controllers) | is16SEL;        break;
        case 6:  series_count = 7;  send_byte = (rec_byte & enabled_controllers) | up;             break;
        case 7:  series_count = 8;  send_byte = (rec_byte & enabled_controllers) | down;           break;
        case 8:  series_count = 9;  send_byte = (rec_byte & enabled_controllers) | right;          break;
        case 9:  series_count = 10; send_byte = (rec_byte & enabled_controllers) | left;           break;
        case 10: series_count = 11; send_byte = (rec_byte & enabled_controllers) | a;              break;
        case 11: series_count = 12; send_byte = (rec_byte & enabled_controllers) | b;              break;
        case 12: series_count = 13; send_byte = (rec_byte & enabled_controllers) | x;              break;
        case 13: series_count = 14; send_byte = (rec_byte & enabled_controllers) | y;              break; 
        case 14: series_count = 15; send_byte = !enabled_controllers;                              break; // RESERVED (This Line Somehow Helps Physical Controllers)
        case 15: series_count = 16; send_byte = !enabled_controllers;                              break; // RESERVED (This Line Somehow Helps Physical Controllers)
        case 16: series_count = 17; send_byte = (rec_byte & enabled_controllers) | rt;             break;
        case 17: series_count = 18; send_byte = rec_byte;                                          break; // SPARE

        case 18:
          current_series = NO_SERIES;
          series_count = 0;
          send_byte = rec_byte | priority_byte;
          priority_byte = 0x00;
          break;

        default:
          current_series = NO_SERIES;
          series_count = 0;
          send_byte = 0x00;
          break;
      }
      break;


    case EDIT_SELECT_SERIES:
      switch (series_count) {
        case 1:
          series_count = 2;
          send_byte = p1_control ? p1_select : rec_byte;
          break;

        case 2:
          series_count = 3;
          send_byte = p2_control ? p2_select : rec_byte;
          break;

        case 3:
          series_count = 4;
          send_byte = p3_control ? p3_select : rec_byte;
          break;

        case 4:
          series_count = 5;
          send_byte = p4_control ? p4_select : rec_byte;
          break;

        case 5:
          series_count = 6;
          send_byte = v1_select;
          break;

        case 6:
          series_count = 7;
          send_byte = v2_select;
          break;

        case 7:
          series_count = 8;
          send_byte = v3_select;
          break;

        case 8:
          series_count = 9;
          send_byte = v4_select;
          break;

        case 9:
          current_series = NO_SERIES;
          series_count = 0;
          send_byte = 0x00;
          break;

        default:
          current_series = NO_SERIES;
          series_count = 0;
          send_byte = 0x00;
          break;
      }
      break;


    default:
      current_series = NO_SERIES;
      series_count = 0;
      send_byte = 0x00;
      break;
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
