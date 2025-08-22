import os
import sys
import socket
import struct
import time
from PyQt6 import uic, QtCore
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

# 30초에 한번 시스템 모니터링

# UI 파일 로드
current_dir = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(current_dir, "system_manage.ui")
Ui_Tab, QWidgetBase = uic.loadUiType(ui_file)

# TCP 서버 상태 모니터링 스레드
class SystemStatusThread(QThread):
    """
    시스템 상태를 모니터링하는 스레드
    GUI/LMS/Hardware 상태를 주기적으로 확인
    """
    status_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True
        self.host = "localhost"
        self.port = 9999
    
    def run(self):
        """스레드 실행 함수"""
        while self._is_running:
            try:
                # LMS 서버 연결 테스트
                lms_status = self.test_lms_connection()
                # GUI 상태는 이 스레드가 실행되고 있으므로 True
                gui_status = True
                # 하드웨어 상태는 LMS 서버를 통해 확인 (일단 LMS와 같은 상태로 설정)
                hardware_status = lms_status
                
                status_data = {
                    'gui_status': gui_status,
                    'lms_status': lms_status,
                    'agv_status': hardware_status,
                    'storage_status': hardware_status
                }
                
                self.status_updated.emit(status_data)
                
            except Exception as e:
                print(f"시스템 상태 확인 오류: {e}")
                # 오류 시 모든 상태를 False로 설정
                status_data = {
                    'gui_status': True,  # GUI는 실행 중이므로 True
                    'lms_status': False,
                    'agv_status': False,
                    'storage_status': False
                }
                self.status_updated.emit(status_data)
            
            # 3초마다 상태 확인
            time.sleep(3)
    
    def test_lms_connection(self):
        """LMS 서버 연결 상태 테스트"""
        try:
            with socket.create_connection((self.host, self.port), timeout=2) as sock:
                # AI 명령어로 연결 테스트
                request = b'AI\x00\x00\x00\x00\n'
                sock.sendall(request)
                
                # 응답 수신 (간단한 헤더만 확인)
                header = sock.recv(3)
                if len(header) == 3:
                    return True
                return False
        except:
            return False
    
    def stop(self):
        """스레드 중지"""
        self._is_running = False

class SystemManageTab(QWidget, Ui_Tab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        
        # 현재 로봇 위치 (0: 입고, 1: R, 2: G, 3: Y, 4: 출고)
        self.current_robot_position = 0
        self.position_names = ["입고", "R구역", "G구역", "Y구역", "출고"]
        
        # UI 초기화
        self.init_ui_components()
        
        # 시스템 상태 모니터링 시작
        self.init_status_monitoring()
    
    def init_ui_components(self):
        """UI 컴포넌트 초기화"""
        # 슬라이더 이벤트 연결
        self.robot_position_slider.valueChanged.connect(self.on_slider_changed)
        
        # 로봇 이동 버튼 이벤트 연결
        self.btn_move_receiving.clicked.connect(lambda: self.move_robot(0))
        self.btn_move_red.clicked.connect(lambda: self.move_robot(1))
        self.btn_move_green.clicked.connect(lambda: self.move_robot(2))
        self.btn_move_yellow.clicked.connect(lambda: self.move_robot(3))
        self.btn_move_shipping.clicked.connect(lambda: self.move_robot(4))
        
        # 모터 테스트 버튼 이벤트 연결
        self.btn_conveyor_test.clicked.connect(self.test_conveyor_motor)
        self.btn_agv_servo_test.clicked.connect(self.test_agv_servo)
        self.btn_r_motor_test.clicked.connect(lambda: self.test_storage_motor('R'))
        self.btn_g_motor_test.clicked.connect(lambda: self.test_storage_motor('G'))
        self.btn_y_motor_test.clicked.connect(lambda: self.test_storage_motor('Y'))
        
        # 초기 위치 표시 업데이트
        self.update_position_display()
    
    def init_status_monitoring(self):
        """시스템 상태 모니터링 초기화"""
        self.status_thread = SystemStatusThread()
        self.status_thread.status_updated.connect(self.update_status_display)
        self.status_thread.start()
    
    def update_status_display(self, status_data):
        """시스템 상태 표시 업데이트"""
        # GUI 상태 업데이트
        self.gui_status_btn.setChecked(status_data['gui_status'])
        self.gui_status_btn.setText("연결됨" if status_data['gui_status'] else "연결 끊김")
        
        # LMS 상태 업데이트
        self.lms_status_btn.setChecked(status_data['lms_status'])
        self.lms_status_btn.setText("실행중" if status_data['lms_status'] else "중지됨")
        
        # AGV 상태 업데이트
        self.agv_status_btn.setChecked(status_data['agv_status'])
        self.agv_status_btn.setText("연결됨" if status_data['agv_status'] else "연결 끊김")
        
        # Storage 상태 업데이트
        self.storage_status_btn.setChecked(status_data['storage_status'])
        self.storage_status_btn.setText("연결됨" if status_data['storage_status'] else "연결 끊김")
    
    def on_slider_changed(self, value):
        """슬라이더 값 변경 시 호출"""
        self.current_robot_position = value
        self.update_position_display()
        # 실제 로봇 이동 명령은 슬라이더 변경만으로는 전송하지 않음
    
    def update_position_display(self):
        """현재 위치 표시 업데이트"""
        position_name = self.position_names[self.current_robot_position]
        self.position_value_label.setText(position_name)
    
    def move_robot(self, target_position):
        """로봇을 특정 위치로 이동"""
        try:
            # 슬라이더 위치 업데이트
            self.robot_position_slider.setValue(target_position)
            self.current_robot_position = target_position
            self.update_position_display()
            
            # LMS 서버에 로봇 이동 명령 전송
            success = self.send_robot_move_command(target_position)
            if success:
                print(f"로봇 이동 성공: {self.position_names[target_position]}")
            else:
                print(f"로봇 이동 실패: {self.position_names[target_position]}")
                
        except Exception as e:
            print(f"로봇 이동 오류: {e}")
    
    def send_robot_move_command(self, position):
        """로봇 이동 명령을 LMS 서버에 전송"""
        try:
            with socket.create_connection(("localhost", 9999), timeout=3) as sock:
                # RM (Robot Move) 명령 전송
                request = b'RM' + bytes([position]) + b'\x00\x00\x00' + b'\n'
                sock.sendall(request)
                
                # 응답 수신
                header = sock.recv(3)  # Command(2) + Status(1)
                if len(header) == 3:
                    status_code = header[2]
                    end_byte = sock.recv(1)
                    return status_code == 0x00  # 성공
                    
        except Exception as e:
            print(f"로봇 이동 명령 전송 실패: {e}")
            return False
        
        return False
    
    def test_conveyor_motor(self):
        """컨베이어 벨트 모터 테스트"""
        success = self.send_motor_test_command('CB')  # Conveyor Belt
        if success:
            print("컨베이어 벨트 테스트 성공")
        else:
            print("컨베이어 벨트 테스트 실패")
    
    def test_agv_servo(self):
        """AGV 서보모터 테스트"""
        success = self.send_motor_test_command('AS')  # AGV Servo
        if success:
            print("AGV 서보모터 테스트 성공")
        else:
            print("AGV 서보모터 테스트 실패")
    
    def test_storage_motor(self, color):
        """보관함 서보모터 테스트"""
        color_codes = {'R': 0x01, 'G': 0x02, 'Y': 0x03}
        color_code = color_codes.get(color, 0x01)
        
        success = self.send_motor_test_command('SM', color_code)  # Storage Motor
        if success:
            print(f"{color} 구역 서보모터 테스트 성공")
        else:
            print(f"{color} 구역 서보모터 테스트 실패")
    
    def send_motor_test_command(self, command, data_byte=0):
        """모터 테스트 명령을 LMS 서버에 전송"""
        try:
            with socket.create_connection(("localhost", 9999), timeout=30) as sock:
                # 모터 테스트 명령 전송
                if data_byte > 0:
                    request = command.encode('ascii') + bytes([data_byte]) + b'\x00\x00\x00' + b'\n'
                else:
                    request = command.encode('ascii') + b'\x00\x00\x00\x00' + b'\n'
                    
                sock.sendall(request)
                
                # 응답 수신
                header = sock.recv(3)  # Command(2) + Status(1)
                if len(header) == 3:
                    status_code = header[2]
                    end_byte = sock.recv(1)
                    return status_code == 0x00  # 성공
                    
        except Exception as e:
            print(f"모터 테스트 명령 전송 실패: {e}")
            return False
        
        return False
    
    def stop_status_monitoring(self):
        """상태 모니터링 중지"""
        if hasattr(self, 'status_thread') and self.status_thread.isRunning():
            self.status_thread.stop()
            self.status_thread.wait()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemManageTab()
    window.show()
    sys.exit(app.exec())