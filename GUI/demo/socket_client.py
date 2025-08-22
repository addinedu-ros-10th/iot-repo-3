# tcp_client.py
import socket
import struct

def run_client():
    HOST = '127.0.0.1'
    PORT = 9999

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            print(f"[*] 서버({HOST}:{PORT})에 연결되었습니다.")

            # 서버에 보낼 데이터 정의 (II: Item In)
            command = b'II'
            # Item ID는 8바이트로 맞추기 위해 b'\x00' (null)으로 패딩
            item_id = b'ITEM1234'.ljust(8, b'\x00') 
            quantity = 50
            location = 10305 # Zone: 1, Rack: 03, Level: 05
            end_marker = b'\n'
            
            print(f"\n[요청] Command: {command.decode()}, Item ID: {item_id.strip(b'\\x00').decode()}, Quantity: {quantity}, Location: {location}")
            
            # 명세서의 '보내는 형식'에 따라 데이터 패킹
            packet = struct.pack('<2s8sIIc', command, item_id, quantity, location, end_marker)
            
            # 서버에 데이터 전송
            s.sendall(packet)
            print("[전송] 입고 요청 패킷을 서버로 전송했습니다.")
            
            # 서버로부터 응답 수신 (받는 형식 크기: 8 Bytes)
            response = s.recv(8)
            
            if response:
                # 응답 데이터 언패킹
                unpacked_response = struct.unpack('<2sBIc', response)
                
                resp_command = unpacked_response[0]
                resp_status = unpacked_response[1]
                resp_data1 = unpacked_response[2]

                status_str = "성공" if resp_status == 0x01 else "실패"
                
                print("\n[응답] 서버로부터 응답을 수신했습니다.")
                print(f"  - Command: {resp_command.decode()}")
                print(f"  - Status: {hex(resp_status)} ({status_str})")
                print(f"  - 최종 재고 수량: {resp_data1}")

        except ConnectionRefusedError:
            print("[에러] 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        except Exception as e:
            print(f"[에러] 통신 중 에러 발생: {e}")

if __name__ == '__main__':
    run_client()