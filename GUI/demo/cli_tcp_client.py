# tcp_client.py
import socket
import struct

HOST, PORT = "localhost", 9999

# --- 사용자 입력 -> 바이너리 데이터 변환 맵 ---
COLOR_NAME_MAP = {
    'RED': b'\x01',
    'GREEN': b'\x02',
    'YELLOW': b'\x03',
}
# --- [수정] 데이터가 필요한 명령어 리스트에 'SO' 추가 ---
COMMANDS_WITH_DATA = ['CS', 'SI', 'RI', 'SO']

# --- 서버 응답 코드 -> 문자열 변환 맵 ---
STATUS_MAP = {
    0x00: "SUCCESS",
    0x01: "FAILURE",
    0x02: "INVALID_CMD",
    0x03: "INVALID_DATA",
}

def parse_user_input(user_input):
    """사용자 입력을 (명령어, 데이터) 튜플로 변환합니다."""
    parts = user_input.strip().upper().split()
    cmd = parts[0]
    
    # 2글자 명령어가 아닌 경우
    if len(cmd) != 2:
        print("오류: 명령어는 두 글자여야 합니다 (예: RS, SI).")
        return None, None
        
    data = b'\x00\x00\x00\x00' # 기본 데이터는 0으로 채움

    if cmd in COMMANDS_WITH_DATA:
        if len(parts) < 2:
            print(f"오류: {cmd} 명령어는 데이터가 필요합니다 (예: {cmd} RED 또는 {cmd} 3).")
            return None, None
        
        arg = parts[1]
        # --- [수정] 'SO' 명령어도 색상 코드를 사용하므로 조건문에 추가 ---
        if cmd in ['CS', 'SI', 'SO']:
            color_code = COLOR_NAME_MAP.get(arg)
            if not color_code:
                print(f"오류: 유효하지 않은 색상입니다. (사용 가능: RED, GREEN, YELLOW)")
                return None, None
            # 4바이트 데이터의 첫 1바이트에 색상 코드 삽입
            data = color_code + b'\x00\x00\x00'
        
        elif cmd == 'RI':
            try:
                quantity = int(arg)
                if quantity <= 0:
                    print("오류: 입고 수량은 0보다 큰 정수여야 합니다.")
                    return None, None
                data = struct.pack('>I', quantity)
            except ValueError:
                print(f"오류: {cmd} 명령어의 인자({arg})는 숫자여야 합니다.")
                return None, None

    return cmd, data

def format_response(cmd, status, data):
    """서버로부터 받은 응답을 사람이 읽기 좋은 형태로 출력합니다."""
    status_str = STATUS_MAP.get(status, "UNKNOWN_STATUS")
    print(f"<-- 응답: Command={cmd}, Status={status_str} ({hex(status)})")

    if status != 0x00: # 실패 시 데이터 처리 안 함
        return

    if cmd in ['RS', 'SS', 'CS', 'RI']:
        stock = struct.unpack('>I', data)[0]
        if cmd == 'RI':
            print(f"    - 입고 후 재고 수량: {stock}")
        else:
            print(f"    - 재고 수량: {stock}")
            
    elif cmd == 'AS':
        stocks = struct.unpack('>IIIII', data)
        print("    - 전체 재고 수량:")
        print(f"      - RECEIVING : {stocks[0]}")
        print(f"      - RED       : {stocks[1]}")
        print(f"      - GREEN     : {stocks[2]}")
        print(f"      - YELLOW    : {stocks[3]}")
        print(f"      - SHIPPING  : {stocks[4]}")
    # --- [수정] SI, SO는 성공 시 별도 데이터가 없으므로 이 블록에서 처리됨 ---
    # SI, SO는 성공 시 별도 데이터 없음

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((HOST, PORT))
            print(f"{HOST}:{PORT} 서버에 연결되었습니다.")
            # --- [수정] 도움말 메시지에 SO 명령어 추가 ---
            print("사용 가능한 명령어: RS, SS, CS [색상], AS, RI [수량], SI [색상], SO [색상]")
            print("예시: CS RED, SI GREEN, RI 3, SO YELLOW")
            print("종료하려면 'exit' 또는 'quit'을 입력하세요.")

            while True:
                user_input = input("명령어 입력 > ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                cmd, data_bytes = parse_user_input(user_input)
                if not cmd:
                    continue

                # 요청 생성 및 전송
                request = cmd.encode('ascii') + data_bytes + b'\n'
                print(f"--> 요청: {request.hex()}")
                sock.sendall(request)

                # 서버 응답 수신 및 처리
                header = sock.recv(3) # Command(2) + Status(1)
                if not header:
                    print("서버와의 연결이 끊어졌습니다.")
                    break
                
                resp_cmd_bytes, status_code = header[:2], header[2]
                resp_cmd = resp_cmd_bytes.decode('ascii')

                # 명령어에 따라 추가 데이터 수신
                data_size = 0
                if status_code == 0x00: # 성공 시에만 데이터 확인
                    if resp_cmd in ['RS', 'SS', 'CS', 'RI']:
                        data_size = 4
                    elif resp_cmd == 'AS':
                        data_size = 20
                
                response_data = b''
                if data_size > 0:
                    response_data = sock.recv(data_size)
                
                # 종료 문자 수신
                end_byte = sock.recv(1)

                format_response(resp_cmd, status_code, response_data)

        except ConnectionRefusedError:
            print("서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        except Exception as e:
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()