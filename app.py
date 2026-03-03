from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
import logging
import requests
from influxdb import InfluxDBClient
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsColorizeEffect
from PyQt5.QtGui import QColor, QPalette, QFont, QPixmap

CONFIG = {
    'INFLUXDB_HOST': 'automation.local',
    'INFLUXDB_PORT': 8086,
    'INFLUXDB_DATABASE': 'garden',
    'DATA_REFRESH_INTERVAL_MS': 300000,
    'THEME_CHECK_INTERVAL_MS': 60000,
    'ILLUMINATION_THRESHOLD': 20,
    'OPEN_METEO_URL': 'https://api.open-meteo.com/v1/forecast',
    'OPEN_METEO_PARAMS': {
        'latitude': 47.3967,
        'longitude': 8.4478,
        'daily': 'temperature_2m_max,temperature_2m_min,weathercode',
        'timezone': 'Europe/Zurich',
        'forecast_days': 5,
    },
}

ZURICH_TZ = ZoneInfo("Europe/Zurich")


def format_timestamp(timestamp_iso):
    """Parse an ISO 8601 timestamp and return a formatted Zurich-time string."""
    try:
        if timestamp_iso.endswith("Z"):
            timestamp_iso = timestamp_iso.replace("Z", "+00:00")
        utc_time = datetime.fromisoformat(timestamp_iso)
        zurich_time = utc_time.astimezone(tz=ZURICH_TZ)
        return zurich_time.strftime("%H:%M:%S %d/%m/%Y")
    except (ValueError, AttributeError) as e:
        logging.error("Invalid timestamp format: %s", timestamp_iso)
        return "Invalid timestamp"


@dataclass
class Measure:
    temperature: float = 0
    humidity: float = 0
    timestamp: str = ""


@dataclass
class Moisture:
    value: float = 0
    timestamp: str = ""


@dataclass
class DayForecast:
    date: str = ""
    temp_max: float = 0
    temp_min: float = 0
    weathercode: int = 0


class Color(QFrame):
    def __init__(self, color):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

class DashboardWidget(QFrame):
    def __init__(self, widgetTitle):
        super(DashboardWidget, self).__init__()
        labelFont = QFont("Arial", 60)
        labelFont.setBold(True)

        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout()

        title = QWidget()
        title.setFixedHeight(80)

        titleLayout = QVBoxLayout()

        titleLabel = QLabel(widgetTitle)
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titleFont = QFont("Arial", 40)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)

        titleLayout.addWidget(titleLabel)

        title.setLayout(titleLayout)

        body = QWidget()
        bodyLayout = QGridLayout()

        self.labelTemperature = QLabel("36")
        self.labelTemperature.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.labelTemperature.setFont(labelFont)

        self.labelHumidity = QLabel("45")
        self.labelHumidity.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.labelHumidity.setFont(labelFont)

        self.colorEffect = QGraphicsColorizeEffect()
        self.colorEffect.setColor(QColor("red"))
        self.labelHumidity.setGraphicsEffect(self.colorEffect)

        # Preload light and dark pixmaps
        self.temperaturePixmap_light = QPixmap('images/temperature.png')
        self.temperaturePixmap_dark = QPixmap('images/temperature_dark.png')
        self.humidityPixmap_light = QPixmap('images/humidity.png')
        self.humidityPixmap_dark = QPixmap('images/humidity_dark.png')

        self.temperatureIcon = QLabel()
        self.temperatureIcon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temperatureIcon.setPixmap(self.temperaturePixmap_light)

        self.humidityIcon = QLabel()
        self.humidityIcon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.humidityIcon.setPixmap(self.humidityPixmap_light)

        bodyLayout.addWidget(self.temperatureIcon, 0, 0)
        bodyLayout.addWidget(self.humidityIcon, 1, 0)
        bodyLayout.addWidget(self.labelTemperature, 0, 1)
        bodyLayout.addWidget(self.labelHumidity, 1, 1)

        body.setLayout(bodyLayout)

        # Timestamp section
        self.timestampLabel = QLabel("Last updated: --:--:-- --/--/----")
        self.timestampLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timestampFont = QFont("Arial", 10)
        self.timestampLabel.setFont(timestampFont)

        layout.addWidget(title)
        layout.addWidget(body)
        layout.addWidget(self.timestampLabel)

        self.setLayout(layout)

    def updateValues(self, temperature, humidity, timestamp_iso):
        self.labelTemperature.setText(f"{temperature:.1f}")
        self.labelHumidity.setText(f"{humidity:.1f}")

        self.colorEffect = QGraphicsColorizeEffect()
        self.colorEffect.setColor(QColor(self.humidityColor(humidity)))
        self.labelHumidity.setGraphicsEffect(self.colorEffect)

        formatted = format_timestamp(timestamp_iso)
        self.timestampLabel.setText(f"Last updated: {formatted}")

    def humidityColor(self, humidity):
        if humidity < 40 or humidity > 60:
            return 'red'
        else:
            return 'black'

    def setDarkTheme(self):
        self.temperatureIcon.setPixmap(self.temperaturePixmap_dark)
        self.humidityIcon.setPixmap(self.humidityPixmap_dark)

    def setLightTheme(self):
        self.temperatureIcon.setPixmap(self.temperaturePixmap_light)
        self.humidityIcon.setPixmap(self.humidityPixmap_light)

class DashboardLevelWidget(QFrame):
    currentLevel = 0
    currentTimestamp = ""

    def __init__(self, widgetTitle, icon):
        super(DashboardLevelWidget, self).__init__()
        labelFont = QFont("Arial", 70)
        labelFont.setBold(True)

        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout()

        title = QWidget()
        title.setFixedHeight(80)

        titleLayout = QVBoxLayout()

        titleLabel = QLabel(widgetTitle)
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titleFont = QFont("Arial", 40)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)

        titleLayout.addWidget(titleLabel)

        title.setLayout(titleLayout)

        body = QWidget()
        bodyLayout = QHBoxLayout()

        iconPixmap = QPixmap(icon)
        iconLabel = QLabel()
        iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        iconLabel.setPixmap(iconPixmap)

        self.levelIcons_light = []
        self.levelIcons_light.append(QPixmap('images/level1.png'))
        self.levelIcons_light.append(QPixmap('images/level2.png'))
        self.levelIcons_light.append(QPixmap('images/level3.png'))
        self.levelIcons_light.append(QPixmap('images/level4.png'))
        self.levelIcons_light.append(QPixmap('images/level5.png'))

        self.levelIcons_dark = []
        self.levelIcons_dark.append(QPixmap('images/level1_dark.png'))
        self.levelIcons_dark.append(QPixmap('images/level2_dark.png'))
        self.levelIcons_dark.append(QPixmap('images/level3_dark.png'))
        self.levelIcons_dark.append(QPixmap('images/level4_dark.png'))
        self.levelIcons_dark.append(QPixmap('images/level5_dark.png'))

        self.levelIcons = self.levelIcons_light

        levelPixmap = self.levelIcons[0]
        self.iconLevel = QLabel()
        self.iconLevel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.iconLevel.setPixmap(levelPixmap)

        bodyLayout.addWidget(iconLabel)
        bodyLayout.addWidget(self.iconLevel)

        body.setLayout(bodyLayout)

        # Timestamp section
        self.timestampLabel = QLabel("Last updated: --:--:-- --/--/----")
        self.timestampLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timestampFont = QFont("Arial", 10)
        self.timestampLabel.setFont(timestampFont)

        layout.addWidget(title)
        layout.addWidget(body)
        layout.addWidget(self.timestampLabel)

        self.setLayout(layout)

    def updateValues(self, value, timestamp_iso):
        self.iconLevel.setPixmap(self.getLevelIcon(value))

        self.currentLevel = value
        self.currentTimestamp = timestamp_iso

        formatted = format_timestamp(timestamp_iso)
        self.timestampLabel.setText(f"Last updated: {formatted}")

    def getLevelIcon(self, level):
        if level < 3:
            return self.levelIcons[0]
        elif level < 6:
            return self.levelIcons[1]
        elif level < 9:
            return self.levelIcons[2]
        elif level < 12:
            return self.levelIcons[3]
        else:
            return self.levelIcons[4]

    def setDarkTheme(self):
        self.levelIcons = self.levelIcons_dark
        self.updateValues(self.currentLevel, self.currentTimestamp)

    def setLightTheme(self):
        self.levelIcons = self.levelIcons_light
        self.updateValues(self.currentLevel, self.currentTimestamp)

WMO_DESCRIPTIONS = {
    0: "Klar", 1: "Klar", 2: "Bewölkt", 3: "Bewölkt",
    45: "Nebel", 48: "Nebel",
    51: "Nieselregen", 53: "Nieselregen", 55: "Nieselregen",
    56: "Nieselregen", 57: "Nieselregen",
    61: "Regen", 63: "Regen", 65: "Regen",
    66: "Regen", 67: "Regen",
    71: "Schnee", 73: "Schnee", 75: "Schnee", 77: "Schnee",
    80: "Schauer", 81: "Schauer", 82: "Schauer",
    85: "Schnee", 86: "Schnee",
    95: "Gewitter", 96: "Gewitter", 99: "Gewitter",
}

GERMAN_DAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


class DashboardWeatherWidget(QFrame):
    def __init__(self):
        super(DashboardWeatherWidget, self).__init__()

        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout()

        title = QWidget()
        title.setFixedHeight(80)
        titleLayout = QVBoxLayout()
        titleLabel = QLabel("ПРОГНОЗ")
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titleFont = QFont("Arial", 40)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLayout.addWidget(titleLabel)
        title.setLayout(titleLayout)

        body = QWidget()
        bodyLayout = QGridLayout()

        dayFont = QFont("Arial", 24)
        dayFont.setBold(True)
        tempFont = QFont("Arial", 24)
        condFont = QFont("Arial", 20)

        self.dayLabels = []
        self.tempLabels = []
        self.condLabels = []

        for i in range(5):
            dayLabel = QLabel("--")
            dayLabel.setFont(dayFont)
            dayLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

            tempLabel = QLabel("--° / --°")
            tempLabel.setFont(tempFont)
            tempLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

            condLabel = QLabel("--")
            condLabel.setFont(condFont)
            condLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

            bodyLayout.addWidget(dayLabel, i, 0)
            bodyLayout.addWidget(tempLabel, i, 1)
            bodyLayout.addWidget(condLabel, i, 2)

            self.dayLabels.append(dayLabel)
            self.tempLabels.append(tempLabel)
            self.condLabels.append(condLabel)

        body.setLayout(bodyLayout)

        self.timestampLabel = QLabel("Last updated: --:--:-- --/--/----")
        self.timestampLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timestampFont = QFont("Arial", 10)
        self.timestampLabel.setFont(timestampFont)

        layout.addWidget(title)
        layout.addWidget(body)
        layout.addWidget(self.timestampLabel)

        self.setLayout(layout)

    def updateValues(self, forecasts):
        for i, fc in enumerate(forecasts[:5]):
            date = datetime.strptime(fc.date, "%Y-%m-%d")
            day_name = GERMAN_DAYS[date.weekday()]
            self.dayLabels[i].setText(day_name)
            self.tempLabels[i].setText(f"{fc.temp_min:.0f}° / {fc.temp_max:.0f}°")
            self.condLabels[i].setText(WMO_DESCRIPTIONS.get(fc.weathercode, "?"))

        now = datetime.now(tz=ZURICH_TZ)
        self.timestampLabel.setText(f"Last updated: {now.strftime('%H:%M:%S %d/%m/%Y')}")

    def setDarkTheme(self):
        pass

    def setLightTheme(self):
        pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dashboard")
        self.widgets = {}
        self.client = None

        layout = QGridLayout()

        self.widgets['workRoom'] = DashboardWidget('КАБИНЕТ')
        self.widgets['bedRoom'] = DashboardWidget('СПАЛЬНЯ')
        self.widgets['livRoom'] = DashboardWidget('ЗАЛ')
        self.widgets['SashaRoom'] = DashboardWidget('ПЕЩЕРА')

        self.widgets['outdoor'] = DashboardWidget('БАЛКОН')

        layout.addWidget(self.widgets['workRoom'], 0, 0)
        layout.addWidget(self.widgets['bedRoom'], 0, 1)
        layout.addWidget(self.widgets['livRoom'], 0, 2)
        layout.addWidget(self.widgets['SashaRoom'], 0, 3)

        self.widgets['flowerOleandrSensor'] = DashboardLevelWidget('ОЛЕАНДР', 'images/oleandr.png')
        self.widgets['flowerOlivaSensor'] = DashboardLevelWidget('ОЛИВА', 'images/olive.png')

        self.widgets['weather'] = DashboardWeatherWidget()

        layout.addWidget(self.widgets['outdoor'], 1, 0)
        layout.addWidget(self.widgets['flowerOleandrSensor'], 1, 1)
        layout.addWidget(self.widgets['flowerOlivaSensor'], 1, 2)
        layout.addWidget(self.widgets['weather'], 1, 3)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        logging.basicConfig(level=logging.DEBUG)

        logging.info("Connecting to the database")
        try:
            self.client = InfluxDBClient(
                host=CONFIG['INFLUXDB_HOST'],
                port=CONFIG['INFLUXDB_PORT'],
            )
            self.client.switch_database(CONFIG['INFLUXDB_DATABASE'])
        except Exception as e:
            logging.error("Failed to connect to InfluxDB: %s", e)

        self.fetchData()

        # Start a timer to fetch data every 5 minutes
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fetchData)
        self.timer.start(CONFIG['DATA_REFRESH_INTERVAL_MS'])

        # Set up theme change timer
        self.theme_timer = QTimer(self)
        self.theme_timer.timeout.connect(self.applyTheme)
        self.theme_timer.start(CONFIG['THEME_CHECK_INTERVAL_MS'])
        self.applyTheme()

    def applyTheme(self):
        illumination = self.getIllumination()
        if illumination < CONFIG['ILLUMINATION_THRESHOLD']:
            self.setDarkTheme()
        else:
            self.setLightTheme()

    def setDarkTheme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(45, 45, 45))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        QApplication.instance().setPalette(palette)

        for key in self.widgets:
            self.widgets[key].setDarkTheme()

    def setLightTheme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(255, 255, 255))
        palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        QApplication.instance().setPalette(palette)

        for key in self.widgets:
            self.widgets[key].setLightTheme()

    def getIllumination(self):
        try:
            results = self.client.query('SELECT value FROM illuminationSensor ORDER BY time DESC LIMIT 1')
            return results.raw['series'][0]['values'][0][1]
        except Exception as e:
            logging.error("Failed to read illumination: %s", e)
            return 100  # Default to light theme

    def getWeather(self):
        try:
            response = requests.get(
                CONFIG['OPEN_METEO_URL'],
                params=CONFIG['OPEN_METEO_PARAMS'],
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            daily = data['daily']
            forecasts = []
            for i in range(len(daily['time'])):
                forecasts.append(DayForecast(
                    date=daily['time'][i],
                    temp_max=daily['temperature_2m_max'][i],
                    temp_min=daily['temperature_2m_min'][i],
                    weathercode=daily['weathercode'][i],
                ))
            return forecasts
        except Exception as e:
            logging.error("Failed to fetch weather: %s", e)
            return None

    def getMoisture(self, alias):
        try:
            results = self.client.query('SELECT time, Moisture FROM Flowers WHERE alias = \'' + alias + '\'  ORDER BY time desc LIMIT 1')
            moisture = Moisture()
            moisture.value = results.raw['series'][0]['values'][0][1]
            moisture.timestamp = results.raw['series'][0]['values'][0][0]
            return moisture
        except Exception as e:
            logging.error("Failed to read moisture for %s: %s", alias, e)
            return None

    def getMeasure(self, alias):
        try:
            results = self.client.query('SELECT time, Humidity, Temperature FROM Telemetry WHERE alias = \'' + alias + '\'  ORDER BY time desc LIMIT 1')
            measure = Measure()
            measure.temperature = results.raw['series'][0]['values'][0][2]
            measure.humidity = results.raw['series'][0]['values'][0][1]
            measure.timestamp = results.raw['series'][0]['values'][0][0]
            return measure
        except Exception as e:
            logging.error("Failed to read measure for %s: %s", alias, e)
            return None

    def fetchData(self):
        try:
            logging.info("Reading measures")
            workRoom = self.getMeasure('workRoomTempSensor')
            livRoom = self.getMeasure('livRoomTempSensor')
            SashaRoom = self.getMeasure('SashaRoomTempSensor')
            bedRoom = self.getMeasure('bedRoomTempSensor')
            outdoor = self.getMeasure('outdoorTemperatureSensor')

            if workRoom:
                self.widgets['workRoom'].updateValues(workRoom.temperature, workRoom.humidity, workRoom.timestamp)
            if livRoom:
                self.widgets['livRoom'].updateValues(livRoom.temperature, livRoom.humidity, livRoom.timestamp)
            if SashaRoom:
                self.widgets['SashaRoom'].updateValues(SashaRoom.temperature, SashaRoom.humidity, SashaRoom.timestamp)
            if bedRoom:
                self.widgets['bedRoom'].updateValues(bedRoom.temperature, bedRoom.humidity, bedRoom.timestamp)
            if outdoor:
                self.widgets['outdoor'].updateValues(outdoor.temperature, outdoor.humidity, outdoor.timestamp)

            oleandrMoisture = self.getMoisture('flowerOleandrSensor')
            olivaMoisture = self.getMoisture('flowerOlivaSensor')

            if oleandrMoisture:
                self.widgets['flowerOleandrSensor'].updateValues(oleandrMoisture.value, oleandrMoisture.timestamp)
            if olivaMoisture:
                self.widgets['flowerOlivaSensor'].updateValues(olivaMoisture.value, olivaMoisture.timestamp)

            forecasts = self.getWeather()
            if forecasts:
                self.widgets['weather'].updateValues(forecasts)

            temperature = [
                workRoom.temperature if workRoom else None,
                bedRoom.temperature if bedRoom else None,
                livRoom.temperature if livRoom else None,
                SashaRoom.temperature if SashaRoom else None,
                outdoor.temperature if outdoor else None,
            ]
            humidity = [
                workRoom.humidity if workRoom else None,
                bedRoom.humidity if bedRoom else None,
                livRoom.humidity if livRoom else None,
                SashaRoom.humidity if SashaRoom else None,
                outdoor.humidity if outdoor else None,
            ]
            flowers = [
                oleandrMoisture.value if oleandrMoisture else None,
                olivaMoisture.value if olivaMoisture else None,
            ]

            logging.info("Temperature")
            logging.info(temperature)

            logging.info("Humidity")
            logging.info(humidity)

            logging.info("Flowers")
            logging.info(flowers)
        except Exception as e:
            logging.error(f"Exception occurred: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    window.showFullScreen()

    # Hide mouse cursor
    window.setCursor(QCursor(Qt.BlankCursor))

    app.exec()
