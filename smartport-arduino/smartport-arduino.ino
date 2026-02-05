/* SMART PORT ARDUINO DEMO CODE
 * AUTHOR: STEPSTOOLS
 * DATE: 4 FEB 2026
 * ROKENBOK DISCORD: https://discord.gg/pmbbAsq
 */

//   _____ _   _  _____ _     _    _ _____  ______  _____   //
//  |_   _| \ | |/ ____| |   | |  | |  __ \|  ____|/ ____|  //
//    | | |  \| | |    | |   | |  | | |  | | |__  | (___    //
//    | | | . ` | |    | |   | |  | | |  | |  __|  \___ \   //
//   _| |_| |\  | |____| |___| |__| | |__| | |____ ____) |  //
//  |_____|_| \_|\_____|______\____/|_____/|______|_____/   //

#include <Arduino.h>

//   _____  ______ ______ _____ _   _ ______  _____   //
//  |  __ \|  ____|  ____|_   _| \ | |  ____|/ ____|  //
//  | |  | | |__  | |__    | | |  \| | |__  | (___    //
//  | |  | |  __| |  __|   | | | . ` |  __|  \___ \   //
//  | |__| | |____| |     _| |_| |\  | |____ ____) |  //
//  |_____/|______|_|    |_____|_| \_|______|_____/   //

// Fast Write Functions (Cross Platform)
#define SLAVE_READY_PIN 8

#if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__) // Uno, Nano, Pro Mini (Pin 8 = Port B, Bit 0)
#define SET_SLAVE_NOT_READY() (PORTB |= (1 << 0))
#define SET_SLAVE_READY() (PORTB &= ~(1 << 0))
#elif defined(__AVR_ATmega2560__) || defined(__AVR_ATmega1280__) // Mega 2560 (Pin 8 = Port H, Bit 5)
#define SET_SLAVE_NOT_READY() (PORTH |= (1 << 5))
#define SET_SLAVE_READY() (PORTH &= ~(1 << 5))
#elif defined(__AVR_ATmega32U4__) // Leonardo / Micro (Pin 8 = Port B, Bit 4)
#define SET_SLAVE_NOT_READY() (PORTB |= (1 << 4))
#define SET_SLAVE_READY() (PORTB &= ~(1 << 4))
#else // Fallback for unknown boards (Slower, but compatible)
#define SET_SLAVE_NOT_READY() digitalWrite(SLAVE_READY_PIN, HIGH)
#define SET_SLAVE_READY() digitalWrite(SLAVE_READY_PIN, LOW)
#endif

#define EMULATED_SS_PIN 9

#if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__) // Uno, Nano, Pro Mini (Pin 9 = Port B, Bit 1)
#define SET_SS_HIGH() (PORTB |= (1 << 1))
#define SET_SS_LOW() (PORTB &= ~(1 << 1))
#elif defined(__AVR_ATmega2560__) || defined(__AVR_ATmega1280__) // Mega 2560 (Pin 9 = Port H, Bit 6)
#define SET_SS_HIGH() (PORTH |= (1 << 6))
#define SET_SS_LOW() (PORTH &= ~(1 << 6))
#elif defined(__AVR_ATmega32U4__) // Leonardo / Micro (Pin 9 = Port B, Bit 5)
#define SET_SS_HIGH() (PORTB |= (1 << 5))
#define SET_SS_LOW() (PORTB &= ~(1 << 5))
#else // Fallback for unknown boards (Using Pin 9)
#define SET_SS_HIGH() digitalWrite(EMULATED_SS_PIN, HIGH)
#define SET_SS_LOW() digitalWrite(EMULATED_SS_PIN, LOW)
#endif

// Smart Port Byte Codes Sent By Master and Slave
#define NULL_CMD 0x00

// Smart Port Byte Codes Sent By Master
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

// Smart Port Byte Codes Sent By Slave
#define VERIFY_EDIT 0x80
#define SLAVE_SYNC 0x81
#define SLAVE_NO_INS 0x82
#define SLAVE_WANT_INS 0x83
#define DISABLE_ATTRIB_BYTE 0x00       // Smart Port Control Disabled
#define ENABLE_ATTRIB_BYTE 0x0D        // Smart Port Control Enabled, Packet Injection Disabled
#define PACKET_INJECT_ATTRIB_BYTE 0x2D // Smart Port Control Enabled, Packet Injection Enabled
#define NO_SEL_TIMEOUT 0x00            // 1 = Controller Never Times Out, 0 = Normal V4|V3|V2|V1|P4|P3|P2|P1

// ISR State Machine Values
enum SeriesState : uint8_t
{
  STATE_IDLE = 0,

  STATE_SYNC_1,
  STATE_SYNC_2,
  STATE_SYNC_3,

  STATE_EDIT_TPADS_1,
  STATE_EDIT_TPADS_2,
  STATE_EDIT_TPADS_3,
  STATE_EDIT_TPADS_4,
  STATE_EDIT_TPADS_5,
  STATE_EDIT_TPADS_6,
  STATE_EDIT_TPADS_7,
  STATE_EDIT_TPADS_8,
  STATE_EDIT_TPADS_9,
  STATE_EDIT_TPADS_10,
  STATE_EDIT_TPADS_11,
  STATE_EDIT_TPADS_12,
  STATE_EDIT_TPADS_13,
  STATE_EDIT_TPADS_14,
  STATE_EDIT_TPADS_15,
  STATE_EDIT_TPADS_16,
  STATE_EDIT_TPADS_17,
  STATE_EDIT_TPADS_18,
  STATE_EDIT_TPADS_19,

  STATE_EDIT_SELECT_1,
  STATE_EDIT_SELECT_2,
  STATE_EDIT_SELECT_3,
  STATE_EDIT_SELECT_4,
  STATE_EDIT_SELECT_5,
  STATE_EDIT_SELECT_6,
  STATE_EDIT_SELECT_7,
  STATE_EDIT_SELECT_8,
  STATE_EDIT_SELECT_9,
  STATE_EDIT_SELECT_10,

  STATE_PKT_INJECT_1,
  STATE_PKT_INJECT_2,
  STATE_PKT_INJECT_3,
  STATE_PKT_INJECT_4,
  STATE_PKT_INJECT_5
};

//  __      __     _____  _____          ____  _      ______  _____   //
//  \ \    / /\   |  __ \|_   _|   /\   |  _ \| |    |  ____|/ ____|  //
//   \ \  / /  \  | |__) | | |    /  \  | |_) | |    | |__  | (___    //
//    \ \/ / /\ \ |  _  /  | |   / /\ \ |  _ <| |    |  __|  \___ \   //
//     \  / ____ \| | \ \ _| |_ / ____ \| |_) | |____| |____ ____) |  //
//      \/_/    \_\_|  \_\_____/_/    \_\____/|______|______|_____/   //

// Rokenbok Control Logic Variables
volatile uint8_t sp_status = false;

uint8_t share_mode = false;
uint8_t is16sel_mode = true;

volatile uint8_t user_ids[12] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}; // V1, V2, V3, V4, P1, P2, P3, P4, D1, D2, D3, D4, 0 = Unused, 1 = Physical Controller Plugged In
volatile uint8_t selects[12] = {0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F};  // V1, V2, V3, V4, P1, P2, P3, P4, D1, D2, D3, D4

volatile uint8_t controller_enable[12] = {false, false, false, false, false, false, false, false, false, false, false, false}; // V1, V2, V3, V4, P1, P2, P3, P4, D1, D2, D3, D4 // FALSE = Normal, TRUE = SP Controlled
volatile uint8_t controller_enable_bitmask = 0b11111111;                                                                       // V4|V3|V2|V1|P4|P3|P2|P1 // 0 = Enabled, 1 = Disabled
volatile uint8_t sp_a = 0x00;                                                                                                  // V4|V3|V2|V1|P4|P3|P2|P1
volatile uint8_t sp_b = 0x00;
volatile uint8_t sp_x = 0x00;
volatile uint8_t sp_y = 0x00;
volatile uint8_t sp_up = 0x00;
volatile uint8_t sp_down = 0x00;
volatile uint8_t sp_right = 0x00;
volatile uint8_t sp_left = 0x00;
volatile uint8_t sp_rt = 0x00;
volatile uint8_t sp_priority_byte = 0x00;

volatile uint8_t next_dpi_index = 0;
uint8_t dpi_upper[4] = {0x00, 0x00, 0x00, 0x00};
uint8_t dpi_lower[4] = {0x00, 0x00, 0x00, 0x00};

// SPI Loop Tracking Bytes
volatile SeriesState spi_fsm_state = STATE_IDLE;

// Array for Received Serial Bytes
uint8_t serial_rx_bytes[128];
uint8_t serial_rx_index = 0;

//   _    _ ______ _      _____  ______ _____    //
//  | |  | |  ____| |    |  __ \|  ____|  __ \   //
//  | |__| | |__  | |    | |__) | |__  | |__) |  //
//  |  __  |  __| | |    |  ___/|  __| |  _  /   //
//  | |  | | |____| |____| |    | |____| | \ \   //
//  |_|  |_|______|______|_|    |______|_|  \_\  //

/// @brief Clear all Smart Port buttons for a specific controller.
/// @param bit_number The bit number of the controller to clear (V4|V3|V2|V1|P4|P3|P2|P1).
/// @return void
static inline void clear_sp_bits(uint8_t bit_number)
{
  uint8_t clear_mask = ~(0b00000001 << bit_number);
  sp_a &= clear_mask;
  sp_b &= clear_mask;
  sp_x &= clear_mask;
  sp_y &= clear_mask;
  sp_up &= clear_mask;
  sp_down &= clear_mask;
  sp_left &= clear_mask;
  sp_right &= clear_mask;
  sp_rt &= clear_mask;
  sp_priority_byte |= (0b00000001 << bit_number);
  return;
}

/// @brief Evaluates if a bit for a contoller button has changed and updates it if necessary.
/// @param sp_byte Pointer to the Smart Port button variable to be updated.
/// @param sp_bit The bit number in the Smart Port button variable to be updated (V4|V3|V2|V1|P4|P3|P2|P1).
/// @param serial_byte The inbound serial byte to process.
/// @param serial_bit The bit number in the inbound serial byte to process.
/// @param priority_byte Pointer to the Smart Port "priority" byte to be updated.
/// @return void
static inline void process_button_bit(volatile uint8_t *sp_byte, uint8_t sp_bit, uint8_t serial_byte, uint8_t serial_bit, volatile uint8_t *priority_byte)
{
  uint8_t serial_bit_val = (serial_byte >> serial_bit) & 1;
  uint8_t sp_bit_val = (*sp_byte >> sp_bit) & 1;
  uint8_t changed = serial_bit_val ^ sp_bit_val;

  if (changed)
  {
    *sp_byte ^= (1 << sp_bit);
    *priority_byte |= (1 << sp_bit);
  }
}

/// @brief Process data in completed serial_rx_bytes[].
/// @return void
static inline void serial_process_rx_data()
{
  if (serial_rx_bytes[0] == 253) // Process Config Bytes
  {
    share_mode = serial_rx_bytes[1] ? 1 : 0;
    is16sel_mode = serial_rx_bytes[2] ? 1 : 0;
  }
  else if (serial_rx_bytes[0] == 254) // Process Player Bytes
  {
    // First check if any players previously assigned to a controller no longer need one and release those.
    for (uint8_t controller_index = 0; controller_index < 12; controller_index++) // Search for user ID In virtual, physical, and DPI controllers.
    {
      if (user_ids[controller_index] < 2) // If controller is currently unused or plugged in physical controller.
      {
        continue; // Skip to the next controller_index.
      }
      else // The controller is in use by a user ID.
      {
        for (uint8_t byte_count = 1; byte_count < 128; byte_count = byte_count + 4) // Iterate through the serial_rx_bytes.
        // serial_rx_bytes[byte_count] = Player ID // 0 = Unused // 1 = Plugged In Physical Controller // 2-252 = Valid User ID // 253 = Start Config Data // 254 = Start User Data // 255 = End Data
        // serial_rx_bytes[byte_count+1] = Vehicle Selection // 0-7 (With 16 Selection Disabled) or 0-14 (With 16 Selection Enabled) // 15 = No Select
        // serial_rx_bytes[byte_count+2] = First Buttons // Bits (MSB-LSB) = BLANK/BLANK/BLANK/BLANK/UP/DOWN/RIGHT/LEFT
        // serial_rx_bytes[byte_count+3] = Second Buttons // Bits (MSB-LSB) = BLANK/BLANK/BLANK/A/B/X/Y/RT
        {
          if (serial_rx_bytes[byte_count] == 255) // Reached end of serial data and user ID not found, release this controller.
          {
            user_ids[controller_index] = 0;
            selects[controller_index] = 15;
            if (controller_index < 8) // Virtual or Physical Controllers
            {
              uint8_t bitwise_index = (controller_index + 4) & 7; // uint8_t bitwise_index = (controller_index + 4) % 8; // Convert V1-4, P1-4 Array Index to V4|V3|V2|V1|P4|P3|P2|P1 Bitwise

              clear_sp_bits(bitwise_index);
            }
            else if (controller_index < 12) // Direct Packet Injection Controllers
            {
              uint8_t dpi_index = controller_index - 8;
              dpi_upper[dpi_index] = 0x00;
              dpi_lower[dpi_index] = 0x00;
            }
            TCCR2B |= (1 << CS22) | (1 << CS21); // Run the post-release timer (needed to let values propagate before disabling control).
            break;                               // Exit the byte_count for loop after releasing that user ID.
          }
          else if (serial_rx_bytes[byte_count] == user_ids[controller_index]) // User ID found...
          {
            break; // Exit the byte_count for loop without releasing that user ID.
          }
        }
      }
    }

    // Process All User IDs Sent in Data Stream, One at a Time
    for (uint8_t byte_count = 1; byte_count < 252; byte_count = byte_count + 4)
    // serial_rx_bytes[byte_count] = Player ID // 0 = Unused // 1 = Plugged In Physical Controller // 2-252 = Valid User ID // 253 = Start Config Data // 254 = Start User Data // 255 = End Data
    // serial_rx_bytes[byte_count+1] = Vehicle Selection // 0-7 (With 16 Selection Disabled) or 0-14 (With 16 Selection Enabled) // 15 = No Select
    // serial_rx_bytes[byte_count+2] = First Buttons // Bits (MSB-LSB) = BLANK/BLANK/BLANK/BLANK/UP/DOWN/RIGHT/LEFT
    // serial_rx_bytes[byte_count+3] = Second Buttons // Bits (MSB-LSB) = BLANK/BLANK/BLANK/A/B/X/Y/RT
    {
      if (serial_rx_bytes[byte_count] == 255) // End data byte detected.
      {
        return; // Return from the rocess_serial_bytes() function.
      }
      else // End not yet reached, process the next 4 bytes.
      {
        uint8_t controller_index = 255;                             // Variable to hold the controller index of the current player ID's controller, once found or assigned.
        for (uint8_t controller = 0; controller < 12; controller++) // Search for user ID In virtual, physical, and DPI controllers.
        {
          if (user_ids[controller] == serial_rx_bytes[byte_count]) // User ID Found
          {
            controller_index = controller;
            break; // Break from the controller for loop.
          }
        }

        if (controller_index == 255) // User ID Not Found Because controller_index Still = 255
        {
          for (uint8_t controller = 0; controller < 12; controller++) // Search for unused virtual, physical, or DPI controllers.
          {
            if (user_ids[controller] == 0) // Found Unused Controller
            {
              // Assign That Controller to the User ID
              controller_index = controller;
              user_ids[controller] = serial_rx_bytes[byte_count];
              controller_enable[controller] = true;
              if (controller_index < 8) // Only Do This Step For Virtual and Physical Controllers
              {
                controller_enable_bitmask &= ~(0b00000001 << ((controller + 4) & 7)); // controller_enable_bitmask &= ~(0b00000001 << ((controller + 4) % 8));
              }
              break; // Break from the controller for loop.
            }
          }
        }

        if (controller_index == 255) // No Unused Controllers Available Because controller_index Still = 255
        {
          continue; // Skip the rest of this iteration of the byte_count for loop (select and button logic skipped).
        }

        uint8_t b1 = serial_rx_bytes[byte_count + 1];
        uint8_t b2 = serial_rx_bytes[byte_count + 2];
        uint8_t b3 = serial_rx_bytes[byte_count + 3];

        if (controller_index < 8) // User ID Assigned to Virtual or Physical Controller
        {
          selects[controller_index] = b1; // Assign the desired selection. Share logic will be handled by PC.

          uint8_t bitwise_index = (controller_index + 4) & 7; // uint8_t bitwise_index = (controller_index + 4) % 8; // Convert V1-4, P1-4 Array Index to V4|V3|V2|V1|P4|P3|P2|P1 Bitwise

          process_button_bit(&sp_left, bitwise_index, b2, 0, &sp_priority_byte);
          process_button_bit(&sp_right, bitwise_index, b2, 1, &sp_priority_byte);
          process_button_bit(&sp_down, bitwise_index, b2, 2, &sp_priority_byte);
          process_button_bit(&sp_up, bitwise_index, b2, 3, &sp_priority_byte);

          process_button_bit(&sp_rt, bitwise_index, b3, 0, &sp_priority_byte);
          process_button_bit(&sp_y, bitwise_index, b3, 1, &sp_priority_byte);
          process_button_bit(&sp_x, bitwise_index, b3, 2, &sp_priority_byte);
          process_button_bit(&sp_b, bitwise_index, b3, 3, &sp_priority_byte);
          process_button_bit(&sp_a, bitwise_index, b3, 4, &sp_priority_byte);
        }

        else if (controller_index < 12) // User ID Assigned to DPI Controller
        {
          selects[controller_index] = b1; // Assign the desired selection. Share logic will be handled by PC.

          uint8_t dpi_index = controller_index - 8;

          // Generate First Half of DPI Packet (SEL3, SEL2, SEL1, SEL0, UP, DOWN, RIGHT, LEFT)
          dpi_upper[dpi_index] = ((b1 + 1) << 4) | (b2 & 0x0F);

          // Generate Second Half of DPI Packet (A, B, X, Y, A', B', RT, ?)
          uint8_t lower = 0x00;
          if (b3 & 0x04)
            lower |= 0b00100000; // X
          if (b3 & 0x02)
            lower |= 0b00010000; // Y
          if (b3 & 0x01)
            lower |= 0b00000010; // RT

          uint8_t ab_bits = (b3 & 0b00011000); // Isolate A and B
          if (b3 & 0x01)
          {
            lower |= (ab_bits >> 1); // RT is PRESSED: Map A/B to A'/B' slots
          }
          else
          {
            lower |= (ab_bits << 3); // RT is NOT PRESSED: Map A/B to A/B slots
          }
          dpi_lower[dpi_index] = lower;
        }
      }
    }
  }
  return;
}

/// @brief Send current sp_status, user_ids[], and selects[] over serial.
/// @return void
static inline void serial_tx_status()
{
  Serial.write(254); // Initiate with 254
  Serial.write(sp_status);
  for (uint8_t i = 0; i < 12; i++)
  {
    Serial.write(user_ids[i]);
  }
  for (uint8_t i = 0; i < 12; i++)
  {
    Serial.write(selects[i]);
  }
  Serial.write(255); // Terminate with 255
}

//    _____ ______ _______ _    _ _____        __   _      ____   ____  _____    //
//   / ____|  ____|__   __| |  | |  __ \      / /  | |    / __ \ / __ \|  __ \   //
//  | (___ | |__     | |  | |  | | |__) |    / /   | |   | |  | | |  | | |__) |  //
//   \___ \|  __|    | |  | |  | |  ___/    / /    | |   | |  | | |  | |  ___/   //
//   ____) | |____   | |  | |__| | |       / /     | |___| |__| | |__| | |       //
//  |_____/|______|  |_|   \____/|_|      /_/      |______\____/ \____/|_|       //

/// @brief Setup runs once to configure GPIO, SPI, and timer.
/// @return void
void setup(void)
{
  Serial.begin(1000000);

  // Configure Smart Port GPIO
  pinMode(SLAVE_READY_PIN, OUTPUT);
  pinMode(MISO, OUTPUT);
  pinMode(MOSI, INPUT);
  pinMode(SCK, INPUT);
  pinMode(SS, INPUT);
  pinMode(EMULATED_SS_PIN, OUTPUT);
  SET_SS_LOW();

  // Configure SPI Interface
  SPCR = _BV(SPE) | _BV(SPIE); // Enable SPI (Slave Mode) and Enable SPI Interrupt
  SPDR = 0x00;                 // Zero Out SPI Register

  // Configure Timer 1
  TCNT1 = 0;
  TCCR1A = 0;
  TCCR1B = (1 << CS12);   // 256 Prescaler
  TIMSK1 |= (1 << TOIE1); // Enable Timer Overflow Interrupt

  // Configure Timer 2
  TCNT2 = 0;
  TCCR2A = (1 << WGM21);   // Set CTC mode (clear timer on compare match)
  TCCR2B = 0;              // Stop Timer
  OCR2A = 156;             // Compare match register for 0.1 seconds (for 16 MHz clock, prescaler 1024)
  TIMSK2 |= (1 << OCIE2A); // Enable Timer 2 compare interrupt

  // Enable Global Interrupts
  sei();

  // Ready For First Byte
  SET_SLAVE_READY();
}

/// @brief Serial processing in loop().
/// @return void
void loop(void)
{
  if (Serial.available() > 0)
  {
    uint8_t serial_read_byte = Serial.read();

    if (serial_read_byte == 253) // Start Config Bytes
    {
      serial_rx_bytes[0] = 253;
      serial_rx_index = 1;
    }
    else if (serial_read_byte == 254) // Start Player Bytes
    {
      serial_rx_bytes[0] = 254;
      serial_rx_index = 1;
    }
    else if (serial_read_byte == 255) // End Bytes
    {
      serial_rx_bytes[serial_rx_index] = 255;
      serial_process_rx_data();
      serial_tx_status();
    }
    else if (serial_rx_index < 127)
    {
      serial_rx_bytes[serial_rx_index++] = serial_read_byte;
    }
  }
}

//   _____  _____ _____        //
//  |_   _|/ ____|  __ \       //
//    | | | (___ | |__) |___   //
//    | |  \___ \|  _  // __|  //
//   _| |_ ____) | | \ \\__ \  //
//  |_____|_____/|_|  \_\___/  //

/// @brief ISR triggers when SPI byte is received and handles Smart Port logic.
/// @param TIMER1_OVF_vect SPI Serial Transfer Complete Vector
/// @return N/A
ISR(SPI_STC_vect)
{
  SET_SLAVE_NOT_READY();
  SET_SS_HIGH();

  uint8_t recv_byte = SPDR;
  uint8_t send_byte = 0x00;

  // STATE MACHINE IDLE STATE
  switch (spi_fsm_state)
  {
  case STATE_IDLE:
    switch (recv_byte)
    {
    case PRESYNC: // Receive: PRESYNC // Send: SLAVE_SYNC
    {
      spi_fsm_state = STATE_SYNC_1;
      send_byte = SLAVE_SYNC;
      break;
    }
    case EDIT_TPADS: // Receive: EDIT_TPADS // Send: VERIFY_EDIT
    {
      spi_fsm_state = STATE_EDIT_TPADS_1;
      send_byte = VERIFY_EDIT;

      TCNT1 = 0; // RESET SYNC TIMER because EDIT_TPADS byte will only be received with a good sync.
      sp_status = true;
      break;
    }
    case EDIT_SELECT: // Receive: EDIT_SELECT // Send: VERIFY_EDIT
    {
      spi_fsm_state = STATE_EDIT_SELECT_1;
      send_byte = VERIFY_EDIT;
      break;
    }
    case MASTER_ASK_INS: // Receive: MASTER_ASK_INS // Send: First Half of DPI Packet (SEL3, SEL2, SEL1, SEL0, UP, DOWN, RIGHT, LEFT)
    {
      spi_fsm_state = STATE_PKT_INJECT_1;
      uint16_t active_selects_mask = 0x00;
      for (uint8_t i = 0; i < 8; i++)
      {
        if (selects[i] < 0x0F)
        {
          active_selects_mask |= (1 << selects[i]);
        }
      }

      uint8_t original_index = next_dpi_index;
      send_byte = 0b00000000; // Default to NULL Upper Half
      do
      {
        next_dpi_index = (next_dpi_index + 1) & 3; // next_dpi_index = (next_dpi_index + 1) % 4;
        uint16_t dpi_select_mask = 1 << selects[next_dpi_index + 8];
        if (!(active_selects_mask & dpi_select_mask)) // Look for DPI controller that won't overwrite a V/P controller's selection.
        {
          send_byte = dpi_upper[next_dpi_index];
          break; // Found the valid next index, break from do-while.
        }
      } while (next_dpi_index != original_index); // Stop if we've wrapped around back to the original index.
      break;
    }
    default:
    {
      spi_fsm_state = STATE_IDLE;
      send_byte = NULL_CMD;
      break;
    }
    }
    break;

  // STATE MACHINE SYNC STATES
  case STATE_SYNC_1: // Receive: MASTER_SYNC // Send: Attribute Byte
    spi_fsm_state = STATE_SYNC_2;
    send_byte = ENABLE_ATTRIB_BYTE;
    for (uint8_t i = 8; i < 12; i++)
    { // Only enable DPI if needed.
      if (selects[i] != 0x0F)
      {
        send_byte = PACKET_INJECT_ATTRIB_BYTE;
        break;
      }
    }
    break;

  case STATE_SYNC_2: // Receive: READ_ATTRIB // Send: No Timeout Settings
    spi_fsm_state = STATE_SYNC_3;
    send_byte = NO_SEL_TIMEOUT;
    break;

  case STATE_SYNC_3: // Receive: READ_NO_SEL_TIMEOUT // Send: NULL_CMD
    spi_fsm_state = STATE_IDLE;
    send_byte = NULL_CMD;
    break;

  // STATE MACHINE EDIT TPADS STATES
  case STATE_EDIT_TPADS_1: // Receive: Select // Send: Select
    spi_fsm_state = STATE_EDIT_TPADS_2;
    send_byte = recv_byte; // Don't modify received byte.
    break;

  case STATE_EDIT_TPADS_2: // Receive: Left Trigger // Send: Left Trigger (Last Select)
    spi_fsm_state = STATE_EDIT_TPADS_3;
    send_byte = recv_byte; // Don't modify received byte.
    break;

  case STATE_EDIT_TPADS_3: // Receive: Sharing Mode // Send: Sharing Mode (0 = No Sharing, 1 = Allow Sharing)
    spi_fsm_state = STATE_EDIT_TPADS_4;
    if (share_mode)
    {
      send_byte = recv_byte | (~controller_enable_bitmask); // Enable Sharing For Actively Used Physical and Virtual Controllers
    }
    else
    {
      send_byte = recv_byte & controller_enable_bitmask; // Disable Sharing For Actively Used Physical and Virtual Controllers
    }
    break;

  case STATE_EDIT_TPADS_4: // Receive: RESERVED // Send: RESERVED (0 when plugged in, 1 when not)
    spi_fsm_state = STATE_EDIT_TPADS_5;
    send_byte = recv_byte;

    for (uint8_t i = 4; i < 8; i++)
    {                                          // Check if P1-P4 are plugged in.
      uint8_t bitwise_index = (i + 4) & 7;     // uint8_t bitwise_index = (i + 4) % 8;
      if (!(recv_byte & (1 << bitwise_index))) // If it is plugged in...
      {
        if (user_ids[i] != 1) // And it is not currently tracked as physical controlled...
        {
          // Clear out virtual controller data and free for use.
          user_ids[i] = 1;
          selects[i] = 0x0F;

          clear_sp_bits(bitwise_index);

          controller_enable[i] = false;
          controller_enable_bitmask |= (0b00000001 << bitwise_index); // May Be Broken

          // TCCR2B |= (1 << CS22) | (1 << CS21); // Run the post-release timer.
        }
      }
      else // If it is not plugged in...
      {
        if (user_ids[i] == 1) // And if it was being used...
        {
          // Free it back up for use.
          user_ids[i] = 0;
          selects[i] = 0x0F;

          clear_sp_bits(bitwise_index);

          TCCR2B |= (1 << CS22) | (1 << CS21); // Run the post-release timer.
        }
      }
    }
    break;

  case STATE_EDIT_TPADS_5: // Receive: IS16SEL // Send: IS16SEL (0 = 8 Selections, 1 = 16 Selections) (0 when plugged in, 1 when not)
    spi_fsm_state = STATE_EDIT_TPADS_6;
    if (is16sel_mode)
    {
      send_byte = 0xFF;
    }
    else
    {
      send_byte = 0x00;
    }
    break;

  case STATE_EDIT_TPADS_6: // Receive: D Pad Up // Send: D Pad Up
    spi_fsm_state = STATE_EDIT_TPADS_7;
    send_byte = (recv_byte & controller_enable_bitmask) | sp_up;
    break;

  case STATE_EDIT_TPADS_7: // Receive: D Pad Down // Send: D Pad Down
    spi_fsm_state = STATE_EDIT_TPADS_8;
    send_byte = (recv_byte & controller_enable_bitmask) | sp_down;
    break;

  case STATE_EDIT_TPADS_8: // Receive: D Pad Right // Send: D Pad Right
    spi_fsm_state = STATE_EDIT_TPADS_9;
    send_byte = (recv_byte & controller_enable_bitmask) | sp_right;
    break;

  case STATE_EDIT_TPADS_9: // Receive: D Pad Left // Send: D Pad Left
    spi_fsm_state = STATE_EDIT_TPADS_10;
    send_byte = (recv_byte & controller_enable_bitmask) | sp_left;
    break;

  case STATE_EDIT_TPADS_10: // Receive: A Button // Send: A Button
    spi_fsm_state = STATE_EDIT_TPADS_11;
    send_byte = (recv_byte & controller_enable_bitmask) | (~sp_rt & sp_a);
    break;

  case STATE_EDIT_TPADS_11: // Receive: B Button // Send: B Button
    spi_fsm_state = STATE_EDIT_TPADS_12;
    send_byte = (recv_byte & controller_enable_bitmask) | (~sp_rt & sp_b);
    break;

  case STATE_EDIT_TPADS_12: // Receive: X Button // Send: X Button
    spi_fsm_state = STATE_EDIT_TPADS_13;
    send_byte = (recv_byte & controller_enable_bitmask) | sp_x;
    break;

  case STATE_EDIT_TPADS_13: // Receive: Y Button // Send: Y Button
    spi_fsm_state = STATE_EDIT_TPADS_14;
    send_byte = (recv_byte & controller_enable_bitmask) | sp_y;
    break;

  case STATE_EDIT_TPADS_14: // Receive: RESERVED (A' / RT+A) // Send: RESERVED (A' / RT+A) (0 when plugged in, 1 when not)
    spi_fsm_state = STATE_EDIT_TPADS_15;
    send_byte = (recv_byte & controller_enable_bitmask) | (sp_rt & sp_a);
    break;

  case STATE_EDIT_TPADS_15: // Receive: RESERVED (B' / RT+B) // Send: RESERVED (B' / RT+B) (0 when plugged in, 1 when not)
    spi_fsm_state = STATE_EDIT_TPADS_16;
    send_byte = (recv_byte & controller_enable_bitmask) | (sp_rt & sp_b);
    break;

  case STATE_EDIT_TPADS_16: // Receive: Right Trigger // Send: Right Trigger (Slow)
    spi_fsm_state = STATE_EDIT_TPADS_17;
    send_byte = (recv_byte & controller_enable_bitmask) | sp_rt;
    break;

  case STATE_EDIT_TPADS_17: // Receive: SPARE // Send: SPARE (0 regardless if plugged in or not)
    spi_fsm_state = STATE_EDIT_TPADS_18;
    send_byte = 0x00;
    break;

  case STATE_EDIT_TPADS_18: // Receive: Priority Byte // Send: Priority Byte
    spi_fsm_state = STATE_EDIT_TPADS_19;
    send_byte = recv_byte | sp_priority_byte; // Flag bits modified by Smart Port logic.
    sp_priority_byte = 0x00;                  // Reset the priority byte.
    break;

  case STATE_EDIT_TPADS_19: // Receive: EDIT_END // Send: NULL_CMD
    spi_fsm_state = STATE_IDLE;
    send_byte = NULL_CMD;
    break;

  // STATE MACHIE EDIT SELECT STATES
  case STATE_EDIT_SELECT_1: // Receive: P1 Select // Send: P1 Select
    spi_fsm_state = STATE_EDIT_SELECT_2;
    if (controller_enable[4])
    {
      send_byte = selects[4];
    }
    else
    {
      selects[4] = recv_byte;
      send_byte = recv_byte;
    }
    break;

  case STATE_EDIT_SELECT_2: // Receive: P2 Select // Send: P2 Select
    spi_fsm_state = STATE_EDIT_SELECT_3;
    if (controller_enable[5])
    {
      send_byte = selects[5];
    }
    else
    {
      selects[5] = recv_byte;
      send_byte = recv_byte;
    }
    break;

  case STATE_EDIT_SELECT_3: // Receive: P3 Select // Send: P3 Select
    spi_fsm_state = STATE_EDIT_SELECT_4;
    if (controller_enable[6])
    {
      send_byte = selects[6];
    }
    else
    {
      selects[6] = recv_byte;
      send_byte = recv_byte;
    }
    break;

  case STATE_EDIT_SELECT_4: // Receive: P4 Select // Send: P4 Select
    spi_fsm_state = STATE_EDIT_SELECT_5;
    if (controller_enable[7])
    {
      send_byte = selects[7];
    }
    else
    {
      selects[7] = recv_byte;
      send_byte = recv_byte;
    }
    break;

  case STATE_EDIT_SELECT_5: // Receive: V1 Select // Send: V1 Select
    spi_fsm_state = STATE_EDIT_SELECT_6;
    send_byte = selects[0];
    break;

  case STATE_EDIT_SELECT_6: // Receive: V2 Select // Send: V2 Select
    spi_fsm_state = STATE_EDIT_SELECT_7;
    send_byte = selects[1];
    break;

  case STATE_EDIT_SELECT_7: // Receive: V3 Select // Send: V3 Select
    spi_fsm_state = STATE_EDIT_SELECT_8;
    send_byte = selects[2];
    break;

  case STATE_EDIT_SELECT_8: // Receive: V4 Select // Send: V4 Select
    spi_fsm_state = STATE_EDIT_SELECT_9;
    send_byte = selects[3];
    break;

  case STATE_EDIT_SELECT_9: // Receive: Timer Value // Send: Doesn't Matter (Echo or 0x00 is Okay)
    spi_fsm_state = STATE_EDIT_SELECT_10;
    send_byte = recv_byte;
    break;

  case STATE_EDIT_SELECT_10: // Receive: EDIT_END // Send: SLAVE_WANT_INS
    spi_fsm_state = STATE_IDLE;
    send_byte = SLAVE_WANT_INS; // Ready to Insert Packet // TODO: I think you could send a NULL_CMD here.
    break;

  // STATE MACHINE PKT INJECT STATE
  case STATE_PKT_INJECT_1: // Receive: READ_REPLY // Send: Second Half of DPI Packet (A, B, X, Y, A', B', RT, ?)
    spi_fsm_state = STATE_PKT_INJECT_2;
    send_byte = dpi_lower[next_dpi_index];
    break;

  case STATE_PKT_INJECT_2: // Receive: READ_REPLY // Send: NULL
    spi_fsm_state = STATE_PKT_INJECT_3;
    send_byte = NULL_CMD;
    break;

  case STATE_PKT_INJECT_3: // Receive: HAVE_RADIO_PKT // Send: NULL
    spi_fsm_state = STATE_PKT_INJECT_4;
    send_byte = NULL_CMD;
    break;

  case STATE_PKT_INJECT_4: // Receive: Readback of First Half of DPI Packet // Send: NULL
    spi_fsm_state = STATE_PKT_INJECT_5;
    send_byte = NULL_CMD;
    break;

  case STATE_PKT_INJECT_5: // Receive: Readback of Second Half of DPI Packet // Send: NULL
    spi_fsm_state = STATE_IDLE;
    send_byte = NULL_CMD;
    break;

  // CATCH ALL
  default:
    spi_fsm_state = STATE_IDLE;
    send_byte = NULL_CMD;
    break;
  }

  SPDR = send_byte;
  SET_SLAVE_READY();
  SET_SS_LOW();
}

/// @brief ISR triggers if Smart Port sync is lost and resets variables.
/// @param TIMER1_OVF_vect Timer 1 Overflow Vector
/// @return N/A
ISR(TIMER1_OVF_vect)
{
  if (sp_status)
  {
    // Most of this data will be overwritten during the next call of serial_process_rx_data(), but we reset everything out for safety.
    sp_status = false;
    spi_fsm_state = STATE_IDLE;

    for (uint8_t i = 0; i < 12; i++)
    {
      controller_enable[i] = false;
      selects[i] = 0x0F;
      user_ids[i] = 0;
    }

    controller_enable_bitmask = 0b11111111;
    sp_a = 0x00;
    sp_b = 0x00;
    sp_x = 0x00;
    sp_y = 0x00;
    sp_up = 0x00;
    sp_down = 0x00;
    sp_right = 0x00;
    sp_left = 0x00;
    sp_rt = 0x00;
    sp_priority_byte = 0x00;

    for (uint8_t i = 0; i < 4; i++)
    {
      dpi_upper[i] = 0x00;
      dpi_lower[i] = 0x00;
    }

    SPDR = 0x00;

    SET_SS_HIGH();
    delay(100);
    SET_SS_LOW();

    SET_SLAVE_READY();
  }
}

/// @brief ISR triggers 0.1 seconds after a controller was released to do some cleanup.
/// @param TIMER2_COMPA_vect Timer 1 Compare Vector
/// @return N/A
ISR(TIMER2_COMPA_vect)
{
  TCCR2B = 0;                      // Stop Timer 2
  for (uint8_t i = 0; i < 12; i++) // Search through all 12 controllers for unused controllers and ensure they are disabled.
  {
    if (user_ids[i] == 0)
    {
      controller_enable[i] = false;
      if (i < 8) // Only For Virtual and Physical Controllers
      {
        controller_enable_bitmask |= (0b00000001 << ((i + 4) & 7)); // controller_enable_bitmask |= (0b00000001 << ((i + 4) % 8));
      }
    }
  }
}