"""
LMS 클라이언트 핸들러 - Thread 상속 기반
"""

import threading
import struct
import sys
import os

# config 및 프로토콜 임포트
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import PROTOCOL_CONFIG
from communication.message_protocol import MessageProtocol
from LMS.command_processor import CommandProcessor

class ClientHandler(threading.Thread):
    """클라이언트 연결 처리 스레드"""
    
    def __init__(self, client_socket, client_id, server):
        super().__init__(daemon=True)
        self.client_socket = client_socket
        self.client_id = client_id
        self.server = server
        self.is_running = True
        
        # 명령어 처리기 초기화
        self.command_processor = CommandProcessor(server.inventory_manager)
    
    def run(self):
        """클라이언트 처리 메인 루프"""
        try:
            print(f"클라이언트 핸들러 시작: {self.client_id}")
            
            while self.is_running:
                # 17바이트 메시지 수신
                data = self.client_socket.recv(PROTOCOL_CONFIG['message_total_size'])
                
                if not data:
                    print(f"클라이언트 연결 종료: {self.client_id}")
                    break
                
                if len(data) != 17:
                    print(f"잘못된 메시지 크기: {len(data)}바이트")
                    continue
                
                # 메시지 처리
                response = self.handle_message(data)
                
                # 응답 전송
                if response:
                    self.client_socket.send(response)
                    
        except Exception as e:
            print(f"클라이언트 처리 오류: {e}")
        finally:
            self.cleanup()
    
    def handle_message(self, data):
        """메시지 파싱 및 처리"""
        try:
            # 명령어 파싱
            command = data[:2].decode('ascii').rstrip('\x00')
            command_data = data[2:16]
            end_byte = data[16]
            
            if end_byte != 0x0A:
                print(f"잘못된 종료 바이트: 0x{end_byte:02X}")
                return None
            
            print(f"[{self.client_id}] 명령 수신: {command}")
            
            # 명령어 처리기를 통한 처리
            return self.command_processor.processCommand(command, command_data, self.client_id)
            
        except Exception as e:
            print(f"메시지 처리 오류: {e}")
            return self.create_error_response('ER', 0xFF)
    
    def create_success_response(self, command):
        """성공 응답 생성"""
        return command.encode('ascii').ljust(2, b'\x00') + b'\x00\n'
    
    def create_error_response(self, command, error_code):
        """오류 응답 생성"""
        return command.encode('ascii').ljust(2, b'\x00') + bytes([error_code]) + b'\n'
    
    def cleanup(self):
        """리소스 정리"""
        self.is_running = False
        try:
            self.client_socket.close()
        except:
            pass
        print(f"클라이언트 핸들러 종료: {self.client_id}")