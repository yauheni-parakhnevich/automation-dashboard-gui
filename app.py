import sys
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsColorizeEffect
from PyQt5.QtGui import QColor, QPalette, QFont, QPixmap 

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
        title.setFixedHeight(50)

        titleLayout = QVBoxLayout()
        
        titleLabel = QLabel(widgetTitle)       
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titleFont = QFont("Arial", 24)
        titleFont.setBold(True)        
        titleLabel.setFont(titleFont)
        
        titleLayout.addWidget(titleLabel)

        title.setLayout(titleLayout)

        body = QWidget()
        bodyLayout = QGridLayout()

        labelTemperature = QLabel("24")
        labelTemperature.setAlignment(Qt.AlignmentFlag.AlignCenter)
        labelTemperature.setFont(labelFont)

        labelHumidity = QLabel("33")
        labelHumidity.setAlignment(Qt.AlignmentFlag.AlignCenter)
        labelHumidity.setFont(labelFont)
        
        colorEffect = QGraphicsColorizeEffect()
        colorEffect.setColor(QColor("red"))
        labelHumidity.setGraphicsEffect(colorEffect)

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
        bodyLayout.addWidget(labelTemperature, 0, 1)
        bodyLayout.addWidget(labelHumidity, 1, 1)

        body.setLayout(bodyLayout)

        layout.addWidget(title)
        layout.addWidget(body)

        self.setLayout(layout)

class DashboardLevelWidget(QFrame):
    def __init__(self, widgetTitle, icon):
        super(DashboardLevelWidget, self).__init__()
        labelFont = QFont("Arial", 60)
        labelFont.setBold(True)

        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout()
        
        title = QWidget()
        title.setFixedHeight(50)

        titleLayout = QVBoxLayout()
        
        titleLabel = QLabel(widgetTitle)       
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titleFont = QFont("Arial", 24)
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

        levelPixmap = QPixmap('images/level4.png')
        iconLevel = QLabel()
        iconLevel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        iconLevel.setPixmap(levelPixmap)

        bodyLayout.addWidget(iconLabel)
        bodyLayout.addWidget(iconLevel)

        body.setLayout(bodyLayout)

        layout.addWidget(title)
        layout.addWidget(body)

        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dashboard")

        layout = QGridLayout()

        layout.addWidget(DashboardWidget('КАБИНЕТ'), 0, 0)
        layout.addWidget(DashboardWidget('СПАЛЬНЯ'), 0, 1)
        layout.addWidget(DashboardWidget('ЗАЛ'), 0, 2)
        layout.addWidget(DashboardWidget('ПЕЩЕРА'), 1, 0)
        layout.addWidget(DashboardLevelWidget('ОЛЕАНДР', 'images/oleandr.png'), 1, 1)
        layout.addWidget(DashboardLevelWidget('ОЛИВА', 'images/olive.png'), 1, 2)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
    
app = QApplication(sys.argv)

window = MainWindow()
window.setMinimumSize(1024, 600)
window.show()

app.exec()