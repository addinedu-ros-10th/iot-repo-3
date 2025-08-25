# LMS 통합 데모 - TCP 서버 + 재고 관리자

import sys
import os
import threading
import time

# 데모 모듈들 임포트
sys.path.append(os.path.dirname(__file__))
from _2_tcp_server import LMSTCPServerDemo
from _3_inventory_manager import InventoryManagerDemo

class IntegratedLMSDemo:
    """통합 LMS 데모"""
    
    def __init__(self, host='localhost', port=8100):
        # TCP 서버 (재고 관리자와 연동하도록 수정)
        self.tcp_server = None
        self.inventory_manager = InventoryManagerDemo()
        
        self.host = host
        self.port = port
        self.server_thread = None
        
    def create_integrated_server(self):
        """재고 관리자와 연동된 TCP 서버 생성"""
        class IntegratedTCPServer(LMSTCPServerDemo):
            def __init__(self, inventory_manager, host, port):
                super().__init__(host, port)
                self.inventory = inventory_manager
            
            def handle_receive_item(self, data, client_id):
                """입고 명령 - 실제 재고 관리자와 연동"""
                try:
                    import struct
                    red_count, green_count = struct.unpack('<HH', data[:4])
                    print(f"[{client_id}] 입고 요청: RED={red_count}, GREEN={green_count}")
                    
                    # 실제 재고 관리자를 통한 입고 처리
                    success = self.inventory.add_items_to_receiving(red_count, green_count)
                    
                    if success:
                        return self.create_success_response('RI')
                    else:
                        return self.create_error_response('RI', 0x01)  # FAILURE
                        
                except Exception as e:
                    print(f"✗ [{client_id}] 입고 처리 오류: {e}")
                    return self.create_error_response('RI', 0x01)
            
            def handle_ship_item(self, data, client_id):
                """출고 명령 - 실제 재고 관리자와 연동"""
                try:
                    import struct
                    red_count, green_count, yellow_count = struct.unpack('<HHH', data[:6])
                    print(f"[{client_id}] 출고 요청: RED={red_count}, GREEN={green_count}, YELLOW={yellow_count}")
                    
                    # 실제 재고 관리자를 통한 출고 처리
                    success = self.inventory.ship_items(red_count, green_count, yellow_count)
                    
                    if success:
                        return self.create_success_response('SI')
                    else:
                        return self.create_error_response('SI', 0x01)  # FAILURE
                        
                except Exception as e:
                    print(f"✗ [{client_id}] 출고 처리 오류: {e}")
                    return self.create_error_response('SI', 0x01)
            
            def handle_request_all(self, data, client_id):
                """전체 재고 요청 - 실제 재고 관리자 데이터 사용"""
                try:
                    print(f"[{client_id}] 전체 재고 요청")
                    
                    # 실제 재고 데이터 가져오기
                    from communication.message_protocol import MessageProtocol
                    
                    current_stock = self.inventory.get_current_stock()
                    au_data = MessageProtocol.pack_stock_data(current_stock)
                    au_message = MessageProtocol.pack_command('AU', au_data)
                    
                    print(f"  → AU 응답 전송: {current_stock}")
                    return au_message
                    
                except Exception as e:
                    print(f"✗ [{client_id}] 재고 요청 처리 오류: {e}")
                    return self.create_error_response('RA', 0x01)
        
        return IntegratedTCPServer(self.inventory_manager, self.host, self.port)
    
    def start_server(self):
        """통합 서버 시작"""
        self.tcp_server = self.create_integrated_server()
        
        # 서버를 별도 스레드에서 실행
        self.server_thread = threading.Thread(
            target=self.tcp_server.start_server,
            daemon=True
        )
        self.server_thread.start()
        
        print(f"✓ 통합 LMS 서버 시작됨")
        time.sleep(1)  # 서버 시작 대기
    
    def stop_server(self):
        """통합 서버 중지"""
        if self.tcp_server:
            self.tcp_server.stop_server()
        print("✓ 통합 LMS 서버 중지됨")
    
    def show_system_status(self):
        """시스템 상태 출력"""
        print("\n" + "="*50)
        print("통합 LMS 시스템 상태")
        print("="*50)
        
        # TCP 서버 상태
        if self.tcp_server:
            print(f"TCP 서버: 실행 중 ({self.host}:{self.port})")
            print(f"연결된 클라이언트: {len(self.tcp_server.clients)}")
        else:
            print("TCP 서버: 중지됨")
        
        # 재고 관리자 상태
        current_stock = self.inventory_manager.get_current_stock()
        print(f"\n재고 현황:")
        for sector, count in current_stock.items():
            print(f"  {sector}: {count}")
    
    def run_interactive_mode(self):
        """대화형 모드"""
        print("\n=== 통합 LMS 대화형 모드 ===")
        print("명령어:")
        print("  status - 시스템 상태 출력")
        print("  inventory - 상세 재고 현황")
        print("  receive <red> <green> - 직접 입고")
        print("  ship <red> <green> <yellow> - 직접 출고")
        print("  clients - 연결된 클라이언트 목록")
        print("  quit - 종료")
        print("\n외부에서 CLI 테스트: python communication/cli_test.py")
        
        while True:
            try:
                command = input("\nlms> ").strip().split()
                if not command:
                    continue
                
                if command[0] == 'quit':
                    break
                elif command[0] == 'status':
                    self.show_system_status()
                elif command[0] == 'inventory':
                    self.inventory_manager.show_detailed_status()
                elif command[0] == 'receive' and len(command) >= 3:
                    red = int(command[1])
                    green = int(command[2])
                    self.inventory_manager.add_items_to_receiving(red, green)
                elif command[0] == 'ship' and len(command) >= 4:
                    red = int(command[1])
                    green = int(command[2])
                    yellow = int(command[3])
                    self.inventory_manager.ship_items(red, green, yellow)
                elif command[0] == 'clients':
                    if self.tcp_server:
                        print(f"연결된 클라이언트: {len(self.tcp_server.clients)}")
                        for client_id, client_info in self.tcp_server.clients.items():
                            print(f"  {client_id}: {client_info['address']}")
                    else:
                        print("TCP 서버가 실행되지 않음")
                else:
                    print("알 수 없는 명령어입니다.")
                    
            except ValueError:
                print("숫자를 올바르게 입력해주세요.")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"명령어 처리 오류: {e}")

def main():
    """메인 함수"""
    print("="*60)
    print("통합 LMS 데모 (TCP 서버 + 재고 관리자)")
    print("="*60)
    
    lms = IntegratedLMSDemo()
    
    try:
        # 서버 시작
        lms.start_server()
        
        # 초기 상태 출력
        lms.show_system_status()
        
        # 대화형 모드 실행
        lms.run_interactive_mode()
        
    except KeyboardInterrupt:
        print("\n사용자 중단")
    except Exception as e:
        print(f"시스템 오류: {e}")
    finally:
        lms.stop_server()
        print("통합 LMS 데모 종료")

if __name__ == "__main__":
    main()