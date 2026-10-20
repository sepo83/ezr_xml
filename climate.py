"""Climate entities for EZR heating zones."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import ACTOR_KEY_PREFIX, BASE_STATION_KEY

PRESET_AUTO = "auto"
PRESET_DAY = "day"
PRESET_NIGHT = "night"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up one climate entity for each heating zone."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        EzrClimate(coordinator, entry.entry_id, area_nr)
        for area_nr, area_data in coordinator.data.items()
        if isinstance(area_data, dict) and "nr" in area_data
    )


class EzrClimate(CoordinatorEntity, ClimateEntity):
    """Represent one EZR heating zone."""

    _attr_has_entity_name = True
    _attr_translation_key = "climate"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.2
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
    )
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.COOL]
    _attr_preset_modes = [PRESET_AUTO, PRESET_DAY, PRESET_NIGHT]

    def __init__(self, coordinator, config_entry_id, area_nr):
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self.config_entry_id = config_entry_id
        self.area_nr = str(area_nr)
        self._attr_unique_id = (
            f"ezr_xml_{config_entry_id}_climate_{self.area_nr}"
        )

    @property
    def area_data(self):
        """Return the latest data for this heating zone."""
        return self.coordinator.data.get(self.area_nr, {})

    @property
    def available(self):
        """Return whether this zone has current coordinator data."""
        return (
            self.coordinator.last_update_success
            and self.area_nr in self.coordinator.data
        )

    @property
    def device_info(self):
        """Attach this entity to its heating-zone device."""
        area_name = self.area_data.get("HEATAREA_NAME")
        return {
            "identifiers": {
                (DOMAIN, f"{self.config_entry_id}_area_{self.area_nr}"),
            },
            "name": str(area_name or f"Heating zone {self.area_nr}"),
            "translation_key": (
                "heating_zone" if area_name else "unnamed_heating_zone"
            ),
            "translation_placeholders": (
                {"zone_name": str(area_name)}
                if area_name
                else {"zone_number": self.area_nr}
            ),
            "manufacturer": MANUFACTURER,
        }

    @property
    def min_temp(self):
        """Return the minimum target temperature supported by this zone."""
        return float(self.area_data.get("T_TARGET_MIN", 0.0))

    @property
    def max_temp(self):
        """Return the maximum target temperature supported by this zone."""
        return float(self.area_data.get("T_TARGET_MAX", 30.0))

    @property
    def current_temperature(self):
        """Return the current zone temperature."""
        value = self.area_data.get("T_ACTUAL")
        return float(value) if value is not None else None

    @property
    def target_temperature(self):
        """Return the current target temperature."""
        value = self.area_data.get("T_TARGET")
        return float(value) if value is not None else None

    @property
    def hvac_mode(self):
        """Return the controller's active heating or cooling mode."""
        base_station = self.coordinator.data.get(BASE_STATION_KEY, {})
        if base_station.get("SYSTEM_COOLING"):
            return HVACMode.COOL
        return HVACMode.HEAT

    @property
    def hvac_action(self):
        """Return whether this zone is idle, heating, or cooling."""
        actor_data = self.coordinator.data.get(
            f"{ACTOR_KEY_PREFIX}{self.area_nr}",
            {},
        )
        if not actor_data.get("HEATCTRL_STATE"):
            return HVACAction.IDLE
        if self.hvac_mode == HVACMode.COOL:
            return HVACAction.COOLING
        return HVACAction.HEATING

    @property
    def extra_state_attributes(self):
        """Expose actuator values so changes are recorded with the climate state."""
        actor_data = self.coordinator.data.get(
            f"{ACTOR_KEY_PREFIX}{self.area_nr}",
            {},
        )
        attributes = {}

        if "ACTOR" in actor_data:
            attributes["actuator_state"] = (
                "open" if actor_data["ACTOR"] else "closed"
            )
        if "ACTOR_PERCENT" in actor_data:
            attributes["actuator_percent"] = actor_data["ACTOR_PERCENT"]
        if "INUSE" in actor_data:
            attributes["actuator_assigned"] = bool(actor_data["INUSE"])

        return attributes

    @property
    def preset_mode(self):
        """Return the zone's automatic, day, or night preset."""
        mode = self.area_data.get("HEATAREA_MODE")
        if mode == 1:
            return PRESET_DAY
        if mode == 2:
            return PRESET_NIGHT
        return PRESET_AUTO

    async def async_set_hvac_mode(self, hvac_mode):
        """Set the controller's global heating or cooling mode."""
        await self.coordinator.async_set_cooling(hvac_mode == HVACMode.COOL)

    async def async_set_temperature(self, **kwargs):
        """Set this zone's target temperature."""
        target_temperature = kwargs.get(ATTR_TEMPERATURE)
        if target_temperature is not None:
            await self.coordinator.async_set_target_temperature(
                self.area_nr,
                float(target_temperature),
            )

    async def async_set_preset_mode(self, preset_mode):
        """Set the automatic, day, or night preset for this zone."""
        await self.coordinator.async_set_heat_area_mode(
            self.area_nr,
            preset_mode,
        )