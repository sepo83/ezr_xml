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
from .coordinator import BASE_STATION_KEY


SENSOR_FIELDS = {
    "HEATAREA_NAME": ("Name", None, None, None),
    "HEATAREA_MODE": ("Betriebsmodus", None, None, None),
    "T_ACTUAL": (
        "Isttemperatur",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_ACTUAL_EXT": (
        "Externe Isttemperatur",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_TARGET": (
        "Solltemperatur",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_TARGET_BASE": (
        "Basis-Solltemperatur",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "HEATAREA_STATE": ("Heizzonenstatus", None, None, None),
    "PROGRAM_SOURCE": ("Programmquelle", None, None, None),
    "PROGRAM_WEEK": ("Wochenprogramm", None, None, None),
    "PROGRAM_WEEKEND": ("Wochenendprogramm", None, None, None),
    "PARTY": ("Party-Modus", None, None, None),
    "PARTY_REMAININGTIME": ("Party-Restzeit", "min", None, None),
    "PRESENCE": ("Anwesenheit", None, None, None),
    "T_TARGET_MIN": (
        "Minimale Solltemperatur",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_TARGET_MAX": (
        "Maximale Solltemperatur",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "RPM_MOTOR": ("Motordrehzahl", None, None, None),
    "OFFSET": (
        "Temperatur-Offset",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_HEAT_DAY": (
        "Heiztemperatur Tag",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_HEAT_NIGHT": (
        "Heiztemperatur Nacht",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_COOL_DAY": (
        "Kühltemperatur Tag",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_COOL_NIGHT": (
        "Kühltemperatur Nacht",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_FLOOR_DAY": (
        "Fußbodentemperatur Tag",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "T_FLOOR_MAX": (
        "Maximale Fußbodentemperatur",
        UnitOfTemperature.CELSIUS,
        SensorDeviceClass.TEMPERATURE,
        SensorStateClass.MEASUREMENT,
    ),
    "HEATINGSYSTEM": ("Heizungssystem", None, None, None),
    "BLOCK_HC": ("Heizkreis-Sperre", None, None, None),
    "ISLOCKED": ("Gesperrt", None, None, None),
    "LOCK_AVAILABLE": ("Sperrcode verfügbar", None, None, None),
    "LIGHT": ("Beleuchtung", None, None, None),
    "SENSOR_EXT": ("Externer Sensor", None, None, None),
    "T_TARGET_ADJUSTABLE": (
        "Solltemperatur einstellbar",
        None,
        None,
        None,
    ),

    # Stellantrieb / ACTOR
    "ACTOR": ("Stellantrieb", None, None, None),
    "ACTOR_PERCENT": ("Ventilöffnung", PERCENTAGE, None, None),
    "HEATCTRL_STATE": ("Heizstatus", None, None, None),
    "HEATCTRL_NR": ("Zugeordneter Heizaktor", None, None, None),
    "INUSE": ("Stellantrieb in Verwendung", None, None, None),
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


# Deutsche Bezeichnungen der Felder in der Basisstation.
BASE_FIELD_LABELS = {
    # System
    "ID": "Geräte-ID",
    "TYPE": "Gerätetyp",
    "NAME": "Gerätename",
    "ORIGIN": "Herkunft",
    "CID": "Gerätekennung",
    "ERRORCOUNT": "Fehleranzahl",
    "DATETIME": "Gerätezeit",
    "DAYOFWEEK": "Wochentag",
    "TIMEZONE": "Zeitzone",
    "NTPTIMESYNC": "NTP-Zeitsynchronisation",
    "VERS_SW_STM": "Softwareversion Controller",
    "VERS_SW_ETH": "Softwareversion Ethernet",
    "VERS_HW": "Hardwareversion",
    "TEMPERATUREUNIT": "Temperatureinheit",
    "SUMMERWINTER": "Sommer-/Winterbetrieb",
    "TPS": "TPS",
    "LIMITER": "Begrenzer",
    "MASTERID": "Master-ID",
    "CHANGEOVER": "Umschaltstatus",
    "COOLING": "Kühlfunktion",
    "MODE": "Betriebsmodus",
    "OPERATIONMODE_ACTOR": "Betriebsmodus Stellantrieb",
    "ANTIFREEZE": "Frostschutz",
    "ANTIFREEZE_TEMP": "Frostschutztemperatur",
    "FIRSTOPEN_TIME": "Erstöffnungszeit",
    "SMARTSTART": "Smart Start",
    "LOCK_MODE": "Sperrmodus",
    "ECO_DIFF": "Eco-Differenz",
    "ECO_INPUTMODE": "Eco-Eingangsmodus",
    "ECO_INPUT_STATE": "Eco-Eingangszustand",
    "T_HEAT_VACATION": "Urlaubstemperatur",

    # Netzwerk
    "MAC": "MAC-Adresse",
    "DHCP": "DHCP aktiviert",
    "IPV6ACTIVE": "IPv6 aktiviert",
    "IPV4ACTUAL": "IPv4-Adresse aktuell",
    "IPV4SET": "IPv4-Adresse konfiguriert",
    "IPV6ACTUAL": "IPv6-Adresse aktuell",
    "IPV6SET": "IPv6-Adresse konfiguriert",
    "NETMASKACTUAL": "Subnetzmaske aktuell",
    "NETMASKSET": "Subnetzmaske konfiguriert",
    "DNS": "DNS-Server",
    "GATEWAY": "Gateway",

    # Urlaub
    "VACATION_STATE": "Status",
    "START_DATE": "Startdatum",
    "START_TIME": "Startzeit",
    "END_DATE": "Enddatum",
    "END_TIME": "Endzeit",

    # Pumpenausgang
    "LOCALGLOBAL": "Lokaler/globaler Betrieb",
    "PUMP_ISACTIVE": "Aktiv",
    "PUMP_OUTPUT_TYPE": "Ausgangstyp",
    "PUMP_LEADTIME": "Vorlaufzeit",
    "PUMP_STOPPINGTIME": "Nachlaufzeit",
    "PUMP_OPERATIONMODE": "Betriebsmodus",
    "MINRUNTIME": "Mindestlaufzeit",
    "MINSTANDSTILL": "Mindeststillstand",

    # Relais
    "FUNCTION": "Funktion",
    "RELAIS_ISACTIVE": "Aktiv",
    "RELAIS_LEADTIME": "Vorlaufzeit",
    "RELAIS_STOPPINGTIME": "Nachlaufzeit",
    "RELAIS_OPERATIONMODE": "Betriebsmodus",
    "RELAIS_BOILERMODE": "Kesselmodus",

    # Umschaltung
    "CHANGEOVER_FUNC_MODE": "Modus",

    # Notbetrieb
    "EMERGENCYMODE_TIME": "Zeit",
    "PWMCYCLE": "PWM-Zyklus",
    "PWMHEAT": "PWM Heizen",
    "PWMCOOL": "PWM Kühlen",

    # Schutzfunktionen
    "VALVEPROTECT_TIME": "Intervall",
    "PUMPPROTECT_TIME": "Intervall",
    "DURATION": "Dauer",

    # I/O-Geräte
    "IODEVICE_TYPE": "Gerätetyp",
    "IODEVICE_ID": "Geräte-ID",
    "IODEVICE_VERS_HW": "Hardwareversion",
    "IODEVICE_VERS_SW": "Softwareversion",
    "HEATAREA_NR": "Zugeordnete Heizzone",
    "SIGNALSTRENGTH": "Signalstärke",
    "BATTERY": "Batteriestatus",
    "IODEVICE_STATE": "Gerätestatus",
    "IODEVICE_COMERROR": "Kommunikationsfehler",
    "ISON": "Eingeschaltet",
}


BASE_GROUP_LABELS = {
    "SYSTEM": "System",
    "NETWORK": "Netzwerk",
    "VACATION": "Urlaub",
    "PUMP_OUTPUT": "Pumpenausgang",
    "RELAIS": "Relais",
    "CHANGEOVER_FUNC": "Umschaltfunktion",
    "EMERGENCYMODE": "Notbetrieb",
    "VALVEPROTECT": "Ventilschutz",
    "PUMPPROTECT": "Pumpenschutz",
}


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


def _humanize_field(field):
    """Create a readable fallback label from an XML field name."""
    return field.replace("_", " ").capitalize()


def _base_station_label(field):
    """Create a German name with the group name as prefix."""
    match = re.fullmatch(r"IODEVICE_(\d+)_(.+)", field)

    if match:
        device_nr, subfield = match.groups()
        label = BASE_FIELD_LABELS.get(
            subfield,
            _humanize_field(subfield),
        )
        return f"IO-Gerät {device_nr} – {label}"

    if field.startswith("SYSTEM_"):
        subfield = field.removeprefix("SYSTEM_")
        label = BASE_FIELD_LABELS.get(
            subfield,
            _humanize_field(subfield),
        )
        return f"System – {label}"

    for prefix, group_label in BASE_GROUP_LABELS.items():
        marker = f"{prefix}_"

        if field.startswith(marker):
            subfield = field.removeprefix(marker)
            label = BASE_FIELD_LABELS.get(
                subfield,
                _humanize_field(subfield),
            )
            return f"{group_label} – {label}"

    return _humanize_field(field)


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
                        label=_base_station_label(field),
                        unit=None,
                        device_class=None,
                        state_class=None,
                        icon=_base_station_icon(field),
                    )
                )

            continue

        # Existing heating-area sensors.
        for field, (
            label,
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
                    label=label,
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
        label,
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

        self._attr_name = label
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class

        if self._is_base_station:
            self._attr_unique_id = (
                f"ezr_xml_{config_entry_id}_base_station_{field.lower()}"
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

            return {
                "identifiers": {
                    (DOMAIN, f"{self.config_entry_id}_base_station"),
                },
                "name": str(
                    data.get("__name__") or "EZR-Basisstation"
                ),
                "manufacturer": MANUFACTURER,
                "model": "Basisstation",
            }

        data = self.coordinator.data.get(self.area_nr, {})
        area_name = (
            data.get("HEATAREA_NAME")
            or f"Heizzone {self.area_nr}"
        )

        return {
            "identifiers": {
                (
                    DOMAIN,
                    f"{self.config_entry_id}_area_{self.area_nr}",
                ),
            },
            "name": str(area_name),
            "manufacturer": MANUFACTURER,
            "model": "Heizzone",
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