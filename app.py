from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
import logging
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
        self.labelTemperature.setText(str(temperature))
        self.labelHumidity.setText(str(humidity))

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

        layout.addWidget(self.widgets['workRoom'], 0, 0)
        layout.addWidget(self.widgets['bedRoom'], 0, 1)
        layout.addWidget(self.widgets['livRoom'], 0, 2)
        layout.addWidget(self.widgets['SashaRoom'], 1, 0)

        self.widgets['flowerOleandrSensor'] = DashboardLevelWidget('ОЛЕАНДР', 'images/oleandr.png')
        self.widgets['flowerOlivaSensor'] = DashboardLevelWidget('ОЛИВА', 'images/olive.png')

        layout.addWidget(self.widgets['flowerOleandrSensor'], 1, 1)
        layout.addWidget(self.widgets['flowerOlivaSensor'], 1, 2)

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

            if workRoom:
                self.widgets['workRoom'].updateValues(workRoom.temperature, workRoom.humidity, workRoom.timestamp)
            if livRoom:
                self.widgets['livRoom'].updateValues(livRoom.temperature, livRoom.humidity, livRoom.timestamp)
            if SashaRoom:
                self.widgets['SashaRoom'].updateValues(SashaRoom.temperature, SashaRoom.humidity, SashaRoom.timestamp)
            if bedRoom:
                self.widgets['bedRoom'].updateValues(bedRoom.temperature, bedRoom.humidity, bedRoom.timestamp)

            oleandrMoisture = self.getMoisture('flowerOleandrSensor')
            olivaMoisture = self.getMoisture('flowerOlivaSensor')

            if oleandrMoisture:
                self.widgets['flowerOleandrSensor'].updateValues(oleandrMoisture.value, oleandrMoisture.timestamp)
            if olivaMoisture:
                self.widgets['flowerOlivaSensor'].updateValues(olivaMoisture.value, olivaMoisture.timestamp)

            temperature = [
                workRoom.temperature if workRoom else None,
                bedRoom.temperature if bedRoom else None,
                livRoom.temperature if livRoom else None,
                SashaRoom.temperature if SashaRoom else None,
            ]
            humidity = [
                workRoom.humidity if workRoom else None,
                bedRoom.humidity if bedRoom else None,
                livRoom.humidity if livRoom else None,
                SashaRoom.humidity if SashaRoom else None,
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
