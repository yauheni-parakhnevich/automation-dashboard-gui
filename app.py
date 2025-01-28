from datetime import datetime, timezone, timedelta
import sys
import requests
import logging
from influxdb import InfluxDBClient
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsColorizeEffect
from PyQt5.QtGui import QColor, QPalette, QFont, QPixmap 

class Color(QFrame):
    def __init__(self, color):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

class Measure:
    temperature = 0
    humidity = 0
    timestamp = 0

class Moisture:
    value = 0
    timestamp = 0

class DashboardWidget(QFrame):
    def __init__(self, widgetTitle):
        super(DashboardWidget, self).__init__()
        labelFont = QFont("Arial", 70)
        labelFont.setBold(True)

        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout()
        
        title = QWidget()
        title.setFixedHeight(80)

        titleLayout = QVBoxLayout()
        
        titleLabel = QLabel(widgetTitle)       
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titleFont = QFont("Arial", 50)
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
        
        colorEffect = QGraphicsColorizeEffect()
        colorEffect.setColor(QColor("red"))
        self.labelHumidity.setGraphicsEffect(colorEffect)

        temperaturePixmap = QPixmap('images/temperature.png')
        temperatureIcon = QLabel()
        temperatureIcon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        temperatureIcon.setPixmap(temperaturePixmap)

        humidityPixmap = QPixmap('images/humidity.png')
        humidityIcon = QLabel()
        humidityIcon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        humidityIcon.setPixmap(humidityPixmap)

        bodyLayout.addWidget(temperatureIcon, 0, 0)
        bodyLayout.addWidget(humidityIcon, 1, 0)
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

        colorEffect = QGraphicsColorizeEffect()
        colorEffect.setColor(QColor(self.humidityColor(humidity)))
        self.labelHumidity.setGraphicsEffect(colorEffect)        

        # Ensure timestamp is an integer
        try:
            # Parse the ISO 8601 timestamp
            if timestamp_iso.endswith("Z"):
                timestamp_iso = timestamp_iso.replace("Z", "+00:00")  # Convert Z to +00:00 for UTC
            utc_time = datetime.fromisoformat(timestamp_iso)            
            zurich_time = utc_time.astimezone(tz=timezone(timedelta(hours=1)))  # Adjust for Zurich timezone
            formatted_time = zurich_time.strftime("%H:%M:%S %d/%m/%Y")
            
            # Update timestamp label
            self.timestampLabel.setText(f"Last updated: {formatted_time}")        
        except ValueError:
            self.timestampLabel.setText("Last updated: Invalid timestamp")
            return
        
    def humidityColor(self, humidity):
        if humidity < 40 or humidity > 60:
            return 'red'
        else:
            return 'black'

class DashboardLevelWidget(QFrame):
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
        titleFont = QFont("Arial", 50)
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

        self.levelIcons = []
        self.levelIcons.append(QPixmap('images/level1.png'))
        self.levelIcons.append(QPixmap('images/level2.png'))
        self.levelIcons.append(QPixmap('images/level3.png'))
        self.levelIcons.append(QPixmap('images/level4.png'))
        self.levelIcons.append(QPixmap('images/level5.png'))        

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
        #self.labelTemperature.setText(str(temperature))
        #self.labelHumidity.setText(str(humidity))
        self.iconLevel.setPixmap(self.getLevelIcon(value))

        # Ensure timestamp is an integer
        try:
            # Parse the ISO 8601 timestamp
            if timestamp_iso.endswith("Z"):
                timestamp_iso = timestamp_iso.replace("Z", "+00:00")  # Convert Z to +00:00 for UTC
            utc_time = datetime.fromisoformat(timestamp_iso)            
            zurich_time = utc_time.astimezone(tz=timezone(timedelta(hours=1)))  # Adjust for Zurich timezone
            formatted_time = zurich_time.strftime("%H:%M:%S %d/%m/%Y")
            
            # Update timestamp label
            self.timestampLabel.setText(f"Last updated: {formatted_time}")        
        except ValueError:
            self.timestampLabel.setText("Last updated: Invalid timestamp")
            return    
        
    def getLevelIcon(self, level):
        if level < 10:
            return self.levelIcons[0]
        elif level < 13:
            return self.levelIcons[1]
        elif level < 16:
            return self.levelIcons[2]    
        elif level < 19:
            return self.levelIcons[3]
        else:
            return self.levelIcons[4]

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dashboard")
        self.widgets = {}

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
        self.client = InfluxDBClient(host='automation.lan', port=8086)
        self.client.switch_database('garden')

        self.fetchData()

        # Start a timer to fetch data every 5 minutes
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fetchData)
        self.timer.start(300000)  # 5 minutes in milliseconds
        #self.timer.start(30000)

    def getMoisture(self, alias):
        #results = self.client.query('select last("Moisture") from "Flowers" where alias = \'' + alias + '\'')
        results = self.client.query('SELECT time, Moisture FROM Flowers WHERE alias = \'' + alias + '\'  ORDER BY time desc LIMIT 1')

        moisture = Moisture()
        moisture.value = results.raw['series'][0]['values'][0][1]
        moisture.timestamp = results.raw['series'][0]['values'][0][0]

        return moisture

    def getMeasure(self, alias):
        #results = self.client.query('select last("Temperature") as temperature,last( "Humidity") as humidity from Telemetry where alias = \'' + alias + '\'')
        results = self.client.query('SELECT time, Humidity, Temperature FROM Telemetry WHERE alias = \'' + alias + '\'  ORDER BY time desc LIMIT 1')
        
        measure = Measure()
        measure.temperature = results.raw['series'][0]['values'][0][2]
        measure.humidity = results.raw['series'][0]['values'][0][1]
        measure.timestamp = results.raw['series'][0]['values'][0][0]
        
        #logging.info("Measure")
        #logging.info(measure.timestamp)
        
        return measure

    def fetchData(self):
        try:
            logging.info("Reading measures")
            workRoom = self.getMeasure('workRoomTempSensor')
            livRoom = self.getMeasure('livRoomTempSensor')
            SashaRoom = self.getMeasure('SashaRoomTempSensor')
            bedRoom = self.getMeasure('bedRoomTempSensor')

            self.widgets['workRoom'].updateValues(workRoom.temperature, workRoom.humidity, workRoom.timestamp)
            self.widgets['livRoom'].updateValues(livRoom.temperature, livRoom.humidity, livRoom.timestamp)
            self.widgets['SashaRoom'].updateValues(SashaRoom.temperature, SashaRoom.humidity, SashaRoom.timestamp)
            self.widgets['bedRoom'].updateValues(bedRoom.temperature, bedRoom.humidity, bedRoom.timestamp)

            oleandrMoisture = self.getMoisture('flowerOleandrSensor')
            olivaMoisture = self.getMoisture('flowerOlivaSensor')

            self.widgets['flowerOleandrSensor'].updateValues(oleandrMoisture.value, oleandrMoisture.timestamp)
            self.widgets['flowerOlivaSensor'].updateValues(olivaMoisture.value, workRoom.timestamp)

            temperature = [workRoom.temperature, bedRoom.temperature, livRoom.temperature, SashaRoom.temperature]
            humidity = [workRoom.humidity, bedRoom.humidity, livRoom.humidity, SashaRoom.humidity]
            flowers = [oleandrMoisture.value, olivaMoisture.value]

            logging.info("Temperature")
            logging.info(temperature)

            logging.info("Humidity")
            logging.info(humidity)

            logging.info("Flowers")
            logging.info(flowers)
        except Exception as e:
            print(f"Exception occurred: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

app = QApplication(sys.argv)

window = MainWindow()
#window.setMinimumSize(1366, 768)
window.show()
window.showFullScreen()

app.exec()