"""Sensors for EZR XML."""
from __future__ import annotations

import re

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import (
    ACTOR_KEY_PREFIX,
    BASE_STATION_KEY,
    IODEVICE_KEY_PREFIX,
)


SENSOR_FIELDS = {
    "HEATAREA_NAME": ("heatarea_name", None, None, None),
    "HEATAREA_MODE": ("heatarea_mode", None, None, None),
    "T_ACTUAL": (
        "t_actual",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_ACTUAL_EXT": (
        "t_actual_ext",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_TARGET": (
        "t_target",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_TARGET_BASE": (
        "t_target_base",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "HEATAREA_STATE": ("heatarea_state", None, None, None),
    "PROGRAM_SOURCE": ("program_source", None, None, None),
    "PROGRAM_WEEK": ("program_week", None, None, None),
    "PROGRAM_WEEKEND": ("program_weekend", None, None, None),
    "PARTY": ("party", None, None, None),
    "PARTY_REMAININGTIME": ("party_remainingtime", "min", None, None),
    "PRESENCE": ("presence", None, None, None),
    "T_TARGET_MIN": (
        "t_target_min",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_TARGET_MAX": (
        "t_target_max",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "RPM_MOTOR": ("rpm_motor", None, None, None),
    "OFFSET": (
        "offset",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_HEAT_DAY": (
        "t_heat_day",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_HEAT_NIGHT": (
        "t_heat_night",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_COOL_DAY": (
        "t_cool_day",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_COOL_NIGHT": (
        "t_cool_night",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_FLOOR_DAY": (
        "t_floor_day",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_FLOOR_MAX": (
        "t_floor_max",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "HEATINGSYSTEM": ("heatingsystem", None, None, None),
    "BLOCK_HC": ("block_hc", None, None, None),
    "ISLOCKED": ("islocked", None, None, None),
    "LOCK_AVAILABLE": ("lock_available", None, None, None),
    "LIGHT": ("light", None, None, None),
    "SENSOR_EXT": ("sensor_ext", None, None, None),
    "T_TARGET_ADJUSTABLE": (
        "t_target_adjustable",
        None,
        None,
        None,
    ),

    # Stellantrieb / ACTOR
    "ACTOR": ("actor", None, None, None),
    "ACTOR_PERCENT": ("actor_percent", PERCENTAGE, None, None),
    "HEATCTRL_STATE": ("heatctrl_state", None, None, None),
    "HEATCTRL_NR": ("heatctrl_nr", None, None, None),
    "INUSE": ("inuse", None, None, None),
}


SENSOR_ICONS = {
    # Heizbereich
    "HEATAREA_NAME": "mdi:home-thermometer",
    "HEATAREA_MODE": "mdi:thermostat",
    "HEATAREA_STATE": "mdi:radiator",
    "HEATINGSYSTEM": "mdi:heating-coil",
    "BLOCK_HC": "mdi:lock",
    "ISLOCKED": "mdi:lock-alert",
    "LOCK_AVAILABLE": "mdi:shield-key",

    # Temperatur
    "T_ACTUAL": "mdi:thermometer",
    "T_ACTUAL_EXT": "mdi:thermometer-lines",
    "T_TARGET": "mdi:thermometer-chevron-up",
    "T_TARGET_BASE": "mdi:thermometer",
    "T_TARGET_MIN": "mdi:thermometer-chevron-down",
    "T_TARGET_MAX": "mdi:thermometer-high",
    "OFFSET": "mdi:thermometer-plus",
    "T_HEAT_DAY": "mdi:weather-sunny",
    "T_HEAT_NIGHT": "mdi:weather-night",
    "T_COOL_DAY": "mdi:snowflake-thermometer",
    "T_COOL_NIGHT": "mdi:snowflake",
    "T_FLOOR_DAY": "mdi:floor-plan",
    "T_FLOOR_MAX": "mdi:thermometer-alert",
    "T_TARGET_ADJUSTABLE": "mdi:tune-vertical",

    # Programme und Betriebsarten
    "PROGRAM_SOURCE": "mdi:source-branch",
    "PROGRAM_WEEK": "mdi:calendar-week",
    "PROGRAM_WEEKEND": "mdi:calendar-weekend",
    "PARTY": "mdi:party-popper",
    "PARTY_REMAININGTIME": "mdi:timer-sand",
    "PRESENCE": "mdi:account-check",

    # Stellantrieb
    "ACTOR": "mdi:heating-coil",
    "ACTOR_PERCENT": "mdi:valve",
    "HEATCTRL_STATE": "mdi:radiator",
    "HEATCTRL_NR": "mdi:identifier",
    "INUSE": "mdi:check-circle",

    # Weitere Informationen
    "RPM_MOTOR": "mdi:rotate-right",
    "LIGHT": "mdi:lightbulb",
    "SENSOR_EXT": "mdi:thermometer-probe",
}


BASE_GROUP_PREFIXES = (
    "NETWORK",
    "VACATION",
    "PUMP_OUTPUT",
    "RELAIS",
    "CHANGEOVER_FUNC",
    "EMERGENCYMODE",
    "VALVEPROTECT",
    "PUMPPROTECT",
)


BASE_GROUP_ICONS = {
    "SYSTEM": "mdi:chip",
    "NETWORK": "mdi:lan",
    "VACATION": "mdi:calendar-clock",
    "PUMP_OUTPUT": "mdi:pump",
    "RELAIS": "mdi:electric-switch",
    "CHANGEOVER_FUNC": "mdi:swap-horizontal",
    "EMERGENCYMODE": "mdi:alert",
    "VALVEPROTECT": "mdi:valve",
    "PUMPPROTECT": "mdi:pump",
}


BASE_FIELD_ICONS = {
    "DATETIME": "mdi:clock-outline",
    "ERRORCOUNT": "mdi:alert-circle-outline",
    "VERS_SW_STM": "mdi:chip",
    "VERS_SW_ETH": "mdi:ethernet",
    "VERS_HW": "mdi:memory",
    "ANTIFREEZE": "mdi:snowflake",
    "ANTIFREEZE_TEMP": "mdi:thermometer-low",
    "ECO_DIFF": "mdi:thermometer-minus",
    "T_HEAT_VACATION": "mdi:thermometer",
    "MAC": "mdi:network-outline",
    "DHCP": "mdi:ip-network",
    "IPV6ACTIVE": "mdi:network",
    "IPV4ACTUAL": "mdi:ip-network",
    "IPV4SET": "mdi:ip-network-outline",
    "IPV6ACTUAL": "mdi:ip-network",
    "IPV6SET": "mdi:ip-network-outline",
    "NETMASKACTUAL": "mdi:network-outline",
    "NETMASKSET": "mdi:network-outline",
    "DNS": "mdi:dns",
    "GATEWAY": "mdi:router-network",
    "VACATION_STATE": "mdi:calendar-check",
    "START_DATE": "mdi:calendar-start",
    "END_DATE": "mdi:calendar-end",
    "START_TIME": "mdi:clock-start",
    "END_TIME": "mdi:clock-end",
    "PUMP_ISACTIVE": "mdi:pump",
    "PUMP_OUTPUT_TYPE": "mdi:pipe",
    "PUMP_LEADTIME": "mdi:timer-play",
    "PUMP_STOPPINGTIME": "mdi:timer-stop",
    "MINRUNTIME": "mdi:timer-outline",
    "MINSTANDSTILL": "mdi:timer-pause",
    "RELAIS_ISACTIVE": "mdi:electric-switch",
    "CHANGEOVER_FUNC_MODE": "mdi:swap-horizontal",
    "EMERGENCYMODE_TIME": "mdi:timer-alert",
    "PWMCYCLE": "mdi:waveform",
    "PWMHEAT": "mdi:fire",
    "PWMCOOL": "mdi:snowflake",
    "VALVEPROTECT_TIME": "mdi:valve",
    "PUMPPROTECT_TIME": "mdi:pump",
    "SIGNALSTRENGTH": "mdi:wifi",
    "BATTERY": "mdi:battery",
    "IODEVICE_STATE": "mdi:devices",
    "IODEVICE_COMERROR": "mdi:alert-network",
    "ISON": "mdi:power",
}


def _io_device_translation_key(field):
    """Return a translation key for an I/O device field."""
    match = re.fullmatch(r"IODEVICE_\d+_(.+)", field)

    if not match:
        return field.lower()

    subfield = match.group(1).removeprefix("IODEVICE_")
    return f"io_device_{subfield.lower()}"


def _base_station_translation_key(field):
    """Return a translation key for a base-station field."""
    match = re.fullmatch(r"IODEVICE_(\d+)_(.+)", field)

    if match:
        subfield = match.group(2).removeprefix("IODEVICE_")
        return f"base_io_device_{subfield.lower()}"

    if field.startswith("SYSTEM_"):
        subfield = field.removeprefix("SYSTEM_")
        return f"base_system_{subfield.lower()}"

    for prefix in BASE_GROUP_PREFIXES:
        marker = f"{prefix}_"

        if field.startswith(marker):
            subfield = field.removeprefix(marker)
            return f"base_{prefix.lower()}_{subfield.lower()}"

    return f"base_{field.lower()}"


def _base_station_icon(field):
    """Return an appropriate icon for a base-station sensor."""
    match = re.fullmatch(r"IODEVICE_\d+_(.+)", field)

    if match:
        subfield = match.group(1)
        return BASE_FIELD_ICONS.get(subfield, "mdi:devices")

    if field.startswith("SYSTEM_"):
        subfield = field.removeprefix("SYSTEM_")
        return BASE_FIELD_ICONS.get(subfield, "mdi:chip")

    for prefix, icon in BASE_GROUP_ICONS.items():
        if field.startswith(f"{prefix}_"):
            subfield = field.removeprefix(f"{prefix}_")
            return BASE_FIELD_ICONS.get(subfield, icon)

    return "mdi:information-outline"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up area and base-station sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for device_key, data in coordinator.data.items():

        # Separate device for the base station.
        if device_key == BASE_STATION_KEY:
            for field in data:
                if field.startswith("__"):
                    continue

                entities.append(
                    EzrSensor(
                        coordinator=coordinator,
                        config_entry_id=entry.entry_id,
                        area_nr=BASE_STATION_KEY,
                        field=field,
                        translation_key=_base_station_translation_key(field),
                        unit=None,
                        device_class=None,
                        state_class=None,
                        icon=_base_station_icon(field),
                    )
                )

            continue

        if device_key.startswith(IODEVICE_KEY_PREFIX):
            for field in data:
                if field.startswith("__"):
                    continue

                entities.append(
                    EzrSensor(
                        coordinator=coordinator,
                        config_entry_id=entry.entry_id,
                        area_nr=device_key,
                        field=field,
                        translation_key=_io_device_translation_key(field),
                        unit=None,
                        device_class=None,
                        state_class=None,
                        icon=_base_station_icon(field),
                    )
                )

            continue

        if device_key.startswith(ACTOR_KEY_PREFIX):
            for field, (
                translation_key,
                unit,
                device_class,
                state_class,
            ) in SENSOR_FIELDS.items():
                if field not in data:
                    continue

                entities.append(
                    EzrSensor(
                        coordinator=coordinator,
                        config_entry_id=entry.entry_id,
                        area_nr=device_key,
                        field=field,
                        translation_key=translation_key,
                        unit=unit,
                        device_class=device_class,
                        state_class=state_class,
                        icon=SENSOR_ICONS.get(field),
                    )
                )

            continue

        # Existing heating-area sensors.
        for field, (
            translation_key,
            unit,
            device_class,
            state_class,
        ) in SENSOR_FIELDS.items():
            if field not in data:
                continue

            entities.append(
                EzrSensor(
                    coordinator=coordinator,
                    config_entry_id=entry.entry_id,
                    area_nr=device_key,
                    field=field,
                    translation_key=translation_key,
                    unit=unit,
                    device_class=device_class,
                    state_class=state_class,
                    icon=SENSOR_ICONS.get(field),
                )
            )

    async_add_entities(entities)


class EzrSensor(CoordinatorEntity, SensorEntity):
    """Represent one XML field."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        config_entry_id,
        area_nr,
        field,
        translation_key,
        unit,
        device_class,
        state_class,
        icon=None,
    ):
        super().__init__(coordinator)

        self.config_entry_id = config_entry_id
        self.area_nr = str(area_nr)
        self.field = field
        self._is_base_station = self.area_nr == BASE_STATION_KEY
        self._is_io_device = self.area_nr.startswith(IODEVICE_KEY_PREFIX)
        self._is_actor = self.area_nr.startswith(ACTOR_KEY_PREFIX)

        self._attr_translation_key = translation_key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class

        if self._is_base_station:
            self._attr_unique_id = (
                f"ezr_xml_{config_entry_id}_base_station_{field.lower()}"
            )
        elif self._is_io_device:
            self._attr_unique_id = (
                f"ezr_xml_{config_entry_id}_base_station_{field.lower()}"
            )
        elif self._is_actor:
            zone_nr = self.area_nr.removeprefix(ACTOR_KEY_PREFIX)
            self._attr_unique_id = (
                f"ezr_xml_{config_entry_id}_area_{zone_nr}_{field.lower()}"
            )
        else:
            self._attr_unique_id = (
                f"ezr_xml_{config_entry_id}_area_{area_nr}_{field.lower()}"
            )

        if icon:
            self._attr_icon = icon

    @property
    def device_info(self):
        """Return the device this sensor belongs to."""
        if self._is_base_station:
            data = self.coordinator.data.get(
                BASE_STATION_KEY,
                {},
            )
            device_name = data.get("__name__")

            return {
                "identifiers": {
                    (DOMAIN, f"{self.config_entry_id}_base_station"),
                },
                "name": str(device_name or "EZR Base Station"),
                "translation_key": (
                    "named_base_station" if device_name else "base_station"
                ),
                "translation_placeholders": (
                    {"name": str(device_name)} if device_name else {}
                ),
                "manufacturer": MANUFACTURER,
                "model": str(data.get("__model__") or "EZR"),
            }

        if self._is_io_device:
            data = self.coordinator.data.get(self.area_nr, {})
            io_nr = self.area_nr.removeprefix(IODEVICE_KEY_PREFIX)
            area_nr = data.get("__area_nr__")
            zone_name = data.get("__zone_name__")

            return {
                "identifiers": {
                    (DOMAIN, f"{self.config_entry_id}_iodevice_{io_nr}"),
                },
                "name": str(zone_name or f"Heating zone {area_nr}") + " Thermostat",
                "translation_key": (
                    "thermostat" if zone_name else "unnamed_thermostat"
                ),
                "translation_placeholders": (
                    {"zone_name": str(zone_name)}
                    if zone_name
                    else {"zone_number": str(area_nr)}
                ),
                "manufacturer": MANUFACTURER,
                "via_device": (
                    DOMAIN,
                    f"{self.config_entry_id}_area_{area_nr}",
                ),
            }

        if self._is_actor:
            data = self.coordinator.data.get(self.area_nr, {})
            area_nr = data.get("__area_nr__")
            zone_name = data.get("__zone_name__")

            return {
                "identifiers": {
                    (DOMAIN, f"{self.config_entry_id}_actor_{area_nr}"),
                },
                "name": str(zone_name or f"Heating zone {area_nr}") + " Actuator",
                "translation_key": "actuator" if zone_name else "unnamed_actuator",
                "translation_placeholders": (
                    {"zone_name": str(zone_name)}
                    if zone_name
                    else {"zone_number": str(area_nr)}
                ),
                "manufacturer": MANUFACTURER,
                "via_device": (
                    DOMAIN,
                    f"{self.config_entry_id}_area_{area_nr}",
                ),
            }

        data = self.coordinator.data.get(self.area_nr, {})
        area_name = data.get("HEATAREA_NAME")

        return {
            "identifiers": {
                (
                    DOMAIN,
                    f"{self.config_entry_id}_area_{self.area_nr}",
                ),
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
    def available(self):
        """Return whether the sensor has current data."""
        return (
            self.coordinator.last_update_success
            and self.area_nr in self.coordinator.data
            and self.field in self.coordinator.data[self.area_nr]
        )

    @property
    def native_value(self):
        """Return the value from the XML data."""
        return (
            self.coordinator.data
            .get(self.area_nr, {})
            .get(self.field)
        )