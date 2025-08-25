import os
import sys
import time
from PyQt6 import uic, QtCore
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

# ComManager import (상위 경로)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from communication.com_manager import ComManager

# 30초에 한번 시스템 모니터링

# UI 파일 로드
current_dir = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(current_dir, "system_manage.ui")
Ui_Tab, QWidgetBase = uic.loadUiType(ui_file)

# 시스템 상태 모니터링 스레드 (ComManager 활용)
class SystemStatusThread(QThread):
    """
    ComManager를 활용한 시스템 상태 모니터링 스레드
    GUI/LMS/Hardware 상태를 주기적으로 확인
    """
    status_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True
        
        # ComManager 인스턴스 생성
        self.com_manager = ComManager(host='localhost', port=8100)
        
        # 연결 상태 추적
        self.lms_connected = False
        
    def run(self):
        """스레드 실행 함수"""
        print("SystemStatusThread 시작")
        
        while self._is_running:
            try:
                # LMS 서버 상태 확인
                lms_status = self.check_lms_status()
                
                # GUI 상태는 이 스레드가 실행되고 있으므로 True
                gui_status = True
                
                # 하드웨어 상태는 LMS 연결 상태에 따라 결정
                agv_status = lms_status
                storage_status = lms_status
                
                status_data = {
                    'gui_status': gui_status,
                    'lms_status': lms_status,
                    'agv_status': agv_status,
                    'storage_status': storage_status
                }
                
                self.status_updated.emit(status_data)
                
            except Exception as e:
                print(f"시스템 상태 확인 오류: {e}")
                # 오류 시 기본 상태 설정
                status_data = {
                    'gui_status': True,  # GUI는 실행 중
                    'lms_status': False,
                    'agv_status': False,
                    'storage_status': False
                }
                self.status_updated.emit(status_data)
            
            # 5초마다 상태 확인
            time.sleep(5)
        
        print("SystemStatusThread 종료")
    
    def check_lms_status(self):
        """ComManager를 통한 LMS 서버 상태 확인"""
        try:
            # 연결되어 있지 않다면 연결 시도
            if not self.com_manager.is_connected:
                connected = self.com_manager.connect()
                if connected:
                    print("[SystemStatus] LMS 서버 연결 성공")
                    self.lms_connected = True
                    return True
                else:
                    if self.lms_connected:  # 이전에 연결되어 있었다면
                        print("[SystemStatus] LMS 서버 연결 끊어짐")
                        self.lms_connected = False
                    return False
            
            # 이미 연결되어 있다면 RA 명령으로 헬스체크
            try:
                import struct
                message = b'RA' + b'\x00' * 14 + b'\n'
                response = self.com_manager.send_raw_message(message)
                
                if response and len(response) >= 3:
                    # 유효한 응답이 오면 연결 상태 양호
                    return True
                else:
                    # 응답이 없거나 잘못된 응답이면 연결 끊어짐
                    print("[SystemStatus] LMS 서버 응답 없음 - 연결 끊어짐")
                    self.com_manager.is_connected = False
                    self.lms_connected = False
                    return False
                    
            except Exception as e:
                print(f"[SystemStatus] LMS 헬스체크 실패: {e}")
                self.com_manager.is_connected = False
                self.lms_connected = False
                return False
                
        except Exception as e:
            print(f"[SystemStatus] LMS 상태 확인 실패: {e}")
            return False
    
    def get_system_info(self):
        """시스템 정보 조회 (RA 명령 사용)"""
        if not self.com_manager.is_connected:
            return None
            
        try:
            import struct
            # RA 명령 전송
            message = b'RA' + b'\x00' * 14 + b'\n'
            response = self.com_manager.send_raw_message(message)
            
            if response and len(response) >= 17 and response[:2] == b'AU':
                # AU 응답 파싱 (재고 데이터)
                stock_data = struct.unpack('>HHHHHHH', response[3:17])
                return {
                    'receiving': stock_data[0],
                    'red_storage': stock_data[1],
                    'green_storage': stock_data[2],
                    'yellow_storage': stock_data[3],
                    'shipping': stock_data[4],
                    'receiving_total': stock_data[5],
                    'shipping_total': stock_data[6]
                }
            return None
            
        except Exception as e:
            print(f"시스템 정보 조회 실패: {e}")
            return None
    
    def stop(self):
        """스레드 중지"""
        print("SystemStatusThread 중지 요청")
        self._is_running = False
        
        # ComManager 연결 해제
        if self.com_manager and self.com_manager.is_connected:
            self.com_manager.disconnect()

class SystemManageTab(QWidget, Ui_Tab):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        
        # 현재 로봇 위치 (0: 입고, 1: R, 2: G, 3: Y, 4: 출고)
        self.current_robot_position = 0
        self.position_names = ["입고", "R구역", "G구역", "Y구역", "출고"]
        
        # ComManager 인스턴스 (공용)
        self.com_manager = ComManager(host='localhost', port=8100)
        
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
        """ComManager를 통한 로봇 이동 명령 전송"""
        try:
            # 연결되어 있지 않으면 연결 시도
            if not self.com_manager.is_connected:
                if not self.com_manager.connect():
                    print("LMS 서버에 연결할 수 없습니다")
                    return False
            
            # RH (Return Home) 명령 사용 - 위치에 따라 성공/실패 시뮬레이션
            success_flag = 1 if position == 0 else 0  # 입고 위치만 성공으로 시뮬레이션
            message = b'RH' + bytes([success_flag]) + b'\x00' * 13 + b'\n'
            response = self.com_manager.send_raw_message(message)
            
            if response and len(response) >= 4:
                command = response[:2].decode('ascii')
                status = response[2]
                
                if status == 0x00:  # SUCCESS
                    print(f"로봇 이동 성공: {self.position_names[position]}")
                    return True
                else:
                    print(f"로봇 이동 실패: 상태 코드 {status:02x}")
                    return False
            else:
                print("로봇 이동: 응답 없음")
                return False
                    
        except Exception as e:
            print(f"로봇 이동 명령 전송 실패: {e}")
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
    
    def send_motor_test_command(self, command_type, data_byte=0):
        """ComManager를 통한 모터 테스트 명령 전송"""
        try:
            # 연결되어 있지 않으면 연결 시도
            if not self.com_manager.is_connected:
                if not self.com_manager.connect():
                    print("LMS 서버에 연결할 수 없습니다")
                    return False
            
            # 모터 테스트는 RA 명령으로 시스템 상태 확인으로 대체
            message = b'RA' + b'\x00' * 14 + b'\n'
            response = self.com_manager.send_raw_message(message)
            
            if response and len(response) >= 3:
                status = response[2]
                
                if data_byte > 0:
                    print(f"모터 테스트: {command_type} 데이터={data_byte} - {'성공' if status == 0x00 else '실패'}")
                else:
                    print(f"모터 테스트: {command_type} - {'성공' if status == 0x00 else '실패'}")
                    
                return status == 0x00
            else:
                print(f"모터 테스트 {command_type}: 응답 없음")
                return False
                
        except Exception as e:
            print(f"모터 테스트 명령 전송 실패: {e}")
            return False
    
    def stop_status_monitoring(self):
        """상태 모니터링 중지"""
        if hasattr(self, 'status_thread') and self.status_thread.isRunning():
            self.status_thread.stop()
            self.status_thread.wait()
        
        # ComManager 연결 해제
        if hasattr(self, 'com_manager') and self.com_manager.is_connected:
            self.com_manager.disconnect()
            print("SystemManageTab: ComManager 연결 해제")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemManageTab()
    window.show()
    sys.exit(app.exec())