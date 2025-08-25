# 통합 통신 매니저 아키텍처

import socket
import threading
import time
from typing import Dict, Callable, Any

from .message_protocol import MessageProtocol

class ComManager:
  """TCP/IP통신 매니저 구현"""
  
  def __init__(self, host : str = 'localhost', port : int = 8100):
    """
    통신 매니저
    
    Args :
      Host : LMS 서버 호스트 주소
      Port : LMS 서버 포트 번호
    """
    self.host = host
    self.port = port
    self.socket = None
    self.monitoring_thread = None
    self.is_monitoring = False
    self.subscribers = {} # 탭별 콜백 등록
    self.is_connected = False
  
  def connect(self) -> bool:
    """LMS 서버에 연결"""
    try:
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socket.settimeout(5.0)
      self.socket.connect((self.host, self.port))
      self.is_connected = True
      print(f"서버 연결 성공: {self.host}:{self.port}")
      return True
    except Exception as e:
      print(f"서버 연결 실패: {e}")
      self.is_connected = False
      if self.socket:
        self.socket.close()
        self.socket = None
      return False
  
  def disconnect(self):
    """서버 연결 해제"""
    self.stop_monitoring()
    try:
      if self.socket:
        self.socket.close()
    except Exception as e:
      print(f"연결 해제 중 오류: {e}")
    finally:
      self.socket = None
      self.is_connected = False
      print("서버 연결 해제")
  
  def register_subscriber(self, tab_name : str, callback: Callable):
    """각 탭의 데이터 업데이트 콜백 등록"""
    self.subscribers[tab_name] = callback
    print(f"구독자 등록: {tab_name}")
  
  def send_raw_message(self, message: bytes) -> bytes:
    """바이너리 메시지 직접 전송 및 응답 수신"""
    if not self.is_connected:
      print("서버에 연결되지 않음")
      return None
    
    try:
      # 바이너리 메시지 전송
      self.socket.send(message)
      print(f"Raw 메시지 전송: {message.hex()}")
      
      # 응답 수신 (최소 4바이트: Command(2) + Status(1) + End(1))
      response = self.socket.recv(1024)  # 충분한 크기로 수신
      if response:
        print(f"Raw 응답 수신: {response.hex()}")
        return response
      else:
        print("서버 응답 없음")
        return None
        
    except Exception as e:
      print(f"Raw 메시지 전송 실패: {e}")
      self.is_connected = False
      return None

  def send_command(self, command:str, data: Dict[str, Any]):
    """명령어 전송 및 응답 처리"""
    if not self.is_connected:
      return {"success": False, "message" : "서버에 연결되지 않음"}

    try:
      # 명령어별 데이터 패킹
      if command == 'RI':
        msg_data = MessageProtocol.pack_ri_data(data.get('red', 0), data.get('green', 0))
      elif command == 'SI':
        msg_data = MessageProtocol.pack_si_data(data.get('red', 0), data.get('green', 0), data.get('yellow', 0))
      elif command == 'RH':
        msg_data = MessageProtocol.pack_rh_data(data.get('success', False))
      elif command == 'RA':
        msg_data = MessageProtocol.pack_ra_data()
      else:
        return {"success": False, "message": f"지원하지 않는 명령어: {command}"}
      
      # 바이너리 메시지 생성 및 전송
      message = MessageProtocol.pack_command(command, msg_data)
      self.socket.send(message)
      print(f"명령어 전송: {command}, 데이터: {data}")
      
      # 응답 수신 (4바이트 최소 크기)
      response = self.socket.recv(4)
      if response:
        parsed_response = MessageProtocol.unpack_response(response)
        success = parsed_response.get("status") == "SUCCESS"
        return {
          "success": success, 
          "message": parsed_response.get("status", "알 수 없는 상태"),
          "response": parsed_response
        }
      else:
        return {"success": False, "message": "서버 응답 없음"}
        
    except Exception as e:
      print(f"명령어 전송 실패: {e}")
      self.is_connected = False
      return {"success": False, "message": str(e)}
  
  def start_monitoring(self):
    """실시간 데이터 모니터링 시작"""
    if self.is_monitoring:
      print("이미 모니터링 중입니다")
      return
    
    if not self.is_connected:
      print("서버에 연결되지 않음 - 모니터링 시작 불가")
      return
    
    self.is_monitoring = True
    self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
    self.monitoring_thread.start()
    print("실시간 모니터링 시작")
  
  def stop_monitoring(self):
    """모니터링 중지"""
    if not self.is_monitoring:
      return
    
    self.is_monitoring = False
    if self.monitoring_thread and self.monitoring_thread.is_alive():
      self.monitoring_thread.join(timeout=3)
    print("모니터링 중지")
  
  def _monitoring_loop(self):
    """백그라운드 모니터링 루프"""
    print("[모니터링] 백그라운드 스레드 시작")
    
    while self.is_monitoring and self.is_connected:
      try:
        # RA 명령으로 재고 상태 요청
        result = self.send_command('RA', {})
        
        if result.get("success"):
          # AU 응답 수신 대기 (17바이트)
          au_response = self.socket.recv(17)
          
          if len(au_response) >= 17 and au_response[:2] == b'AU':
            stock_data = MessageProtocol.unpack_stock_data(au_response[2:16])
            
            # 구독자들에게 데이터 배포
            notification_data = {
              "command": "AU",
              "timestamp": time.time(),
              "stock_data": stock_data
            }
            
            self._notify_subscribers(notification_data)
          
        time.sleep(2)  # 2초 간격으로 모니터링
        
      except Exception as e:
        print(f"[모니터링] 오류: {e}")
        self.is_connected = False
        break
    
    print("[모니터링] 백그라운드 스레드 종료")
  
  def _notify_subscribers(self, data: Dict[str, Any]):
    """구독자들에게 데이터 전달"""
    for tab_name, callback in self.subscribers.items():
      try:
        callback(data)
      except Exception as e:
        print(f"[모니터링] {tab_name} 콜백 오류: {e}")

# 사용 예제
if __name__ == "__main__":
    def on_data_received(data):
        print(f"데이터 수신: {data}")
    
    # 매니저 생성 및 사용
    comm_manager = ComManager()
    comm_manager.register_subscriber('main_monitor', on_data_received)
    
    # 서버 연결
    if comm_manager.connect():
        # 명령어 테스트
        result = comm_manager.send_command('RI', {'red': 5, 'green': 3})
        print(f"RI 명령 결과: {result}")
        
        # 모니터링 시작
        comm_manager.start_monitoring()
        
        try:
            import time
            time.sleep(10)  # 10초 동안 모니터링 테스트
        except KeyboardInterrupt:
            print("사용자 중단")
        finally:
            comm_manager.disconnect()
    else:
        print("서버 연결 실패")