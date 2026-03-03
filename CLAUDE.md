# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A PyQt5 fullscreen dashboard for home automation. Displays real-time temperature/humidity readings from room sensors and soil moisture levels for plants. Data is pulled from an InfluxDB instance at `automation.local:8086` (database: `garden`).

## Running

```bash
python app.py
```

Dependencies: PyQt5, influxdb, requests. Python venv is at `.venv/`.

## Architecture

Single-file app (`app.py`) with these key classes:

- **`MainWindow`** — Main application window. Manages a grid of widgets, an InfluxDB client, and two timers: data refresh (every 5 min) and theme check (every 1 min). Theme switches between dark/light based on an illumination sensor reading (threshold: 20).
- **`DashboardWidget`** — Displays temperature + humidity for a room. Humidity text turns red when outside 40–60% range.
- **`DashboardLevelWidget`** — Displays soil moisture as a 5-level icon indicator. Thresholds: <3, <6, <9, <12, >=12.
- **`Measure` / `Moisture`** — Simple data containers for sensor readings.

## Data Sources (InfluxDB)

- `Telemetry` measurement — room temperature/humidity, filtered by `alias` tag (e.g., `workRoomTempSensor`, `bedRoomTempSensor`, `livRoomTempSensor`, `SashaRoomTempSensor`)
- `Flowers` measurement — soil moisture, filtered by `alias` tag (e.g., `flowerOleandrSensor`, `flowerOlivaSensor`)
- `illuminationSensor` measurement — ambient light level for theme switching

## UI Layout

2x3 grid: top row has 3 room widgets (КАБИНЕТ, СПАЛЬНЯ, ЗАЛ), bottom row has 1 room widget (ПЕЩЕРА) and 2 plant widgets (ОЛЕАНДР, ОЛИВА). Runs fullscreen with hidden cursor. Press Escape to close.

## Image Assets

`images/` contains light and dark variants of icons (temperature, humidity, level1–5, plant icons). Dark variants use `_dark` suffix.

## Notes

- Timestamps are converted from UTC to Zurich timezone (UTC+1 hardcoded, no DST handling).
- The app uses `influxdb` (InfluxDB 1.x client), not `influxdb-client` (2.x).
