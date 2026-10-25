"""Fetch and parse EZR XML."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import timedelta
import xml.etree.ElementTree as ET

import aiohttp
from moehlenhoff_alpha2 import Alpha2Base

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

BASE_STATION_KEY = "__base_station__"
IODEVICE_KEY_PREFIX = "__iodevice_"
ACTOR_KEY_PREFIX = "__actor_"

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
        "__name__": _value(device, "NAME"),
        "__model__": "EZR",
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
        self._command_lock = asyncio.Lock()
        self._alpha2 = Alpha2Base(url)
        self._alpha2.base_url = url.removesuffix("/data/static.xml")

        super().__init__(
            hass,
            _LOGGER,
            name="EZR XML",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def async_set_target_temperature(
        self,
        area_nr: str,
        target_temperature: float,
    ) -> None:
        """Set a zone target using the Alpha2 changes.xml API."""
        async with self._command_lock:
            await self._async_refresh_alpha2(
                "Failed to set EZR target temperature"
            )
            area_data = next(
                (
                    area
                    for area in self._alpha2.heat_areas
                    if str(area["NR"]) == area_nr
                ),
                None,
            )
            if area_data is None:
                raise HomeAssistantError(f"Unknown EZR heating zone: {area_nr}")

            update_data = {"T_TARGET": target_temperature}
            mode = area_data.get("HEATAREA_MODE", 0)
            if mode in (1, 2):
                period = "DAY" if mode == 1 else "NIGHT"
                temperature_type = "COOL" if self._alpha2.cooling else "HEAT"
                update_data[f"T_{temperature_type}_{period}"] = target_temperature

            try:
                await self._alpha2.update_heat_area(area_nr, update_data)
            except (aiohttp.ClientError, TimeoutError) as err:
                raise HomeAssistantError(
                    "Failed to set EZR target temperature"
                ) from err

            self.data[area_nr].update(update_data)
            self.async_update_listeners()

    async def async_set_heat_area_mode(
        self,
        area_nr: str,
        preset_mode: str,
    ) -> None:
        """Set the automatic, day, or night preset for a heating zone."""
        mode_by_preset = {"auto": 0, "day": 1, "night": 2}
        if preset_mode not in mode_by_preset:
            raise ValueError(f"Invalid EZR preset mode: {preset_mode}")

        async with self._command_lock:
            await self._async_refresh_alpha2(
                "Failed to set EZR heating-zone preset"
            )
            area_data = next(
                (
                    area
                    for area in self._alpha2.heat_areas
                    if str(area["NR"]) == area_nr
                ),
                None,
            )
            if area_data is None:
                raise HomeAssistantError(f"Unknown EZR heating zone: {area_nr}")

            mode = mode_by_preset[preset_mode]
            update_data = {"HEATAREA_MODE": mode}
            if mode in (1, 2):
                period = "DAY" if mode == 1 else "NIGHT"
                temperature_type = "COOL" if self._alpha2.cooling else "HEAT"
                target = area_data.get(f"T_{temperature_type}_{period}")
                if target is not None:
                    update_data["T_TARGET"] = target

            try:
                await self._alpha2.update_heat_area(area_nr, update_data)
            except (aiohttp.ClientError, TimeoutError) as err:
                raise HomeAssistantError(
                    "Failed to set EZR heating-zone preset"
                ) from err

            self.data[area_nr].update(update_data)
            self.async_update_listeners()

    async def async_set_cooling(self, enabled: bool) -> None:
        """Set the base station's global heating or cooling mode."""
        async with self._command_lock:
            await self._async_refresh_alpha2(
                "Failed to set EZR heating/cooling mode"
            )
            try:
                await self._alpha2.set_cooling(enabled)
            except (aiohttp.ClientError, TimeoutError) as err:
                raise HomeAssistantError(
                    "Failed to set EZR heating/cooling mode"
                ) from err

            self.data[BASE_STATION_KEY]["SYSTEM_COOLING"] = int(enabled)
            self.async_update_listeners()

    async def _async_refresh_alpha2(self, error_message: str) -> None:
        """Refresh the library data and translate transport errors for HA."""
        try:
            await self._alpha2.update_data()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise HomeAssistantError(error_message) from err

    async def _async_update_data(self):
        """Fetch XML and return area and base-station data."""
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            session = async_get_clientsession(self.hass)

            for attempt in range(2):
                try:
                    async with session.get(self.url, timeout=timeout) as response:
                        response.raise_for_status()
                        content = await response.read()

                    root = ET.fromstring(content)
                    break
                except (
                    ET.ParseError,
                    aiohttp.ClientError,
                    asyncio.TimeoutError,
                ) as err:
                    retryable_status = (
                        isinstance(err, aiohttp.ClientResponseError)
                        and (err.status == 429 or err.status >= 500)
                    )
                    retryable_error = not isinstance(
                        err, aiohttp.ClientResponseError
                    ) or retryable_status

                    if attempt == 1 or not retryable_error:
                        raise

                    if isinstance(err, ET.ParseError):
                        _LOGGER.warning(
                            "EZR XML response was malformed; retrying once"
                        )
                    else:
                        _LOGGER.warning(
                            "EZR XML request failed (%s); retrying once",
                            type(err).__name__,
                        )
                    await asyncio.sleep(0.5)

        except (
            aiohttp.ClientError,
            ET.ParseError,
            TimeoutError,
        ) as err:
            raise UpdateFailed(
                f"Unable to fetch or parse XML: {err}"
            ) from err

        device = root.find(".//Device")

        if device is None:
            raise UpdateFailed("No Device element found in the XML")

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
            actor_data = None

            if controller is not None:
                actor_data = {
                    "__zone_name__": data.get("HEATAREA_NAME"),
                    "__area_nr__": area_nr,
                }
                controller_nr = controller.get("nr")

                if controller_nr is not None:
                    actor_data["HEATCTRL_NR"] = int(controller_nr)

                for field in ACTOR_FIELDS:
                    value = _value(controller, field)

                    if value is not None:
                        actor_data[field] = value

            result[area_nr] = data

            if actor_data is not None:
                result[f"{ACTOR_KEY_PREFIX}{area_nr}"] = actor_data

        for io_device in device.findall("IODEVICE"):
            io_nr = io_device.get("nr")
            area_nr = _value(io_device, "HEATAREA_NR")

            if io_nr is None or area_nr is None:
                continue

            area_key = str(area_nr)

            if area_key not in result:
                continue

            area_name = result[area_key].get("HEATAREA_NAME")
            io_data = {
                "__zone_name__": area_name,
                "__area_nr__": area_key,
            }
            _flatten_group(io_device, f"IODEVICE_{io_nr}", io_data)
            result[f"{IODEVICE_KEY_PREFIX}{io_nr}"] = io_data

        if not areas:
            raise UpdateFailed("No HEATAREA elements found in the XML")

        return result