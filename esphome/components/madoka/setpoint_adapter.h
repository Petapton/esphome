#pragma once

#include "esphome/components/climate/climate.h"

namespace esphome {
namespace madoka {

enum SetpointMode : uint8_t {
  SETPOINT_MODE_SINGLE = 0,
  SETPOINT_MODE_DUAL = 1,
};

namespace internal {

/**
 * @brief Adapts temperature setpoint behavior between single and dual modes.
 *
 * The SetpointAdapter handles the complexity of supporting both single-setpoint
 * and dual-setpoint temperature control modes in Madoka climate devices.
 *
 * Single Mode: Uses one target temperature for both heating and cooling operations.
 * The same temperature value is used as both heating and cooling setpoints in the
 * protocol, simplifying the user interface to a single temperature control.
 *
 * Dual Mode: Uses separate low (heating) and high (cooling) target temperatures.
 * This allows for more precise climate control with different heating and cooling
 * setpoints, enabling auto heat/cool mode operation.
 *
 * The adapter abstracts away the conditional logic and protocol differences,
 * providing a clean interface for temperature management regardless of mode.
 */
class SetpointAdapter {
 private:
  SetpointMode mode_;
  climate::Climate *climate_;

 public:
  /**
   * @brief Constructs a SetpointAdapter for the given climate component.
   * @param climate Pointer to the climate component to manage
   * @param mode Initial setpoint mode (single or dual)
   */
  SetpointAdapter(climate::Climate *climate, SetpointMode mode) : climate_(climate), mode_(mode) {}

  /**
   * @brief Changes the setpoint mode.
   * @param mode New setpoint mode to use
   */
  void setMode(SetpointMode mode) { mode_ = mode; }

  /**
   * @brief Handles incoming high temperature value from device.
   * In dual mode: Sets target_temperature_high
   * In single mode: Sets target_temperature
   * @param temp Temperature value received from device
   */
  void handleHighTemperature(float temp);

  /**
   * @brief Handles incoming low temperature value from device.
   * In dual mode: Sets target_temperature_low
   * In single mode: Sets target_temperature
   * @param temp Temperature value received from device
   */
  void handleLowTemperature(float temp);

  /**
   * @brief Resets all temperature values to NAN (disconnected state).
   */
  void resetTemperatures();

  /**
   * @brief Builds protocol command for setpoint changes.
   * In dual mode: Uses separate low/high values from ClimateCall
   * In single mode: Uses single temperature for both protocol fields
   * @param call Climate call containing new target temperatures
   * @return Protocol command bytes, or empty vector if no change needed
   */
  std::vector<uint8_t> buildSetpointCommand(const climate::ClimateCall &call);

  /**
   * @brief Checks if currently in dual setpoint mode.
   * @return true if dual mode, false if single mode
   */
  bool isDualMode() const { return mode_ == SETPOINT_MODE_DUAL; }
};

}  // namespace internal
}  // namespace madoka
}  // namespace esphome