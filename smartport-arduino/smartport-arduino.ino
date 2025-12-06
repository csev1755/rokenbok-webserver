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

volatile bool smart_port_status = false;

volatile uint8_t current_series = 0;
volatile uint8_t series_count = 0;

volatile uint8_t rec_byte = 0;
volatile uint8_t send_byte = 0;

volatile uint8_t p1_control, p2_control, p3_control, p4_control;
volatile uint8_t enabled_controllers;

uint8_t* control_map[] = {
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

volatile uint8_t p1_select, p2_select, p3_select, p4_select;
volatile uint8_t v1_select, v2_select, v3_select, v4_select;

uint8_t* controller_map[] = {
  &p1_select, &p2_select, &p3_select, &p4_select,
  &v1_select, &v2_select, &v3_select, &v4_select
};

volatile uint8_t sel_button, lt, share, is16SEL;
volatile uint8_t up, down, right, left;
volatile uint8_t a, b, x, y, rt;
volatile uint8_t priority_byte;

uint8_t* button_map[] = {
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
// RECEIVE COMMANDS VIA SERIAL
//---------------------------------------------------------------------------------------------

void setup() {
  pinMode(MISO, OUTPUT);
  pinMode(MOSI, INPUT);
  pinMode(SCK, INPUT);
  pinMode(slaveReadyPin, OUTPUT);

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
  Serial.begin(115200); 
}

void receive_command(uint8_t *cmd, size_t len) {
  if (len < 3) return;

  uint8_t command    = cmd[0];
  uint8_t controller = cmd[1];
  uint8_t value      = cmd[2];

  switch (command) {
    case 0: // PRESS
      if (value < (sizeof(button_map) / sizeof(button_map[0]))) {
        *button_map[value] |= (1 << controller);
        priority_byte |= (1 << controller);
      }
      break;

    case 1: // RELEASE
      if (value < (sizeof(button_map) / sizeof(button_map[0]))) {
        *button_map[value] &= ~(1 << controller);
        priority_byte |= (1 << controller);
      }
      break;

    case 2: // EDIT
      if (controller < 8) {
        *controller_map[controller] = value;
      }
      break;

    case 3: // ENABLE
      if (controller < 4) {
        *control_map[controller] = 1;
        enabled_controllers &= ~controller_masks[controller];
      }
      break;

    case 4: // DISABLE
      if (controller < 4) {
        *control_map[controller] = 0;
        enabled_controllers |= controller_masks[controller];
      }
      break;

    default:
      break;
  }
}

void loop() {
  if (Serial.available() >= 3) {
    uint8_t cmd[3];
    Serial.readBytes(cmd, 3);
    receive_command(cmd, 3);
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
