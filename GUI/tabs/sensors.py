import os
import sys
import random
from PyQt6 import uic
from PyQt6.QtGui import QColor, QPainter, QFont, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QTableWidgetItem, QPushButton
from PyQt6.QtCore import Qt, QTimer
from functools import partial

# 서보모터 1개 / 스태핑모터 4개

# src/base/sector_manager.py를 임포트
# 경로가 다른 경우 sys.path.append() 등을 사용하여 경로를 맞춰주세요.
from stw_lib.sector_manager2 import SectorManager, SectorName, MotorStatus

# --- UI 파일 로드 ---
# 제공된 sensors.ui 파일을 사용하도록 수정
current_dir = os.path.dirname(os.path.abspath(__file__))
ui_file = os.path.join(current_dir, "sensors.ui")
Ui_Tab, QWidgetBase = uic.loadUiType(ui_file)

class SensorsTab(QWidget, Ui_Tab): # QWidget과 UI 폼 클래스를 상속
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self) # uic.loadUiType으로 로드한 클래스의 setupUi 호출

        # --- 싱글톤 구역 관리자 인스턴스 ---
        self.manager = SectorManager()
        
        # --- 전체 센서 목록 및 초기 상태 설정 ---
        self.all_sensors = self._get_all_sensor_instances()
        self.all_motors = self._get_all_motor_instances()
        self.sensor_statuses = {sensor: "Normal" for sensor in self.all_sensors}

        # --- UI 초기화 및 연결 ---
        self._initialize_ui()

        self.healthLabel = self.findChild(QLabel, "labelHealth")

        # --- 시스템 상태 주기적 업데이트 ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system_health)
        self.timer.timeout.connect(self.update_state)
        self.timer.start(2000)

                
        self.update_system_health()
        self.update_state()

    def _get_all_sensor_instances(self) -> list:
        """SectorManager에서 모든 센서 인스턴스 목록을 가져옵니다 (중복 포함)."""
        all_sensor_instances = []
        for sector in self.manager.sectors.values():
            for sensor_name in sector.sensor_list:
                # (SectorName, sensor_name) 튜플로 저장하여 고유성 보장
                all_sensor_instances.append((sector.name, sensor_name))
        print(f"발견된 전체 센서 인스턴스 (총 {len(all_sensor_instances)}개): {all_sensor_instances}")
        return all_sensor_instances

    def _get_all_motor_instances(self) -> list:
        """SectorManager에서 모든 모터 인스턴스 목록을 가져옵니다."""
        all_motor_instances = []
        for sector in self.manager.sectors.values():
            for motor_name in sector.motors.keys():
                # (SectorName, motor_name) 튜플로 저장
                all_motor_instances.append((sector.name, motor_name))
        print(f"발견된 전체 모터 인스턴스 (총 {len(all_motor_instances)}개): {all_motor_instances}")
        return all_motor_instances

    # def _get_unique_sensors(self) -> list:
    #     """SectorManager에서 모든 고유한 센서 목록을 가져옵니다."""
    #     unique_sensors = set()
    #     for sector in self.manager.sectors.values():
    #         for sensor_name in sector.sensor_list:
    #             unique_sensors.add(sensor_name)
    #     print(f"발견된 고유 센서 목록: {list(unique_sensors)}")
    #     return list(unique_sensors)

    def _initialize_ui(self):
        """UI 위젯과 백엔드 데이터를 매핑하고 시그널을 연결합니다."""
        self.ui_map = {
            # 로봇 (RECEIVING)
            (SectorName.RECEIVING, 'sensor', 'RGB1'): self.robot_rgb1,
            (SectorName.RECEIVING, 'sensor', 'RGB2'): self.robot_rgb2,
            (SectorName.RECEIVING, 'motor', 'SERVO1'): self.robot_serbo1,
            (SectorName.RECEIVING, 'motor', 'STEP1'): self.robot_step1,
            (SectorName.RECEIVING, 'motor', 'DC1'): self.robot_dc1,
            
            # R 구역 (RED_STORAGE)
            (SectorName.RED_STORAGE, 'sensor', 'PROXI1'): self.r_proxi1,
            (SectorName.RED_STORAGE, 'motor', 'STEP1'): self.r_step1,

            # G 구역 (GREEN_STORAGE) - UI 파일의 복제된 R구역을 G구역으로 가정
            (SectorName.GREEN_STORAGE, 'sensor', 'PROXI1'): self.g_proxi1,
            (SectorName.GREEN_STORAGE, 'motor', 'STEP1'): self.g_step1,
            
            # Y 구역 (YELLOW_STORAGE)
            (SectorName.YELLOW_STORAGE, 'sensor', 'PROXI1'): self.y_proxi1,
            (SectorName.YELLOW_STORAGE, 'motor', 'STEP1'): self.y_step1,
            
            # 출고 구역 (SHIPPING)
            (SectorName.SHIPPING, 'sensor', 'RGB1'): self.sh_rgb1,
        }

        # 모든 버튼을 상태 표시용으로만 사용하도록 비활성화
        for button in self.ui_map.values():
            button.setEnabled(False)

    # def simulate_sensor_failure(self):
    #     """센서 고장을 시뮬레이션합니다."""
    #     normal_sensors = [s for s, status in self.sensor_statuses.items() if status == "Normal"]
    #     if normal_sensors:
    #         sensor_to_break = random.choice(normal_sensors)
    #         self.sensor_statuses[sensor_to_break] = "Error"
    #         print(f"!! 시뮬레이션: 센서 '{sensor_to_break}' 고장 발생")
    #         self.update_system_health()

    # def simulate_sensor_fix(self):
    #     """센서 수리를 시뮬레이션합니다."""
    #     failed_sensors = [s for s, status in self.sensor_statuses.items() if status == "Error"]
    #     if failed_sensors:
    #         sensor_to_fix = random.choice(failed_sensors)
    #         self.sensor_statuses[sensor_to_fix] = "Normal"
    #         print(f"** 시뮬레이션: 센서 '{sensor_to_fix}' 수리 완료")
    #         self.update_system_health()

    def update_system_health(self):
        """센서 상태를 확인하고 HealthLabel UI를 업데이트합니다."""
        total_sensors = len(self.all_sensors)
        normal_sensors = list(self.sensor_statuses.values()).count("Normal")
        
        health_ratio = normal_sensors / total_sensors if total_sensors > 0 else 1.0

        if health_ratio == 1.0:
            health_color = QColor("#2ECC71")
            health_text = "정상"
        # elif health_ratio >= 0.5:
        #     health_color = QColor("#F1C40F")
        #     health_text = "WARNING"
        else:
            health_color = QColor("#E74C3C")
            health_text = "에러"
            
        print(f"시스템 상태 업데이트: 정상 센서 {normal_sensors}/{total_sensors} ({health_ratio:.0%}) -> {health_text}")

        pixmap = self.create_health_circle(100, health_color, health_text, f"센서상태 : {normal_sensors}/{total_sensors}",, f"센서상태 : {normal_sensors}/{total_sensors}")
        self.healthLabel.setPixmap(pixmap)

    def create_health_circle(self, size: int, color: QColor, text: str, sensor_sub_text: str, motor_sub_text: str) -> QPixmap:
        """주어진 색상과 텍스트로 원형 QPixmap을 생성합니다."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, size, size)
        
        painter.setPen(QColor("white"))
        
        font_main = QFont("Arial", 15, QFont.Weight.Bold)
        painter.setFont(font_main)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)

        font_sub = QFont("Arial", 10)
        painter.setFont(font_sub)
        rect_sub = pixmap.rect().adjusted(0, 25, 0, 25)
        # rect_sub = pixmap.rect().adjusted(0, size // 4, 0, 0)
        painter.drawText(rect_sub, Qt.AlignmentFlag.AlignCenter, sensor_sub_text)

        rect_sub = pixmap.rect().adjusted(0, 40, 0, 40)
        # rect_sub = pixmap.rect().adjusted(0, size // 4, 0, 0)
        painter.drawText(rect_sub, Qt.AlignmentFlag.AlignCenter, motor_sub_text)

        painter.end()
        return pixmap

    # draw_toggle_status_button 메소드와 각 구역 for문 순회를 이용해 모든 on/off 토글 스위치 그리기
    def draw_all_buttons(self):
        # 그리는 형식
        # self.draw_toggle_status_button(20, 8, "Off")
        
        '''
        robot_status(QFrame) 아래의 모든 모터/센서 QPushButton
        r_status(QFrame) 아래의 모든 모터/센서 QPushButton
        g_status(QFrame) 아래의 모든 모터/센서 QPushButton
        y_status(QFrame) 아래의 모든 모터/센서 QPushButton
        sh_status(QFrame) 아래의 모든 모터/센서 QPushButton
        1. readonly로 설정 및 상태 업데이트
        '''
        
        
        # # 각 구역마다 순회
        # for sector in self.manager.sectors.values():
        #     # 모터가 없으면 건너뜀
        #     if not sector.motors:
        #         continue
            
        #     for sensor in sector.motors.values():
                
        pass


    def update_state(self):
        """모든 모터 및 센서의 UI 상태를 현재 백엔드 상태와 동기화합니다."""
        for (sector_name, comp_type, comp_name), button in self.ui_map.items():
            if comp_type == 'motor':
                status = self.manager.get_sector(sector_name).get_motor_status(comp_name)
                self._update_button_style(button, status)
            elif comp_type == 'sensor':
                status_text = self.sensor_statuses.get(comp_name, "Unknown")
                self._update_button_style(button, status_text)
        
        self._update_sensor_table()

    def _update_sensor_table(self):
        """센서 테이블 위젯을 최신 정보로 업데이트합니다."""
        self.tableSensor.setRowCount(0) # 테이블 초기화
        # 수정: self.all_sensors는 이제 (sector_name, sensor_name) 튜플 리스트
        for idx, sensor_instance in enumerate(self.all_sensors):
            status = self.sensor_statuses.get(sensor_instance, "Unknown")
            
            self.tableSensor.insertRow(idx)
            self.tableSensor.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            # 수정: 튜플에서 센서 이름(인덱스 1)만 표시
            sensor_display_name = f"{sensor_instance[1]} ({sensor_instance[0].name[:1]})"
            self.tableSensor.setItem(idx, 1, QTableWidgetItem(sensor_display_name))
            
            status_item = QTableWidgetItem(status)
            if status == "Error":
                status_item.setForeground(QColor("#E74C3C")) # 빨간색
            else:
                status_item.setForeground(QColor("#2ECC71")) # 초록색
            self.tableSensor.setItem(idx, 2, status_item)
            
            # 값은 시뮬레이션이므로 랜덤 값 또는 'N/A'로 표시
            self.tableSensor.setItem(idx, 3, QTableWidgetItem(f"{random.randint(0, 255)}"))

    def _update_button_style(self, button: QPushButton, status):
        """버튼의 텍스트와 스타일을 상태에 따라 변경합니다."""
        font = QFont()
        font.setPointSize(8)
        button.setFont(font)
        
        if status == MotorStatus.ON or status == "Normal":
            button.setText("ON")
            button.setStyleSheet("background-color: #2ECC71; color: white; border-radius: 5px;")
        elif status == "Error":
            button.setText("ERR")
            button.setStyleSheet("background-color: #E74C3C; color: white; border-radius: 5px;")
        else: # MotorStatus.OFF or "Unknown"
            button.setText("OFF")
            # 비활성화된 버튼의 스타일을 명확하게 하기 위해 회색 배경 적용
            button.setStyleSheet("background-color: #BDC3C7; color: #7F8C8D; border-radius: 5px;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = SensorsTab()
    myWindows.show()
    sys.exit(app.exec())