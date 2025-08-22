"""
재고 관리 모듈

TCP 명세서에 따른 구역별 재고 데이터를 관리합니다.
"""

import threading
from enum import Enum
from typing import Dict, Optional


class SectorType(Enum):
    """구역 타입 정의 (TCP 명세서 기준)"""
    RECEIVING = "RECEIVING"        # 입고 구역
    RED_STORAGE = "RED_STORAGE"    # 빨간색 저장 구역
    GREEN_STORAGE = "GREEN_STORAGE"  # 초록색 저장 구역
    YELLOW_STORAGE = "YELLOW_STORAGE"  # 노란색 저장 구역
    SHIPPING = "SHIPPING"          # 출고 구역


class ColorCode(Enum):
    """색상 코드 정의 (TCP 명세서 기준)"""
    RED = 0x01
    GREEN = 0x02
    YELLOW = 0x03


class InventoryManager:
    """
    재고 관리자 클래스
    
    TCP 명세서에 따른 모든 구역의 재고를 관리하고
    물품 이동을 처리합니다.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        # 각 구역별 재고 수량 초기화
        self._inventory: Dict[SectorType, int] = {
            SectorType.RECEIVING: 0,
            SectorType.RED_STORAGE: 0,
            SectorType.GREEN_STORAGE: 0,
            SectorType.YELLOW_STORAGE: 0,
            SectorType.SHIPPING: 0,
        }
        
        # 구역별 최대 용량 설정
        self._max_capacity: Dict[SectorType, int] = {
            SectorType.RECEIVING: 0, # 제한 없음
            SectorType.RED_STORAGE: 3,
            SectorType.GREEN_STORAGE: 3,
            SectorType.YELLOW_STORAGE: 3,
            SectorType.SHIPPING: 0, # 제한 없음
        }
        
        # 누적 입출고 카운터 (CU 명령어용)
        self._cumulative_stock: Dict[SectorType, int] = {
            SectorType.RECEIVING: 0,  # 총 입고 수량
            SectorType.SHIPPING: 0,   # 총 출고 수량
        }
    
    def get_receiving_stock(self) -> int:
        """RS - 입고 구역 재고 조회"""
        with self._lock:
            return self._inventory[SectorType.RECEIVING]
    
    def get_shipping_stock(self) -> int:
        """SS - 출고 구역 재고 조회"""
        with self._lock:
            return self._inventory[SectorType.SHIPPING]
    
    def get_color_storage_stock(self, color_code: int) -> Optional[int]:
        """CS - 특정 색상 저장 구역 재고 조회"""
        try:
            color = ColorCode(color_code)
            sector_map = {
                ColorCode.RED: SectorType.RED_STORAGE,
                ColorCode.GREEN: SectorType.GREEN_STORAGE,
                ColorCode.YELLOW: SectorType.YELLOW_STORAGE,
            }
            
            with self._lock:
                return self._inventory[sector_map[color]]
                
        except ValueError:
            return None  # 잘못된 색상 코드
    
    def get_all_stock(self) -> Dict[SectorType, int]:
        """AI - 모든 구역 재고 조회"""
        with self._lock:
            return self._inventory.copy()
    
    def get_cumulative_stock(self) -> Dict[SectorType, int]:
        """CU - 누적 입출고 재고 조회"""
        with self._lock:
            return self._cumulative_stock.copy()
    
    def receive_items(self, quantity: int) -> tuple[bool, int]:
        """
        RI - 입고 구역으로 물품 입고
        
        Returns:
            (성공 여부, 입고 후 재고 수량)
        """
        with self._lock:
            current_stock = self._inventory[SectorType.RECEIVING]
            max_capacity = self._max_capacity[SectorType.RECEIVING]
            
            if max_capacity == 0:            
                self._inventory[SectorType.RECEIVING] += quantity
                # 누적 입고 수량 업데이트
                self._cumulative_stock[SectorType.RECEIVING] += quantity
                return True, self._inventory[SectorType.RECEIVING]
            elif current_stock + quantity > max_capacity:
                return False, current_stock  # 용량 초과
    
            self._inventory[SectorType.RECEIVING] += quantity
            # 누적 입고 수량 업데이트
            self._cumulative_stock[SectorType.RECEIVING] += quantity
            return True, self._inventory[SectorType.RECEIVING]

    
    def ship_item(self, color_code: int) -> bool:
        """
        SI - 특정 색상 저장 구역에서 출고 구역으로 물품 이동
        
        Returns:
            성공 여부
        """
        try:
            color = ColorCode(color_code)
            sector_map = {
                ColorCode.RED: SectorType.RED_STORAGE,
                ColorCode.GREEN: SectorType.GREEN_STORAGE,
                ColorCode.YELLOW: SectorType.YELLOW_STORAGE,
            }
            
            source_sector = sector_map[color]
            
            with self._lock:
                # 출발지에 재고가 있는지 확인
                if self._inventory[source_sector] <= 0:
                    return False
                
                # 목적지 용량 확인
                if self._inventory[SectorType.SHIPPING] >= self._max_capacity[SectorType.SHIPPING]:
                    return False
                
                # 물품 이동 실행
                self._inventory[source_sector] -= 1
                self._inventory[SectorType.SHIPPING] += 1
                # 누적 출고 수량 업데이트
                self._cumulative_stock[SectorType.SHIPPING] += 1
                return True
                
        except ValueError:
            return False  # 잘못된 색상 코드
    
    def sort_item(self, color_code: int) -> bool:
        """
        SO - 입고 구역에서 특정 색상 저장 구역으로 물품 이동 (데모 명령어)
        
        Returns:
            성공 여부
        """
        try:
            color = ColorCode(color_code)
            sector_map = {
                ColorCode.RED: SectorType.RED_STORAGE,
                ColorCode.GREEN: SectorType.GREEN_STORAGE,
                ColorCode.YELLOW: SectorType.YELLOW_STORAGE,
            }
            
            target_sector = sector_map[color]
            
            with self._lock:
                # 입고 구역에 재고가 있는지 확인
                if self._inventory[SectorType.RECEIVING] <= 0:
                    return False
                
                # 목적지 용량 확인
                if self._inventory[target_sector] >= self._max_capacity[target_sector]:
                    return False
                
                # 물품 이동 실행
                self._inventory[SectorType.RECEIVING] -= 1
                self._inventory[target_sector] += 1
                return True
                
        except ValueError:
            return False  # 잘못된 색상 코드
    
    def set_stock(self, sector: SectorType, quantity: int) -> None:
        """테스트/초기화용 재고 설정"""
        with self._lock:
            if 0 <= quantity <= self._max_capacity[sector]:
                self._inventory[sector] = quantity
    
    def get_capacity_info(self) -> Dict[SectorType, tuple[int, int]]:
        """각 구역의 (현재 재고, 최대 용량) 정보 반환"""
        with self._lock:
            return {
                sector: (stock, self._max_capacity[sector])
                for sector, stock in self._inventory.items()
            }
    
    def reset_all_stock(self) -> None:
        """모든 구역 재고 초기화"""
        with self._lock:
            for sector in self._inventory:
                self._inventory[sector] = 0
    
    def reset_receiving_stock(self) -> None:
        """입고 구역 재고 초기화"""
        with self._lock:
            self._inventory[SectorType.RECEIVING] = 0
    
    def reset_storage_stock(self) -> None:
        """보관 구역 재고 초기화 (R, G, Y)"""
        with self._lock:
            self._inventory[SectorType.RED_STORAGE] = 0
            self._inventory[SectorType.GREEN_STORAGE] = 0
            self._inventory[SectorType.YELLOW_STORAGE] = 0
    
    def reset_shipping_stock(self) -> None:
        """출고 구역 재고 초기화"""
        with self._lock:
            self._inventory[SectorType.SHIPPING] = 0


# 전역 인벤토리 매니저 인스턴스 (싱글톤)
_inventory_manager_instance: Optional[InventoryManager] = None
_inventory_manager_lock = threading.Lock()


def get_inventory_manager() -> InventoryManager:
    """전역 인벤토리 매니저 인스턴스 반환"""
    global _inventory_manager_instance
    
    if _inventory_manager_instance is None:
        with _inventory_manager_lock:
            if _inventory_manager_instance is None:
                _inventory_manager_instance = InventoryManager()
                
                # 초기 데이터 설정
                _inventory_manager_instance.set_stock(SectorType.RECEIVING, 0)
                _inventory_manager_instance.set_stock(SectorType.RED_STORAGE, 0)
                _inventory_manager_instance.set_stock(SectorType.GREEN_STORAGE, 0)
                _inventory_manager_instance.set_stock(SectorType.YELLOW_STORAGE, 0)
                _inventory_manager_instance.set_stock(SectorType.SHIPPING, 0)

                # # 초기 테스트 데이터 설정
                # _inventory_manager_instance.set_stock(SectorType.RECEIVING, 3)
                # _inventory_manager_instance.set_stock(SectorType.RED_STORAGE, 5)
                # _inventory_manager_instance.set_stock(SectorType.GREEN_STORAGE, 2)
                # _inventory_manager_instance.set_stock(SectorType.YELLOW_STORAGE, 4)
                # _inventory_manager_instance.set_stock(SectorType.SHIPPING, 1)
    
    return _inventory_manager_instance