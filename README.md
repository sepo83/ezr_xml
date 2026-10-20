# EZR XML

A Home Assistant custom integration for Möhlenhoff Alpha 2 heating controllers
that expose their data through the local XML interface.

## Features

- Polls the controller's `static.xml` endpoint over the local network.
- Creates separate Home Assistant devices for the base station, heating zones,
  actuators, and associated thermostats.
- Adds a writable Climate entity to each heating zone, with target temperature,
  automatic/day/night presets, and global heating/cooling mode.
- Exposes available temperatures, target values, operating states, program
  information, actuator data, and device status as sensors.
- Supports configurable polling intervals from 10 seconds to 1 hour.

Climate commands use the controller's local `/data/changes.xml` endpoint.

## Installation

1. Copy this integration directory to `config/custom_components/ezr_xml` in
   your Home Assistant configuration.
2. Restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration** and search for
   **EZR XML**.

## Configuration

Enter the controller's base URL, for example:

```text
http://192.168.1.100
```

The integration appends `/data/static.xml` automatically. You can also enter
the complete endpoint URL. The Home Assistant host must be able to reach the
controller over the network.

Set the polling interval in seconds. It defaults to 30 seconds and accepts
values from 10 to 3600 seconds.

## Home Assistant devices

- The base station contains system and network information.
- Each heating zone is represented as a device.
- An actuator is linked to its heating zone.
- Each I/O thermostat is linked to the heating zone specified by its
  `HEATAREA_NR` value.

Sensor names and availability depend on the fields returned by the controller.