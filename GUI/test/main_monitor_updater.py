"""
MainMonitorTab 싱글톤 업데이트 관리자

TCP 명세서에 따라 MainMonitorTab 인스턴스를 싱글톤 패턴으로 관리하고
재고 데이터를 실시간으로 업데이트하는 모듈입니다.
"""

import threading
import time
from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication

from GUI.tabs.main_monitor import MainMonitorTab
from stw_lib.sector_manager2 import SectorManager, SectorName


class MainMonitorTabSingleton(QObject):
    """
    MainMonitorTab의 싱글톤 인스턴스를 관리하는 클래스
    TCP 명세서에 따른 실시간 데이터 업데이트를 담당합니다.
    """
    
    # 인스턴스 업데이트 시그널
    instance_updated = pyqtSignal(object)  # MainMonitorTab 인스턴스 전달
    data_updated = pyqtSignal(dict)  # 업데이트된 데이터 전달
    
    _instance: Optional['MainMonitorTabSingleton'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'MainMonitorTabSingleton':
        """싱글톤 패턴 구현"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 중복 초기화 방지
        if hasattr(self, '_initialized'):
            return
            
        super().__init__()
        self._initialized = True
        self._monitor_tab: Optional[MainMonitorTab] = None
        self._sector_manager = SectorManager()
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._periodic_update)
        self._last_update_data: Dict[str, Any] = {}
        
    def get_monitor_tab(self) -> Optional[MainMonitorTab]:
        """
        MainMonitorTab 인스턴스를 반환합니다.
        인스턴스가 없으면 새로 생성합니다.
        """
        if self._monitor_tab is None:
            self._create_monitor_tab()
        return self._monitor_tab
    
    def _create_monitor_tab(self) -> None:
        """MainMonitorTab 인스턴스를 생성합니다."""
        if QApplication.instance() is None:
            raise RuntimeError("QApplication이 초기화되지 않았습니다.")
            
        self._monitor_tab = MainMonitorTab()
        self.instance_updated.emit(self._monitor_tab)
        
    def update_stock_data(self, stock_data: Dict[SectorName, int]) -> None:
        """
        TCP 명세서에 따른 재고 데이터를 업데이트합니다.
        
        Args:
            stock_data: 구역별 재고 수량 딕셔너리
                       {SectorName.RECEIVING: 5, SectorName.RED_STORAGE: 3, ...}
        """
        if self._monitor_tab is None:
            return
            
        # 재고 데이터를 리스트 형태로 변환 (TCP 명세서 순서에 맞춤)
        stock_list = [
            stock_data.get(SectorName.RECEIVING, 0),
            stock_data.get(SectorName.RED_STORAGE, 0),
            stock_data.get(SectorName.GREEN_STORAGE, 0),
            stock_data.get(SectorName.YELLOW_STORAGE, 0),
            stock_data.get(SectorName.SHIPPING, 0)
        ]
        
        # MainMonitorTab의 재고 표시 업데이트
        self._monitor_tab.update_stock_display(stock_list)
        
        # 데이터 변경 기록
        self._last_update_data = {
            'timestamp': time.time(),
            'stock_data': stock_data.copy(),
            'total_stock': sum(stock_data.values())
        }
        
        self.data_updated.emit(self._last_update_data)
    
    def update_connection_status(self, status: str) -> None:
        """
        TCP 연결 상태를 업데이트합니다.
        
        Args:
            status: 연결 상태 메시지
        """
        if self._monitor_tab is None:
            return
            
        self._monitor_tab.update_connection_status(status)
    
    def update_sector_status(self, sector_name: SectorName, stock_count: int = None) -> None:
        """
        특정 구역의 상태를 업데이트하고 그래픽을 다시 그립니다.
        
        Args:
            sector_name: 업데이트할 구역 이름
            stock_count: 선택적 재고 수량 (None이면 SectorManager에서 가져옴)
        """
        if self._monitor_tab is None:
            return
            
        # SectorManager에서 구역 정보 가져오기
        sector = self._sector_manager.get_sector(sector_name)
        
        # 재고 수량이 제공된 경우 업데이트
        if stock_count is not None:
            # 재고에 따른 상태 업데이트 로직은 SectorManager에서 처리
            pass
            
        # 그래픽 업데이트
        self._monitor_tab.update_sector(sector)
    
    def start_periodic_updates(self, interval_ms: int = 1000) -> None:
        """
        주기적 업데이트를 시작합니다.
        
        Args:
            interval_ms: 업데이트 간격 (밀리초)
        """
        self._update_timer.start(interval_ms)
    
    def stop_periodic_updates(self) -> None:
        """주기적 업데이트를 중지합니다."""
        self._update_timer.stop()
    
    def _periodic_update(self) -> None:
        """
        주기적으로 호출되는 업데이트 함수
        필요한 경우 추가적인 상태 검사나 데이터 동기화를 수행합니다.
        """
        if self._monitor_tab is None:
            return
            
        # 현재는 TCP 스레드가 자동으로 업데이트하므로 추가 작업 없음
        # 필요시 여기에 추가 로직 구현
        pass
    
    def get_last_update_data(self) -> Dict[str, Any]:
        """마지막 업데이트 데이터를 반환합니다."""
        return self._last_update_data.copy()
    
    def is_instance_created(self) -> bool:
        """MainMonitorTab 인스턴스가 생성되었는지 확인합니다."""
        return self._monitor_tab is not None
    
    def cleanup(self) -> None:
        """
        리소스를 정리합니다.
        애플리케이션 종료 시 호출되어야 합니다.
        """
        self.stop_periodic_updates()
        
        if self._monitor_tab is not None:
            self._monitor_tab.stop_tcp_client()
            self._monitor_tab = None


# 전역 싱글톤 인스턴스 접근 함수들
def get_main_monitor_updater() -> MainMonitorTabSingleton:
    """MainMonitorTabSingleton 인스턴스를 반환합니다."""
    return MainMonitorTabSingleton()


def get_main_monitor_tab() -> Optional[MainMonitorTab]:
    """MainMonitorTab 싱글톤 인스턴스를 반환합니다."""
    updater = get_main_monitor_updater()
    return updater.get_monitor_tab()


def update_monitor_stock_data(stock_data: Dict[SectorName, int]) -> None:
    """
    모니터 탭의 재고 데이터를 업데이트합니다.
    
    Usage:
        update_monitor_stock_data({
            SectorName.RECEIVING: 5,
            SectorName.RED_STORAGE: 3,
            SectorName.GREEN_STORAGE: 2,
            SectorName.YELLOW_STORAGE: 1,
            SectorName.SHIPPING: 0
        })
    """
    updater = get_main_monitor_updater()
    updater.update_stock_data(stock_data)


def update_monitor_connection_status(status: str) -> None:
    """
    모니터 탭의 연결 상태를 업데이트합니다.
    
    Usage:
        update_monitor_connection_status("서버 연결 성공")
    """
    updater = get_main_monitor_updater()
    updater.update_connection_status(status)


# 사용 예제 및 테스트 코드
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 싱글톤 인스턴스 테스트
    updater1 = get_main_monitor_updater()
    updater2 = get_main_monitor_updater()
    
    print(f"싱글톤 확인: {updater1 is updater2}")  # True여야 함
    
    # MainMonitorTab 인스턴스 생성 및 테스트
    monitor_tab = get_main_monitor_tab()
    print(f"MainMonitorTab 인스턴스 생성: {monitor_tab is not None}")
    
    # 재고 데이터 업데이트 테스트
    test_stock_data = {
        SectorName.RECEIVING: 5,
        SectorName.RED_STORAGE: 3,
        SectorName.GREEN_STORAGE: 2,
        SectorName.YELLOW_STORAGE: 1,
        SectorName.SHIPPING: 0
    }
    
    update_monitor_stock_data(test_stock_data)
    update_monitor_connection_status("테스트 연결 성공")
    
    # 마지막 업데이트 데이터 확인
    last_data = updater1.get_last_update_data()
    print(f"마지막 업데이트 데이터: {last_data}")
    
    if monitor_tab:
        monitor_tab.show()
    
    sys.exit(app.exec())