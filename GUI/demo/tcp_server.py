# tcp_server.py
import socketserver
import struct
from base.sector_manager2 import SectorManager, SectorName, ItemColor, SectorStatus

# --- 상수 정의 ---
HOST, PORT = "localhost", 9999
STATUS_SUCCESS = 0x00
STATUS_FAILURE = 0x01
STATUS_INVALID_CMD = 0x02
STATUS_INVALID_DATA = 0x03

# 색상 코드와 ItemColor Enum 매핑
COLOR_MAP = {
    0x01: ItemColor.RED,
    0x02: ItemColor.GREEN,
    0x03: ItemColor.YELLOW,
}

class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    서버의 요청 핸들러 클래스.
    클라이언트로부터의 연결 및 데이터 수신을 처리합니다.
    """
    # 서버 시작 시 생성된 SectorManager 인스턴스를 공유
    manager = SectorManager()

    def handle(self):
        print(f"클라이언트 접속: {self.client_address[0]}")
        
        try:
            while True:
                # GUI -> LMS 요청 형식: Command(2) + Data(4) + End(1) = 7 Bytes
                data = self.request.recv(7)
                if not data:
                    break

                # 요청 파싱
                cmd_bytes, data_bytes, end_byte = data[:2], data[2:6], data[6:]

                # \n 문자가 아니면 무시
                if end_byte != b'\n':
                    print(f"잘못된 종료 문자 수신: {end_byte}")
                    continue

                cmd = cmd_bytes.decode('ascii')
                print(f"수신: Command='{cmd}', Data={data_bytes.hex()}")

                # 기본 응답 값 초기화
                status_code = STATUS_SUCCESS
                response_data = b''

                # --- 명령어 처리 로직 ---
                if cmd == 'RS':
                    stock = self.manager.get_sector(SectorName.RECEIVING).stock
                    response_data = struct.pack('>I', stock) # 4바이트 정수
                
                elif cmd == 'SS':
                    stock = self.manager.get_sector(SectorName.SHIPPING).stock
                    response_data = struct.pack('>I', stock)

                elif cmd == 'CS':
                    color_code = data_bytes[0]
                    color = COLOR_MAP.get(color_code)
                    if color:
                        sector_name = self.manager._get_storage_sector_name(color)
                        stock = self.manager.get_sector(sector_name).stock
                        response_data = struct.pack('>I', stock)
                    else:
                        status_code = STATUS_INVALID_DATA

                elif cmd == 'AS':
                    stocks = [
                        self.manager.get_sector(SectorName.RECEIVING).stock,
                        self.manager.get_sector(SectorName.RED_STORAGE).stock,
                        self.manager.get_sector(SectorName.GREEN_STORAGE).stock,
                        self.manager.get_sector(SectorName.YELLOW_STORAGE).stock,
                        self.manager.get_sector(SectorName.SHIPPING).stock
                    ]
                    response_data = struct.pack('>IIIII', *stocks) # 5개의 4바이트 정수

                elif cmd == 'RI':
                    try:
                        quantity = struct.unpack('>I', data_bytes)[0]
                        if quantity == 0:
                            status_code = STATUS_INVALID_DATA
                        else:
                            success = True
                            # 요청받은 수량만큼 입고 시도
                            for _ in range(quantity):
                                if not self.manager.receive_new_item():
                                    success = False # 하나라도 실패하면 중단
                                    break
                            
                            if success:
                                # 성공 시, 입고 후 재고 수량 반환
                                stock = self.manager.get_sector(SectorName.RECEIVING).stock
                                response_data = struct.pack('>I', stock)
                            else:
                                status_code = STATUS_FAILURE
                    except struct.error:
                        status_code = STATUS_INVALID_DATA
                
                elif cmd == 'SP': # 참고: 명세서의 SI와 동일한 기능
                    color_code = data_bytes[0]
                    color = COLOR_MAP.get(color_code)
                    if color:
                        if not self.manager.prepare_for_shipping(color):
                            status_code = STATUS_FAILURE
                    else:
                        status_code = STATUS_INVALID_DATA
                
                # --- [수정] SO 명령어 처리 로직 추가 ---
                elif cmd == 'SO':
                    color_code = data_bytes[0]
                    color = COLOR_MAP.get(color_code)
                    if color:
                        if not self.manager.classify_and_store(color):
                            status_code = STATUS_FAILURE
                    else:
                        status_code = STATUS_INVALID_DATA
                
                else:
                    status_code = STATUS_INVALID_CMD

                # --- 응답 생성 및 전송 ---
                status_byte = status_code.to_bytes(1, 'big')
                response = cmd.encode('ascii') + status_byte + response_data + b'\n'
                
                self.request.sendall(response)
                print(f"응답: {response.hex()}")

        except Exception as e:
            print(f"오류 발생: {e}")
        finally:
            print(f"클라이언트 접속 종료: {self.client_address[0]}")


if __name__ == "__main__":
    # SectorManager 인스턴스 생성 및 초기화
    manager = SectorManager()
    manager.initialize_all_sectors()
    # 초기 상태를 AVAILABLE로 변경
    for sector_name in SectorName:
        manager.update_sector_status(sector_name, SectorStatus.AVAILABLE)
    manager.display_all_statuses()

    # MyTCPHandler가 SectorManager 인스턴스를 공유하도록 설정
    MyTCPHandler.manager = manager

    try:
        # ThreadingTCPServer를 사용하여 여러 클라이언트를 동시에 처리
        with socketserver.ThreadingTCPServer((HOST, PORT), MyTCPHandler) as server:
            print(f"TCP 서버 시작 (주소: {HOST}, 포트: {PORT})")
            # 서버를 계속 실행
            server.serve_forever()
    except KeyboardInterrupt:
        print("서버를 종료합니다.")
        server.shutdown()