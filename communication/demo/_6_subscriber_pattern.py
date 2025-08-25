# 구독자 패턴 데모

from typing import Dict, Callable, Any, List

class SubscriberPatternDemo:
    """구독자 패턴 관리 데모"""
    
    def __init__(self):
        self.subscribers: Dict[str, Callable] = {}
        self.data_filters: Dict[str, List[str]] = {}  # 탭별 관심 데이터 타입
    
    def register_subscriber(self, tab_name: str, callback: Callable, data_types: List[str] = None):
        """탭별 콜백 등록 (데이터 타입 필터 포함)"""
        self.subscribers[tab_name] = callback
        self.data_filters[tab_name] = data_types or ['ALL']
        print(f"구독자 등록: {tab_name}, 관심 데이터: {data_types}")
    
    def unregister_subscriber(self, tab_name: str):
        """구독자 등록 해제"""
        if tab_name in self.subscribers:
            del self.subscribers[tab_name]
            del self.data_filters[tab_name]
            print(f"구독자 해제: {tab_name}")
    
    def notify_subscribers(self, data_type: str, data: Dict[str, Any]):
        """구독자들에게 데이터 배포 (필터링 적용)"""
        print(f"\n[배포] 데이터 타입: {data_type}")
        
        for tab_name, callback in self.subscribers.items():
            # 데이터 타입 필터링
            interested_types = self.data_filters[tab_name]
            if 'ALL' in interested_types or data_type in interested_types:
                try:
                    print(f"  → {tab_name}에게 전달")
                    callback(data_type, data)
                except Exception as e:
                    print(f"  → {tab_name} 콜백 오류: {e}")
            else:
                print(f"  → {tab_name} 필터링됨 (관심 없는 데이터)")
    
    def get_subscribers(self) -> List[str]:
        """등록된 구독자 목록 반환"""
        return list(self.subscribers.keys())
    
    def simulate_data_event(self, data_type: str, data: Dict[str, Any]):
        """데이터 이벤트 시뮬레이션"""
        print(f"=== 데이터 이벤트 발생: {data_type} ===")
        self.notify_subscribers(data_type, data)

# 탭별 콜백 함수 예제
def main_monitor_callback(data_type: str, data: Dict[str, Any]):
    """MainMonitorTab 콜백"""
    if data_type == 'STOCK_UPDATE':
        print(f"    [MainMonitor] 재고 업데이트: {data}")
    elif data_type == 'SYSTEM_STATUS':
        print(f"    [MainMonitor] 시스템 상태: {data}")

def sensors_tab_callback(data_type: str, data: Dict[str, Any]):
    """SensorsTab 콜백"""
    if data_type == 'SENSOR_DATA':
        print(f"    [SensorsTab] 센서 데이터: {data}")
    elif data_type == 'MOTOR_STATUS':
        print(f"    [SensorsTab] 모터 상태: {data}")

def system_manage_callback(data_type: str, data: Dict[str, Any]):
    """SystemManageTab 콜백"""
    if data_type == 'COMMAND_RESULT':
        print(f"    [SystemManage] 명령 결과: {data}")
    elif data_type == 'CONNECTION_STATUS':
        print(f"    [SystemManage] 연결 상태: {data}")

if __name__ == "__main__":
    demo = SubscriberPatternDemo()
    
    print("=== 구독자 등록 ===")
    
    # 각 탭별로 관심 있는 데이터 타입 지정하여 등록
    demo.register_subscriber('main_monitor', main_monitor_callback, 
                            ['STOCK_UPDATE', 'SYSTEM_STATUS'])
    
    demo.register_subscriber('sensors_tab', sensors_tab_callback,
                            ['SENSOR_DATA', 'MOTOR_STATUS'])
    
    demo.register_subscriber('system_manage', system_manage_callback,
                            ['COMMAND_RESULT', 'CONNECTION_STATUS'])
    
    print(f"\n등록된 구독자: {demo.get_subscribers()}")
    
    print("\n=== 데이터 배포 테스트 ===")
    
    # 재고 업데이트 이벤트 (MainMonitorTab만 수신)
    demo.simulate_data_event('STOCK_UPDATE', {
        'receiving': 10,
        'red_storage': 15,
        'green_storage': 8
    })
    
    # 센서 데이터 이벤트 (SensorsTab만 수신)
    demo.simulate_data_event('SENSOR_DATA', {
        'temperature': 25.3,
        'humidity': 60.5
    })
    
    # 명령 결과 이벤트 (SystemManageTab만 수신)
    demo.simulate_data_event('COMMAND_RESULT', {
        'command': 'RI',
        'status': 'SUCCESS',
        'message': '입고 성공'
    })
    
    # 시스템 상태 이벤트 (MainMonitorTab만 수신)
    demo.simulate_data_event('SYSTEM_STATUS', {
        'lms_connected': True,
        'agv_status': 'READY'
    })
    
    # 관심 없는 데이터 타입 (필터링됨)
    demo.simulate_data_event('UNKNOWN_DATA', {
        'test': 'data'
    })
    
    print("\n=== 구독자 해제 테스트 ===")
    demo.unregister_subscriber('sensors_tab')
    print(f"남은 구독자: {demo.get_subscribers()}")
    
    # 해제된 구독자는 더 이상 데이터를 받지 않음
    demo.simulate_data_event('SENSOR_DATA', {
        'temperature': 26.1
    })