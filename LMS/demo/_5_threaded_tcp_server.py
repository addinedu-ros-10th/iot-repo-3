# 스레드 상속 기반 LMS TCP 서버

import socket
import threading
import struct
import sys
import os
import time

# config 및 message_protocol 임포트
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import *
from communication.message_protocol import MessageProtocol

class ClientHandler(threading.Thread):
    """클라이언트 처리 스레드"""
    
    def __init__(self, client_socket, client_id, client_address, server):
        super().__init__(daemon=True)
        self.client_socket = client_socket
        self.client_id = client_id
        self.client_address = client_address
        self.server = server
        self.is_running = True
    
    def run(self):
        """클라이언트 처리 메인 루프"""
        try:
            print(f"✓ 클라이언트 처리 스레드 시작: {self.client_id}")
            
            while self.is_running:
                # 메시지 수신 (17바이트)
                data = self.client_socket.recv(PROTOCOL_CONFIG['message_total_size'])
                
                if not data:
                    print(f"✗ 클라이언트 연결 종료: {self.client_id}")
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
                
                print(f"[{self.client_id}] 명령 수신: {command}")
                
                # 서버의 명령어 처리 호출
                response = self.server.process_command(command, command_data, self.client_id)
                
                # 응답 전송
                if response:
                    self.client_socket.send(response)
                    print(f"[{self.client_id}] 응답 전송: {len(response)}바이트")
                
        except Exception as e:
            print(f"✗ [{self.client_id}] 클라이언트 처리 오류: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """리소스 정리"""
        self.is_running = False
        try:
            self.client_socket.close()
        except:
            pass
        # 서버에서 클라이언트 제거
        self.server.remove_client(self.client_id)
    
    def stop(self):
        """스레드 중지"""
        self.is_running = False

class ThreadedTCPServer(threading.Thread):
    """스레드 상속 기반 TCP 서버"""
    
    def __init__(self, host='localhost', port=8100, inventory_manager=None):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.inventory_manager = inventory_manager
        
        self.server_socket = None
        self.is_running = False
        self.client_handlers = {}  # client_id -> ClientHandler
        self.client_counter = 0
        
        # 재고 관리자가 없으면 가상 데이터 사용
        if not self.inventory_manager:
            self.stock_data = {
                'receiving': 0,
                'red_storage': 15,
                'green_storage': 8,
                'yellow_storage': 12,
                'shipping': 3,
                'receiving_total': 150,
                'shipping_total': 87
            }
    
    def run(self):
        """서버 메인 루프"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(SERVER_CONFIG['max_connections'])
            
            self.is_running = True
            print(f"✓ 스레드 기반 LMS TCP 서버 시작: {self.host}:{self.port}")
            print(f"  최대 연결 수: {SERVER_CONFIG['max_connections']}")
            
            # 클라이언트 연결 대기
            while self.is_running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self.client_counter += 1
                    client_id = f"client_{self.client_counter}"
                    
                    print(f"✓ 클라이언트 연결: {client_address} (ID: {client_id})")
                    
                    # 클라이언트 핸들러 생성 및 시작
                    client_handler = ClientHandler(
                        client_socket, client_id, client_address, self
                    )
                    client_handler.start()
                    
                    self.client_handlers[client_id] = client_handler
                    
                except socket.error as e:
                    if self.is_running:
                        print(f"✗ 서버 소켓 오류: {e}")
                    break
                    
        except Exception as e:
            print(f"✗ 서버 시작 실패: {e}")
        finally:
            self.stop()
    
    def process_command(self, command, data, client_id):
        """명령어 처리 (하위 클래스에서 오버라이드 가능)"""
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
        """입고 명령 처리"""
        try:
            red_count, green_count = struct.unpack('<HH', data[:4])
            print(f"[{client_id}] 입고 요청: RED={red_count}, GREEN={green_count}")
            
            if self.inventory_manager:
                # 실제 재고 관리자 사용
                success = self.inventory_manager.add_items_to_receiving(red_count, green_count)
                if success:
                    return self.create_success_response('RI')
                else:
                    return self.create_error_response('RI', 0x01)
            else:
                # 가상 데이터 업데이트
                self.stock_data['red_storage'] += red_count
                self.stock_data['green_storage'] += green_count
                self.stock_data['receiving_total'] += red_count + green_count
                return self.create_success_response('RI')
                
        except Exception as e:
            print(f"✗ [{client_id}] 입고 처리 오류: {e}")
            return self.create_error_response('RI', 0x01)
    
    def handle_ship_item(self, data, client_id):
        """출고 명령 처리"""
        try:
            red_count, green_count, yellow_count = struct.unpack('<HHH', data[:6])
            print(f"[{client_id}] 출고 요청: RED={red_count}, GREEN={green_count}, YELLOW={yellow_count}")
            
            if self.inventory_manager:
                # 실제 재고 관리자 사용
                success = self.inventory_manager.ship_items(red_count, green_count, yellow_count)
                if success:
                    return self.create_success_response('SI')
                else:
                    return self.create_error_response('SI', 0x01)
            else:
                # 가상 재고 확인 및 차감
                if (self.stock_data['red_storage'] >= red_count and 
                    self.stock_data['green_storage'] >= green_count and 
                    self.stock_data['yellow_storage'] >= yellow_count):
                    
                    self.stock_data['red_storage'] -= red_count
                    self.stock_data['green_storage'] -= green_count
                    self.stock_data['yellow_storage'] -= yellow_count
                    self.stock_data['shipping_total'] += red_count + green_count + yellow_count
                    
                    return self.create_success_response('SI')
                else:
                    return self.create_error_response('SI', 0x01)
                
        except Exception as e:
            print(f"✗ [{client_id}] 출고 처리 오류: {e}")
            return self.create_error_response('SI', 0x01)
    
    def handle_request_all(self, data, client_id):
        """전체 재고 요청 처리"""
        try:
            print(f"[{client_id}] 전체 재고 요청")
            
            if self.inventory_manager:
                # 실제 재고 데이터
                current_stock = self.inventory_manager.get_current_stock()
            else:
                # 가상 재고 데이터
                current_stock = self.stock_data
            
            # AU 응답 생성
            au_data = MessageProtocol.pack_stock_data(current_stock)
            au_message = MessageProtocol.pack_command('AU', au_data)
            
            print(f"  → AU 응답 전송: {current_stock}")
            return au_message
            
        except Exception as e:
            print(f"✗ [{client_id}] 재고 요청 처리 오류: {e}")
            return self.create_error_response('RA', 0x01)
    
    def handle_return_home(self, data, client_id):
        """홈 복귀 명령 처리"""
        try:
            success = struct.unpack('<B', data[:1])[0]
            print(f"[{client_id}] 홈 복귀: success={success}")
            return self.create_success_response('RH')
            
        except Exception as e:
            print(f"✗ [{client_id}] 홈 복귀 처리 오류: {e}")
            return self.create_error_response('RH', 0x01)
    
    def create_success_response(self, command):
        """성공 응답 생성"""
        return command.encode('ascii').ljust(2, b'\x00') + b'\x00\n'
    
    def create_error_response(self, command, error_code):
        """오류 응답 생성"""
        return command.encode('ascii').ljust(2, b'\x00') + bytes([error_code]) + b'\n'
    
    def remove_client(self, client_id):
        """클라이언트 제거"""
        if client_id in self.client_handlers:
            del self.client_handlers[client_id]
            print(f"✓ 클라이언트 제거: {client_id}")
    
    def get_client_count(self):
        """연결된 클라이언트 수 반환"""
        return len(self.client_handlers)
    
    def get_client_list(self):
        """클라이언트 목록 반환"""
        return list(self.client_handlers.keys())
    
    def stop(self):
        """서버 중지"""
        print("✓ 서버 중지 시작...")
        self.is_running = False
        
        # 모든 클라이언트 핸들러 중지
        for client_handler in self.client_handlers.values():
            client_handler.stop()
        
        # 서버 소켓 종료
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("✓ 스레드 기반 TCP 서버 중지 완료")

def main():
    """메인 함수"""
    print("=== 스레드 상속 기반 LMS TCP 서버 데모 ===")
    
    server = ThreadedTCPServer()
    
    try:
        # 서버 시작
        server.start()
        
        print("서버가 백그라운드에서 실행 중입니다.")
        print("명령어:")
        print("  status - 서버 상태")
        print("  clients - 연결된 클라이언트")
        print("  quit - 종료")
        
        # 대화형 모드
        while True:
            try:
                command = input("\nserver> ").strip()
                
                if command == 'quit':
                    break
                elif command == 'status':
                    print(f"서버 실행 중: {server.is_running}")
                    print(f"연결된 클라이언트 수: {server.get_client_count()}")
                elif command == 'clients':
                    clients = server.get_client_list()
                    if clients:
                        print(f"연결된 클라이언트: {', '.join(clients)}")
                    else:
                        print("연결된 클라이언트 없음")
                else:
                    print("알 수 없는 명령어")
                    
            except KeyboardInterrupt:
                break
    
    except KeyboardInterrupt:
        print("\n사용자 중단")
    finally:
        server.stop()
        # 서버 스레드가 종료될 때까지 대기
        if server.is_alive():
            server.join(timeout=2)

if __name__ == "__main__":
    main()