"""
간단한 모니터 탭 (분리된 GUI 버전)

LMS 서버에서 받은 데이터만 표시하는 역할만 담당합니다.
비즈니스 로직은 모두 LMS 서버에서 처리됩니다.
"""

import os
import sys
from PyQt6 import uic, QtGui
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGroupBox
from PyQt6.QtCore import Qt

from ..client.tcp_client import get_tcp_client, TCPResponse


class SimpleMonitorTab(QWidget):
    """
    간단한 모니터 탭 - 데이터 표시 전용
    
    LMS 서버에서 받은 재고 데이터를 화면에 표시하기만 합니다.
    모든 비즈니스 로직은 LMS 서버에서 처리됩니다.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tcp_client = get_tcp_client()
        self.setup_ui()
        self.connect_signals()
        
        # TCP 클라이언트 시작
        if not self.tcp_client.isRunning():
            self.tcp_client.start()
    
    def setup_ui(self):
        """UI 초기화 - 간단한 데이터 표시 레이아웃"""
        layout = QVBoxLayout(self)
        
        # 연결 상태 표시
        self.connection_label = QLabel("연결 상태: 대기 중")
        self.connection_label.setStyleSheet("color: orange; font-weight: bold;")
        layout.addWidget(self.connection_label)
        
        # 재고 정보 표시 그룹
        stock_group = QGroupBox("재고 현황")
        stock_layout = QVBoxLayout(stock_group)
        
        # 각 구역별 재고 라벨
        self.stock_labels = {}
        sectors = [
            ("receiving", "입고 구역"),
            ("red_storage", "빨간색 저장소"),
            ("green_storage", "초록색 저장소"),
            ("yellow_storage", "노란색 저장소"),
            ("shipping", "출고 구역")
        ]
        
        for sector_id, sector_name in sectors:
            label = QLabel(f"{sector_name}: -")
            label.setStyleSheet("font-size: 14px; padding: 5px;")
            self.stock_labels[sector_id] = label
            stock_layout.addWidget(label)
        
        layout.addWidget(stock_group)
        
        # 수동 요청 버튼들
        button_group = QGroupBox("수동 요청")
        button_layout = QHBoxLayout(button_group)
        
        self.refresh_button = QPushButton("전체 재고 새로고침")
        self.refresh_button.clicked.connect(self.request_all_stock)
        button_layout.addWidget(self.refresh_button)
        
        # 간단한 명령 버튼들
        self.receive_button = QPushButton("입고 (5개)")
        self.receive_button.clicked.connect(lambda: self.tcp_client.request_receive_items(5))
        button_layout.addWidget(self.receive_button)
        
        self.ship_red_button = QPushButton("빨간색 출고")
        self.ship_red_button.clicked.connect(lambda: self.tcp_client.request_ship_item(1))
        button_layout.addWidget(self.ship_red_button)
        
        layout.addWidget(button_group)
        
        # 응답 로그 표시
        self.log_label = QLabel("응답 로그: 대기 중...")
        self.log_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; font-family: monospace;")
        self.log_label.setWordWrap(True)
        layout.addWidget(self.log_label)
        
        # 레이아웃 여백 설정
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
    
    def connect_signals(self):
        """TCP 클라이언트 시그널 연결"""
        self.tcp_client.connected.connect(self.on_connected)
        self.tcp_client.disconnected.connect(self.on_disconnected)
        self.tcp_client.response_received.connect(self.on_response_received)
        self.tcp_client.error_occurred.connect(self.on_error)
    
    def on_connected(self, message: str):
        """서버 연결 성공"""
        self.connection_label.setText(f"연결 상태: {message}")
        self.connection_label.setStyleSheet("color: green; font-weight: bold;")
        self.log_label.setText("응답 로그: 서버 연결 성공")
    
    def on_disconnected(self, message: str):
        """서버 연결 끊김"""
        self.connection_label.setText(f"연결 상태: {message}")
        self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        
        # 모든 재고 표시를 초기화
        for label in self.stock_labels.values():
            text = label.text().split(":")[0] + ": -"
            label.setText(text)
    
    def on_response_received(self, response: TCPResponse):
        """서버 응답 수신 - 데이터를 화면에 표시만 함"""
        if not response.is_success:
            self.log_label.setText(f"응답 로그: {response.command} 실패 (상태: {response.status})")
            return
        
        # 명령어별로 데이터 표시
        if response.command == 'AS':  # 전체 재고
            stock_data = response.get_all_stock_data()
            if stock_data:
                self.update_all_stock_display(stock_data)
                self.log_label.setText(f"응답 로그: 전체 재고 업데이트 완료")
        
        elif response.command in ['RS', 'SS', 'CS', 'RI']:  # 단일 재고 데이터
            stock_value = response.get_stock_data()
            if stock_value is not None:
                self.update_single_stock_display(response.command, stock_value)
                self.log_label.setText(f"응답 로그: {response.command} 응답 - {stock_value}개")
        
        elif response.command in ['SI', 'SO']:  # 성공/실패만 있는 명령어
            self.log_label.setText(f"응답 로그: {response.command} 성공")
            # 전체 재고 다시 요청하여 최신 상태 반영
            self.tcp_client.request_all_stock()
    
    def update_all_stock_display(self, stock_data: dict):
        """전체 재고 데이터를 화면에 표시"""
        sector_mapping = {
            'receiving': '입고 구역',
            'red_storage': '빨간색 저장소',
            'green_storage': '초록색 저장소',
            'yellow_storage': '노란색 저장소',
            'shipping': '출고 구역'
        }
        
        for sector_id, count in stock_data.items():
            if sector_id in self.stock_labels:
                sector_name = sector_mapping[sector_id]
                self.stock_labels[sector_id].setText(f"{sector_name}: {count}개")
    
    def update_single_stock_display(self, command: str, value: int):
        """단일 재고 데이터를 화면에 표시"""
        command_mapping = {
            'RS': 'receiving',
            'SS': 'shipping',
            'RI': 'receiving',  # 입고 후 입고 구역 재고
        }
        
        if command in command_mapping:
            sector_id = command_mapping[command]
            if sector_id in self.stock_labels:
                current_text = self.stock_labels[sector_id].text()
                sector_name = current_text.split(":")[0]
                self.stock_labels[sector_id].setText(f"{sector_name}: {value}개")
    
    def on_error(self, error_message: str):
        """오류 발생"""
        self.connection_label.setText("연결 상태: 오류 발생")
        self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        self.log_label.setText(f"응답 로그: 오류 - {error_message}")
    
    def request_all_stock(self):
        """전체 재고 수동 요청"""
        self.tcp_client.request_all_stock()
        self.log_label.setText("응답 로그: 전체 재고 요청 전송...")
    
    def closeEvent(self, event):
        """탭 종료 시 TCP 클라이언트 정리"""
        # 주의: 전역 클라이언트이므로 여기서는 중지하지 않음
        # 메인 윈도우에서 전체적으로 관리해야 함
        event.accept()


# 테스트용 메인 실행
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 간단한 모니터 탭 테스트
    monitor = SimpleMonitorTab()
    monitor.setWindowTitle("Simple Monitor - LMS GUI")
    monitor.resize(500, 400)
    monitor.show()
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("사용자에 의해 중단됨")
    finally:
        # TCP 클라이언트 정리
        from ..client.tcp_client import stop_tcp_client
        stop_tcp_client()