import sys
from PyQt6 import uic
from PyQt6 import QtGui
# from PyQt6.QtGui import QColor, QPainter, QFont
from PyQt6.QtGui import *
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import *

from src.lib.sector_library import *

# from PyQt6.QtWidgets import QApplication, QDialog, QWidget, QVBoxLayout
# from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
# from PyQt6.QtCore import Qt, QTimer, QRectF

Ui_MainMonitorTab, QWidgetBase = uic.loadUiType("tab_main_monitor.ui")

class MainMonitorTab(QWidget, Ui_MainMonitorTab): # QWidget과 UI 폼 클래스를 상속
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.pixmap = QtGui.QPixmap(self.sensor_status.width(), self.sensor_status.height())
        self.pixmap.fill(Qt.GlobalColor.white)
        self.sensor_status.setPixmap(self.pixmap)
        self.draw()

        # 초기 센서 상태 설정
        self.receive_sensor_status = 'R'
        self.shipping_sensor_status = 'R'
        self.r_status = 'R'
        self.y_status = 'R'
        self.g_status = 'R'

        # 상태별 색상 맵핑
        self.status_colors = {
            'R': QColor(255, 107, 107),  # Red: 센서 이상
            'Y': QColor(255, 229, 107),  # Yellow: 센서 사용중
            'G': QColor(107, 255, 139)   # Green: 센서 사용 가능
        }

    def update_statuses(self, r_status, y_status, g_status):
        """
        외부에서 각 구역의 센서 상태를 업데이트하는 메서드
        """
        self.r_status = r_status
        self.y_status = y_status
        self.g_status = g_status
        self.update()  # 위젯을 다시 그리도록 요청 (paintEvent 호출)

    def draw(self):
        """
        위젯에 다이어그램을 그리는 메서드
        """
        pixmap = self.sensor_status.pixmap()
        painter = QPainter(pixmap)

        painter.setPen(QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.SolidLine))
        # painter.drawEllipse(70, 70, 70, 70)
        radius = 40
        
        # painter.setBrush(QBrush(Qt.GlobalColor.))
        painter.drawEllipse(210 - radius, 90 - radius, 80, 80) # x, y, w, h
        painter.drawEllipse(210 - radius, 370 - radius, 80, 80)
        painter.drawEllipse(210 - radius, 230 - radius, 80, 80)

        painter.drawEllipse(70 - radius, 230 - radius, 80, 80)
        painter.drawEllipse(350 - radius, 230 - radius, 80, 80)

        painter.end()
        self.sensor_status.setPixmap(pixmap)

    # # 모든 구역 그래픽 그리기
    # def draw_all_sector(self):
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = MainMonitorTab()
    myWindows.show()
    
    sys.exit(app.exec())