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
      error = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
      if error != 0:
        self._is_connected = False
        return False
      return True
    except:
      self._is_connected = False
      return False
  
  def receive_raw(self, buffet_size = 1024) -> bytes:
    