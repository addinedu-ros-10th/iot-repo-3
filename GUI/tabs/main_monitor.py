import os
import sys
import socket
import struct
import time
from PyQt6 import uic, QtGui
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont, QPolygon
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint

from stw_lib.sector_manager2 import SectorName, SectorStatus, SectorManager

'''
1. 로봇 상태와, 서버의 로봇 위치 연동
    - ()
'''

# --- UI 파일 로드 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(current_dir, "main_monitor.ui")
Ui_Tab, QWidgetBase = uic.loadUiType(ui_file)

# --- TCP 클라이언트 스레드 ---
class TCPClientThread(QThread):
    """
    백그라운드에서 TCP 서버와 통신하여 재고 정보를 주기적으로 요청하고,
    결과를 GUI로 전달하는 스레드.
    """
    # 재고 정보 업데이트를 위한 시그널 (리스트 형태의 재고 데이터 전달)
    stock_updated = pyqtSignal(list)
    # 연결 상태 업데이트를 위한 시그널 (문자열 메시지 전달)
    connection_status = pyqtSignal(str)

    def __init__(self, host, port, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port
        self._is_running = True

    def run(self):
        """스레드 실행 함수"""
        while self._is_running:
            try:
                self.connection_status.emit("서버에 연결 중...")
                with socket.create_connection((self.host, self.port), timeout=5) as sock:
                    self.connection_status.emit(f"서버 연결 성공 ({self.host}:{self.port})")
                    while self._is_running:
                        # 'AI' (All Inventory) 명령어 전송 요청 (서버에서 AI 명령어를 사용)
                        request = b'AI\x00\x00\x00\x00\n'
                        sock.sendall(request)
                        
                        # --- 응답 수신 ---
                        # Command (2) + Status (1)
                        header = sock.recv(3)
                        if not header or len(header) != 3:
                            break

                        cmd, status_code = header[:2].decode('ascii'), header[2]

                        # 성공(0x00) 응답이 아니면 데이터 처리 안함
                        if status_code == 0x00:
                            # Data (20) + End (1)
                            response_data = sock.recv(20)
                            end_byte = sock.recv(1)

                            if len(response_data) == 20 and end_byte == b'\n':
                                # 5개의 4바이트 정수 (big-endian)로 언패킹
                                stocks = struct.unpack('>IIIII', response_data)
                                # 시그널을 통해 메인 스레드로 데이터 전송
                                self.stock_updated.emit(list(stocks))
                        
                        # 1초마다 재고 요청
                        time.sleep(1)

            except (socket.timeout, ConnectionRefusedError, ConnectionResetError, OSError) as e:
                self.connection_status.emit(f"연결 실패: {e}")
                stocks = [-1, -1, -1, -1, -1] # 에러 상태를 나타내는 값
                self.stock_updated.emit(stocks)
            
            # 연결 실패 시 3초 후 재시도
            if self._is_running:
                time.sleep(3)
    
    def stop(self):
        """스레드를 안전하게 종료"""
        self._is_running = False

# --- 메인 모니터 탭 위젯 ---
class MainMonitorTab(QWidget, Ui_Tab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.pixmap = QtGui.QPixmap(self.sensor_status.width(), self.sensor_status.height())
        self.pixmap.fill(Qt.GlobalColor.white)
        self.draw_system_layout()
        self.sensor_status.setPixmap(self.pixmap)

        # TCP 클라이언트 스레드 시작
        self.init_tcp_client()


    def init_tcp_client(self):
        """TCP 클라이언트 스레드를 초기화하고 시그널을 슬롯에 연결합니다."""
        host, port = "localhost", 9999
        self.tcp_thread = TCPClientThread(host, port)
        # 시그널-슬롯 연결
        # self.tcp_thread.connection_status.connect(self.update_connection_status)
        # 스레드 시작
        self.tcp_thread.start()

    def stop_tcp_client(self):
        """외부에서 TCP 클라이언트를 중지시킬 때 호출됩니다."""
        if self.tcp_thread and self.tcp_thread.isRunning():
            self.tcp_thread.stop()
            self.tcp_thread.wait() # 스레드가 완전히 종료될 때까지 대기

    # def update_connection_status(self, status: str):
    #     """TCP 연결 상태 라벨을 업데이트합니다."""
    #     self.connection_label.setText(f"연결 상태: {status}")



    def draw_system_layout(self):
        """물류 시스템 평면도를 그립니다 (image.png 기반)"""
        painter = QPainter(self.pixmap)
        pen = QPen(QColor(0, 0, 0))  # 검은색 선
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.GlobalColor.white))  # 하얀색 배경
        
        # 폰트 설정
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        
        # 입고구역 (상단 직사각형)
        painter.drawRect(20, 20, 360, 60)
        painter.drawText(170, 55, "입고구역")
        
        # 로봇 (우상단 작은 직사각형)
        self.drawRobot(painter, 320, 30)
        # painter.drawRect(320, 30, 40, 40)
        # painter.drawRect(330, 25, 20, 5) # 로봇 상단 작은 사각형 (바퀴 그래픽)
        # painter.drawRect(330, 70, 20, 5) # 로봇 하단 작은 사각형 (바퀴 그래픽)
        # painter.drawText(330, 55, "로봇")
        
        # R, G, Y 보관구역 (깔때기 모양의 구역들)
        # R 보관구역
        painter.drawPolygon(self.getPolygon(20, 220))        
        painter.drawText(25, 195, "R 보관구역")
        painter.drawText(30, 210, "재고 : ")
        
        # G 보관구역 
        painter.drawPolygon(self.getPolygon(160, 220))        
        # painter.drawRect(160, 100, 80, 120)
        painter.drawText(165, 195, "G 보관구역")
        painter.drawText(170, 210, "재고 : ")
        
        # painter.drawText(190, 165, "G")
        # painter.drawText(180, 180, "보관구역")
        
        # Y 보관구역
        painter.drawPolygon(self.getPolygon(300, 220))        
        # painter.drawRect(300, 100, 80, 120)
        painter.drawText(305, 195, "Y 보관구역")
        painter.drawText(310, 210, "재고 : ")

        # 출고구역 (하단 직사각형)
        painter.drawRect(20, 320, 360, 80)
        painter.drawText(170, 365, "출고구역")
        
        painter.end()

    def getPolygon(self, x, y):
        return QPolygon([
            QPoint(x, y),
            QPoint(x, y - 70),
            QPoint(x + 20, y - 70),
            QPoint(x + 20, y - 120),
            QPoint(x + 60, y - 120),
            QPoint(x + 60, y - 70),
            QPoint(x + 80, y - 70),
            QPoint(x + 80, y),
            QPoint(x + 60, y + 80),
            QPoint(x + 20, y + 80),
            QPoint(x, y),
        ])

    def drawRobot(self, painter : QPainter, x, y):
        '''
        Y 기준위치 : 320, 30
        '''
        painter.drawRect(x, y, 40, 40)
        painter.drawRect(x + 10, y - 5, 20, 5)
        painter.drawRect(x + 10, y + 40, 20, 5)
        painter.drawText(x + 7, y + 25, "로봇")
        # # 로봇 (우상단 작은 직사각형)
        # painter.drawRect(320, 30, 40, 40)
        # painter.drawRect(330, 25, 20, 5) # 로봇 상단 작은 사각형 (바퀴 그래픽)
        # painter.drawRect(330, 70, 20, 5) # 로봇 하단 작은 사각형 (바퀴 그래픽)
        # painter.drawText(330, 55, "로봇")
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = MainMonitorTab()
    myWindows.show()
    sys.exit(app.exec())