import sys
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from PyQt5.QtWidgets import QApplication

# Ensure a QApplication exists before importing widgets
app = QApplication.instance() or QApplication(sys.argv)

from app import (
    format_timestamp,
    Measure,
    Moisture,
    DashboardWidget,
    DashboardLevelWidget,
    MainWindow,
    CONFIG,
)


# ---------------------------------------------------------------------------
# 1. format_timestamp — pure function
# ---------------------------------------------------------------------------

class TestFormatTimestamp:
    def test_utc_z_suffix_winter(self):
        # 2024-01-15 12:30:00 UTC → CET (UTC+1) = 13:30:00
        result = format_timestamp("2024-01-15T12:30:00Z")
        assert result == "13:30:00 15/01/2024"

    def test_utc_offset_suffix_winter(self):
        result = format_timestamp("2024-01-15T12:30:00+00:00")
        assert result == "13:30:00 15/01/2024"

    def test_summer_dst(self):
        # 2024-07-15 12:00:00 UTC → CEST (UTC+2) = 14:00:00
        result = format_timestamp("2024-07-15T12:00:00Z")
        assert result == "14:00:00 15/07/2024"

    def test_winter_no_dst(self):
        # 2024-12-01 08:00:00 UTC → CET (UTC+1) = 09:00:00
        result = format_timestamp("2024-12-01T08:00:00Z")
        assert result == "09:00:00 01/12/2024"

    def test_invalid_string(self):
        assert format_timestamp("not-a-date") == "Invalid timestamp"

    def test_empty_string(self):
        assert format_timestamp("") == "Invalid timestamp"

    def test_none_input(self):
        assert format_timestamp(None) == "Invalid timestamp"


# ---------------------------------------------------------------------------
# 2. Dataclasses
# ---------------------------------------------------------------------------

class TestMeasure:
    def test_defaults(self):
        m = Measure()
        assert m.temperature == 0
        assert m.humidity == 0
        assert m.timestamp == ""

    def test_custom_values(self):
        m = Measure(temperature=22.5, humidity=55.0, timestamp="2024-01-01T00:00:00Z")
        assert m.temperature == 22.5
        assert m.humidity == 55.0
        assert m.timestamp == "2024-01-01T00:00:00Z"


class TestMoisture:
    def test_defaults(self):
        m = Moisture()
        assert m.value == 0
        assert m.timestamp == ""

    def test_custom_values(self):
        m = Moisture(value=7.5, timestamp="2024-06-01T10:00:00Z")
        assert m.value == 7.5
        assert m.timestamp == "2024-06-01T10:00:00Z"


# ---------------------------------------------------------------------------
# 3. DashboardWidget.humidityColor
# ---------------------------------------------------------------------------

class TestHumidityColor:
    @pytest.fixture(autouse=True)
    def widget(self):
        self.w = DashboardWidget("TEST")

    def test_below_40(self):
        assert self.w.humidityColor(39) == "red"

    def test_at_40(self):
        assert self.w.humidityColor(40) == "black"

    def test_mid_range(self):
        assert self.w.humidityColor(50) == "black"

    def test_at_60(self):
        assert self.w.humidityColor(60) == "black"

    def test_above_60(self):
        assert self.w.humidityColor(61) == "red"

    def test_zero(self):
        assert self.w.humidityColor(0) == "red"

    def test_100(self):
        assert self.w.humidityColor(100) == "red"


# ---------------------------------------------------------------------------
# 4. DashboardLevelWidget.getLevelIcon — index logic
# ---------------------------------------------------------------------------

class TestGetLevelIcon:
    @pytest.fixture(autouse=True)
    def widget(self):
        self.w = DashboardLevelWidget("TEST", "images/oleandr.png")

    def test_level_0(self):
        assert self.w.getLevelIcon(0) is self.w.levelIcons[0]

    def test_level_2(self):
        assert self.w.getLevelIcon(2) is self.w.levelIcons[0]

    def test_level_3(self):
        assert self.w.getLevelIcon(3) is self.w.levelIcons[1]

    def test_level_5(self):
        assert self.w.getLevelIcon(5) is self.w.levelIcons[1]

    def test_level_6(self):
        assert self.w.getLevelIcon(6) is self.w.levelIcons[2]

    def test_level_8(self):
        assert self.w.getLevelIcon(8) is self.w.levelIcons[2]

    def test_level_9(self):
        assert self.w.getLevelIcon(9) is self.w.levelIcons[3]

    def test_level_11(self):
        assert self.w.getLevelIcon(11) is self.w.levelIcons[3]

    def test_level_12(self):
        assert self.w.getLevelIcon(12) is self.w.levelIcons[4]

    def test_level_15(self):
        assert self.w.getLevelIcon(15) is self.w.levelIcons[4]


# ---------------------------------------------------------------------------
# 5. DashboardWidget.updateValues — label updates
# ---------------------------------------------------------------------------

class TestDashboardWidgetUpdateValues:
    @pytest.fixture(autouse=True)
    def widget(self):
        self.w = DashboardWidget("TEST")

    def test_labels_update(self):
        self.w.updateValues(23.4, 55, "2024-01-15T12:00:00Z")
        assert self.w.labelTemperature.text() == "23.4"
        assert self.w.labelHumidity.text() == "55"
        assert "13:00:00 15/01/2024" in self.w.timestampLabel.text()


# ---------------------------------------------------------------------------
# 6. MainWindow — InfluxDB methods with mocked client
# ---------------------------------------------------------------------------

@pytest.fixture
def main_window():
    """Create a MainWindow with a mocked InfluxDB client (skip real connection)."""
    with patch("app.InfluxDBClient") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        # Default query returns empty result so __init__'s fetchData/applyTheme don't crash
        mock_client.query.return_value = MagicMock(
            raw={"series": [{"values": [["2024-01-01T00:00:00Z", 100]]}]}
        )
        window = MainWindow()
        yield window, mock_client


class TestGetIllumination:
    def test_returns_value(self, main_window):
        window, mock_client = main_window
        mock_client.query.return_value = MagicMock(
            raw={"series": [{"values": [[None, 42]]}]}
        )
        assert window.getIllumination() == 42

    def test_exception_returns_100(self, main_window):
        window, mock_client = main_window
        mock_client.query.side_effect = Exception("connection error")
        assert window.getIllumination() == 100


class TestGetMeasure:
    def test_returns_measure(self, main_window):
        window, mock_client = main_window
        mock_client.query.return_value = MagicMock(
            raw={
                "series": [
                    {"values": [["2024-01-15T12:00:00Z", 55.0, 22.5]]}
                ]
            }
        )
        m = window.getMeasure("workRoomTempSensor")
        assert isinstance(m, Measure)
        assert m.temperature == 22.5
        assert m.humidity == 55.0
        assert m.timestamp == "2024-01-15T12:00:00Z"

    def test_exception_returns_none(self, main_window):
        window, mock_client = main_window
        mock_client.query.side_effect = Exception("query failed")
        assert window.getMeasure("workRoomTempSensor") is None


class TestGetMoisture:
    def test_returns_moisture(self, main_window):
        window, mock_client = main_window
        mock_client.query.return_value = MagicMock(
            raw={"series": [{"values": [["2024-06-01T10:00:00Z", 7.5]]}]}
        )
        m = window.getMoisture("flowerOleandrSensor")
        assert isinstance(m, Moisture)
        assert m.value == 7.5
        assert m.timestamp == "2024-06-01T10:00:00Z"

    def test_exception_returns_none(self, main_window):
        window, mock_client = main_window
        mock_client.query.side_effect = Exception("query failed")
        assert window.getMoisture("flowerOleandrSensor") is None


class TestFetchData:
    def test_widgets_updated_on_success(self, main_window):
        window, mock_client = main_window

        measure = Measure(temperature=21.0, humidity=50.0, timestamp="2024-01-15T12:00:00Z")
        moisture = Moisture(value=8.0, timestamp="2024-01-15T12:00:00Z")

        with patch.object(window, "getMeasure", return_value=measure), \
             patch.object(window, "getMoisture", return_value=moisture):
            window.fetchData()

        assert window.widgets["workRoom"].labelTemperature.text() == "21.0"
        assert window.widgets["workRoom"].labelHumidity.text() == "50.0"

    def test_widgets_not_updated_on_none(self, main_window):
        window, mock_client = main_window

        # Store original text
        orig_temp = window.widgets["workRoom"].labelTemperature.text()

        with patch.object(window, "getMeasure", return_value=None), \
             patch.object(window, "getMoisture", return_value=None):
            window.fetchData()

        # Labels should remain unchanged
        assert window.widgets["workRoom"].labelTemperature.text() == orig_temp


class TestApplyTheme:
    def test_dark_theme_below_threshold(self, main_window):
        window, mock_client = main_window

        with patch.object(window, "getIllumination", return_value=10), \
             patch.object(window, "setDarkTheme") as mock_dark, \
             patch.object(window, "setLightTheme") as mock_light:
            window.applyTheme()
            mock_dark.assert_called_once()
            mock_light.assert_not_called()

    def test_light_theme_at_threshold(self, main_window):
        window, mock_client = main_window

        with patch.object(window, "getIllumination", return_value=CONFIG["ILLUMINATION_THRESHOLD"]), \
             patch.object(window, "setDarkTheme") as mock_dark, \
             patch.object(window, "setLightTheme") as mock_light:
            window.applyTheme()
            mock_light.assert_called_once()
            mock_dark.assert_not_called()

    def test_light_theme_above_threshold(self, main_window):
        window, mock_client = main_window

        with patch.object(window, "getIllumination", return_value=50), \
             patch.object(window, "setDarkTheme") as mock_dark, \
             patch.object(window, "setLightTheme") as mock_light:
            window.applyTheme()
            mock_light.assert_called_once()
            mock_dark.assert_not_called()
