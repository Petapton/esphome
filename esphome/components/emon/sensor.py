import esphome.codegen as cg
from esphome.components import sensor
from esphome.components.adc import (
    ATTENUATION_MODES,
    ESP32_VARIANT_ADC1_PIN_TO_CHANNEL,
    ESP32_VARIANT_ADC2_PIN_TO_CHANNEL,
    adc_unit_t,
    validate_adc_pin,
)
from esphome.components.esp32 import get_esp32_variant
from esphome.components.esp32.const import (
    VARIANT_ESP32,
    VARIANT_ESP32C2,
    VARIANT_ESP32C3,
    VARIANT_ESP32C5,
    VARIANT_ESP32C6,
    VARIANT_ESP32C61,
    VARIANT_ESP32H2,
    VARIANT_ESP32P4,
    VARIANT_ESP32S2,
    VARIANT_ESP32S3,
)
import esphome.config_validation as cv
from esphome.const import (
    CONF_ACTIVE_POWER,
    CONF_APPARENT_POWER,
    CONF_ATTENUATION,
    CONF_CURRENT,
    CONF_ID,
    CONF_NUMBER,
    CONF_PIN,
    CONF_POWER_FACTOR,
    CONF_VOLTAGE,
    DEVICE_CLASS_APPARENT_POWER,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_POWER_FACTOR,
    DEVICE_CLASS_VOLTAGE,
    STATE_CLASS_MEASUREMENT,
    UNIT_AMPERE,
    UNIT_VOLT,
    UNIT_VOLT_AMPS,
    UNIT_WATT,
)
from esphome.core import TimePeriod

# ADC2 continuous (DMA) mode support per variant.
# True = supported, False = not supported.
# Source: ADC_LL_DIG_SUPPORTED_UNIT in esp-idf/components/esp_hal_ana_conv/{chip}/include/hal/adc_ll.h
# Unknown variants default to False (safe: ADC1-only).
_ADC2_CONTINUOUS_STATUS = {
    VARIANT_ESP32: False,  # HAL forces ADC_LL_DIGI_CONV_ONLY_ADC1 regardless of conv_mode
    VARIANT_ESP32S2: True,  # ADC_LL_DIG_SUPPORTED_UNIT(UNIT) = 1 for both units
    VARIANT_ESP32S3: False,  # hardware errata; driver rejects ADC2 unless CONFIG_ADC_CONTINUOUS_FORCE_USE_ADC2_ON_C3_S3
    VARIANT_ESP32C2: False,  # SOC_ADC_PERIPH_NUM=1, no ADC2 hardware
    VARIANT_ESP32C3: False,  # hardware errata; same Kconfig escape hatch as S3
    VARIANT_ESP32C5: False,  # SOC_ADC_PERIPH_NUM=1, no ADC2 hardware
    VARIANT_ESP32C6: False,  # SOC_ADC_PERIPH_NUM=1, no ADC2 hardware
    VARIANT_ESP32C61: False,  # SOC_ADC_PERIPH_NUM=1, no ADC2 hardware
    VARIANT_ESP32H2: False,  # SOC_ADC_PERIPH_NUM=1, no ADC2 hardware
    VARIANT_ESP32P4: True,  # ADC_LL_DIG_SUPPORTED_UNIT(UNIT) = 1 for both units
}
# TYPE1 output format (2 bytes, no unit bit): both pins must be on the same ADC unit
_TYPE1_VARIANTS = {VARIANT_ESP32, VARIANT_ESP32S2}

adc_digi_convert_mode_t = cg.global_ns.enum("adc_digi_convert_mode_t")


def _resolve_pin_unit(variant, pin_num, input_key):
    """Return (adc_unit, adc_channel) for a pin, or raise cv.Invalid."""
    adc1_pins = ESP32_VARIANT_ADC1_PIN_TO_CHANNEL.get(variant, {})
    adc2_pins = ESP32_VARIANT_ADC2_PIN_TO_CHANNEL.get(variant, {})

    if pin_num in adc1_pins:
        return 1, adc1_pins[pin_num]
    if pin_num in adc2_pins:
        if not _ADC2_CONTINUOUS_STATUS.get(variant, False):
            raise cv.Invalid(
                f"Pin {pin_num} is on ADC2, which does not support continuous mode "
                f"on {variant}. Use an ADC1 pin instead",
                path=[input_key, CONF_PIN],
            )
        return 2, adc2_pins[pin_num]
    raise cv.Invalid(
        f"Pin {pin_num} is not a valid ADC pin for {variant}",
        path=[input_key, CONF_PIN],
    )


def final_validate_config(config):
    variant = get_esp32_variant()

    v_pin = config[CONF_V_INPUT][CONF_PIN][CONF_NUMBER]
    i_pin = config[CONF_I_INPUT][CONF_PIN][CONF_NUMBER]

    v_unit, _ = _resolve_pin_unit(variant, v_pin, CONF_V_INPUT)
    i_unit, _ = _resolve_pin_unit(variant, i_pin, CONF_I_INPUT)

    if v_unit != i_unit and variant in _TYPE1_VARIANTS:
        raise cv.Invalid(
            f"V pin {v_pin} (ADC{v_unit}) and I pin {i_pin} (ADC{i_unit}) are on "
            f"different units. {variant} uses TYPE1 output format which cannot "
            f"distinguish units in the DMA data. Both pins must be on the same "
            f"ADC unit",
        )

    return config


emon_ns = cg.esphome_ns.namespace("emon")
Emon = emon_ns.class_("Emon", cg.Component)

CONF_CAL = "cal"

channel_schema = cv.Schema(
    {
        cv.Required(CONF_PIN): validate_adc_pin,
        cv.SplitDefault(CONF_ATTENUATION, esp32="0db"): cv.enum(
            ATTENUATION_MODES, lower=True
        ),
        cv.Optional(CONF_CAL, default=1.0): cv.Coerce(float),
    },
)

CONF_V_INPUT = "v_input"
CONF_I_INPUT = "i_input"

CONF_DATA_INTERVAL = "data_interval"

CONFIG_SCHEMA = cv.All(
    cv.only_on_esp32,
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(Emon),
            cv.Required(CONF_V_INPUT): channel_schema,
            cv.Required(CONF_I_INPUT): channel_schema,
            cv.Optional(
                CONF_DATA_INTERVAL, default=TimePeriod(milliseconds=200)
            ): cv.positive_not_null_time_period,
            cv.Optional(CONF_VOLTAGE): sensor.sensor_schema(
                unit_of_measurement=UNIT_VOLT,
                accuracy_decimals=2,
                device_class=DEVICE_CLASS_VOLTAGE,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_CURRENT): sensor.sensor_schema(
                unit_of_measurement=UNIT_AMPERE,
                accuracy_decimals=3,
                device_class=DEVICE_CLASS_CURRENT,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_ACTIVE_POWER): sensor.sensor_schema(
                unit_of_measurement=UNIT_WATT,
                accuracy_decimals=2,
                device_class=DEVICE_CLASS_POWER,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_APPARENT_POWER): sensor.sensor_schema(
                unit_of_measurement=UNIT_VOLT_AMPS,
                accuracy_decimals=2,
                device_class=DEVICE_CLASS_APPARENT_POWER,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_POWER_FACTOR): sensor.sensor_schema(
                accuracy_decimals=2,
                device_class=DEVICE_CLASS_POWER_FACTOR,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
        }
    ).extend(cv.COMPONENT_SCHEMA),
)

FINAL_VALIDATE_SCHEMA = final_validate_config


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    cg.add_define("DATA_INTERVAL_MS", config[CONF_DATA_INTERVAL].total_milliseconds)

    # if config[CONF_PIN] == "VCC":
    #     cg.add_define("USE_ADC_SENSOR_VCC")
    # elif config[CONF_PIN] == "TEMPERATURE":
    #     cg.add(var.set_is_temperature())
    # else:
    #     pin = await cg.gpio_pin_expression(config[CONF_PIN])
    #     cg.add(var.set_pin(pin))

    # cg.add(var.set_output_raw(config[CONF_RAW]))

    # if attenuation := config.get(CONF_ATTENUATION):
    #     if attenuation == "auto":
    #         cg.add(var.set_autorange(cg.global_ns.true))
    #     else:
    #         cg.add(var.set_attenuation(attenuation))

    variant = get_esp32_variant()
    adc1_pins = ESP32_VARIANT_ADC1_PIN_TO_CHANNEL.get(variant, {})
    adc2_pins = ESP32_VARIANT_ADC2_PIN_TO_CHANNEL.get(variant, {})

    units_used = set()
    for dim, set_dim in [(CONF_V_INPUT, var.set_v), (CONF_I_INPUT, var.set_i)]:
        pin_num = config[dim][CONF_PIN][CONF_NUMBER]
        if pin_num in adc1_pins:
            unit = adc_unit_t.ADC_UNIT_1
            chan = adc1_pins[pin_num]
            units_used.add(1)
        else:
            unit = adc_unit_t.ADC_UNIT_2
            chan = adc2_pins[pin_num]
            units_used.add(2)
        cg.add(
            set_dim(
                unit,
                chan,
                config[dim].get(CONF_ATTENUATION),
                config[dim].get(CONF_CAL),
            )
        )

    if units_used == {1, 2}:
        conv_mode = adc_digi_convert_mode_t.ADC_CONV_BOTH_UNIT
    elif 2 in units_used:
        conv_mode = adc_digi_convert_mode_t.ADC_CONV_SINGLE_UNIT_2
    else:
        conv_mode = adc_digi_convert_mode_t.ADC_CONV_SINGLE_UNIT_1
    cg.add(var.set_conv_mode(conv_mode))

    for dim in [
        CONF_VOLTAGE,
        CONF_CURRENT,
        CONF_ACTIVE_POWER,
        CONF_APPARENT_POWER,
        CONF_POWER_FACTOR,
    ]:
        if dim in config:
            sens = await sensor.new_sensor(config[dim])
            cg.add(getattr(var, f"set_{dim}_sensor")(sens))
