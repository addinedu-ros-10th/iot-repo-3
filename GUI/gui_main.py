import os
import sys
from PyQt6.QtWidgets import QTabWidget, QMainWindow, QApplication
from PyQt6 import uic

from GUI.tabs.main_monitor import MainMonitorTab
from GUI.tabs.simple_monitor import SimpleMonitorTab
from GUI.tabs.system_manage import SystemManageTab
from GUI.client.tcp_client import stop_tcp_client

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

        # 기존 복잡한 모니터 탭
        self.monitor_tab = MainMonitorTab()
        self.tabWidget.addTab(self.monitor_tab, "복합 모니터")
        
        # 새로운 간단한 모니터 탭 (LMS 분리 버전)
        self.simple_monitor_tab = SimpleMonitorTab()
        self.tabWidget.addTab(self.simple_monitor_tab, "LMS 모니터")
        
        # 시스템 관리 탭
        self.system_manage_tab = SystemManageTab()
        self.tabWidget.addTab(self.system_manage_tab, "시스템 관리")

        # self.sensor_tab = SensorsTab()
        # self.tabWidget.addTab(self.sensor_tab, "Sensor Tab")

    def closeEvent(self, event):
        """
        메인 윈도우가 닫힐 때 TCP 클라이언트 스레드를 안전하게 종료합니다.
        """
        print("Closing application and stopping TCP clients...")
        
        # 기존 모니터 탭의 TCP 클라이언트 중지
        self.monitor_tab.stop_tcp_client()
        
        # 새로운 LMS TCP 클라이언트 중지
        stop_tcp_client()
        
        # 시스템 관리 탭의 상태 모니터링 중지
        self.system_manage_tab.stop_status_monitoring()
        
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = StoreWorldMain()
    myWindows.show()
    
    sys.exit(app.exec())