import os
import sys
from PyQt6.QtWidgets import QTabWidget, QMainWindow, QApplication
from PyQt6 import uic

from src.GUI_v2.tabs.main_monitor import MainMonitorTab
# from src.GUI_v2.tabs.sensors import SensorsTab

current_dir = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(current_dir, "gui_main.ui")
Ui_main, QWidgetBase = uic.loadUiType(ui_file)

class StoreWorldMain(QMainWindow, Ui_main):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.tabWidget = self.findChild(QTabWidget, "tabmain")
        self.initTabs()
    
    def initTabs(self):
        while self.tabWidget.count() > 0:
            self.tabWidget.removeTab(0)

        self.monitor_tab = MainMonitorTab()
        self.tabWidget.addTab(self.monitor_tab, "Main Monitoring")

        # self.sensor_tab = SensorsTab()
        # self.tabWidget.addTab(self.sensor_tab, "Sensor Tab")

    def closeEvent(self, event):
        """
        메인 윈도우가 닫힐 때 TCP 클라이언트 스레드를 안전하게 종료합니다.
        """
        print("Closing application and stopping TCP client...")
        self.monitor_tab.stop_tcp_client()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = StoreWorldMain()
    myWindows.show()
    
    sys.exit(app.exec())