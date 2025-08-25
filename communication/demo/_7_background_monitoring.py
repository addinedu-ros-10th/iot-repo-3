# 백그라운드 모니터링 데모

import threading
import time
import socket
from typing import Dict, Callable, Any

class BackgroundMonitoringDemo:
    """백그라운드 모니터링 데모"""
    
    def __init__(self, host='localhost', port=8100):
        self.host = host
        self.port = port
        self.socket = None
        self.is_connected = False
        
        # 모니터링 스레드 관리
        self.monitoring_thread = None
        self.is_monitoring = False
        
        # 구독자 관리
        self.subscribers = {}
        
        # 모니터링 주기 (초)
        self.monitoring_interval = 2
    
    def connect(self) -> bool:
        """서버 연결"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            print(f"모니터링 서버 연결: {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"서버 연결 실패: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """서버 연결 해제"""
        self.stop_monitoring()
        if self.socket:
            self.socket.close()
            self.socket = None
        self.is_connected = False
        print("모니터링 서버 연결 해제")
    
    def register_subscriber(self, tab_name: str, callback: Callable):
        """구독자 등록"""
        self.subscribers[tab_name] = callback
        print(f"모니터링 구독자 등록: {tab_name}")
    
    def _send_ra_command(self) -> bool:
        """RA 명령어 전송 (재고 상태 요청)"""
        if not self.is_connected or not self.socket:
            return False
        
        try:
            # RA 명령어: Command(2B) + EmptyData(14B) + End(1B)
            ra_command = b'RA' + b'\x00' * 14 + b'\n'
            self.socket.send(ra_command)
            print("[모니터링] RA 명령 전송")
            return True
        except Exception as e:
            print(f"[모니터링] RA 명령 전송 실패: {e}")
            self.is_connected = False
            return False
    
    def _receive_au_response(self) -> Dict[str, Any]:
        """AU 응답 수신 및 파싱"""
        if not self.is_connected or not self.socket:
            return {}
        
        try:
            # AU 응답 대기 (Command(2B) + StockData(14B) + End(1B))
            response = self.socket.recv(17)
            
            if len(response) >= 17 and response[:2] == b'AU':
                stock_data = response[2:16]  # 14바이트 재고 데이터
                
                # 간단한 재고 데이터 시뮬레이션 (실제로는 struct.unpack 사용)
                import struct
                stock = struct.unpack('<HHHHHHH', stock_data)
                
                parsed_data = {
                    'command': 'AU',
                    'timestamp': time.time(),
                    'stock_data': {
                        'receiving': stock[0],
                        'red_storage': stock[1],
                        'green_storage': stock[2],
                        'yellow_storage': stock[3],
                        'shipping': stock[4],
                        'receiving_total': stock[5],
                        'shipping_total': stock[6]
                    }
                }
                
                print(f"[모니터링] AU 응답 수신: {parsed_data['stock_data']}")
                return parsed_data
            
        except Exception as e:
            print(f"[모니터링] AU 응답 수신 실패: {e}")
            self.is_connected = False
        
        return {}
    
    def _simulate_stock_data(self) -> Dict[str, Any]:
        """실제 서버 없이 재고 데이터 시뮬레이션"""
        import random
        
        return {
            'command': 'AU',
            'timestamp': time.time(),
            'stock_data': {
                'receiving': random.randint(0, 20),
                'red_storage': random.randint(0, 50),
                'green_storage': random.randint(0, 50),
                'yellow_storage': random.randint(0, 50),
                'shipping': random.randint(0, 15),
                'receiving_total': random.randint(100, 200),
                'shipping_total': random.randint(50, 150)
            }
        }
    
    def _notify_subscribers(self, data: Dict[str, Any]):
        """구독자들에게 데이터 전달"""
        for tab_name, callback in self.subscribers.items():
            try:
                callback(data)
            except Exception as e:
                print(f"[모니터링] {tab_name} 콜백 오류: {e}")
    
    def _monitoring_loop(self):
        """백그라운드 모니터링 루프"""
        print("[모니터링] 백그라운드 스레드 시작")
        
        while self.is_monitoring:
            try:
                if self.is_connected:
                    # 실제 서버와 통신
                    if self._send_ra_command():
                        stock_data = self._receive_au_response()
                        if stock_data:
                            self._notify_subscribers(stock_data)
                    else:
                        # 연결 실패시 재연결 시도
                        print("[모니터링] 재연결 시도...")
                        self.connect()
                else:
                    # 서버 없이 시뮬레이션 모드
                    stock_data = self._simulate_stock_data()
                    print(f"[시뮬레이션] 가상 재고 데이터: {stock_data['stock_data']}")
                    self._notify_subscribers(stock_data)
                
                # 설정된 간격으로 대기
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"[모니터링] 루프 오류: {e}")
                time.sleep(self.monitoring_interval)
        
        print("[모니터링] 백그라운드 스레드 종료")
    
    def start_monitoring(self):
        """백그라운드 모니터링 시작"""
        if self.is_monitoring:
            print("이미 모니터링 중입니다")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        print("백그라운드 모니터링 시작")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=3)
        print("백그라운드 모니터링 중지")
    
    def set_monitoring_interval(self, seconds: int):
        """모니터링 주기 설정"""
        self.monitoring_interval = max(1, seconds)  # 최소 1초
        print(f"모니터링 주기 설정: {self.monitoring_interval}초")

# 콜백 함수 예제
def main_monitor_callback(data: Dict[str, Any]):
    """MainMonitorTab 콜백"""
    if data.get('command') == 'AU':
        stock = data['stock_data']
        print(f"    [MainMonitor] 재고 현황 - R:{stock['red_storage']}, G:{stock['green_storage']}, Y:{stock['yellow_storage']}")

def system_status_callback(data: Dict[str, Any]):
    """SystemStatus 콜백"""
    if data.get('command') == 'AU':
        total_stock = sum([
            data['stock_data']['red_storage'],
            data['stock_data']['green_storage'], 
            data['stock_data']['yellow_storage']
        ])
        print(f"    [SystemStatus] 총 저장 재고: {total_stock}개")

if __name__ == "__main__":
    demo = BackgroundMonitoringDemo()
    
    print("=== 백그라운드 모니터링 데모 ===")
    
    # 구독자 등록
    demo.register_subscriber('main_monitor', main_monitor_callback)
    demo.register_subscriber('system_status', system_status_callback)
    
    # 모니터링 주기 설정
    demo.set_monitoring_interval(3)
    
    # 모니터링 시작 (실제 서버 연결 시도, 실패시 시뮬레이션 모드)
    if not demo.connect():
        print("서버 연결 실패 - 시뮬레이션 모드로 동작")
    
    demo.start_monitoring()
    
    try:
        # 10초 동안 모니터링 실행
        print("10초 동안 모니터링 실행...")
        time.sleep(10)
    except KeyboardInterrupt:
        print("\n사용자 중단")
    finally:
        demo.disconnect()
        print("데모 종료")