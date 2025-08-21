import esphome.codegen as cg
from esphome.components import ble_client, climate
import esphome.config_validation as cv
from esphome.const import CONF_ID

CONF_SETPOINT_MODE = "setpoint_mode"

CODEOWNERS = ["@Petapton"]
DEPENDENCIES = ["ble_client"]

madoka_ns = cg.esphome_ns.namespace("madoka")
Madoka = madoka_ns.class_(
    "Madoka", climate.Climate, ble_client.BLEClientNode, cg.PollingComponent
)

SetpointMode = madoka_ns.enum("SetpointMode")
SETPOINT_MODES = {
    "SINGLE": SetpointMode.SETPOINT_MODE_SINGLE,
    "DUAL": SetpointMode.SETPOINT_MODE_DUAL,
}
validate_setpoint_mode = cv.enum(SETPOINT_MODES, upper=True)

CONFIG_SCHEMA = (
    climate.climate_schema(Madoka)
    .extend(ble_client.BLE_CLIENT_SCHEMA)
    .extend(cv.polling_component_schema("10s"))
    .extend(
        {
            cv.Optional(CONF_SETPOINT_MODE, default="DUAL"): validate_setpoint_mode,
        }
    )
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await climate.register_climate(var, config)
    await ble_client.register_ble_node(var, config)

    cg.add(var.set_setpoint_mode(config[CONF_SETPOINT_MODE]))
