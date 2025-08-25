# TCP 연결/해제 데모

import socket
import time

class TCPConnectionDemo:
    """TCP 연결 관리 데모"""
    
    def __init__(self, host='localhost', port=8100):
        self.host = host
        self.port = port
        self.socket = None
        self._is_connected = False
    
    def connect(self) -> bool:
        """LMS 서버에 연결"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5초 타임아웃
            self.socket.connect((self.host, self.port))
            self._is_connected = True
            print(f"서버 연결 성공: {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"서버 연결 실패: {e}")
            self._is_connected = False
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
    
    def disconnect(self):
        """서버 연결 해제"""
        try:
            if self.socket:
                self.socket.close()
        except Exception as e:
            print(f"연결 해제 중 오류: {e}")
        finally:
            self.socket = None
            self._is_connected = False
            print("서버 연결 해제")
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        if not self._is_connected or not self.socket:
            return False
        
        try:
            # SO_ERROR 옵션으로 소켓 상태 확인
            error = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if error != 0:
                self._is_connected = False
                return False
            return True
        except:
            self._is_connected = False
            return False
    
    def send_raw(self, data: bytes) -> bool:
        """원시 데이터 전송"""
        if not self.is_connected():
            print("서버에 연결되지 않음")
            return False
        
        try:
            self.socket.send(data)
            print(f"데이터 전송: {data.hex()}")
            return True
        except Exception as e:
            print(f"전송 실패: {e}")
            self._is_connected = False
            return False
    
    def receive_raw(self, buffer_size=1024) -> bytes:
        """원시 데이터 수신"""
        if not self.is_connected():
            print("서버에 연결되지 않음")
            return b''
        
        try:
            data = self.socket.recv(buffer_size)
            if data:
                print(f"데이터 수신: {data.hex()}")
            else:
                print("서버에서 연결 종료")
                self._is_connected = False
            return data
        except Exception as e:
            print(f"수신 실패: {e}")
            self._is_connected = False
            return b''
    
    def test_connectivity(self) -> bool:
        """연결 테스트 (간단한 핑)"""
        if not self.is_connected():
            return False
        
        try:
            # 간단한 테스트 메시지 전송
            test_msg = b'TEST\x00' * 3 + b'\n'  # 17바이트 테스트 메시지
            self.socket.send(test_msg)
            
            # 응답 대기 (타임아웃 1초)
            self.socket.settimeout(1.0)
            response = self.socket.recv(4)  # 최소 응답 크기
            self.socket.settimeout(5.0)  # 원래 타임아웃으로 복원
            
            return len(response) > 0
        except:
            return False

'''
if __name__ == "__main__":
    demo = TCPConnectionDemo()
    
    print("=== TCP 연결 테스트 ===")
    
    # 연결 시도
    if demo.connect():
        print(f"연결 상태: {demo.is_connected()}")
        
        # 간단한 데이터 전송 테스트
        test_data = b'RA' + b'\x00' * 14 + b'\n'
        if demo.send_raw(test_data):
            response = demo.receive_raw()
            if response:
                print(f"응답 수신 성공")
            else:
                print("응답 없음")
        
        # 연결 테스트
        print(f"연결 테스트: {demo.test_connectivity()}")
        
        time.sleep(1)
        demo.disconnect()
    else:
        print("연결 테스트 실패 - LMS 서버가 실행 중인지 확인하세요")
    
    print(f"최종 연결 상태: {demo.is_connected()}")
'''