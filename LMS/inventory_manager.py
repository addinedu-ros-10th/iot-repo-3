class InventoryManager:
    # 명령어 전송 기능을 지원하기 위해 생성자 호출시 인자 전달
    def __init__(self, tcp_sencer = None, serial_sender = None):
        self.tcp_sender = tcp_sencer
        self.serial_sender = serial_sender