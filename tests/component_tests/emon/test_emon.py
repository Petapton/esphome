"""Tests for emon component configuration validation."""

import pytest

from esphome.components.emon.sensor import (
    CONF_I_INPUT,
    CONF_V_INPUT,
    _resolve_pin_unit,
    final_validate_config,
)
from esphome.components.esp32.const import (
    KEY_VARIANT,
    VARIANT_ESP32,
    VARIANT_ESP32C3,
    VARIANT_ESP32P4,
    VARIANT_ESP32S2,
    VARIANT_ESP32S3,
)
import esphome.config_validation as cv
from esphome.const import CONF_NUMBER, CONF_PIN, PlatformFramework
from tests.component_tests.types import SetCoreConfigCallable


def _make_config(v_pin: int, i_pin: int) -> dict:
    return {
        CONF_V_INPUT: {CONF_PIN: {CONF_NUMBER: v_pin}},
        CONF_I_INPUT: {CONF_PIN: {CONF_NUMBER: i_pin}},
    }


class TestResolvePinUnit:
    @pytest.mark.parametrize(
        ("variant", "pin", "expected_unit"),
        [
            pytest.param(VARIANT_ESP32, 36, 1, id="esp32_adc1_gpio36"),
            pytest.param(VARIANT_ESP32, 39, 1, id="esp32_adc1_gpio39"),
            pytest.param(VARIANT_ESP32S2, 1, 1, id="esp32s2_adc1_gpio1"),
            pytest.param(VARIANT_ESP32S3, 1, 1, id="esp32s3_adc1_gpio1"),
            pytest.param(VARIANT_ESP32C3, 0, 1, id="esp32c3_adc1_gpio0"),
            pytest.param(VARIANT_ESP32P4, 16, 1, id="esp32p4_adc1_gpio16"),
        ],
    )
    def test_adc1_pins_resolve(self, variant, pin, expected_unit):
        unit, _ = _resolve_pin_unit(variant, pin, CONF_V_INPUT)
        assert unit == expected_unit

    @pytest.mark.parametrize(
        ("variant", "pin"),
        [
            pytest.param(VARIANT_ESP32S2, 11, id="esp32s2_adc2_gpio11"),
            pytest.param(VARIANT_ESP32S2, 20, id="esp32s2_adc2_gpio20"),
            pytest.param(VARIANT_ESP32P4, 49, id="esp32p4_adc2_gpio49"),
            pytest.param(VARIANT_ESP32P4, 54, id="esp32p4_adc2_gpio54"),
        ],
    )
    def test_adc2_pins_resolve_on_supported_variants(self, variant, pin):
        unit, _ = _resolve_pin_unit(variant, pin, CONF_V_INPUT)
        assert unit == 2

    @pytest.mark.parametrize(
        ("variant", "pin"),
        [
            pytest.param(VARIANT_ESP32, 4, id="esp32_adc2_gpio4"),
            pytest.param(VARIANT_ESP32, 25, id="esp32_adc2_gpio25"),
            pytest.param(VARIANT_ESP32C3, 5, id="esp32c3_adc2_gpio5"),
            pytest.param(VARIANT_ESP32S3, 11, id="esp32s3_adc2_gpio11"),
        ],
    )
    def test_adc2_pins_rejected_on_unsupported_variants(self, variant, pin):
        with pytest.raises(cv.Invalid, match="ADC2.*does not support continuous mode"):
            _resolve_pin_unit(variant, pin, CONF_V_INPUT)

    @pytest.mark.parametrize(
        ("variant", "pin"),
        [
            pytest.param(VARIANT_ESP32, 6, id="esp32_non_adc_gpio6"),
            pytest.param(VARIANT_ESP32S2, 0, id="esp32s2_non_adc_gpio0"),
            pytest.param(VARIANT_ESP32C3, 10, id="esp32c3_non_adc_gpio10"),
        ],
    )
    def test_non_adc_pin_rejected(self, variant, pin):
        with pytest.raises(cv.Invalid, match="not a valid ADC pin"):
            _resolve_pin_unit(variant, pin, CONF_V_INPUT)

    def test_unknown_variant_rejects_any_pin(self):
        with pytest.raises(cv.Invalid, match="not a valid ADC pin"):
            _resolve_pin_unit("ESP32XX", 1, CONF_V_INPUT)


class TestFinalValidateConfig:
    def test_both_adc1_on_esp32(self, set_core_config: SetCoreConfigCallable):
        set_core_config(
            PlatformFramework.ESP32_IDF,
            platform_data={KEY_VARIANT: VARIANT_ESP32},
        )
        config = _make_config(v_pin=36, i_pin=39)
        result = final_validate_config(config)
        assert result is config

    def test_both_adc1_on_esp32s2(self, set_core_config: SetCoreConfigCallable):
        set_core_config(
            PlatformFramework.ESP32_IDF,
            platform_data={KEY_VARIANT: VARIANT_ESP32S2},
        )
        config = _make_config(v_pin=1, i_pin=2)
        result = final_validate_config(config)
        assert result is config

    def test_both_adc2_on_esp32s2(self, set_core_config: SetCoreConfigCallable):
        set_core_config(
            PlatformFramework.ESP32_IDF,
            platform_data={KEY_VARIANT: VARIANT_ESP32S2},
        )
        config = _make_config(v_pin=11, i_pin=12)
        result = final_validate_config(config)
        assert result is config

    def test_mixed_units_rejected_on_esp32s2(
        self, set_core_config: SetCoreConfigCallable
    ):
        set_core_config(
            PlatformFramework.ESP32_IDF,
            platform_data={KEY_VARIANT: VARIANT_ESP32S2},
        )
        config = _make_config(v_pin=1, i_pin=11)
        with pytest.raises(cv.Invalid, match="TYPE1 output format"):
            final_validate_config(config)

    def test_mixed_units_allowed_on_esp32p4(
        self, set_core_config: SetCoreConfigCallable
    ):
        set_core_config(
            PlatformFramework.ESP32_IDF,
            platform_data={KEY_VARIANT: VARIANT_ESP32P4},
        )
        config = _make_config(v_pin=16, i_pin=49)
        result = final_validate_config(config)
        assert result is config

    def test_adc2_rejected_on_esp32(self, set_core_config: SetCoreConfigCallable):
        set_core_config(
            PlatformFramework.ESP32_IDF,
            platform_data={KEY_VARIANT: VARIANT_ESP32},
        )
        config = _make_config(v_pin=36, i_pin=4)
        with pytest.raises(cv.Invalid, match="ADC2.*does not support continuous mode"):
            final_validate_config(config)

    def test_adc2_rejected_on_esp32s3(self, set_core_config: SetCoreConfigCallable):
        set_core_config(
            PlatformFramework.ESP32_IDF,
            platform_data={KEY_VARIANT: VARIANT_ESP32S3},
        )
        config = _make_config(v_pin=1, i_pin=11)
        with pytest.raises(cv.Invalid, match="ADC2.*does not support continuous mode"):
            final_validate_config(config)

    def test_adc2_rejected_on_esp32c3(self, set_core_config: SetCoreConfigCallable):
        set_core_config(
            PlatformFramework.ESP32_IDF,
            platform_data={KEY_VARIANT: VARIANT_ESP32C3},
        )
        config = _make_config(v_pin=0, i_pin=5)
        with pytest.raises(cv.Invalid, match="ADC2.*does not support continuous mode"):
            final_validate_config(config)
