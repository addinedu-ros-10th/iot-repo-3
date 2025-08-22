import sys
from PyQt6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget, 
    QPushButton, 
    QVBoxLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QSize

# 센서 / 모터 상태를 나타내는
# 위젯을 그리시오. 5개 (QPushButton)
# height = 20
# width = 40
# FontSize = 8


class ToggleSwitchWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 윈도우 기본 설정
        self.setWindowTitle("Toggle Switch Demo (Single File)")
        self.setGeometry(300, 300, 400, 250)

        # 중앙 위젯과 레이아웃 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 토글 버튼 생성 및 설정
        self.toggleButton = QPushButton("ToggleButton")
        self.toggleButton.setMinimumHeight(20) # 버튼의 최소 높이 지정
        
        # 버튼 폰트 설정
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        self.toggleButton.setFont(font)

        # 레이아웃에 버튼 추가
        layout.addWidget(self.toggleButton)
        
        # --- 로직 부분 (이전 코드와 동일) ---

        # 초기 상태를 'OFF' (비정상)으로 설정합니다.
        self.is_on = False 
        
        # 버튼의 'clicked' 시그널을 토글 함수에 연결합니다.
        self.toggleButton.clicked.connect(self.toggle_state)

        # 초기 UI 상태를 업데이트합니다.
        self.update_ui_state()

    def toggle_state(self):
        """버튼이 클릭될 때마다 상태를 반전시킵니다."""
        self.is_on = not self.is_on
        self.update_ui_state()

    def update_ui_state(self):
        """현재 상태에 따라 버튼의 텍스트와 스타일을 업데이트합니다."""
        if self.is_on:
            # ON (정상) 상태일 때
            self.toggleButton.setText("ON")
            # 스타일시트를 사용하여 배경색을 초록색으로, 글자색을 흰색으로 설정합니다.
            self.toggleButton.setStyleSheet("""
                background-color: #28a745; 
                color: white;
                border-radius: 10px;
                border: 1px solid #1e7e34;
            """)
        else:
            # OFF (비정상) 상태일 때
            self.toggleButton.setText("OFF")
            # 스타일시트를 사용하여 배경색을 빨간색으로, 글자색을 흰색으로 설정합니다.
            self.toggleButton.setStyleSheet("""
                background-color: #dc3545;
                color: white;
                border-radius: 10px;
                border: 1px solid #b21f2d;
            """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToggleSwitchWindow()
    window.show()
    sys.exit(app.exec())