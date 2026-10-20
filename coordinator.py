"""Fetch and parse EZR XML."""
from __future__ import annotations

import logging
import re
from datetime import timedelta
import xml.etree.ElementTree as ET

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

BASE_STATION_KEY = "__base_station__"

# Diese XML-Gruppen werden bewusst nicht verarbeitet.
EXCLUDED_GROUPS = {
    "CLOUD",
    "KWLCTRL",
    "CODE",
    "PROGRAM",
}

AREA_FIELDS = [
    "HEATAREA_NAME",
    "HEATAREA_MODE",
    "T_ACTUAL",
    "T_ACTUAL_EXT",
    "T_TARGET",
    "T_TARGET_BASE",
    "HEATAREA_STATE",
    "PROGRAM_SOURCE",
    "PROGRAM_WEEK",
    "PROGRAM_WEEKEND",
    "PARTY",
    "PARTY_REMAININGTIME",
    "PRESENCE",
    "T_TARGET_MIN",
    "T_TARGET_MAX",
    "RPM_MOTOR",
    "OFFSET",
    "T_HEAT_DAY",
    "T_HEAT_NIGHT",
    "T_COOL_DAY",
    "T_COOL_NIGHT",
    "T_FLOOR_DAY",
    "T_FLOOR_MAX",
    "HEATINGSYSTEM",
    "BLOCK_HC",
    "ISLOCKED",
    "LOCK_AVAILABLE",
    "LIGHT",
    "SENSOR_EXT",
    "T_TARGET_ADJUSTABLE",
]

ACTOR_FIELDS = [
    "ACTOR",
    "ACTOR_PERCENT",
    "HEATCTRL_STATE",
    "INUSE",
]


def _value(element, key):
    """Read a child value and convert numbers where possible."""
    child = element.find(key)

    if child is None or child.text is None:
        return None

    value = child.text.strip()

    if not value:
        return None

    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except ValueError:
        return value


def _read_leaf_value(element):
    """Read the value of an XML leaf element."""
    if len(element):
        return None

    if element.text is None:
        return None

    value = element.text.strip()

    if not value:
        return None

    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except ValueError:
        return value


def _flatten_group(element, prefix, result):
    """Flatten a configuration group into prefixed sensor keys.

    Example:
        NETWORK/IPV4ACTUAL -> NETWORK_IPV4ACTUAL
        PUMP_OUTPUT/MINRUNTIME -> PUMP_OUTPUT_MINRUNTIME

    Nested groups are handled recursively.
    """
    for child in element:
        # Do not expose credential-like values.
        if child.tag in {"PASSWORD", "LOCK_CODE", "EXPERT"}:
            continue

        key = f"{prefix}_{child.tag}"

        if len(child):
            _flatten_group(child, key, result)
            continue

        value = _read_leaf_value(child)

        if value is not None:
            result[key] = value


def _build_base_station(device):
    """Extract base-station information, excluding ignored groups."""
    result = {
        "__name__": _value(device, "NAME") or "EZR-Basisstation",
        "__model__": "Basisstation",
    }

    for child in device:
        if child.tag in EXCLUDED_GROUPS:
            continue

        # Heating areas and heating controllers are handled separately.
        if child.tag in {"HEATAREA", "HEATCTRL", "IODEVICE"}:
            continue

        if len(child):
            _flatten_group(child, child.tag, result)
            continue

        value = _read_leaf_value(child)

        if value is not None:
            result[f"SYSTEM_{child.tag}"] = value

    # Read every I/O device by its explicit nr attribute.
    for io_device in device.findall("IODEVICE"):
        io_nr = io_device.get("nr")

        if io_nr is None:
            continue

        prefix = f"IODEVICE_{io_nr}"
        _flatten_group(io_device, prefix, result)

    return result


class EzrCoordinator(DataUpdateCoordinator):
    """Coordinate XML updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        url: str,
        scan_interval: int,
    ):
        self.url = url

        super().__init__(
            hass,
            _LOGGER,
            name="EZR XML",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        """Fetch XML and return area and base-station data."""
        try:
            timeout = aiohttp.ClientTimeout(total=15)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.url) as response:
                    response.raise_for_status()
                    content = await response.read()

            root = ET.fromstring(content)

        except (
            aiohttp.ClientError,
            ET.ParseError,
            TimeoutError,
        ) as err:
            raise UpdateFailed(
                f"XML konnte nicht abgerufen oder geparst werden: {err}"
            ) from err

        device = root.find(".//Device")

        if device is None:
            raise UpdateFailed(
                "Kein Device-Element in der XML-Datei gefunden"
            )

        # The base station gets its own device in Home Assistant.
        result = {
            BASE_STATION_KEY: _build_base_station(device),
        }

        areas = device.findall("HEATAREA")
        controllers = device.findall("HEATCTRL")

        # Match controllers to areas using HEATAREA_NR.
        # Never depend on the XML element order.
        controllers_by_area = {}

        for controller in controllers:
            area_ref = _value(controller, "HEATAREA_NR")

            if area_ref is None:
                continue

            controllers_by_area[str(area_ref)] = controller

        for area in areas:
            nr = area.get("nr")

            if nr is None:
                continue

            area_nr = str(nr)
            data = {"nr": int(nr)}

            for field in AREA_FIELDS:
                value = _value(area, field)

                if value is not None:
                    data[field] = value

            controller = controllers_by_area.get(area_nr)

            if controller is not None:
                controller_nr = controller.get("nr")

                if controller_nr is not None:
                    data["HEATCTRL_NR"] = int(controller_nr)

                for field in ACTOR_FIELDS:
                    value = _value(controller, field)

                    if value is not None:
                        data[field] = value

            result[area_nr] = data

        if not areas:
            raise UpdateFailed(
                "Keine HEATAREA-Elemente in der XML-Datei gefunden"
            )

        return result