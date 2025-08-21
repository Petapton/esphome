#include "setpoint_adapter.h"

namespace esphome {
namespace madoka {
namespace internal {

void SetpointAdapter::handleHighTemperature(float temp) {
  if (mode_ == SETPOINT_MODE_DUAL) {
    climate_->target_temperature_high = temp;
  } else {
    climate_->target_temperature = temp;
  }
}

void SetpointAdapter::handleLowTemperature(float temp) {
  if (mode_ == SETPOINT_MODE_DUAL) {
    climate_->target_temperature_low = temp;
  } else {
    climate_->target_temperature = temp;
  }
}

void SetpointAdapter::resetTemperatures() {
  climate_->current_temperature = NAN;
  climate_->target_temperature = NAN;
  climate_->target_temperature_high = NAN;
  climate_->target_temperature_low = NAN;
}

std::vector<uint8_t> SetpointAdapter::buildSetpointCommand(const climate::ClimateCall &call) {
  if (mode_ == SETPOINT_MODE_DUAL) {
    if (call.get_target_temperature_low().has_value() && call.get_target_temperature_high().has_value()) {
      uint16_t target_low = *call.get_target_temperature_low() * 128;
      uint16_t target_high = *call.get_target_temperature_high() * 128;
      return std::vector<uint8_t>{0x20, 0x02, (uint8_t) ((target_high >> 8) & 0xFF), (uint8_t) (target_high & 0xFF),
                                  0x21, 0x02, (uint8_t) ((target_low >> 8) & 0xFF),  (uint8_t) (target_low & 0xFF)};
    }
  } else {
    if (call.get_target_temperature().has_value()) {
      uint16_t target_temp = *call.get_target_temperature() * 128;
      return std::vector<uint8_t>{0x20, 0x02, (uint8_t) ((target_temp >> 8) & 0xFF), (uint8_t) (target_temp & 0xFF),
                                  0x21, 0x02, (uint8_t) ((target_temp >> 8) & 0xFF), (uint8_t) (target_temp & 0xFF)};
    }
  }
  return std::vector<uint8_t>{};
}

}  // namespace internal
}  // namespace madoka
}  // namespace esphome