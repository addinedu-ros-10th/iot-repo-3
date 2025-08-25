#!/usr/bin/env python3
# ComManager CLI 테스트 도구

import sys
import time
import json
from communication.com_manager import ComManager

class ComManagerCLI:
    """ComManager 명령줄 인터페이스"""
    
    def __init__(self):
        self.com_manager = ComManager()
        self.commands = {
            'connect': self.cmd_connect,
            'disconnect': self.cmd_disconnect,
            'status': self.cmd_status,
            'ri': self.cmd_receive_items,
            'si': self.cmd_ship_items,
            'ra': self.cmd_request_all,
            'rh': self.cmd_return_home,
            'monitor': self.cmd_monitor,
            'help': self.cmd_help,
            'exit': self.cmd_exit
        }
        self.running = True
        
    def cmd_connect(self, args):
        """LMS 서버 연결"""
        host = args[0] if args else 'localhost'
        port = int(args[1]) if len(args) > 1 else 8100
        
        self.com_manager.host = host
        self.com_manager.port = port
        
        if self.com_manager.connect():
            print(f"✓ 서버 연결 성공: {host}:{port}")
            return True
        else:
            print(f"✗ 서버 연결 실패: {host}:{port}")
            return False
    
    def cmd_disconnect(self, args):
        """서버 연결 해제"""
        self.com_manager.disconnect()
        print("✓ 서버 연결 해제")
    
    def cmd_status(self, args):
        """연결 상태 확인"""
        if self.com_manager.is_connected:
            print(f"✓ 연결됨: {self.com_manager.host}:{self.com_manager.port}")
        else:
            print("✗ 연결되지 않음")
    
    def cmd_receive_items(self, args):
        """입고 명령 (RI)"""
        if not self.com_manager.is_connected:
            print("✗ 서버에 연결되지 않음")
            return
        
        try:
            red = int(args[0]) if args else 0
            green = int(args[1]) if len(args) > 1 else 0
            
            result = self.com_manager.send_command('RI', {'red': red, 'green': green})
            
            if result['success']:
                print(f"✓ 입고 성공: RED={red}, GREEN={green}")
                print(f"  서버 응답: {result['response']}")
            else:
                print(f"✗ 입고 실패: {result['message']}")
                
        except (ValueError, IndexError):
            print("사용법: ri <red_count> <green_count>")
            print("예제: ri 5 3")
    
    def cmd_ship_items(self, args):
        """출고 명령 (SI)"""
        if not self.com_manager.is_connected:
            print("✗ 서버에 연결되지 않음")
            return
        
        try:
            red = int(args[0]) if args else 0
            green = int(args[1]) if len(args) > 1 else 0
            yellow = int(args[2]) if len(args) > 2 else 0
            
            result = self.com_manager.send_command('SI', {
                'red': red, 
                'green': green, 
                'yellow': yellow
            })
            
            if result['success']:
                print(f"✓ 출고 성공: RED={red}, GREEN={green}, YELLOW={yellow}")
                print(f"  서버 응답: {result['response']}")
            else:
                print(f"✗ 출고 실패: {result['message']}")
                
        except (ValueError, IndexError):
            print("사용법: si <red_count> <green_count> <yellow_count>")
            print("예제: si 2 1 4")
    
    def cmd_request_all(self, args):
        """전체 재고 요청 (RA)"""
        if not self.com_manager.is_connected:
            print("✗ 서버에 연결되지 않음")
            return
        
        result = self.com_manager.send_command('RA', {})
        
        if result['success']:
            print("✓ 재고 요청 성공")
            print("  AU 응답을 기다리는 중...")
            # AU 응답은 백그라운드 모니터링에서 처리됨
        else:
            print(f"✗ 재고 요청 실패: {result['message']}")
    
    def cmd_return_home(self, args):
        """홈 위치 복귀 (RH)"""
        if not self.com_manager.is_connected:
            print("✗ 서버에 연결되지 않음")
            return
        
        success = args[0].lower() in ['true', '1', 'yes'] if args else True
        
        result = self.com_manager.send_command('RH', {'success': success})
        
        if result['success']:
            print(f"✓ 홈 복귀 명령 성공: success={success}")
            print(f"  서버 응답: {result['response']}")
        else:
            print(f"✗ 홈 복귀 명령 실패: {result['message']}")
    
    def cmd_monitor(self, args):
        """백그라운드 모니터링 시작/중지"""
        if not self.com_manager.is_connected:
            print("✗ 서버에 연결되지 않음")
            return
        
        action = args[0].lower() if args else 'start'
        
        if action == 'start':
            # 콜백 등록
            self.com_manager.register_subscriber('cli_monitor', self.monitor_callback)
            self.com_manager.start_monitoring()
            print("✓ 백그라운드 모니터링 시작")
        elif action == 'stop':
            self.com_manager.stop_monitoring()
            print("✓ 백그라운드 모니터링 중지")
        else:
            print("사용법: monitor [start|stop]")
    
    def monitor_callback(self, data):
        """모니터링 데이터 출력 콜백"""
        if data.get('command') == 'AU':
            stock_data = data.get('stock_data', {})
            print("\n=== 재고 현황 업데이트 ===")
            print(f"입고구역: {stock_data.get('receiving', 0)}")
            print(f"RED 저장: {stock_data.get('red_storage', 0)}")
            print(f"GREEN 저장: {stock_data.get('green_storage', 0)}")
            print(f"YELLOW 저장: {stock_data.get('yellow_storage', 0)}")
            print(f"출고구역: {stock_data.get('shipping', 0)}")
            print(f"누적 입고: {stock_data.get('receiving_total', 0)}")
            print(f"누적 출고: {stock_data.get('shipping_total', 0)}")
            print("=" * 30)
    
    def cmd_help(self, args):
        """도움말 출력"""
        print("\n=== ComManager CLI 테스트 도구 ===")
        print("connect [host] [port]  - LMS 서버 연결 (기본: localhost:8100)")
        print("disconnect             - 서버 연결 해제")
        print("status                 - 연결 상태 확인")
        print("ri <red> <green>       - 입고 명령 (RI)")
        print("si <red> <green> <yellow> - 출고 명령 (SI)")
        print("ra                     - 전체 재고 요청 (RA)")
        print("rh [success]           - 홈 복귀 명령 (RH)")
        print("monitor [start|stop]   - 백그라운드 모니터링")
        print("help                   - 이 도움말")
        print("exit                   - 프로그램 종료")
        print("\n예제:")
        print("  connect")
        print("  ri 5 3")
        print("  si 2 1 4")
        print("  monitor start")
        print("  ra")
        print()
    
    def cmd_exit(self, args):
        """프로그램 종료"""
        if self.com_manager.is_connected:
            self.com_manager.disconnect()
        print("✓ 프로그램 종료")
        self.running = False
    
    def parse_command(self, input_line):
        """명령줄 파싱"""
        parts = input_line.strip().split()
        if not parts:
            return None, []
        return parts[0].lower(), parts[1:]
    
    def run(self):
        """CLI 메인 루프"""
        print("=== ComManager CLI 테스트 도구 ===")
        print("'help' 명령으로 사용법을 확인하세요.")
        print()
        
        while self.running:
            try:
                input_line = input("com> ").strip()
                if not input_line:
                    continue
                
                command, args = self.parse_command(input_line)
                
                if command in self.commands:
                    self.commands[command](args)
                else:
                    print(f"알 수 없는 명령: {command}")
                    print("'help' 명령으로 사용법을 확인하세요.")
                
            except KeyboardInterrupt:
                print("\n프로그램을 종료하시려면 'exit'를 입력하세요.")
            except EOFError:
                break
            except Exception as e:
                print(f"오류 발생: {e}")

def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        # 명령줄 인자로 바로 실행
        cli = ComManagerCLI()
        command_line = ' '.join(sys.argv[1:])
        command, args = cli.parse_command(command_line)
        
        if command in cli.commands:
            cli.commands[command](args)
        else:
            print(f"알 수 없는 명령: {command}")
            cli.cmd_help([])
    else:
        # 대화형 모드
        cli = ComManagerCLI()
        try:
            cli.run()
        except KeyboardInterrupt:
            print("\n프로그램 종료")

if __name__ == "__main__":
    main()