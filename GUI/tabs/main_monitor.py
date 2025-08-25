import os
import sys
import time
import struct
from PyQt6 import uic, QtGui
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont, QPolygon, QIntValidator
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint

from stw_lib.sector_manager2 import SectorName, SectorStatus, SectorManager

# ComManager import (상위 경로)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from communication.com_manager import ComManager


# --- UI 파일 로드 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(current_dir, "main_monitor.ui")
Ui_Tab, QWidgetBase = uic.loadUiType(ui_file)

# --- 메인 모니터 탭 위젯 ---
class MainMonitorTab(QWidget, Ui_Tab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.pixmap = QtGui.QPixmap(self.sensor_status.width(), self.sensor_status.height())
        self.pixmap.fill(Qt.GlobalColor.white)
        self.draw_system_layout()
        self.sensor_status.setPixmap(self.pixmap)

        # ComManager 초기화 및 연결
        self.com_manager = ComManager(host='localhost', port=8100)
        
        # LMS 서버 연결 시도
        if self.com_manager.connect():
            print("MainMonitor: LMS 서버 연결 성공")
            print(f"연결 상태: {self.com_manager.is_connected}")
        else:
            print("MainMonitor: LMS 서버 연결 실패")
            print(f"연결 상태: {self.com_manager.is_connected}")
            print("주의: LMS 서버가 실행되지 않았을 수 있습니다!")
        
        # UI 초기화
        self.init_ui_components()

    def init_ui_components(self):
        """UI 컴포넌트를 초기화합니다."""
        print("=== UI 컴포넌트 초기화 시작 ===")
        
        # UI 요소 존재 확인
        print(f"admin_receive 존재: {hasattr(self, 'admin_receive')}")
        print(f"btn_admin_receive 존재: {hasattr(self, 'btn_admin_receive')}")
        
        # 입력 필드에 QIntValidator 설정 (양수만 허용)
        int_validator = QIntValidator(0, 65535)  # 0부터 65535까지 양수만 허용
        
        # 입고 관리 필드
        if hasattr(self, 'admin_receive'):
            self.admin_receive.setValidator(int_validator)
            print("admin_receive 필드 초기화 완료")
        
        # 출고 관리 필드들
        if hasattr(self, 'admin_ship_r'):
            self.admin_ship_r.setValidator(int_validator)
        if hasattr(self, 'admin_ship_g'):
            self.admin_ship_g.setValidator(int_validator)
        if hasattr(self, 'admin_ship_y'):
            self.admin_ship_y.setValidator(int_validator)
        
        # 버튼 이벤트 연결
        if hasattr(self, 'btn_admin_receive'):
            self.btn_admin_receive.clicked.connect(self.handle_receive_request)
            print("입고 버튼 이벤트 연결 완료")
        else:
            print("ERROR: btn_admin_receive 버튼을 찾을 수 없습니다!")
            
        if hasattr(self, 'btn_admin_ship'):
            self.btn_admin_ship.clicked.connect(self.handle_ship_request)
            print("출고 버튼 이벤트 연결 완료")
        
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
            # 지역 입고수량 업데이트 (주넉)
            # self.receive_count_r.setText(stocks[])
            
            # QProgressBar 업데이트 (최대값 3으로 설정)
            self.stock_count_r.setMaximum(3)
            self.stock_count_g.setMaximum(3)
            self.stock_count_y.setMaximum(3)
            
            # 현재 재고 반영 (stocks[1]=RED, stocks[2]=GREEN, stocks[3]=YELLOW)
            self.stock_count_r.setValue(min(stocks[1], 3))
            self.stock_count_g.setValue(min(stocks[2], 3))
            self.stock_count_y.setValue(min(stocks[3], 3))
            
            # 누적 재고 반영 (stock[5]=RECEIVING_TOTAL, stock[6]=SHIPPING_TOTAL)
            self.acc_receive_count.setText(str(stocks[5]))
            self.acc_ship_count.setText(str(stocks[6]))
    
    def update_cumulative_data(self):
        """누적 데이터 업데이트"""
        # RA 명령을 통해 실제 누적 데이터 수신
        self.send_ra_command()
        
    def create_ri_command(self, quantity):
        """RI (Receive Item) 명령어 생성"""
        command = b'RI'
        receive_req = struct.pack('>H', quantity)  # 2 bytes
        padding = b'\x00' * 12  # 나머지 12 bytes
        data = receive_req + padding
        end = b'\n'
        return command + data + end
    
    def create_si_command(self, red, green, yellow):
        """SI (Ship Item Request) 명령어 생성"""
        command = b'SI'
        ship_req = struct.pack('>HHH', red, green, yellow)  # 6 bytes
        padding = b'\x00' * 8  # 나머지 8 bytes
        data = ship_req + padding
        end = b'\n'
        return command + data + end
    
    def create_ra_command(self):
        """RA (Request All stock) 명령어 생성"""
        command = b'RA'
        data = b'\x00' * 14  # 14 bytes 모두 0
        end = b'\n'
        return command + data + end
    
    def send_ra_command(self):
        """RA 명령 전송하여 재고 상태 요청"""
        try:
            message = self.create_ra_command()
            response = self.com_manager.send_raw_message(message)
            if response:
                self.parse_response(response)
        except Exception as e:
            print(f"RA 명령 전송 실패: {e}")
    
    def parse_response(self, response_data):
        """LMS → GUI 응답 파싱"""
        if len(response_data) < 4:
            return
            
        command = response_data[:2].decode('ascii')
        status = response_data[2]
        
        if status == 0x00:  # SUCCESS
            if command == 'AU':  # All Stock Update 응답
                self.parse_au_response(response_data[3:-1])  # 헤더와 끝 문자 제외
        else:
            print(f"명령 실패: {command}, 상태: {status:02x}")
    
    def parse_au_response(self, data):
        """AU 응답 데이터 파싱"""
        if len(data) >= 14:
            stocks = struct.unpack('>HHHHHHH', data[:14])
            self.update_stock_display(stocks)

    def handle_receive_request(self):
        """RI 명령어로 입고 요청을 처리"""
        print("=== 입고 실행 버튼 클릭됨 ===")
        try:
            quantity_text = self.admin_receive.text()
            print(f"입력된 수량: '{quantity_text}'")
            if not quantity_text or quantity_text == "0":
                print("수량이 0이거나 비어있음 - 처리 중단")
                return
                
            quantity = int(quantity_text)
            print(f"파싱된 수량: {quantity}")
            
            # 연결 상태 체크
            if not self.com_manager.is_connected:
                print("LMS 서버에 연결되지 않음 - 재연결 시도")
                if not self.com_manager.connect():
                    print("재연결 실패")
                    self.receive_status.setText("실패: 서버 미연결")
                    self.receive_status.setStyleSheet("color: red; font-size: 10px;")
                    return
                    
            # RI 명령 전송
            print(f"RI 명령 전송 시도: 수량={quantity}")
            message = self.create_ri_command(quantity)
            print(f"생성된 메시지: {message.hex()}")
            response = self.com_manager.send_raw_message(message)
            print(f"서버 응답: {response.hex() if response else 'None'}")
            
            if response and len(response) >= 4:
                command = response[:2].decode('ascii')
                status = response[2]
                
                if status == 0x00:  # SUCCESS
                    print(f"입고 요청 성공: {quantity}개")
                    self.receive_status.setText("성공")
                    self.receive_status.setStyleSheet("color: green; font-size: 10px;")
                else:
                    print(f"입고 요청 실패: 상태 {status:02x}")
                    self.receive_status.setText("실패: 서버 오류")
                    self.receive_status.setStyleSheet("color: red; font-size: 10px;")
            else:
                print("입고 요청: 응답 없음")
                self.receive_status.setText("실패: 통신 오류")
                self.receive_status.setStyleSheet("color: red; font-size: 10px;")
            
            self.admin_receive.setText("0")
            # 누적 데이터 업데이트 - 약간의 지연 후 실행
            import threading
            def delayed_update():
                import time
                time.sleep(0.5)  # 0.5초 지연
                self.update_cumulative_data()
            threading.Thread(target=delayed_update, daemon=True).start()
                        
        except ValueError as e:
            print(f"입고 요청 실패 - 입력 값 오류: {e}")
            self.receive_status.setText("실패: 입력 값 오류")
            self.receive_status.setStyleSheet("color: red; font-size: 10px;")
        except Exception as e:
            print(f"입고 요청 실패 - 일반 오류: {e}")
            import traceback
            traceback.print_exc()
            self.receive_status.setText("실패: 시스템 오류")
            self.receive_status.setStyleSheet("color: red; font-size: 10px;")
    
    def handle_ship_request(self):
        """SI 명령어로 출고 요청을 처리"""
        try:
            # R, G, Y 중에서 입력된 값들 확인
            r_quantity = int(self.admin_ship_r.text()) if self.admin_ship_r.text() else 0
            g_quantity = int(self.admin_ship_g.text()) if self.admin_ship_g.text() else 0
            y_quantity = int(self.admin_ship_y.text()) if self.admin_ship_y.text() else 0
            
            total_quantity = r_quantity + g_quantity + y_quantity
            
            if total_quantity > 0:
                # SI 명령 전송
                message = self.create_si_command(r_quantity, g_quantity, y_quantity)
                response = self.com_manager.send_raw_message(message)
                
                if response and len(response) >= 4:
                    command = response[:2].decode('ascii')
                    status = response[2]
                    
                    if status == 0x00:  # SUCCESS
                        print(f"출고 요청 성공: R={r_quantity}, G={g_quantity}, Y={y_quantity}")
                        self.ship_status.setText("성공")
                        self.ship_status.setStyleSheet("color: green; font-size: 10px;")
                    else:
                        print(f"출고 요청 실패: 상태 {status:02x}")
                        self.ship_status.setText("실패: 서버 오류")
                        self.ship_status.setStyleSheet("color: red; font-size: 10px;")
                else:
                    print("출고 요청: 응답 없음")
                    self.ship_status.setText("실패: 통신 오류")
                    self.ship_status.setStyleSheet("color: red; font-size: 10px;")
                
                # 입력 필드 초기화
                self.admin_ship_r.setText("0")
                self.admin_ship_g.setText("0")
                self.admin_ship_y.setText("0")
                # 누적 데이터 업데이트 - 약간의 지연 후 실행
                import threading
                def delayed_update():
                    import time
                    time.sleep(0.5)  # 0.5초 지연
                    self.update_cumulative_data()
                threading.Thread(target=delayed_update, daemon=True).start()
            else:
                print("출고 요청 실패: 수량이 0개입니다")
                self.ship_status.setText("실패: 수량 0")
                self.ship_status.setStyleSheet("color: red; font-size: 10px;")
                
        except Exception as e:
            print(f"출고 요청 실패: {e}")
            self.ship_status.setText("실패: 입력 오류")
            self.ship_status.setStyleSheet("color: red; font-size: 10px;")


    def draw_system_layout(self):
        """물류 시스템 평면도"""
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = MainMonitorTab()
    myWindows.show()
    sys.exit(app.exec())