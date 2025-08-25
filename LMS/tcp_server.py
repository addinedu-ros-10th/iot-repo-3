"""
LMS TCP 서버 - Thread 상속 기반 구현
간단한 기능부터 시작
"""

import socket
import threading
import sys
import os

from config import SERVER_CONFIG, PROTOCOL_CONFIG
from LMS.client_handler import ClientHandler

class LMSTCPServer(threading.Thread):
    """LMS TCP 서버 - Thread 상속"""
    
    def __init__(self, host=None, port=None, inventory_manager=None):
        super().__init__(daemon=True)
        
        self.host = host or SERVER_CONFIG['host']
        self.port = port or SERVER_CONFIG['port']
        self.inventory_manager = inventory_manager
        self.server_socket = None
        self.is_running = False
        self.client_handlers = {}
        self.client_counter = 0
        
        print(f"TCP 서버 초기화: {self.host}:{self.port}")
    
    def run(self):
        """서버 메인 루프"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(SERVER_CONFIG['max_connections'])
            
            self.is_running = True
            print(f"✓ TCP 서버 시작: {self.host}:{self.port}")
            
            # 연결 대기 루프 (현재는 기본 구조만)
            while self.is_running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    print(f"클라이언트 연결: {client_address}")
                    
                    # 클라이언트 핸들러 생성 및 시작
                    self.client_counter += 1
                    client_id = f"client_{self.client_counter}"
                    
                    handler = ClientHandler(client_socket, client_id, self)
                    handler.start()
                    self.client_handlers[client_id] = handler
                    
                except socket.error as e:
                    if self.is_running:
                        print(f"소켓 오류: {e}")
                    break
                    
        except Exception as e:
            print(f"TCP 서버 오류: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """서버 중지"""
        self.is_running = False
        
        # 모든 클라이언트 핸들러 중지
        for handler in self.client_handlers.values():
            handler.cleanup()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print("✓ TCP 서버 중지")