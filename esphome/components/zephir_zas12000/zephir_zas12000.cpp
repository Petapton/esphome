#include "zephir_zas12000.h"
#include "esphome/core/log.h"

namespace esphome {
namespace zephir_zas12000 {

static const char *const TAG = "zephir_zas12000.climate";

void ZephirZAS12000Climate::transmit_state() {
  uint8_t ir_message[13] = {0};

  // Static bytes
  ir_message[0] = AC1_STATIC1;
  ir_message[2] = AC1_STATIC2;
  ir_message[3] = AC1_STATIC3;
  ir_message[10] = AC1_STATIC4;

  // Byte 1 : Temperature | Swing
  // -- Temperature
  ir_message[1] = (uint8_t) (this->target_temperature - 8.0f) << 3;

  // -- Swing
  switch (this->swing_mode) {
    case climate::CLIMATE_SWING_OFF:
      ir_message[1] |= AC1_VDIR_FIXED;
      break;
    case climate::CLIMATE_SWING_VERTICAL:
      ir_message[1] |= AC1_VDIR_SWING;
      break;
  }

  // Byte 4 : Fan speed
  switch (this->fan_mode.value()) {
    case climate::CLIMATE_FAN_LOW:
      ir_message[4] = AC1_FAN3;
      break;
    case climate::CLIMATE_FAN_MEDIUM:
      ir_message[4] = AC1_FAN2;
      break;
    case climate::CLIMATE_FAN_HIGH:
      ir_message[4] = AC1_FAN1;
      break;
    case climate::CLIMATE_FAN_AUTO:
      ir_message[4] = AC1_FAN_AUTO;
      break;
  }

  // Byte 6 : AC Mode
  switch (this->mode) {
    case climate::CLIMATE_MODE_AUTO:
    case climate::CLIMATE_MODE_HEAT_COOL:
      ir_message[6] = AC1_MODE_AUTO;
      break;
    case climate::CLIMATE_MODE_COOL:
      ir_message[6] = AC1_MODE_COOL;
      break;
    case climate::CLIMATE_MODE_HEAT:
      ir_message[6] = AC1_MODE_HEAT;
      break;
    case climate::CLIMATE_MODE_DRY:
      ir_message[6] = AC1_MODE_DRY;
      break;
    case climate::CLIMATE_MODE_FAN_ONLY:
      ir_message[6] = AC1_MODE_FAN;
      break;
    default:
      break;
  }

  // Byte 9 : Power
  if (this->mode == climate::CLIMATE_MODE_OFF) {
    ir_message[9] = AC1_POWER_OFF;
  } else {
    ir_message[9] = AC1_POWER_ON;
  }

  // Byte 11 : Last pressed button
  ir_message[11] = 0x05;  // fixed as power button

  // Set checksum byte
  for (int i = 0; i < 12; i++) {
    ir_message[12] += ir_message[i];
  }
  // ir_message[12] &= 0x7F;

  // Send the code
  auto transmit = this->transmitter_->transmit();
  auto *data = transmit.get_data();

  data->set_carrier_frequency(38000);  // 38 kHz PWM

  // Header
  data->mark(AC1_HDR_MARK);
  data->space(AC1_HDR_SPACE);

  // Data
  for (uint8_t i : ir_message) {
    for (uint8_t j = 0; j < 8; j++) {
      data->mark(AC1_BIT_MARK);
      bool bit = i & (1 << j);
      data->space(bit ? AC1_ONE_SPACE : AC1_ZERO_SPACE);
    }
  }

  // Footer
  data->mark(AC1_BIT_MARK);
  data->space(0);

  transmit.perform();
}

bool ZephirZAS12000Climate::on_receive(remote_base::RemoteReceiveData data) {
  // Validate header
  if (!data.expect_item(AC1_HDR_MARK, AC1_HDR_SPACE)) {
    ESP_LOGV(TAG, "Header fail");
    return false;
  }

  // Decode IR message
  uint8_t ir_message[13] = {0};
  // Read all bytes
  for (int i = 0; i < 13; i++) {
    // Read bit
    for (int j = 0; j < 8; j++) {
      if (data.expect_item(AC1_BIT_MARK, AC1_ONE_SPACE)) {
        ir_message[i] |= 1 << j;
      } else if (!data.expect_item(AC1_BIT_MARK, AC1_ZERO_SPACE)) {
        ESP_LOGV(TAG, "Byte %d bit %d fail", i, j);
        return false;
      }
    }
    ESP_LOGVV(TAG, "Byte %d %02X", i, ir_message[i]);
  }

  // Validate footer
  if (!data.expect_mark(AC1_BIT_MARK)) {
    ESP_LOGV(TAG, "Footer fail");
    return false;
  }

  // Validate checksum
  for (int i = 0; i < 12; i++) {
    ir_message[12] -= ir_message[i];
  }
  // ir_message[12] &= 0x7F;
  if (ir_message[12] != 0) {
    ESP_LOGV(TAG, "Checksum fail");
    return false;
  }

  // Validate static bytes
  if (ir_message[0] != AC1_STATIC1 || ir_message[2] != AC1_STATIC2 || ir_message[3] != AC1_STATIC3 ||
      ir_message[10] != AC1_STATIC4) {
    ESP_LOGV(TAG, "Static bytes fail");
    return false;
  }

  // All is good to go

  if (ir_message[9] != AC1_POWER_ON) {
    this->mode = climate::CLIMATE_MODE_OFF;
  } else {
    // Taregt Temperature
    this->target_temperature = (ir_message[1] >> 3) + 8.0f;

    // Swing mode
    switch (ir_message[1] & 0x07) {
      case AC1_VDIR_FIXED:
        this->swing_mode = climate::CLIMATE_SWING_OFF;
        break;
      case AC1_VDIR_SWING:
        this->swing_mode = climate::CLIMATE_SWING_VERTICAL;
        break;
      default:
        break;
    }

    // Fan speed
    switch (ir_message[4]) {
      case AC1_FAN_AUTO:
        this->fan_mode = climate::CLIMATE_FAN_AUTO;
        break;
      case AC1_FAN1:
        this->fan_mode = climate::CLIMATE_FAN_HIGH;
        break;
      case AC1_FAN2:
        this->fan_mode = climate::CLIMATE_FAN_MEDIUM;
        break;
      case AC1_FAN3:
        this->fan_mode = climate::CLIMATE_FAN_LOW;
        break;
      default:
        break;
    }

    // AC Mode
    switch (ir_message[6]) {
      case AC1_MODE_AUTO:
        this->mode = climate::CLIMATE_MODE_HEAT_COOL;
        break;
      case AC1_MODE_COOL:
        this->mode = climate::CLIMATE_MODE_COOL;
        break;
      case AC1_MODE_HEAT:
        this->mode = climate::CLIMATE_MODE_HEAT;
        break;
      case AC1_MODE_DRY:
        this->mode = climate::CLIMATE_MODE_DRY;
        break;
      case AC1_MODE_FAN:
        this->mode = climate::CLIMATE_MODE_FAN_ONLY;
        break;
      default:
        break;
    }
  }

  this->publish_state();
  return true;
}

}  // namespace zephir_zas12000
}  // namespace esphome
