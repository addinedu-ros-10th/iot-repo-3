import os
import sys
import socket
import struct
import time
from PyQt6 import uic, QtGui
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from src.base.sector_manager2 import SectorName, SectorStatus, SectorManager

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
                        # 'AS' (All Stock) 명령어 전송 요청
                        request = b'AS\x00\x00\x00\x00\n'
                        sock.sendall(request)
                        
                        # --- 응답 수신 ---
                        # Command (2) + Status (1)
                        header = sock.recv(3)
                        if not header:
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
        self.sensor_status.setPixmap(self.pixmap)

        # 재고 표시를 위한 라벨 초기화
        self.init_stock_labels()
        # TCP 클라이언트 스레드 시작
        self.init_tcp_client()

        # 싱글톤 구역 관리자 인스턴스 생성 (초기 그래픽 표시에 사용)
        manager = SectorManager()
        for sector_name in SectorName:
            sector = manager.get_sector(sector_name)
            self.update_sector(sector)

    # --- 입고 수량 UI 업데이트 ---
    def update_receiving_count(self, count: int):
        """
        SectorManager로부터 받은 누적 입고 수량을 QLineEdit('receive_count_r')에 업데이트합니다.
        이 메서드는 SectorManager의 receiving_count_changed 시그널에 의해 호출됩니다.
        """
        self.receive_count_r.setText(str(count))

    def init_stock_labels(self):
        """
        각 구역의 재고를 표시할 라벨을 생성하고 배치합니다.
        좌표는 그래픽 요소(원)를 기준으로 설정합니다.
        """
        font = QFont("Arial", 10, QFont.Weight.Bold)
        
        # 라벨 생성 및 설정
        self.receiving_label = QLabel("재고: -", parent=self.sensor_status)
        self.receiving_label.setGeometry(170, 135, 80, 20)
        self.receiving_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.receiving_label.setFont(font)

        self.red_label = QLabel("재고: -", parent=self.sensor_status)
        self.red_label.setGeometry(30, 275, 80, 20)
        self.red_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.red_label.setFont(font)

        self.green_label = QLabel("재고: -", parent=self.sensor_status)
        self.green_label.setGeometry(170, 275, 80, 20)
        self.green_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.green_label.setFont(font)

        self.yellow_label = QLabel("재고: -", parent=self.sensor_status)
        self.yellow_label.setGeometry(310, 275, 80, 20)
        self.yellow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.yellow_label.setFont(font)

        self.shipping_label = QLabel("재고: -", parent=self.sensor_status)
        self.shipping_label.setGeometry(170, 415, 80, 20)
        self.shipping_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shipping_label.setFont(font)
        
        # 연결 상태 표시 라벨
        self.connection_label = QLabel("연결 상태: 대기 중", self)
        self.connection_label.setGeometry(10, self.height() - 30, 400, 20)
        
        self.stock_labels = {
            SectorName.RECEIVING: self.receiving_label,
            SectorName.RED_STORAGE: self.red_label,
            SectorName.GREEN_STORAGE: self.green_label,
            SectorName.YELLOW_STORAGE: self.yellow_label,
            SectorName.SHIPPING: self.shipping_label,
        }

    def init_tcp_client(self):
        """TCP 클라이언트 스레드를 초기화하고 시그널을 슬롯에 연결합니다."""
        host, port = "localhost", 9999
        self.tcp_thread = TCPClientThread(host, port)
        # 시그널-슬롯 연결
        self.tcp_thread.stock_updated.connect(self.update_stock_display)
        self.tcp_thread.connection_status.connect(self.update_connection_status)
        # 스레드 시작
        self.tcp_thread.start()

    def stop_tcp_client(self):
        """외부에서 TCP 클라이언트를 중지시킬 때 호출됩니다."""
        if self.tcp_thread and self.tcp_thread.isRunning():
            self.tcp_thread.stop()
            self.tcp_thread.wait() # 스레드가 완전히 종료될 때까지 대기

    def update_stock_display(self, stocks: list):
        """
        TCP 스레드로부터 받은 재고 정보로 라벨 텍스트를 업데이트합니다.
        stocks: [RECEIVING, RED, GREEN, YELLOW, SHIPPING] 순서의 리스트
        """
        if stocks[0] == -1: # 연결 실패 시
            for label in self.stock_labels.values():
                label.setText("재고: ?")
            return
            
        stock_map = {
            SectorName.RECEIVING: stocks[0],
            SectorName.RED_STORAGE: stocks[1],
            SectorName.GREEN_STORAGE: stocks[2],
            SectorName.YELLOW_STORAGE: stocks[3],
            SectorName.SHIPPING: stocks[4],
        }
        for sector_name, stock in stock_map.items():
            self.stock_labels[sector_name].setText(f"재고: {stock}")

    def update_connection_status(self, status: str):
        """TCP 연결 상태 라벨을 업데이트합니다."""
        self.connection_label.setText(f"연결 상태: {status}")

    # 특정 구역 그래픽 업데이트 (기존 코드)
    def update_sector(self, sector):
        pixmap = self.sensor_status.pixmap()
        painter = QPainter(pixmap)
        pen = QPen(QColor(0,0,0))
        pen.setWidth(2)
        painter.setPen(pen)
        
        color = QColor()
        if sector.status == SectorStatus.AVAILABLE:
            brush = QBrush(QColor(80, 200, 80)) # Green
        elif sector.status == SectorStatus.PROCESSING:
            brush = QBrush(QColor(255, 193, 7)) # Yellow
        else: # UNAVAILABLE or FULL
            brush = QBrush(QColor(220, 53, 69)) # Red
        painter.setBrush(brush)
        
        radius = 40
        if sector.name == SectorName.RECEIVING:
            painter.drawEllipse(210 - radius, 90 - radius, 80, 80)
        elif sector.name == SectorName.RED_STORAGE:
            painter.drawEllipse(70 - radius, 230 - radius, 80, 80)
        elif sector.name == SectorName.GREEN_STORAGE:
            painter.drawEllipse(210 - radius, 230 - radius, 80, 80)
        elif sector.name == SectorName.YELLOW_STORAGE:
            painter.drawEllipse(350 - radius, 230 - radius, 80, 80)
        elif sector.name == SectorName.SHIPPING:
            painter.drawEllipse(210 - radius, 370 - radius, 80, 80)
        
        painter.end()
        self.sensor_status.setPixmap(pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = MainMonitorTab()
    myWindows.show()
    sys.exit(app.exec())