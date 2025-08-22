import sys
from PyQt6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget, 
    QPushButton, 
    QVBoxLayout,
    QHBoxLayout,
    QLabel
)
from PyQt6.QtGui import QFont
'''

근접센서 3개 - RGY 구역

서보모터 1개 - 1개 로봇

컬러센서 3개 - 1개 로봇 - 1개 입고 - 1개 출고

스탭모터 3개 - RGY구역




로봇 (ESP32) - RGB센서 2개 / 서보모터 1개 / 스탭모터 1개 / DC모터 1개

R / G / Y 구역 - 스탭모터 1개 / 근접센서 1개

출고구역 - 컬러센서 1개
'''
class StatusIndicatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 윈도우 기본 설정
        self.setWindowTitle("센서 / 모터 상태")
        self.setGeometry(300, 300, 320, 150) # 윈도우 크기 조절

        # 중앙 위젯과 전체 레이아웃 (수직)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 상태 표시 위젯들을 담을 레이블과 수평 레이아웃
        status_label = QLabel("실시간 상태 표시")
        main_layout.addWidget(status_label)
        
        button_layout = QHBoxLayout() # 버튼들을 수평으로 나열할 레이아웃
        main_layout.addLayout(button_layout)
        
        # 위젯 이름과 위젯을 저장할 리스트
        self.widget_names = ["센서 1", "센서 2", "센서 3", "모터 1", "모터 2"]
        self.status_buttons = []
        # 각 버튼의 상태를 저장 (False: OFF, True: ON)
        self.button_states = [False] * 5

        # 5개의 버튼을 생성하는 루프
        for i in range(5):
            # 버튼 생성 및 고정 크기/폰트 설정
            button = QPushButton("OFF")
            button.setFixedSize(40, 20) # width=40, height=20
            
            font = QFont()
            font.setPointSize(8) # FontSize=8
            button.setFont(font)
            
            # 버튼 클릭 시 어떤 버튼이 눌렸는지 알기 위해 lambda 사용
            # idx=i 부분은 클로저 문제를 해결하여 각 버튼의 올바른 인덱스를 전달합니다.
            button.clicked.connect(lambda checked, idx=i: self.toggle_state(idx))

            # 생성된 버튼을 리스트와 레이아웃에 추가
            self.status_buttons.append(button)
            button_layout.addWidget(button)

        main_layout.addStretch(1) # 위젯들이 위로 붙도록 스트레치 추가

        # 모든 버튼의 초기 UI 상태 설정
        for i in range(5):
            self.update_ui_state(i)

    def toggle_state(self, index):
        """지정된 인덱스의 버튼 상태를 토글합니다."""
        self.button_states[index] = not self.button_states[index]
        print(f"'{self.widget_names[index]}' 상태 변경 -> {'ON' if self.button_states[index] else 'OFF'}")
        self.update_ui_state(index)

    def update_ui_state(self, index):
        """지정된 인덱스의 버튼 UI(텍스트, 색상)를 업데이트합니다."""
        button = self.status_buttons[index]
        is_on = self.button_states[index]

        if is_on:
            button.setText("ON")
            button.setStyleSheet("""
                background-color: #28a745; 
                color: white;
                border-radius: 5px;
                border: 1px solid #1e7e34;
            """)
        else:
            button.setText("OFF")
            button.setStyleSheet("""
                background-color: #dc3545;
                color: white;
                border-radius: 5px;
                border: 1px solid #b21f2d;
            """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StatusIndicatorWindow()
    window.show()
    sys.exit(app.exec())
