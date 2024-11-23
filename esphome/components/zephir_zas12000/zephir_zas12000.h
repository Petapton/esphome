#pragma once

#include "esphome/components/climate_ir/climate_ir.h"

/***********************************************************************************
 * SOURCE
 ***********************************************************************************
 * This component is based on the ZephirZAS12000 component.
 * Timings are based on measurements taken from a Zephir ZAS12000 unit.
 *
 ***********************************************************************************/

namespace esphome {
namespace zephir_zas12000 {

/********************************************************************************
 *  TIMINGS
 *  Space:        Not used
 *  Header Mark:  8960 us
 *  Header Space: 4485 us
 *  Bit Mark:      625 us
 *  Zero Space:    685 us
 *  One Space:    1935 us
 *
 *******************************************************************************/
static const uint32_t AC1_HDR_MARK = 8960;
static const uint32_t AC1_HDR_SPACE = 4485;
static const uint32_t AC1_BIT_MARK = 625;
static const uint32_t AC1_ZERO_SPACE = 685;
static const uint32_t AC1_ONE_SPACE = 1935;

/********************************************************************************
 *
 * Zephir ZAS12000 codes
 *
 *******************************************************************************/

// Power
static const uint8_t AC1_POWER_OFF = 0x00;
static const uint8_t AC1_POWER_ON = 0x20;

// Operating Modes
static const uint8_t AC1_MODE_AUTO = 0x00;
static const uint8_t AC1_MODE_COOL = 0x20;
static const uint8_t AC1_MODE_DRY = 0x40;
static const uint8_t AC1_MODE_HEAT = 0x80;
static const uint8_t AC1_MODE_FAN = 0xC0;

// Fan control
static const uint8_t AC1_FAN_AUTO = 0xA0;
static const uint8_t AC1_FAN1 = 0x60;
static const uint8_t AC1_FAN2 = 0x40;
static const uint8_t AC1_FAN3 = 0x20;

// Vertical Swing
static const uint8_t AC1_VDIR_FIXED = 0x00;  // Fixed
static const uint8_t AC1_VDIR_SWING = 0x07;  // Swing

// Static bytes
static const uint8_t AC1_STATIC1 = 0xC3;
static const uint8_t AC1_STATIC2 = 0x20;
static const uint8_t AC1_STATIC3 = 0x12;
static const uint8_t AC1_STATIC4 = 0x20;

// Temperature range
static const float AC1_TEMP_MIN = 16.0f;
static const float AC1_TEMP_MAX = 30.0f;
static const float AC1_TEMP_INC = 1.0f;

class ZephirZAS12000Climate : public climate_ir::ClimateIR {
 public:
  ZephirZAS12000Climate()
      : climate_ir::ClimateIR(AC1_TEMP_MIN, AC1_TEMP_MAX, AC1_TEMP_INC, true, true,
                              {climate::CLIMATE_FAN_AUTO, climate::CLIMATE_FAN_LOW, climate::CLIMATE_FAN_MEDIUM,
                               climate::CLIMATE_FAN_HIGH},
                              {climate::CLIMATE_SWING_OFF, climate::CLIMATE_SWING_VERTICAL}) {}

  void setup() override { climate_ir::ClimateIR::setup(); }

 protected:
  /// Transmit via IR the state of this climate controller.
  void transmit_state() override;
  /// Handle received IR Buffer
  bool on_receive(remote_base::RemoteReceiveData data) override;
};

}  // namespace zephir_zas12000
}  // namespace esphome
