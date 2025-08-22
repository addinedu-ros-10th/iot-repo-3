#!/usr/bin/env python3
"""
물류 센터 메인 실행 파일

GUI와 LMS를 분리한 시스템의 실행 진입점입니다.
- LMS 서버: 비즈니스 로직 처리
- GUI 클라이언트: 데이터 표시만 담당
"""

import sys
import threading
import time
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from LMS.core.lms_server import LMSServer
from GUI.gui_main import StoreWorldMain
from PyQt6.QtWidgets import QApplication


def run_lms_server():
    """LMS 서버를 별도 스레드에서 실행"""
    print("🚀 LMS 서버 시작 중...")
    server = LMSServer(host='localhost', port=9999)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n⌨️ LMS 서버 중단 요청")
        server.stop()
    except Exception as e:
        print(f"❌ LMS 서버 오류: {e}")
        server.stop()


def run_gui_client():
    """GUI 클라이언트 실행"""
    print("🖥️ GUI 클라이언트 시작 중...")
    
    # LMS 서버가 시작될 시간을 주기 위해 잠시 대기
    time.sleep(2)
    
    app = QApplication(sys.argv)
    
    # 메인 윈도우 생성 및 표시
    main_window = StoreWorldMain()
    main_window.setWindowTitle("물류 센터 관리 시스템 (GUI + LMS 분리)")
    main_window.show()
    
    print("✅ GUI 준비 완료 - LMS 서버에 연결 시도 중...")
    
    try:
        return app.exec()
    except KeyboardInterrupt:
        print("\n⌨️ GUI 클라이언트 중단 요청")
        return 0


def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("🏢 물류 센터 관리 시스템")
    print("📊 GUI + LMS 분리 아키텍처")
    print("=" * 70)
    print()
    print("시스템 구성:")
    print("  🖥️  GUI: 데이터 표시 전용 (TCP 클라이언트)")
    print("  🏗️  LMS: 비즈니스 로직 처리 (TCP 서버)")
    print("  📡 통신: TCP 명세서 기반")
    print()
    
    # LMS 서버를 별도 스레드에서 시작
    lms_thread = threading.Thread(target=run_lms_server, daemon=True)
    lms_thread.start()
    
    # GUI 클라이언트 실행 (메인 스레드)
    try:
        exit_code = run_gui_client()
        print("👋 시스템 정상 종료")
        return exit_code
        
    except Exception as e:
        print(f"❌ 시스템 실행 중 오류: {e}")
        return 1


# # 이전 코드를 백업으로 보관
# class SensorStatusWidget_Backup:
#     """
#     물류센터의 한 구역과 센서 상태를 표시하는 커스텀 위젯.
#     구역 이름과 상태를 나타내는 색상 원으로 구성됩니다.
#     """
#     def __init__(self, name, parent=None):
#         super().__init__(parent)
#         self.zone_name = name
#         self.status = 'G'  # 초기 상태는 'G' (사용 가능)
#         self.status_colors = {
#             'G': QColor(80, 200, 80),   # Green: 사용 가능
#             'Y': QColor(255, 193, 7),   # Yellow: 사용 중
#             'R': QColor(220, 53, 69)    # Red: 센서 이상
#         }
#         self.setMinimumSize(200, 150)

#     def setStatus(self, status):
#         """센서의 상태를 업데이트하고 위젯을 다시 그리도록 요청합니다."""
#         if status in self.status_colors:
#             self.status = status
#             self.update()  # paintEvent()를 다시 호출하여 화면을 갱신합니다.

#     def paintEvent(self, event):
#         """위젯의 그래픽 요소를 그립니다."""
#         painter = QPainter(self)
#         painter.setRenderHint(QPainter.RenderHint.Antialiasing)

#         # 위젯 배경 그리기
#         painter.setBrush(QColor(50, 50, 60))
#         painter.setPen(Qt.PenStyle.NoPen)
#         painter.drawRoundedRect(self.rect(), 10, 10)

#         # 센서 상태를 나타내는 원 그리기
#         sensor_color = self.status_colors[self.status]
#         painter.setBrush(sensor_color)
        
#         # 원의 크기와 위치 계산
#         rect_size = self.width() if self.width() < self.height() else self.height()
#         diameter = int(rect_size * 0.4)
#         offset_x = (self.width() - diameter) // 2
#         offset_y = (self.height() - diameter) // 2 - 15  # 라벨을 위한 공간 확보
#         painter.drawEllipse(offset_x, offset_y, diameter, diameter)

#         # 구역 이름 텍스트 그리기
#         painter.setPen(QColor(240, 240, 240))
#         font = QFont("Arial", 12)
#         font.setBold(True)
#         painter.setFont(font)
        
#         text_rect = self.rect().adjusted(0, diameter // 2 + 30, 0, 0)
#         painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.zone_name)


# class LogisticsCenterWindow(QMainWindow):
#     """
#     가상 물류센터의 메인 윈도우.
#     여러 SensorStatusWidget을 그리드 레이아웃으로 배치합니다.
#     """
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("가상 물류센터 센서 모니터링")
#         self.setGeometry(100, 100, 700, 500)

#         # 중앙 위젯 및 레이아웃 설정
#         central_widget = QWidget()
#         self.setCentralWidget(central_widget)
#         self.grid_layout = QGridLayout(central_widget)
#         central_widget.setStyleSheet("background-color: #2c3e50;")

#         # 물류센터 구역 정의
#         self.zones = {
#             "입고 구역": (0, 0),
#             "보관 구역 A": (0, 1),
#             "피킹 구역": (0, 2),
#             "컨베이어 벨트": (1, 0, 1, 2), # 1행 0열부터 1행 2열까지 차지
#             "포장 구역": (1, 2),
#             "출고 구역": (2, 0, 1, 3) # 2행 0열부터 2행 3열까지 차지
#         }
        
#         self.sensor_widgets = {}
#         self._setup_ui()
        
#         # 타이머를 사용하여 주기적으로 센서 상태 업데이트
#         self.timer = QTimer(self)
#         self.timer.timeout.connect(self.update_sensor_statuses)
#         self.timer.start(1500) # 1.5초마다 업데이트

#     def _setup_ui(self):
#         """UI 요소를 생성하고 레이아웃에 배치합니다."""
#         for name, position in self.zones.items():
#             sensor_widget = SensorStatusWidget(name)
#             self.sensor_widgets[name] = sensor_widget
            
#             # 위치 정보에 따라 위젯 배치
#             if len(position) == 2:
#                 self.grid_layout.addWidget(sensor_widget, position[0], position[1])
#             elif len(position) == 4: # (row, col, rowspan, colspan)
#                 self.grid_layout.addWidget(sensor_widget, position[0], position[1], position[2], position[3])

#     def update_sensor_statuses(self):
#         """모든 센서의 상태를 무작위로 업데이트합니다."""
#         statuses = ['G', 'Y', 'R']
#         # 상태별 가중치를 두어 '사용 가능' 상태가 더 자주 나타나도록 설정
#         weights = [0.7, 0.2, 0.1] 
        
#         for name, widget in self.sensor_widgets.items():
#             # 가중치를 적용하여 새로운 상태를 무작위로 선택
#             new_status = random.choices(statuses, weights)[0]
#             widget.setStatus(new_status)


if __name__ == "__main__":
    sys.exit(main())