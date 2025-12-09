/* SMART PORT ARDUINO DEMO CODE
 * AUTHORS: STEPSTOOLS, CSEV1755
 * DATE: 2 DEC 25
 * ROKENBOK DISCORD: https://discord.gg/pmbbAsq
 */

// DEFINE MAGIC BYTES

#define SLAVE_READY_PIN 9

#define ENABLE_ATTRIB_BYTE   0x0D
#define DISABLE_ATTRIB_BYTE  0x00
#define NO_SEL_TIMEOUT       0x00

#define NULL_CMD 0x00
#define BCAST_TPADS 0xc0
#define BCAST_SELECT 0xC1
#define BCAST_END 0xC2
#define EDIT_TPADS 0xC3
#define EDIT_SELECT 0xC4
#define EDIT_END 0xC5
#define PRESYNC 0xC6
#define MASTER_SYNC 0xC7
#define READ_ATTRIB 0xC8
#define MASTER_NO_INS 0xC9
#define MASTER_ASK_INS 0xCA
#define READ_REPLY 0xCB
#define READ_NO_SEL_TIMEOUT 0xCC
#define NO_RADIO_PKT 0xCD
#define HAVE_RADIO_PKT 0xCE

#define NULL_CMD 0x00
#define VERIFY_EDIT 0x80
#define SLAVE_SYNC 0x81
#define SLAVE_NO_INS 0x82
#define SLAVE_WAIT_INS 0x83
#define PACKET_INJECT_ATTRIB_BYTE 0x2D // Packet Injection
#define ENABLE_ATTRIB_BYTE 0x0D // No Packet Injection
#define DISABLE_ATTRIB_BYTE 0x00
#define NO_SEL_TIMEOUT 0x00 // 1 = Controller Never Times Out, 0 = Normal V4|V3|V2|V1|P4|P3|P2|P1

#define NO_SERIES 0
#define SYNC_SERIES 1
#define EDIT_TPADS_SERIES 2
#define EDIT_SELECT_SERIES 3
#define PKT_INJECT_SERIES 4

#define CMD_PRESS   0
#define CMD_RELEASE 1
#define CMD_EDIT    2
#define CMD_ENABLE  3
#define CMD_DISABLE 4
#define CMD_RESET   5

// DEFINE VARIABLES

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

volatile uint8_t command;
volatile uint8_t controller;
volatile uint8_t value;
volatile uint8_t ctrl_bit;

uint8_t rec_cmd[3];

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

// SMARTPORT FUNCTIONS

void setup() {
  pinMode(MISO, OUTPUT);
  pinMode(MOSI, INPUT);
  pinMode(SCK, INPUT);
  pinMode(SLAVE_READY_PIN, OUTPUT);

  SPCR |= _BV(SPE);  // Enable SPI (Slave Mode)
  SPCR |= _BV(SPIE); // Enable SPI Interrupt
  SPDR = 0x00; // Zero Out SPI Register

  TCCR1A = 0;
  TCCR1B = 0;

  TCNT1 = 0;
  TCCR1B |= (1 << CS10);    // 64 prescaler 
  TCCR1B |= (1 << CS11);    // 64 prescaler
  TIMSK1 |= (1 << TOIE1);   // enable timer overflow interrupt

  Serial.begin(115200); 
}

void loop() {
  if (Serial.available() >= 3) {
    Serial.readBytes(rec_cmd, 3); // Read bytes
    receive_command(rec_cmd, 3); // Interpret command
  }
}

void receive_command(uint8_t *cmd, size_t len) {
  command = cmd[0];
  controller = cmd[1];
  value = cmd[2];
  ctrl_bit = (1 << controller);

  switch (command) {
    case CMD_PRESS:
      *button_map[value] |= ctrl_bit;
      priority_byte |= ctrl_bit;
      break;

    case CMD_RELEASE:
      *button_map[value] &= ~ctrl_bit;
      priority_byte |= ctrl_bit;
      break;

    case CMD_EDIT:
      *controller_map[controller] = value;
      break;

    case CMD_ENABLE:
      *control_map[controller] = 1;
      enabled_controllers &= ~controller_masks[controller];
      break;

    case CMD_DISABLE:
      *control_map[controller] = 0;
      enabled_controllers |= controller_masks[controller];
      break;
    
    case CMD_RESET:
      reset_smartport();
      break;
  }
}

volatile uint8_t rok_respond(uint8_t rec_byte) {
  switch (current_series) {

    case NO_SERIES:
      switch (rec_byte) {
        case PRESYNC:
          current_series = SYNC_SERIES;
          series_count = 1;
          send_byte = SLAVE_SYNC;
          break;

        case EDIT_TPADS:
          current_series = EDIT_TPADS_SERIES;
          series_count = 1;
          send_byte = VERIFY_EDIT;
          TCNT1 = 0; // Reset timer.
          break;

        case EDIT_SELECT:
          current_series = EDIT_SELECT_SERIES;
          series_count = 1;
          send_byte = VERIFY_EDIT;
          break;

        default:
          current_series = NO_SERIES;
          series_count = 0;
          send_byte = NULL_CMD;
          break;
      }
      break;

      
    case SYNC_SERIES:
      switch (series_count) {
        case 1:
          series_count = 2;
          send_byte = ENABLE_ATTRIB_BYTE;
          break;

        case 2:
          series_count = 3;
          send_byte = NO_SEL_TIMEOUT;
          break;
          
        default:
          current_series = NO_SERIES;
          series_count = 0;
          send_byte = NULL_CMD;
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
          priority_byte = NULL_CMD;
          break;

        default:
          current_series = NO_SERIES;
          series_count = 0;
          send_byte = NULL_CMD;
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
          send_byte = NULL_CMD;
          break;

        default:
          current_series = NO_SERIES;
          series_count = 0;
          send_byte = NULL_CMD;
          break;
      }
      break;


    default:
      current_series = NO_SERIES;
      series_count = 0;
      send_byte = NULL_CMD;
      break;
  }

  return send_byte;
}

void reset_smartport() {
  SPDR = 0x00;
  current_series = 0;
  series_count = 0;
  SPCR = 0;
  SPCR |= _BV(SPE);  // Enable SPI (Slave Mode)
  SPCR |= _BV(SPIE); // Enable SPI Interrupt
}

ISR (SPI_STC_vect) {
  digitalWrite(SLAVE_READY_PIN, HIGH); // NOT READY
  rec_byte = SPDR; // RECEIVE BYTE
  SPDR = rok_respond(rec_byte); // SEND BYTE
  digitalWrite(SLAVE_READY_PIN, LOW); // READY
}

ISR(TIMER1_OVF_vect) {
  reset_smartport();
}
