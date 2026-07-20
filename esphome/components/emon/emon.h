#pragma once

#include "esphome/core/component.h"
#include "esphome/components/sensor/sensor.h"

#ifdef USE_ESP32
#include <esp_adc/adc_continuous.h>
#include <esp_adc/adc_cali.h>
#endif

#define ADC_SAMPLE_RATE_HZ (20 * 1000)

#define BUF_LEN (DATA_INTERVAL_MS * ADC_SAMPLE_RATE_HZ / 1000)
#define READ_LEN (2048 * SOC_ADC_DIGI_DATA_BYTES_PER_CONV)

#define ADC_BIT_WIDTH SOC_ADC_DIGI_MAX_BITWIDTH

#if CONFIG_IDF_TARGET_ESP32 || CONFIG_IDF_TARGET_ESP32S2
#define ADC_OUTPUT_TYPE ADC_DIGI_OUTPUT_FORMAT_TYPE1
#define ADC_GET_DATA(p_data) ((p_data)->type1.data)
#define ADC_GET_CHANNEL(p_data) ((p_data)->type1.channel)
#define ADC_GET_UNIT(p_data) ADC_UNIT_1  // TODO: What happens when using ADC_UNIT_2 on ESP32-S2?
#else
#define ADC_OUTPUT_TYPE ADC_DIGI_OUTPUT_FORMAT_TYPE2
#define ADC_GET_DATA(p_data) ((p_data)->type2.data)
#define ADC_GET_CHANNEL(p_data) ((p_data)->type2.channel)
#define ADC_GET_UNIT(p_data) ((p_data)->type2.unit)
#endif

namespace esphome::emon {

struct EmonData {
  float v;
  float i;
  float p;
  float q;
  float s;
  float pf;
};

class Emon : public Component, public sensor::Sensor {
 public:
  float get_setup_priority() const override { return esphome::setup_priority::LATE; }
  float get_loop_priority() const override { return 10.0f; }

  void setup() override;
  void loop() override;
  void dump_config() override;

  void set_v(adc_unit_t unit, adc_channel_t channel, adc_atten_t attenuation, float cal) {
    this->v_adc_unit_ = unit;
    this->v_channel_ = channel;
    this->v_attenuation_ = attenuation;
    this->v_cal_ = cal;
  }
  void set_i(adc_unit_t unit, adc_channel_t channel, adc_atten_t attenuation, float cal) {
    this->i_adc_unit_ = unit;
    this->i_channel_ = channel;
    this->i_attenuation_ = attenuation;
    this->i_cal_ = cal;
  }

  void set_voltage_sensor(sensor::Sensor *voltage_sensor) { voltage_sensor_ = voltage_sensor; }
  void set_current_sensor(sensor::Sensor *current_sensor) { current_sensor_ = current_sensor; }
  void set_active_power_sensor(sensor::Sensor *active_power_sensor) { active_power_sensor_ = active_power_sensor; }
  void set_apparent_power_sensor(sensor::Sensor *apparent_power_sensor) {
    apparent_power_sensor_ = apparent_power_sensor;
  }
  void set_power_factor_sensor(sensor::Sensor *power_factor_sensor) { power_factor_sensor_ = power_factor_sensor; }

 protected:
  uint8_t adc_conv_[READ_LEN] = {0};
  adc_continuous_handle_t adc_handle_ = NULL;

  int16_t v_data_[BUF_LEN] = {0};
  int16_t i_data_[BUF_LEN] = {0};
  uint16_t v_offset_ = 1 << (ADC_BIT_WIDTH - 1);
  uint16_t i_offset_ = 1 << (ADC_BIT_WIDTH - 1);
  uint32_t v_idx_ = 0;
  uint32_t i_idx_ = 0;

  adc_unit_t v_adc_unit_;
  adc_unit_t i_adc_unit_;
  adc_channel_t v_channel_;
  adc_channel_t i_channel_;
  adc_atten_t v_attenuation_;
  adc_atten_t i_attenuation_;
  float v_cal_;
  float i_cal_;

  sensor::Sensor *voltage_sensor_{nullptr};
  sensor::Sensor *current_sensor_{nullptr};
  sensor::Sensor *active_power_sensor_{nullptr};
  sensor::Sensor *apparent_power_sensor_{nullptr};
  sensor::Sensor *power_factor_sensor_{nullptr};
};

}  // namespace esphome::emon
