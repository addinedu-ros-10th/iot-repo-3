#!/usr/bin/env python3
"""
LMS (Logistics Management System) 메인 시스템
"""

import sys
import os
import signal
import threading
import time
from datetime import datetime

# config 및 컴포넌트 임포트
# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import SERVER_CONFIG
from LMS.tcp_server import LMSTCPServer
from LMS.inventory_manager import InventoryManager

class LMSMain:
    """LMS 메인 시스템 - 개선된 구조"""
    
    def __init__(self):
        self.name = "Logistics Management System"
        self.version = "1.0.0"
        self.is_running = False
        self.start_time = None
        
        # 컴포넌트들
        self.tcp_server = None
        self.inventory_manager = None
        
        # 모니터링 및 통계
        self.command_stats = {
            'RI': {'count': 0, 'success': 0, 'failure': 0},
            'SI': {'count': 0, 'success': 0, 'failure': 0},
            'RA': {'count': 0, 'success': 0, 'failure': 0},
            'RH': {'count': 0, 'success': 0, 'failure': 0}
        }
        self.client_connections = []
        self.system_alerts = []
        
        # 상태 모니터링 스레드
        self.status_thread = None
        self.is_status_monitoring = False
        
        # 시스템 설정
        self.config = {
            'host': SERVER_CONFIG['host'],
            'port': SERVER_CONFIG['port'],
            'status_report_interval': 30  # 30초마다 상태 보고
        }
        
    def initialize(self):
        """시스템 초기화"""
        print(f"=== {self.name} v{self.version} ===")
        print(f"시스템 초기화 중...")
        print(f"서버 설정: {self.config['host']}:{self.config['port']}")
        
        # 재고 관리자 초기화 (먼저)
        self.inventory_manager = InventoryManager()
        
        # TCP 서버 초기화 (재고 관리자와 연결)
        self.tcp_server = LMSTCPServer(
            host=self.config['host'],
            port=self.config['port'],
            inventory_manager=self.inventory_manager
        )
        
        print("✓ 시스템 초기화 완료")
        return True
    
    def start(self):
        """시스템 시작"""
        if not self.initialize():
            print("✗ 시스템 초기화 실패")
            return False
        
        self.is_running = True
        self.start_time = datetime.now()
        print("✓ LMS 시스템 시작됨")
        
        # TCP 서버 시작
        if self.tcp_server:
            self.tcp_server.start()
        
        # 상태 모니터링 시작
        self.start_status_monitoring()
        
        return True
    
    def stop(self):
        """시스템 중지"""
        print("LMS 시스템 중지 중...")
        self.is_running = False
        
        # 상태 모니터링 중지
        self.stop_status_monitoring()
        
        # TCP 서버 중지
        if self.tcp_server:
            self.tcp_server.stop()
        
        print("✓ LMS 시스템 중지 완료")
    
    def get_status(self):
        """시스템 상태 반환"""
        uptime = None
        if self.start_time:
            uptime = str(datetime.now() - self.start_time)
        
        return {
            'name': self.name,
            'version': self.version,
            'running': self.is_running,
            'uptime': uptime,
            'config': self.config,
            'command_stats': self.command_stats,
            'active_clients': len([c for c in self.client_connections if c.get('action') == 'connected']),
            'total_commands': sum(stats['count'] for stats in self.command_stats.values())
        }
    
    def update_command_stats(self, command: str, success: bool):
        """명령어 실행 통계 업데이트"""
        if command in self.command_stats:
            self.command_stats[command]['count'] += 1
            if success:
                self.command_stats[command]['success'] += 1
            else:
                self.command_stats[command]['failure'] += 1
            
            print(f"[통계] {command} 명령 처리 - {'성공' if success else '실패'}")
    
    def log_client_connection(self, client_id: str, action: str):
        """클라이언트 연결 로그"""
        log_entry = {
            'timestamp': datetime.now(),
            'client_id': client_id,
            'action': action  # 'connected', 'disconnected'
        }
        self.client_connections.append(log_entry)
        
        # 오래된 로그 정리 (최근 100개만 유지)
        if len(self.client_connections) > 100:
            self.client_connections = self.client_connections[-100:]
        
        print(f"[{log_entry['timestamp']}] 클라이언트 {client_id}: {action}")
    
    def add_system_alert(self, level: str, message: str):
        """시스템 알림 추가"""
        alert = {
            'timestamp': datetime.now(),
            'level': level,  # 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
            'message': message
        }
        self.system_alerts.append(alert)
        
        # 오래된 알림 정리 (최근 50개만 유지)
        if len(self.system_alerts) > 50:
            self.system_alerts = self.system_alerts[-50:]
        
        print(f"[ALERT] {level}: {message}")
    
    def start_status_monitoring(self):
        """상태 모니터링 시작"""
        if self.is_status_monitoring:
            return
        
        self.is_status_monitoring = True
        self.status_thread = threading.Thread(
            target=self._status_monitoring_loop, 
            daemon=True
        )
        self.status_thread.start()
        print("✓ 상태 모니터링 시작")
    
    def stop_status_monitoring(self):
        """상태 모니터링 중지"""
        self.is_status_monitoring = False
        if self.status_thread and self.status_thread.is_alive():
            self.status_thread.join(timeout=3)
        print("✓ 상태 모니터링 중지")
    
    def _status_monitoring_loop(self):
        """상태 모니터링 루프"""
        while self.is_status_monitoring and self.is_running:
            try:
                # 상태 보고
                status = self.get_status()
                
                print(f"\n=== LMS 시스템 상태 [{datetime.now().strftime('%H:%M:%S')}] ===")
                print(f"가동시간: {status.get('uptime', 'N/A')}")
                print(f"활성 클라이언트: {status['active_clients']}")
                print(f"총 명령 처리: {status['total_commands']}")
                
                # 명령어 통계
                total_commands = status['total_commands']
                if total_commands > 0:
                    print("명령어 처리 통계:")
                    for cmd, stats in status['command_stats'].items():
                        if stats['count'] > 0:
                            success_rate = (stats['success'] / stats['count']) * 100
                            print(f"  {cmd}: {stats['count']}회 (성공률: {success_rate:.1f}%)")
                
                # 재고 현황
                if self.inventory_manager:
                    stock = self.inventory_manager.get_current_stock()
                    print(f"재고 현황: R={stock['red_storage']}, G={stock['green_storage']}, Y={stock['yellow_storage']}")
                
                time.sleep(self.config['status_report_interval'])
                
            except Exception as e:
                print(f"상태 모니터링 오류: {e}")
                time.sleep(10)

def signal_handler(signum, frame):
    """시그널 핸들러"""
    print(f"\n시그널 {signum} 수신. 시스템 종료 중...")
    if 'lms' in globals():
        lms.stop()
    sys.exit(0)

def main():
    """메인 함수"""
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # LMS 시스템 생성 및 시작
    global lms
    lms = LMSMain()
    
    try:
        if lms.start():
            print("LMS 시스템이 실행 중입니다. Ctrl+C로 종료하세요.")
            
            # 메인 루프 (현재는 대기만)
            while lms.is_running:
                import time
                time.sleep(1)
        else:
            print("✗ LMS 시스템 시작 실패")
            return 1
            
    except KeyboardInterrupt:
        print("\n사용자 중단")
    except Exception as e:
        print(f"✗ 시스템 오류: {e}")
        return 1
    finally:
        lms.stop()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())