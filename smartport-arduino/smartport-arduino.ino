/* SMART PORT ARDUINO DEMO CODE
 * AUTHOR: STEPSTOOLS
 * DATE: 13 DEC 2025
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

// GPIO Pinout
#define SLAVE_READY_PIN 9

#define CMD_ENABLED_CONTROLLERS  0x01
#define CMD_SELECT               0x02
#define CMD_SP_BUTTON            0x03

// Smart Port Byte Codes Sent By Master
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

// Smart Port Byte Codes Sent By Slave
#define NULL_CMD 0x00
#define VERIFY_EDIT 0x80
#define SLAVE_SYNC 0x81
#define SLAVE_NO_INS 0x82
#define SLAVE_WAIT_INS 0x83
#define DISABLE_ATTRIB_BYTE 0x00       // Smart Port Control Disabled
#define ENABLE_ATTRIB_BYTE 0x0D        // Smart Port Control Enabled, Packet Injection Disabled
#define PACKET_INJECT_ATTRIB_BYTE 0x2D // Smart Port Control Enabled, Packet Injection Enabled
#define NO_SEL_TIMEOUT 0x00            // 1 = Controller Never Times Out, 0 = Normal V4|V3|V2|V1|P4|P3|P2|P1

// Series Logic Codes
#define NO_SERIES 0
#define SYNC_SERIES 1
#define EDIT_TPADS_SERIES 2
#define EDIT_SELECT_SERIES 3
#define PKT_INJECT_SERIES 4

//  __      __     _____  _____          ____  _      ______  _____   //
//  \ \    / /\   |  __ \|_   _|   /\   |  _ \| |    |  ____|/ ____|  //
//   \ \  / /  \  | |__) | | |    /  \  | |_) | |    | |__  | (___    //
//    \ \/ / /\ \ |  _  /  | |   / /\ \ |  _ <| |    |  __|  \___ \   //
//     \  / ____ \| | \ \ _| |_ / ____ \| |_) | |____| |____ ____) |  //
//      \/_/    \_\_|  \_\_____/_/    \_\____/|______|______|_____/   //

// Rokenbok Control Logic Variables
uint8_t timeouts[12] = {false, false, false, false, false, false, false, false, false, false, false, false};       // V1, V2, V3, V4, P1, P2, P3, P4, D1, D2, D3, D4
uint8_t enable_control[12] = {false, false, false, false, false, false, false, false, false, false, false, false}; // V1, V2, V3, V4, P1, P2, P3, P4, D1, D2, D3, D4 // FALSE = Normal, TRUE = SP Controlled
uint8_t control_keys[12] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};               // V1, V2, V3, V4, P1, P2, P3, P4, D1, D2, D3, D4
uint8_t next_control_key = 2;                                                                                      // 0 = Unused, 1 = Physical Controller Plugged In

uint8_t next_dpi_index = 0;

uint8_t selects[12] = {0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F}; // V1, V2, V3, V4, P1, P2, P3, P4, D1, D2, D3, D4

uint8_t share_mode = true;
uint8_t is16sel_mode = true;
uint8_t controller_timeout = 10;

uint8_t enabled_controllers = 0b11111111; // V4|V3|V2|V1|P4|P3|P2|P1 // 0 = Enabled, 1 = Disabled
uint8_t sp_a = 0x00;                      // V4|V3|V2|V1|P4|P3|P2|P1
uint8_t sp_b = 0x00;
uint8_t sp_x = 0x00;
uint8_t sp_y = 0x00;
uint8_t sp_up = 0x00;
uint8_t sp_down = 0x00;
uint8_t sp_right = 0x00;
uint8_t sp_left = 0x00;
uint8_t sp_rt = 0x00;
// uint8_t sp_sel_button = 0x00;
// uint8_t sp_lt = 0x00;
// uint8_t sp_share = 0x00;
// uint8_t sp_is16SEL = 0x00;
uint8_t sp_priority_byte = 0x00;

uint8_t dpi_a[4] = {false, false, false, false};
uint8_t dpi_b[4] = {false, false, false, false};
uint8_t dpi_x[4] = {false, false, false, false};
uint8_t dpi_y[4] = {false, false, false, false};
uint8_t dpi_up[4] = {false, false, false, false};
uint8_t dpi_down[4] = {false, false, false, false};
uint8_t dpi_left[4] = {false, false, false, false};
uint8_t dpi_right[4] = {false, false, false, false};
uint8_t dpi_rt[4] = {false, false, false, false};

uint8_t sp_status = 0;

uint8_t spi_current_series = 0;
uint8_t spi_series_count = 0;

//   _    _ ______ _      _____  ______ _____    //
//  | |  | |  ____| |    |  __ \|  ____|  __ \   //
//  | |__| | |__  | |    | |__) | |__  | |__) |  //
//  |  __  |  __| | |    |  ___/|  __| |  _  /   //
//  | |  | | |____| |____| |    | |____| | \ \   //
//  |_|  |_|______|______|_|    |______|_|  \_\  //

/// @brief Helper function to determine if an array contains a value.
/// @param array The array to be checked.
/// @param size The size of the array.
/// @param value The value being looked for.
/// @return true or false boolean value.
bool contains(uint8_t array[], size_t size, uint8_t value)
{
  for (size_t i = 0; i < size; i++)
  {
    if (array[i] == value)
    {
      return true;
    }
  }
  return false;
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
  Serial.begin(115200);

  // Configure Smart Port GPIO
  pinMode(MISO, OUTPUT);
  pinMode(MOSI, INPUT);
  pinMode(SCK, INPUT);
  pinMode(SLAVE_READY_PIN, OUTPUT);

  // Configure SPI Interface
  SPCR |= _BV(SPE);  // Enable SPI (Slave Mode)
  SPCR |= _BV(SPIE); // Enable SPI Interrupt
  SPDR = 0x00;       // Zero Out SPI Register

  // Configure Timer
  TCCR1A = 0;
  TCCR1B = 0;
  TCNT1 = 0;
  TCCR1B |= (1 << CS10);  // 64 Prescaler
  TCCR1B |= (1 << CS11);  // 64 Prescaler
  TIMSK1 |= (1 << TOIE1); // Enable Timer Overflow Interrupt

  // Ready For First Byte
  digitalWrite(SLAVE_READY_PIN, HIGH);

}

/// @brief Receive commands via serial
/// @return void
void loop(void)
{
  while (Serial.available() >= 2)
  {
    uint8_t cmd = Serial.read();

    switch (cmd)
    {
      case CMD_ENABLED_CONTROLLERS:
      {
        uint8_t value = Serial.read();
        enabled_controllers = value;
        break;
      }

      case CMD_SELECT:
      {
        // Needs 2 more bytes
        while (Serial.available() < 2);
        uint8_t index = Serial.read();  // 0–11
        uint8_t value = Serial.read();  // select value

        if (index < 12)
          selects[index] = value;
        break;
      }

      case CMD_SP_BUTTON:
      {
        // Wait for the 9 bytes to arrive
        while (Serial.available() < 9);
        
        // Read the 9 bytes in order
        sp_a     = Serial.read();
        sp_b     = Serial.read();
        sp_x     = Serial.read();
        sp_y     = Serial.read();
        sp_up    = Serial.read();
        sp_down  = Serial.read();
        sp_right = Serial.read();
        sp_left  = Serial.read();
        sp_rt    = Serial.read();
        break;
      }
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
  digitalWrite(SLAVE_READY_PIN, HIGH); // We are NOT ready for a new byte.

  uint8_t recv_byte = SPDR;
  uint8_t send_byte = 0x00;

  // Serial.println(rec_data, HEX);

  // NO SERIES
  if (spi_current_series == NO_SERIES)
  {
    if (recv_byte == PRESYNC)
    {
      spi_current_series = SYNC_SERIES;
      spi_series_count = 1;
      send_byte = SLAVE_SYNC;
    }
    else if (recv_byte == EDIT_TPADS)
    {
      spi_current_series = EDIT_TPADS_SERIES;
      spi_series_count = 1;
      send_byte = VERIFY_EDIT;

      // RESET SYNC TIMER
      // EDIT_TPADS byte will only be received with a good sync.
      TCNT1 = 0;
      sp_status = true;
    }
    else if (recv_byte == EDIT_SELECT)
    {
      spi_current_series = EDIT_SELECT_SERIES;
      spi_series_count = 1;
      send_byte = VERIFY_EDIT;
    }
    else if (recv_byte == MASTER_ASK_INS)
    {
      spi_current_series = PKT_INJECT_SERIES;
      spi_series_count = 1;

      // Generate First Half of DPI Packet (SEL3, SEL2, SEL1, SEL0, UP, DOWN, RIGHT, LEFT)
      uint8_t original_index = next_dpi_index;
      uint8_t valid_found = false;
      do
      {
        next_dpi_index = (next_dpi_index + 1) % 4;

        // A DPI should only be broadcast if it has a selection and isn't the same as another V/P/D controller selection.
        if (selects[next_dpi_index + 8] != 0x0F && !contains(selects, 8, selects[next_dpi_index + 8]))
        {
          valid_found = true;
          break; // Found the valid next index
        }

      } while (next_dpi_index != original_index); // Stop if we've wrapped around back to the original index

      if (valid_found)
      { // Only generate a send_byte if a valid controller was found
        send_byte = (selects[next_dpi_index + 8] + 1) << 4;
        if (dpi_up[next_dpi_index])
        {
          send_byte |= 0b00001000;
        }
        if (dpi_down[next_dpi_index])
        {
          send_byte |= 0b00000100;
        }
        if (dpi_right[next_dpi_index])
        {
          send_byte |= 0b00000010;
        }
        if (dpi_left[next_dpi_index])
        {
          send_byte |= 0b00000001;
        }
      }
      else
      {
        send_byte = 0b00000000; // Send NULL Upper Half
      }
    }
    else
    {
      spi_current_series = NO_SERIES;
      spi_series_count = 0;
      send_byte = NULL_CMD;
    }
  }

  // SYNC SERIES
  else if (spi_current_series == SYNC_SERIES)
  {
    if (spi_series_count == 1)
    {
      spi_series_count = 2;
      send_byte = ENABLE_ATTRIB_BYTE;
      for (uint8_t i = 8; i < 12; i++)
      { // Only enable DPI if needed.
        if (selects[i] != 0x0F)
        {
          send_byte = PACKET_INJECT_ATTRIB_BYTE;
          break;
        }
      }
    }
    else if (spi_series_count == 2)
    {
      spi_series_count = 3;
      send_byte = NO_SEL_TIMEOUT;
    }
    else if (spi_series_count == 3)
    {
      spi_current_series = NO_SERIES;
      spi_series_count = 0;
      send_byte = NULL_CMD;
    }
    else
    {
      spi_current_series = NO_SERIES;
      spi_series_count = 0;
      send_byte = NULL_CMD;
    }
  }

  // EDIT TPADS SERIES
  else if (spi_current_series == EDIT_TPADS_SERIES)
  {
    if (spi_series_count == 1)
    {
      spi_series_count = 2; // Select Button
      // spi_rec_tpads[0] = recv_byte;
      send_byte = recv_byte; //(recv_byte & enabled_controllers) | sp_sel_button;
    }
    else if (spi_series_count == 2)
    {
      spi_series_count = 3; // Left Trigger (Last Select)
      // spi_rec_tpads[1] = recv_byte;
      send_byte = recv_byte; //(recv_byte & enabled_controllers) | sp_lt;
    }
    else if (spi_series_count == 3)
    {
      spi_series_count = 4; // Sharing Mode (1 = Allow Sharing)
      // spi_rec_tpads[2] = recv_byte;
      if (share_mode)
      {
        send_byte = recv_byte | (~enabled_controllers); // Enable Sharing For Virtual Controllers
      }
      else
      {
        send_byte = recv_byte & enabled_controllers; // Disable Sharing For Virtual Controllers
      }
      // send_byte = recv_byte; //(recv_byte & enabled_controllers) | sp_share;
    }
    else if (spi_series_count == 4)
    {
      spi_series_count = 5; // RESERVED (0 when plugged in, 1 when not)
      // spi_rec_tpads[3] = recv_byte;
      send_byte = recv_byte;

      for (uint8_t i = 4; i < 8; i++)
      { // Check if P1-P4 are plugged in.
        uint8_t bitwise_index = (i + 4) % 8;
        if (!(recv_byte & (1 << bitwise_index)))
        { // If it is plugged in...
          if (control_keys[i] != 1)
          { // And it is not currently tracked as physical controlled...
            // Clear out virtual controller data and free for use.
            control_keys[i] = 1;
            selects[i] = 0x0F;
            sp_a &= ~(0b00000001 << bitwise_index);
            sp_b &= ~(0b00000001 << bitwise_index);
            sp_x &= ~(0b00000001 << bitwise_index);
            sp_y &= ~(0b00000001 << bitwise_index);
            sp_up &= ~(0b00000001 << bitwise_index);
            sp_down &= ~(0b00000001 << bitwise_index);
            sp_left &= ~(0b00000001 << bitwise_index);
            sp_right &= ~(0b00000001 << bitwise_index);
            sp_rt &= ~(0b00000001 << bitwise_index);
            sp_priority_byte |= (0b00000001 << bitwise_index);
            enable_control[i] = false;
            enabled_controllers |= (0b00000001 << bitwise_index); // THIS MAY BE BORKED????
          }
          timeouts[i] = true;
        }
        else
        { // If it is not plugged in...
          if (control_keys[i] == 1)
          { // And if it was being used...
            // Free it back up for use.
            control_keys[i] = 0;
            selects[i] = 0x0F;
            sp_a &= ~(0b00000001 << bitwise_index);
            sp_b &= ~(0b00000001 << bitwise_index);
            sp_x &= ~(0b00000001 << bitwise_index);
            sp_y &= ~(0b00000001 << bitwise_index);
            sp_up &= ~(0b00000001 << bitwise_index);
            sp_down &= ~(0b00000001 << bitwise_index);
            sp_left &= ~(0b00000001 << bitwise_index);
            sp_right &= ~(0b00000001 << bitwise_index);
            sp_rt &= ~(0b00000001 << bitwise_index);
            sp_priority_byte |= (0b00000001 << bitwise_index);
            timeouts[i] = false;
          }
        }
      }
    }
    else if (spi_series_count == 5)
    {
      spi_series_count = 6; // IS16SEL? (0 when plugged in, 1 when not)
      // spi_rec_tpads[4] = recv_byte;
      if (is16sel_mode)
      {
        send_byte = 0xFF; //(recv_byte & enabled_controllers) | sp_is16SEL;
      }
      else
      {
        send_byte = 0x00;
      }
    }
    else if (spi_series_count == 6)
    {
      spi_series_count = 7; // D Pad Up
      // spi_rec_tpads[5] = recv_byte;
      send_byte = (recv_byte & enabled_controllers) | sp_up;
    }
    else if (spi_series_count == 7)
    {
      spi_series_count = 8; // D Pad Down
      // spi_rec_tpads[6] = recv_byte;
      send_byte = (recv_byte & enabled_controllers) | sp_down;
    }
    else if (spi_series_count == 8)
    {
      spi_series_count = 9; // D Pad Right
      // spi_rec_tpads[7] = recv_byte;
      send_byte = (recv_byte & enabled_controllers) | sp_right;
    }
    else if (spi_series_count == 9)
    {
      spi_series_count = 10; // D Pad Left
      // spi_rec_tpads[8] = recv_byte;
      send_byte = (recv_byte & enabled_controllers) | sp_left;
    }
    else if (spi_series_count == 10)
    {
      spi_series_count = 11; // A
      // spi_rec_tpads[9] = recv_byte;
      send_byte = (recv_byte & enabled_controllers) | (~sp_rt & sp_a);
    }
    else if (spi_series_count == 11)
    {
      spi_series_count = 12; // B
      // spi_rec_tpads[10] = recv_byte;
      send_byte = (recv_byte & enabled_controllers) | (~sp_rt & sp_b);
    }
    else if (spi_series_count == 12)
    {
      spi_series_count = 13; // X
      // spi_rec_tpads[11] = recv_byte;
      send_byte = (recv_byte & enabled_controllers) | sp_x;
    }
    else if (spi_series_count == 13)
    {
      spi_series_count = 14; // Y
      // spi_rec_tpads[12] = recv_byte;
      send_byte = (recv_byte & enabled_controllers) | sp_y;
    }
    else if (spi_series_count == 14)
    {
      spi_series_count = 15; // RESERVED FOR A' (RT+A) (0 when plugged in, 1 when not)
      // spi_rec_tpads[13] = recv_byte;
      send_byte = (recv_byte & enabled_controllers) | (sp_rt & sp_a);
    }
    else if (spi_series_count == 15)
    {
      spi_series_count = 16; // RESERVED FOR B' (RT+B) (0 when plugged in, 1 when not)
      // spi_rec_tpads[14] = recv_byte;
      send_byte = (recv_byte & enabled_controllers) | (sp_rt & sp_b);
    }
    else if (spi_series_count == 16)
    {
      spi_series_count = 17; // Right Trigger (Slow)
      // spi_rec_tpads[15] = recv_byte;
      send_byte = (recv_byte & enabled_controllers) | sp_rt;
    }
    else if (spi_series_count == 17)
    {
      spi_series_count = 18; // Spare (0 regardless if plugged in or not)
      // spi_rec_tpads[16] = recv_byte;
      send_byte = 0x00; // recv_byte;
    }
    else if (spi_series_count == 18)
    {
      spi_series_count = 19; // Priority Byte
      // spi_rec_tpads[17] = recv_byte;
      send_byte = recv_byte | sp_priority_byte;
      sp_priority_byte = 0x00;
    }
    else if (spi_series_count == 19)
    {
      spi_current_series = NO_SERIES;
      spi_series_count = 0;
      send_byte = NULL_CMD;
    }
    else
    {
      spi_current_series = NO_SERIES;
      spi_series_count = 0;
      send_byte = NULL_CMD;
    }
  }

  // EDIT SELECT SERIES
  else if (spi_current_series == EDIT_SELECT_SERIES)
  {
    if (spi_series_count == 1)
    {
      spi_series_count = 2; // P1 Select
      // spi_rec_select[0] = recv_byte;
      if (enable_control[4])
      {
        send_byte = selects[4];
      }
      else
      {
        selects[4] = recv_byte;
        send_byte = recv_byte;
      }
    }
    else if (spi_series_count == 2)
    {
      spi_series_count = 3; // P2 Select
      // spi_rec_select[1] = recv_byte;
      if (enable_control[5])
      {
        send_byte = selects[5];
      }
      else
      {
        selects[5] = recv_byte;
        send_byte = recv_byte;
      }
    }
    else if (spi_series_count == 3)
    {
      spi_series_count = 4; // P3 Select
      // spi_rec_select[2] = recv_byte;
      if (enable_control[6])
      {
        send_byte = selects[6];
      }
      else
      {
        selects[6] = recv_byte;
        send_byte = recv_byte;
      }
    }
    else if (spi_series_count == 4)
    {
      spi_series_count = 5; // P4 Select
      // spi_rec_select[3] = recv_byte;
      if (enable_control[7])
      {
        send_byte = selects[7];
      }
      else
      {
        selects[7] = recv_byte;
        send_byte = recv_byte;
      }
    }
    else if (spi_series_count == 5)
    {
      spi_series_count = 6; // V1 Select
      // spi_rec_select[4] = recv_byte;
      send_byte = selects[0];
    }
    else if (spi_series_count == 6)
    {
      spi_series_count = 7; // V2 Select
      // spi_rec_select[5] = recv_byte;
      send_byte = selects[1];
    }
    else if (spi_series_count == 7)
    {
      spi_series_count = 8; // V3 Select
      // spi_rec_select[6] = recv_byte;
      send_byte = selects[2];
    }
    else if (spi_series_count == 8)
    {
      spi_series_count = 9; // V4 Select
      // spi_rec_select[7] = recv_byte;
      send_byte = selects[3];
    }
    else if (spi_series_count == 9)
    {
      spi_series_count = 10; // Timer Value (Counts Up From 0-15 and Repeats)
      send_byte = recv_byte;
    }
    else if (spi_series_count == 10)
    {
      spi_current_series = NO_SERIES;
      spi_series_count = 0;
      send_byte = SLAVE_WAIT_INS; // Ready to Insert Packet
    }
    else
    {
      spi_current_series = NO_SERIES;
      spi_series_count = 0;
      send_byte = NULL_CMD;
    }
  }

  // PKT INJECT SERIES
  else if (spi_current_series == PKT_INJECT_SERIES)
  {
    if (spi_series_count == 1)
    {
      spi_current_series = NO_SERIES;
      spi_series_count = 0;

      // Generate First Half of DPI Packet (A, B, X, Y, A', B', RT, ?)
      send_byte = 0b00000000;

      if (dpi_a[next_dpi_index])
      {
        send_byte |= 0b10000000;
      }
      if (dpi_b[next_dpi_index])
      {
        send_byte |= 0b01000000;
      }
      if (dpi_x[next_dpi_index])
      {
        send_byte |= 0b00100000;
      }
      if (dpi_y[next_dpi_index])
      {
        send_byte |= 0b00010000;
      }
      if (dpi_rt[next_dpi_index])
      {
        send_byte |= 0b00000010;
      }
    }
  }
  // CATCH ALL
  else
  {
    spi_current_series = NO_SERIES;
    spi_series_count = 0;
    send_byte = NULL_CMD;
  }

  SPDR = send_byte;

  digitalWrite(SLAVE_READY_PIN, LOW); // We are ready for a new byte.
}

/// @brief ISR triggers if Smart Port sync is lost and resets variables.
/// @param TIMER1_OVF_vect Timer 1 Overflow Vector
/// @return N/A
ISR(TIMER1_OVF_vect)
{
  if (sp_status == 1)
  {
    sp_status = 0;

    for (int i = 0; i < 12; i++)
    {
      selects[i] = 0x0F;
      enable_control[i] = false;
    }

    enabled_controllers = 0b11111111;
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

    spi_current_series = 0;
    spi_series_count = 0;
  }
}
