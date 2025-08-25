# LMS 기본 아키텍처 데모

import sys
import os

# config 임포트를 위한 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import *

class LMSArchitectureDemo:
    """LMS 기본 아키텍처 구조 데모"""
    
    def __init__(self):
        self.name = "Logistics Management System"
        self.version = "1.0.0"
        
        # 시스템 구성요소
        self.components = {
            'tcp_server': 'TCP 통신 서버',
            'inventory_manager': '재고 관리자',
            'sector_controller': '구역 제어기', 
            'command_processor': '명령어 처리기',
            'data_manager': '데이터 관리자'
        }
        
        # 지원 명령어
        self.supported_commands = list(COMMANDS.keys())
        
        # 구역 정보
        self.sectors = {
            'receiving': {'name': 'RECEIVING', 'capacity': 0, 'current_stock': 0},
            'red_storage': {'name': 'RED_STORAGE', 'capacity': 3, 'current_stock': 0},
            'green_storage': {'name': 'GREEN_STORAGE', 'capacity': 3, 'current_stock': 0},
            'yellow_storage': {'name': 'YELLOW_STORAGE', 'capacity': 3, 'current_stock': 0},
            'shipping': {'name': 'SHIPPING', 'capacity': 0, 'current_stock': 0}
        }
        
        # 누적 통계
        self.cumulative_stats = {
            'total_received': 0,
            'total_shipped': 0,
            'total_processed': 0
        }
    
    def show_system_info(self):
        """시스템 정보 출력"""
        print(f"=== {self.name} v{self.version} ===")
        print("\n시스템 구성요소:")
        for component, description in self.components.items():
            print(f"  - {component}: {description}")
        
        print(f"\n지원 명령어: {', '.join(self.supported_commands)}")
        
        print(f"\n네트워크 설정:")
        print(f"  - Host: {SERVER_CONFIG['host']}")
        print(f"  - Port: {SERVER_CONFIG['port']}")
        print(f"  - Max Connections: {SERVER_CONFIG['max_connections']}")
    
    def show_sector_layout(self):
        """구역 배치도 출력"""
        print("\n=== 구역 배치도 ===")
        print("┌─────────────┬─────────────┬─────────────┐")
        print("│  RECEIVING  │ RED_STORAGE │GREEN_STORAGE│")
        print("│   (입고)    │   (빨강)    │   (초록)    │")
        print("├─────────────┼─────────────┼─────────────┤")
        print("│  SHIPPING   │YELLOW_STORAGE│             │")
        print("│   (출고)    │   (노랑)    │             │")
        print("└─────────────┴─────────────┴─────────────┘")
        
        print("\n구역별 정보:")
        for sector_key, sector_info in self.sectors.items():
            name = sector_info['name']
            capacity = sector_info['capacity']
            current = sector_info['current_stock']
            capacity_str = f"{capacity}" if capacity > 0 else "무제한"
            print(f"  {name}: {current}/{capacity_str}")
    
    def show_command_flow(self):
        """명령어 처리 흐름도"""
        print("\n=== 명령어 처리 흐름 ===")
        
        flows = {
            'RI (입고)': [
                "1. GUI → LMS: RI 명령 (RED, GREEN 수량)",
                "2. LMS: RECEIVING 구역에 물품 추가",
                "3. LMS: 색상별 저장구역으로 분류 이동",
                "4. LMS → GUI: 성공/실패 응답"
            ],
            'SI (출고)': [
                "1. GUI → LMS: SI 명령 (R, G, Y 수량)",
                "2. LMS: 저장구역에서 재고 확인",
                "3. LMS: SHIPPING 구역으로 물품 이동",
                "4. LMS → GUI: 성공/실패 응답"
            ],
            'RA/AU (재고조회)': [
                "1. GUI → LMS: RA 명령 (재고 요청)",
                "2. LMS: 전체 구역 재고 수집",
                "3. LMS → GUI: AU 데이터 (14바이트 재고정보)",
                "4. GUI: 화면 업데이트"
            ]
        }
        
        for cmd, steps in flows.items():
            print(f"\n{cmd}:")
            for step in steps:
                print(f"  {step}")
    
    def show_data_structure(self):
        """데이터 구조 설명"""
        print("\n=== 데이터 구조 ===")
        
        print("\n1. 메시지 프로토콜 (17바이트):")
        print("  Command(2B) + Data(14B) + End(1B)")
        
        print("\n2. AU 재고 데이터 (14바이트):")
        au_fields = [
            "RECEIVING 재고 (2B)",
            "RED_STORAGE 재고 (2B)", 
            "GREEN_STORAGE 재고 (2B)",
            "YELLOW_STORAGE 재고 (2B)",
            "SHIPPING 재고 (2B)",
            "RECEIVING 누적 재고 (2B)",
            "SHIPPING 누적 재고 (2B)"
        ]
        for i, field in enumerate(au_fields, 1):
            print(f"  {i}. {field}")
        
        print("\n3. 상태 코드:")
        for code, description in STATUS_CODES.items():
            print(f"  0x{code:02X}: {description}")
    
    def simulate_operation(self):
        """운영 시뮬레이션 예제"""
        print("\n=== 운영 시뮬레이션 예제 ===")
        
        scenarios = [
            {
                'name': '입고 시나리오',
                'steps': [
                    'RI 명령: RED=5, GREEN=3 입고 요청',
                    'RECEIVING 구역에 8개 물품 임시 저장',
                    'AGV가 RED 5개를 RED_STORAGE로 이동',
                    'AGV가 GREEN 3개를 GREEN_STORAGE로 이동',
                    '성공 응답 전송'
                ]
            },
            {
                'name': '출고 시나리오',
                'steps': [
                    'SI 명령: RED=2, GREEN=1, YELLOW=0 출고 요청',
                    '각 저장구역에서 재고 확인',
                    'RED_STORAGE에서 2개, GREEN_STORAGE에서 1개 선택',
                    'AGV가 선택된 물품을 SHIPPING 구역으로 이동',
                    '성공 응답 전송'
                ]
            },
            {
                'name': '실시간 모니터링',
                'steps': [
                    'GUI에서 주기적으로 RA 명령 전송',
                    'LMS가 전체 구역 재고 수집',
                    'AU 데이터로 14바이트 재고 정보 전송',
                    'GUI가 화면 업데이트'
                ]
            }
        ]
        
        for scenario in scenarios:
            print(f"\n{scenario['name']}:")
            for i, step in enumerate(scenario['steps'], 1):
                print(f"  {i}. {step}")
    
    def run_demo(self):
        """전체 데모 실행"""
        self.show_system_info()
        self.show_sector_layout()
        self.show_command_flow()
        self.show_data_structure()
        self.simulate_operation()
        
        print("\n" + "="*50)
        print("LMS 아키텍처 데모 완료")
        print("다음 단계: TCP 서버, 재고 관리자, 명령어 처리기 구현")

if __name__ == "__main__":
    demo = LMSArchitectureDemo()
    demo.run_demo()