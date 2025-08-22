# tcp_server.py
import socket
import struct
import threading

# 가상 재고 데이터베이스 (딕셔너리)
# key: item_id, value: {'quantity': 수량, 'location': 위치}
inventory = {
    b'ITEM0001': {'quantity': 100, 'location': 10101},
    b'ITEM0002': {'quantity': 50, 'location': 10102},
}

# 상태 코드 정의
STATUS_SUCCESS = 0x01
STATUS_ERROR_INVALID_ITEM = 0x03

def handle_client(conn, addr):
    """
    클라이언트 연결을 처리하는 함수 (스레드에서 실행)
    """
    print(f"[+] {addr} 클라이언트 연결됨.")
    
    try:
        while True:
            # 클라이언트로부터 19바이트 데이터 수신 (명세서의 보내는 형식 크기)
            # Command(2) + Item ID(8) + Data1(4) + Data2(4) + End(1) = 19 Bytes
            data = conn.recv(19)
            if not data:
                print(f"[-] {addr} 클라이언트 연결 끊김 (데이터 없음).")
                break

            # 수신된 데이터 언패킹 (Little-endian, <)
            # 2s: 2바이트 문자열, 8s: 8바이트 문자열, I: 4바이트 부호 없는 정수, c: 1바이트 문자
            unpacked_data = struct.unpack('<2s8sIIc', data)
            
            command = unpacked_data[0]
            item_id = unpacked_data[1].strip(b'\x00') # Null 바이트 제거
            data1 = unpacked_data[2]
            data2 = unpacked_data[3]
            
            print(f"[수신] Command: {command.decode()}, Item ID: {item_id.decode()}, Data1: {data1}, Data2: {data2}")

            # 'II' (Item In, 입고) 명령어 처리
            if command == b'II':
                quantity_in = data1
                location = data2
                
                # 재고 업데이트
                if item_id in inventory:
                    inventory[item_id]['quantity'] += quantity_in
                    inventory[item_id]['location'] = location # 위치 정보 업데이트
                    final_quantity = inventory[item_id]['quantity']
                    status_code = STATUS_SUCCESS
                    print(f"[처리] {item_id.decode()} 입고 완료. 최종 수량: {final_quantity}")
                else:
                    # 재고에 없는 아이템이면 새로 추가
                    inventory[item_id] = {'quantity': quantity_in, 'location': location}
                    final_quantity = quantity_in
                    status_code = STATUS_SUCCESS
                    print(f"[처리] 신규 아이템 {item_id.decode()} 입고. 최종 수량: {final_quantity}")

                # 클라이언트에 보낼 응답 패킷 생성
                # 받는 형식: Command(2) + Status(1) + Data1(4) + End(1) = 8 Bytes
                # B: 1바이트 부호 없는 정수
                response_packet = struct.pack('<2sBIc', command, status_code, final_quantity, b'\n')
                conn.sendall(response_packet)
                print(f"[송신] {item_id.decode()} 입고 처리 결과 전송 완료.")

            # 다른 명령어들(IS, IO 등)에 대한 처리 로직 추가...

    except Exception as e:
        print(f"[에러] {addr} 처리 중 에러 발생: {e}")
    finally:
        conn.close()
        print(f"[-] {addr} 클라이언트 연결 종료.")


def start_server():
    HOST = '127.0.0.1'
    PORT = 9999

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[*] 서버가 {HOST}:{PORT} 에서 대기 중입니다...")

    while True:
        conn, addr = server_socket.accept()
        # 각 클라이언트를 별도의 스레드에서 처리
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()

if __name__ == '__main__':
    start_server()