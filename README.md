# automation-dashboard-gui

A PyQt5 fullscreen dashboard for home automation. Displays real-time temperature/humidity readings from room sensors and soil moisture levels for plants. Data is pulled from an InfluxDB 1.x instance.

## UI Layout

2x3 grid:

| КАБИНЕТ | СПАЛЬНЯ | ЗАЛ    |
|---------|---------|--------|
| ПЕЩЕРА  | ОЛЕАНДР | ОЛИВА  |

- Top row + bottom-left: room widgets showing temperature and humidity
- Bottom-right two: plant widgets showing soil moisture as a 5-level icon indicator
- Humidity text turns red when outside the 40–60% comfort range
- Theme switches automatically between dark/light based on an ambient light sensor (threshold: 20 lux)

## Prerequisites

- Python 3.10+
- InfluxDB 1.x running at `automation.local:8086` with a `garden` database
- Sensor data in `Telemetry`, `Flowers`, and `illuminationSensor` measurements

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
python app.py
```

The app launches fullscreen with a hidden cursor. Press **Escape** to close.

## Testing

```bash
python -m pytest test_app.py -v
```

## Data Sources (InfluxDB)

| Measurement          | Fields                    | Filter (`alias` tag)                                                        |
|----------------------|---------------------------|-----------------------------------------------------------------------------|
| `Telemetry`          | Temperature, Humidity     | `workRoomTempSensor`, `bedRoomTempSensor`, `livRoomTempSensor`, `SashaRoomTempSensor` |
| `Flowers`            | Moisture                  | `flowerOleandrSensor`, `flowerOlivaSensor`                                  |
| `illuminationSensor` | value                     | —                                                                           |

## Project Structure

```
app.py              # Single-file application
test_app.py         # Pytest test suite
requirements.txt    # Python dependencies
images/             # Light and dark icon variants
CLAUDE.md           # AI assistant context
```