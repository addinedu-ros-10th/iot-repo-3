import threading
import socket
from config import TCP_PROTOCOL_CONFIG

"""

"""
class TCPHandler(threading.Thread):
  def __init__(self):
    # daemon = True 옵션으로 메인 스레드 (lms_main.py)가 종료되면 즉시 종료되도록 설정
    super().__init__(daemon=True)
    self.host = None or TCP_PROTOCOL_CONFIG['host']
    self.port = None or TCP_PROTOCOL_CONFIG['port']
    
    """
    핸들러 클래스에서는 is_running = True인동안 무한 루프로 실행하고, 
    종료시킬 경우에는 외부에서 is_running 플래그를 False로 변경하는
    등의 방법을 사용해서 제어한다.
    """
    self.is_running = False
  
    # 로그
    # print(f"TCP 서버 초기화: {self.host}:{self.port}")
  
  def run(self):
    try:
      # 서버 소켓 설정
      # 소켓 객체 생성 : IPv4로 설정 / 연결 지향 TCP 소켓으로 설정
      self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      # 테스트환경 : SO_REUSEADDR 옵션 활성화
      self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.server_socket.bind((self.host, self.port))
      self.server_socket.listen(TCP_PROTOCOL_CONFIG['max_message'])
      
      # 로그
      # print(f" TCP 서버 시작: {self.host}:{self.port}")
      
      # 핸들러 클래스 상태 변경
      self.is_running = True
      while self.is_running:
        # 연결 대기 반복
        client_socket, client_address = self.server_socket.accept()
        data = self.server_socket.recv(TCP_PROTOCOL_CONFIG['message_size']) # 17바이트 메시지 읽어오기
    
        # 
        if not data:
          break
    
    except Exception as e:
      print(f"TCP 핸들러 처리 오류: {e}")
    finally:
      self.stop() # TCP 핸들러 중지 및 소켓 닫기
  
  def stop(self):
    """서버 중지"""
    self.is_running = False
    
    if self.server_socket:
      try:
        self.server_socket.close() # 소켓 닫기
      except:
        pass
    print(f"TCP 핸들러 종료")