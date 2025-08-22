"""
간단한 GUI TCP 클라이언트

LMS 서버와 통신하여 TCP 명세서에 따른 명령을 전송하고
응답을 받아 GUI에 표시하는 역할만 담당합니다.
"""

import socket
import struct
import threading
import time
from typing import Optional, Callable, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QThread


class TCPResponse:
    """TCP 응답 데이터 클래스"""
    
    def __init__(self, command: str, status: int, data: bytes):
        self.command = command
        self.status = status
        self.data = data
        self.is_success = status == 0x00
        
    def get_stock_data(self) -> Optional[int]:
        """4바이트 재고 데이터를 정수로 변환"""
        if len(self.data) == 4:
            return struct.unpack('>I', self.data)[0]
        return None
    
    def get_all_stock_data(self) -> Optional[Dict[str, int]]:
        """AS 명령어의 20바이트 응답을 파싱"""
        if len(self.data) == 20:
            stocks = struct.unpack('>IIIII', self.data)
            return {
                'receiving': stocks[0],
                'red_storage': stocks[1],
                'green_storage': stocks[2],
                'yellow_storage': stocks[3],
                'shipping': stocks[4]
            }
        return None


class SimpleTCPClient(QThread):
    """
    간단한 TCP 클라이언트 스레드
    
    LMS 서버와 통신하여 명령을 전송하고 응답을 받습니다.
    GUI는 이 클라이언트를 통해서만 데이터를 받아 화면에 표시합니다.
    """
    
    # 시그널 정의
    connected = pyqtSignal(str)  # 연결 상태 메시지
    disconnected = pyqtSignal(str)  # 연결 끊김 메시지
    response_received = pyqtSignal(object)  # TCPResponse 객체
    error_occurred = pyqtSignal(str)  # 오류 메시지
    
    def __init__(self, host: str = 'localhost', port: int = 9999, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.is_running = False
        self.auto_request_all_stock = True  # 자동으로 전체 재고 요청
        self.request_interval = 2.0  # 요청 간격 (초)
        
    def run(self):
        """스레드 실행 - 서버에 연결하고 주기적으로 데이터 요청"""
        self.is_running = True
        
        while self.is_running:
            try:
                # 서버 연결 시도
                self._connect_to_server()
                
                # 연결 성공 후 주기적 데이터 요청
                while self.is_running and self.socket:
                    if self.auto_request_all_stock:
                        self.send_command('AS')  # 전체 재고 요청
                    
                    time.sleep(self.request_interval)
                    
            except Exception as e:
                self.error_occurred.emit(f"통신 오류: {e}")
                self._disconnect()
                
                # 재연결 시도 전 대기
                if self.is_running:
                    time.sleep(3.0)
    
    def _connect_to_server(self):
        """LMS 서버에 연결"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            
            self.connected.emit(f"LMS 서버 연결 성공 ({self.host}:{self.port})")
            
        except Exception as e:
            self.error_occurred.emit(f"서버 연결 실패: {e}")
            self._disconnect()
            raise
    
    def _disconnect(self):
        """서버 연결 끊기"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            finally:
                self.socket = None
                self.disconnected.emit("LMS 서버 연결 끊김")
    
    def send_command(self, command: str, data: bytes = b'\x00\x00\x00\x00') -> bool:
        """
        LMS 서버에 명령어 전송
        
        Args:
            command: 2글자 명령어 ('RS', 'AS', 'RI' 등)
            data: 4바이트 명령 데이터
        
        Returns:
            전송 성공 여부
        """
        if not self.socket or not self.is_running:
            return False
        
        try:
            # TCP 명세서에 따른 요청 패킷 생성
            request = command.encode('ascii') + data + b'\n'
            
            # 요청 전송
            self.socket.sendall(request)
            
            # 응답 수신
            response = self._receive_response()
            if response:
                self.response_received.emit(response)
                return True
            
        except Exception as e:
            self.error_occurred.emit(f"명령 전송 실패: {e}")
            self._disconnect()
        
        return False
    
    def _receive_response(self) -> Optional[TCPResponse]:
        """서버로부터 응답 수신"""
        try:
            # Command (2) + Status (1) 수신
            header = self.socket.recv(3)
            if len(header) != 3:
                return None
            
            command = header[:2].decode('ascii')
            status = header[2]
            
            # 데이터 길이 결정 (명령어별로 다름)
            data_length = self._get_response_data_length(command, status)
            
            # 데이터 수신
            data = b''
            if data_length > 0:
                data = self.socket.recv(data_length)
                if len(data) != data_length:
                    return None
            
            # End byte 수신
            end_byte = self.socket.recv(1)
            if end_byte != b'\n':
                return None
            
            return TCPResponse(command, status, data)
            
        except Exception as e:
            raise Exception(f"응답 수신 오류: {e}")
    
    def _get_response_data_length(self, command: str, status: int) -> int:
        """명령어와 상태에 따른 응답 데이터 길이 반환"""
        if status != 0x00:  # 성공이 아니면 데이터 없음
            return 0
        
        # TCP 명세서에 따른 응답 데이터 길이
        data_lengths = {
            'RS': 4,   # 4바이트 정수
            'SS': 4,   # 4바이트 정수
            'CS': 4,   # 4바이트 정수
            'AS': 20,  # 5개의 4바이트 정수
            'RI': 4,   # 4바이트 정수
            'SI': 0,   # 데이터 없음
            'SO': 0,   # 데이터 없음
        }
        
        return data_lengths.get(command, 0)
    
    def request_receiving_stock(self):
        """RS - 입고 구역 재고 요청"""
        self.send_command('RS')
    
    def request_shipping_stock(self):
        """SS - 출고 구역 재고 요청"""
        self.send_command('SS')
    
    def request_color_stock(self, color_code: int):
        """CS - 특정 색상 재고 요청"""
        data = struct.pack('>I', color_code)
        self.send_command('CS', data)
    
    def request_all_stock(self):
        """AS - 전체 재고 요청"""
        self.send_command('AS')
    
    def request_receive_items(self, quantity: int):
        """RI - 물품 입고 요청"""
        data = struct.pack('>I', quantity)
        self.send_command('RI', data)
    
    def request_ship_item(self, color_code: int):
        """SI - 물품 출고 요청"""
        data = struct.pack('>I', color_code)
        self.send_command('SI', data)
    
    def request_sort_item(self, color_code: int):
        """SO - 물품 분류 요청"""
        data = struct.pack('>I', color_code)
        self.send_command('SO', data)
    
    def set_auto_request(self, enabled: bool, interval: float = 2.0):
        """자동 요청 설정"""
        self.auto_request_all_stock = enabled
        self.request_interval = interval
    
    def stop(self):
        """클라이언트 중지"""
        self.is_running = False
        self._disconnect()
        self.wait()  # 스레드 종료 대기


# 전역 TCP 클라이언트 인스턴스 관리
_tcp_client_instance: Optional[SimpleTCPClient] = None
_tcp_client_lock = threading.Lock()


def get_tcp_client() -> SimpleTCPClient:
    """전역 TCP 클라이언트 인스턴스 반환"""
    global _tcp_client_instance
    
    if _tcp_client_instance is None:
        with _tcp_client_lock:
            if _tcp_client_instance is None:
                _tcp_client_instance = SimpleTCPClient()
    
    return _tcp_client_instance


def start_tcp_client():
    """TCP 클라이언트 시작"""
    client = get_tcp_client()
    if not client.isRunning():
        client.start()


def stop_tcp_client():
    """TCP 클라이언트 중지"""
    global _tcp_client_instance
    if _tcp_client_instance:
        _tcp_client_instance.stop()
        _tcp_client_instance = None