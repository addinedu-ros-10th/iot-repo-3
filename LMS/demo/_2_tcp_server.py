# LMS TCP 서버 데모

import socket
import threading
import struct
import sys
import os

# config 및 message_protocol 임포트
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import *
from communication.message_protocol import MessageProtocol

class LMSTCPServerDemo:
    """LMS TCP 서버 데모"""
    
    def __init__(self, host='localhost', port=8100):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.clients = {}  # 클라이언트 연결 관리
        self.client_counter = 0
        
        # 가상 재고 데이터
        self.stock_data = {
            'receiving': 0,
            'red_storage': 0,
            'green_storage': 1,
            'yellow_storage': 2,
            'shipping': 3,
            'receiving_total': 150,
            'shipping_total': 87
        }
    
    def start_server(self):
        """서버 시작"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(SERVER_CONFIG['max_connections'])
            
            self.is_running = True
            print(f"✓ LMS TCP 서버 시작: {self.host}:{self.port}")
            print(f"  최대 연결 수: {SERVER_CONFIG['max_connections']}")
            
            # 클라이언트 연결 대기
            while self.is_running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self.client_counter += 1
                    client_id = f"client_{self.client_counter}"
                    
                    print(f"✓ 클라이언트 연결: {client_address} (ID: {client_id})")
                    
                    # 클라이언트별 스레드 생성
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_id, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    
                    self.clients[client_id] = {
                        'socket': client_socket,
                        'address': client_address,
                        'thread': client_thread
                    }
                    
                except socket.error as e:
                    if self.is_running:
                        print(f"✗ 서버 소켓 오류: {e}")
                    break
                    
        except Exception as e:
            print(f"✗ 서버 시작 실패: {e}")
        finally:
            self.stop_server()
    
    def handle_client(self, client_socket, client_id, client_address):
        """클라이언트 처리"""
        try:
            while self.is_running:
                # 메시지 수신 (17바이트)
                data = client_socket.recv(PROTOCOL_CONFIG['message_total_size'])
                
                if not data:
                    print(f"✗ 클라이언트 연결 종료: {client_id}")
                    break
                
                if len(data) != 17:
                    print(f"✗ 잘못된 메시지 크기: {len(data)}바이트 (예상: 17바이트)")
                    continue
                
                # 명령어 파싱
                command = data[:2].decode('ascii').rstrip('\x00')
                command_data = data[2:16]  # 14바이트 데이터
                end_byte = data[16]
                
                if end_byte != 0x0A:  # \n
                    print(f"✗ 잘못된 종료 바이트: 0x{end_byte:02X}")
                    continue
                
                print(f"[{client_id}] 명령 수신: {command}")
                
                # 명령어 처리
                response = self.process_command(command, command_data, client_id)
                
                # 응답 전송
                if response:
                    client_socket.send(response)
                    print(f"[{client_id}] 응답 전송: {len(response)}바이트")
                
        except Exception as e:
            print(f"✗ [{client_id}] 클라이언트 처리 오류: {e}")
        finally:
            client_socket.close()
            if client_id in self.clients:
                del self.clients[client_id]
    
    def process_command(self, command, data, client_id):
        """명령어 처리"""
        try:
            if command == 'RI':
                return self.handle_receive_item(data, client_id)
            elif command == 'SI':
                return self.handle_ship_item(data, client_id)
            elif command == 'RA':
                return self.handle_request_all(data, client_id)
            elif command == 'RH':
                return self.handle_return_home(data, client_id)
            else:
                print(f"✗ [{client_id}] 알 수 없는 명령어: {command}")
                return self.create_error_response(command, 0x02)  # INVALID_CMD
                
        except Exception as e:
            print(f"✗ [{client_id}] 명령어 처리 오류 ({command}): {e}")
            return self.create_error_response(command, 0xFF)  # INTERNAL_ERROR
    
    def handle_receive_item(self, data, client_id):
        """입고 명령 처리 (RI)"""
        try:
            red_count, green_count = struct.unpack('<HH', data[:4])
            print(f"[{client_id}] 입고 요청: RED={red_count}, GREEN={green_count}")
            
            # 재고 업데이트 (시뮬레이션)
            self.stock_data['red_storage'] += red_count
            self.stock_data['green_storage'] += green_count
            self.stock_data['receiving_total'] += red_count + green_count
            
            print(f"  → 재고 업데이트: RED={self.stock_data['red_storage']}, GREEN={self.stock_data['green_storage']}")
            
            # 성공 응답
            return self.create_success_response('RI')
            
        except Exception as e:
            print(f"✗ [{client_id}] 입고 처리 오류: {e}")
            return self.create_error_response('RI', 0x01)  # FAILURE
    
    def handle_ship_item(self, data, client_id):
        """출고 명령 처리 (SI)"""
        try:
            red_count, green_count, yellow_count = struct.unpack('<HHH', data[:6])
            print(f"[{client_id}] 출고 요청: RED={red_count}, GREEN={green_count}, YELLOW={yellow_count}")
            
            # 재고 확인
            if (self.stock_data['red_storage'] >= red_count and 
                self.stock_data['green_storage'] >= green_count and 
                self.stock_data['yellow_storage'] >= yellow_count):
                
                # 재고 차감
                self.stock_data['red_storage'] -= red_count
                self.stock_data['green_storage'] -= green_count
                self.stock_data['yellow_storage'] -= yellow_count
                self.stock_data['shipping_total'] += red_count + green_count + yellow_count
                
                print(f"  → 출고 완료: 남은 재고 R={self.stock_data['red_storage']}, G={self.stock_data['green_storage']}, Y={self.stock_data['yellow_storage']}")
                
                return self.create_success_response('SI')
            else:
                print(f"  → 재고 부족")
                return self.create_error_response('SI', 0x01)  # FAILURE
                
        except Exception as e:
            print(f"✗ [{client_id}] 출고 처리 오류: {e}")
            return self.create_error_response('SI', 0x01)  # FAILURE
    
    def handle_request_all(self, data, client_id):
        """전체 재고 요청 처리 (RA) - AU 응답"""
        try:
            print(f"[{client_id}] 전체 재고 요청")
            
            # AU 데이터 생성 (14바이트)
            au_data = MessageProtocol.pack_stock_data(self.stock_data)
            au_message = MessageProtocol.pack_command('AU', au_data)
            
            print(f"  → AU 응답 전송: {self.stock_data}")
            
            return au_message
            
        except Exception as e:
            print(f"✗ [{client_id}] 재고 요청 처리 오류: {e}")
            return self.create_error_response('RA', 0x01)  # FAILURE
    
    def handle_return_home(self, data, client_id):
        """홈 복귀 명령 처리 (RH)"""
        try:
            success = struct.unpack('<B', data[:1])[0]
            print(f"[{client_id}] 홈 복귀: success={success}")
            
            # 항상 성공으로 처리 (시뮬레이션)
            return self.create_success_response('RH')
            
        except Exception as e:
            print(f"✗ [{client_id}] 홈 복귀 처리 오류: {e}")
            return self.create_error_response('RH', 0x01)  # FAILURE
    
    def create_success_response(self, command):
        """성공 응답 생성"""
        return command.encode('ascii').ljust(2, b'\x00') + b'\x00\n'
    
    def create_error_response(self, command, error_code):
        """오류 응답 생성"""
        return command.encode('ascii').ljust(2, b'\x00') + bytes([error_code]) + b'\n'
    
    def stop_server(self):
        """서버 중지"""
        self.is_running = False
        
        # 클라이언트 연결 종료
        for client_id, client_info in self.clients.items():
            try:
                client_info['socket'].close()
            except:
                pass
        
        # 서버 소켓 종료
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("✓ LMS TCP 서버 중지")
    
    def show_status(self):
        """서버 상태 출력"""
        print(f"\n=== LMS 서버 상태 ===")
        print(f"실행 중: {self.is_running}")
        print(f"연결된 클라이언트: {len(self.clients)}")
        for client_id, client_info in self.clients.items():
            print(f"  - {client_id}: {client_info['address']}")
        
        print(f"\n현재 재고:")
        for sector, count in self.stock_data.items():
            print(f"  {sector}: {count}")

def main():
    """메인 함수"""
    server = LMSTCPServerDemo()
    
    try:
        print("=== LMS TCP 서버 데모 ===")
        print("Ctrl+C로 종료")
        server.start_server()
    except KeyboardInterrupt:
        print("\n사용자 중단")
    finally:
        server.stop_server()

if __name__ == "__main__":
    main()