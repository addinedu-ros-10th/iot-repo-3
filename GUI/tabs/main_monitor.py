import os
import sys
import socket
import struct
import time
from PyQt6 import uic, QtGui
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont, QPolygon, QIntValidator
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint

from stw_lib.sector_manager2 import SectorName, SectorStatus, SectorManager

'''
30초에 한번 재고 요청

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
                        time.sleep(30)

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
        
        # UI 초기화
        self.init_ui_components()


    def init_tcp_client(self):
        """TCP 클라이언트 스레드를 초기화하고 시그널을 슬롯에 연결합니다."""
        host, port = "localhost", 9999
        self.tcp_thread = TCPClientThread(host, port)
        # 시그널-슬롯 연결
        self.tcp_thread.stock_updated.connect(self.update_stock_display)
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
    
    def init_ui_components(self):
        """UI 컴포넌트를 초기화합니다."""
        # 입력 필드에 QIntValidator 설정 (양수만 허용)
        int_validator = QIntValidator(0, 999999)  # 0부터 999999까지 양수만 허용
        
        # 입고 관리 필드
        self.admin_receive.setValidator(int_validator)
        
        # 출고 관리 필드들
        self.admin_ship_r.setValidator(int_validator)
        self.admin_ship_g.setValidator(int_validator)
        self.admin_ship_y.setValidator(int_validator)
        
        # 버튼 이벤트 연결
        self.btn_admin_receive.clicked.connect(self.handle_receive_request)
        self.btn_admin_ship.clicked.connect(self.handle_ship_request)
        
        # 재고 초기화 버튼 이벤트 연결
        self.btn_receive_clear.clicked.connect(self.handle_receive_clear)
        self.btn_store_clear.clicked.connect(self.handle_store_clear)
        self.btn_ship_clear.clicked.connect(self.handle_ship_clear)
        self.btn_all_clear.clicked.connect(self.handle_all_clear)
        
        # 누적 데이터 업데이트 (CU 명령어 사용)
        self.update_cumulative_data()
        
        # 상태 라벨 생성
        self.create_status_labels()
    
    def create_status_labels(self):
        """receive_status와 ship_status 라벨을 동적으로 생성합니다."""
        # receive_status 라벨 (입고 관리 섹션 아래)
        self.receive_status = QLabel(self.frame)
        self.receive_status.setGeometry(20, 90, 121, 20)
        self.receive_status.setText("대기 중")
        self.receive_status.setStyleSheet("color: gray; font-size: 10px;")
        
        # ship_status 라벨 (출고 관리 섹션 아래)
        self.ship_status = QLabel(self.frame)
        self.ship_status.setGeometry(190, 160, 121, 20)
        self.ship_status.setText("대기 중")
        self.ship_status.setStyleSheet("color: gray; font-size: 10px;")
    
    def update_stock_display(self, stocks):
        """재고 정보를 UI에 업데이트합니다."""
        if len(stocks) >= 5:
            # QProgressBar 업데이트 (최대값 3으로 설정)
            self.stock_count_r.setMaximum(3)
            self.stock_count_g.setMaximum(3)
            self.stock_count_y.setMaximum(3)
            
            # 현재 재고 반영 (stocks[1]=RED, stocks[2]=GREEN, stocks[3]=YELLOW)
            self.stock_count_r.setValue(min(stocks[1], 3))
            self.stock_count_g.setValue(min(stocks[2], 3))
            self.stock_count_y.setValue(min(stocks[3], 3))
    
    def update_cumulative_data(self):
        """CU 명령어를 사용해 누적 입출고 데이터를 가져와 표시합니다."""
        try:
            with socket.create_connection(("localhost", 9999), timeout=3) as sock:
                # CU 명령어 전송
                request = b'CU\x00\x00\x00\x00\n'
                sock.sendall(request)
                
                # 응답 수신
                header = sock.recv(3)  # Command(2) + Status(1)
                if len(header) == 3:
                    cmd, status_code = header[:2].decode('ascii'), header[2]
                    
                    if status_code == 0x00:  # 성공
                        response_data = sock.recv(8)  # 8바이트 (누적 입고, 누적 출고)
                        end_byte = sock.recv(1)
                        
                        if len(response_data) == 8 and end_byte == b'\n':
                            # 2개의 4바이트 정수 (big-endian)로 언패킹
                            cumulative_receive, cumulative_ship = struct.unpack('>II', response_data)
                            
                            # UI에 표시
                            self.acc_receive_count.setText(str(cumulative_receive))
                            self.acc_ship_count.setText(str(cumulative_ship))
                            
        except Exception as e:
            print(f"누적 데이터 요청 실패: {e}")
            self.acc_receive_count.setText("연결 실패")
            self.acc_ship_count.setText("연결 실패")
    
    def handle_receive_request(self):
        """RE 명령어로 입고 요청을 처리합니다."""
        try:
            quantity_text = self.admin_receive.text()
            if not quantity_text or quantity_text == "0":
                return
                
            quantity = int(quantity_text)
            
            with socket.create_connection(("localhost", 9999), timeout=3) as sock:
                # RE 명령어 전송
                request = b'RE' + struct.pack('>I', quantity) + b'\n'
                sock.sendall(request)
                
                # 응답 수신
                header = sock.recv(3)  # Command(2) + Status(1)
                if len(header) == 3:
                    status_code = header[2]
                    response_data = sock.recv(4)  # 4바이트 (입고 후 재고)
                    end_byte = sock.recv(1)
                    
                    if status_code == 0x00:  # 성공
                        new_stock = struct.unpack('>I', response_data)[0]
                        print(f"입고 성공: {quantity}개 입고됨, 현재 재고: {new_stock}")
                        self.admin_receive.setText("0")
                        self.receive_status.setText(f"성공: {quantity}개 입고")
                        self.receive_status.setStyleSheet("color: green; font-size: 10px;")
                        # 누적 데이터 업데이트
                        self.update_cumulative_data()
                    else:
                        print("입고 실패: 용량 초과 또는 오류")
                        self.receive_status.setText("실패: 용량 초과")
                        self.receive_status.setStyleSheet("color: red; font-size: 10px;")
                        
        except Exception as e:
            print(f"입고 요청 실패: {e}")
            self.receive_status.setText("실패: 연결 오류")
            self.receive_status.setStyleSheet("color: red; font-size: 10px;")
    
    def handle_ship_request(self):
        """SH 명령어로 출고 요청을 처리합니다."""
        try:
            # R, G, Y 중에서 입력된 값들 확인
            r_quantity = int(self.admin_ship_r.text()) if self.admin_ship_r.text() else 0
            g_quantity = int(self.admin_ship_g.text()) if self.admin_ship_g.text() else 0
            y_quantity = int(self.admin_ship_y.text()) if self.admin_ship_y.text() else 0
            
            # 각 색상별로 출고 요청
            color_requests = []
            if r_quantity > 0:
                color_requests.extend([(0x01, r_quantity)])  # RED
            if g_quantity > 0:
                color_requests.extend([(0x02, g_quantity)])  # GREEN
            if y_quantity > 0:
                color_requests.extend([(0x03, y_quantity)])  # YELLOW
            
            success_count = 0
            for color_code, quantity in color_requests:
                for _ in range(quantity):
                    try:
                        with socket.create_connection(("localhost", 9999), timeout=3) as sock:
                            # SH 명령어 전송 (1개씩)
                            request = b'SH' + bytes([color_code]) + b'\x00\x00\x00' + b'\n'
                            sock.sendall(request)
                            
                            # 응답 수신
                            header = sock.recv(3)  # Command(2) + Status(1)
                            if len(header) == 3:
                                status_code = header[2]
                                end_byte = sock.recv(1)
                                
                                if status_code == 0x00:  # 성공
                                    success_count += 1
                    except:
                        continue
            
            if success_count > 0:
                print(f"출고 성공: {success_count}개 출고됨")
                # 입력 필드 초기화
                self.admin_ship_r.setText("0")
                self.admin_ship_g.setText("0")
                self.admin_ship_y.setText("0")
                self.ship_status.setText(f"성공: {success_count}개 출고")
                self.ship_status.setStyleSheet("color: green; font-size: 10px;")
                # 누적 데이터 업데이트
                self.update_cumulative_data()
            else:
                print("출고 실패: 재고 부족 또는 오류")
                self.ship_status.setText("실패: 재고 부족")
                self.ship_status.setStyleSheet("color: red; font-size: 10px;")
                
        except Exception as e:
            print(f"출고 요청 실패: {e}")
            self.ship_status.setText("실패: 연결 오류")
            self.ship_status.setStyleSheet("color: red; font-size: 10px;")
    
    def send_clear_command(self, command: str) -> bool:
        """재고 초기화 명령을 서버에 전송합니다."""
        try:
            with socket.create_connection(("localhost", 9999), timeout=3) as sock:
                # 초기화 명령 전송
                request = command.encode('ascii') + b'\x00\x00\x00\x00\n'
                sock.sendall(request)
                
                # 응답 수신
                header = sock.recv(3)  # Command(2) + Status(1)
                if len(header) == 3:
                    status_code = header[2]
                    end_byte = sock.recv(1)
                    
                    return status_code == 0x00  # 성공
        except Exception as e:
            print(f"초기화 명령 실패: {e}")
            return False
        
        return False
    
    def handle_receive_clear(self):
        """입고 구역 재고 초기화"""
        if self.send_clear_command("CR"):
            print("입고 구역 재고 초기화 성공")
        else:
            print("입고 구역 재고 초기화 실패")
    
    def handle_store_clear(self):
        """보관 구역 재고 초기화"""
        if self.send_clear_command("CS"):
            print("보관 구역 재고 초기화 성공")
        else:
            print("보관 구역 재고 초기화 실패")
    
    def handle_ship_clear(self):
        """출고 구역 재고 초기화"""
        if self.send_clear_command("CH"):
            print("출고 구역 재고 초기화 성공")
        else:
            print("출고 구역 재고 초기화 실패")
    
    def handle_all_clear(self):
        """전체 구역 재고 초기화"""
        if self.send_clear_command("CA"):
            print("전체 구역 재고 초기화 성공")
            # 누적 데이터도 업데이트
            self.update_cumulative_data()
        else:
            print("전체 구역 재고 초기화 실패")



    def draw_system_layout(self):
        """물류 시스템 평면도를 그립니다 """
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